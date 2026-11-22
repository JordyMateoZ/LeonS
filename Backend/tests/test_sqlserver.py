"""Pruebas de integración del repositorio SQL Server (Fase 6).

Solo se ejecutan si `DB_TEST_URL` está configurada y apunta a `LeonsDB_Test`.
Nunca tocan `LeonsDB`: el fixture verifica el nombre de la base antes de
migrar y sembrar. No hay `DELETE`, `TRUNCATE` ni recreación de la base; los
datos de prueba se crean con valores únicos y, cuando el protocolo lo permite,
se eliminan al final.
"""

from __future__ import annotations

import hashlib
import inspect
import logging
import re
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import case, delete, event, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
logger = logging.getLogger("leons.tests.sqlserver")
if str(RAIZ_BACKEND) not in sys.path:
    sys.path.insert(0, str(RAIZ_BACKEND))

from app.app import create_app
from app.config import Settings, get_settings
from app.data.loader import SeedData, cargar_seed
from app.db import models as db
from app.mapper import mascota_out
from app.db.session import crear_engine
from app.domain import (
    AlertaRescate,
    Favorito,
    FiltroMascotas,
    Mensaje,
    Repositorio,
    Solicitud,
    Usuario,
    ahora_utc,
    ficha_predeterminada,
)
from app.errors import ConflictError, ForbiddenError, TransitorioError, ValidationError
from app.repositories.sqlserver import (
    SqlServerRepository,
    _codigo_transitorio_sqlserver,
    _parsear_fecha,
)
from db.seed import sembrar

from .conftest import autenticar


@pytest.fixture(scope="session")
def ajustes():
    settings = get_settings()
    if not settings.db_test_url:
        pytest.skip("DB_TEST_URL no está configurada; se omiten las pruebas de SQL Server.")
    return settings


@pytest.fixture(scope="session")
def seed(ajustes) -> SeedData:
    return cargar_seed(ajustes.seed_path)


@pytest.fixture(scope="session")
def motor(ajustes):
    engine = crear_engine(ajustes.db_test_url)
    with engine.connect() as conexion:
        nombre = conexion.execute(text("SELECT DB_NAME()")).scalar_one()
    if nombre != "LeonsDB_Test":
        engine.dispose()
        pytest.skip(f"DB_TEST_URL apunta a {nombre!r}; solo se permite LeonsDB_Test.")

    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "-x", "target=test", "upgrade", "head"],
        cwd=str(RAIZ_BACKEND),
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, resultado.stderr
    sembrar(engine, cargar_seed(ajustes.seed_path))
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def repo(motor) -> SqlServerRepository:
    return SqlServerRepository(get_settings().db_test_url)


@pytest.fixture(scope="session")
def cliente_sql(motor, tmp_path_factory) -> TestClient:
    """App HTTP con el repositorio SQL Server apuntando solo a LeonsDB_Test."""
    configuracion = get_settings()
    settings = Settings(
        app_env="test",
        jwt_secret="test-secret-con-mas-de-32-bytes-para-hs256",
        repos_backend="sqlserver",
        db_url=configuracion.db_test_url,
        db_test_url=configuracion.db_test_url,
        seed_path=configuracion.seed_path,
        uploads_dir=tmp_path_factory.mktemp("uploads-sql"),
    )
    with TestClient(create_app(settings)) as cliente:
        yield cliente


def _conteos(engine) -> dict[str, int]:
    tablas = (
        db.Distrito,
        db.Refugio,
        db.RefugioEspecie,
        db.Usuario,
        db.Mascota,
        db.MascotaSalud,
        db.MascotaFoto,
        db.MascotaRasgo,
        db.MascotaHistoria,
        db.MascotaCuidado,
        db.ContenidoPaso,
        db.ContenidoFaq,
        db.Solicitud,
    )
    with engine.connect() as conexion:
        return {
            tabla.__tablename__: conexion.execute(
                select(func.count()).select_from(tabla)
            ).scalar_one()
            for tabla in tablas
        }


def test_base_de_pruebas_es_leonsdb_test(repo):
    with repo.engine.connect() as conexion:
        assert conexion.execute(text("SELECT DB_NAME()")).scalar_one() == "LeonsDB_Test"


def test_repositorio_cumple_el_protocolo(repo):
    esperados = [
        nombre for nombre, _ in inspect.getmembers(Repositorio, inspect.isfunction)
    ]
    assert esperados, "El protocolo Repositorio no expone métodos"
    faltantes = [
        nombre for nombre in esperados if not callable(getattr(repo, nombre, None))
    ]
    assert faltantes == []


def test_seed_es_idempotente(motor, seed):
    antes = _conteos(motor)
    resumen = sembrar(motor, seed)
    despues = _conteos(motor)
    assert antes == despues
    assert all(
        valor == 0 for clave, valor in resumen.items() if not clave.endswith("_existentes")
    )


def test_catalogo_y_refugios(repo, seed):
    mascotas = {mascota.id: mascota for mascota in repo.listar_mascotas()}
    assert set(range(1, 17)) <= set(mascotas)

    lista_refugios = repo.listar_refugios()
    refugios = {refugio.id: refugio for refugio in lista_refugios}
    assert set(refugio.id for refugio in seed.refugios) <= set(refugios)
    # D-035: el listado conserva el orden editorial del seed.
    assert [refugio.id for refugio in lista_refugios] == [
        refugio.id for refugio in seed.refugios
    ]

    for esperado in seed.refugios:
        obtenido = repo.obtener_refugio(esperado.id)
        assert obtenido is not None
        assert obtenido.nombre == esperado.nombre
        assert obtenido.distrito == esperado.distrito
        assert obtenido.direccion == esperado.direccion
        assert obtenido.tipo == esperado.tipo
        assert obtenido.desde == esperado.desde
        assert obtenido.contacto == esperado.contacto
        assert obtenido.cargo == esperado.cargo
        assert obtenido.telefono == esperado.telefono
        assert obtenido.whatsapp == esperado.whatsapp
        assert obtenido.adoptadas == esperado.adoptadas
        assert obtenido.en_acogida == esperado.en_acogida
        assert obtenido.verificado == esperado.verificado
        assert sorted(obtenido.especies) == sorted(esperado.especies)
        assert obtenido.logo == esperado.logo


def test_paridad_de_las_16_mascotas(repo, seed):
    for esperada in seed.mascotas:
        obtenida = repo.obtener_mascota(esperada.id)
        assert obtenida is not None, f"Falta la mascota {esperada.id}"

        assert obtenida.nombre == esperada.nombre
        assert obtenida.nombre_corto == esperada.nombre_corto
        assert obtenida.especie == esperada.especie
        assert obtenida.sexo == esperada.sexo
        assert obtenida.raza == esperada.raza
        assert obtenida.edad_anios == pytest.approx(esperada.edad_anios)
        assert obtenida.tamano == esperada.tamano
        assert obtenida.peso_kg == pytest.approx(esperada.peso_kg)
        assert obtenida.distrito == esperada.distrito
        assert obtenida.lugar == esperada.lugar
        assert obtenida.foto == esperada.foto
        assert obtenida.alt == esperada.alt
        assert obtenida.descripcion == esperada.descripcion
        assert obtenida.etiqueta == esperada.etiqueta
        assert obtenida.etiqueta_icono == esperada.etiqueta_icono
        assert obtenida.etiqueta_clase == esperada.etiqueta_clase
        assert obtenida.urgente == esperada.urgente
        assert obtenida.refugio_id == esperada.refugio_id
        assert obtenida.energia == esperada.energia
        assert obtenida.ficha_id == esperada.ficha_id == ficha_predeterminada(esperada.id)
        assert obtenida.estado == esperada.estado
        # `actualizado_dias` se recalcula contra la fecha actual en SQL Server,
        # así que crece con los días transcurridos desde la siembra. La semilla
        # guarda el valor del día de la exportación: se compara como cota.
        assert obtenida.actualizado_dias >= esperada.actualizado_dias

        # Derivados de `mascota_salud.texto` (D-028), no columnas propias.
        assert obtenida.esterilizado == esperada.esterilizado
        assert obtenida.vacunado == esperada.vacunado

        assert [(item.texto, item.ok) for item in obtenida.salud] == [
            (item.texto, item.ok) for item in esperada.salud
        ]
        assert [(foto.src, foto.alt) for foto in obtenida.galeria] == [
            (foto.src, foto.alt) for foto in esperada.galeria
        ]
        assert [
            (rasgo.icono, rasgo.texto, rasgo.clase, rasgo.icono_clase)
            for rasgo in obtenida.rasgos
        ] == [
            (rasgo.icono, rasgo.texto, rasgo.clase, rasgo.icono_clase)
            for rasgo in esperada.rasgos
        ]


def test_galerias_y_contadores_reportados_en_sql_server(repo):
    """INC-002/004: el repositorio no inventa fotos ni mezcla contadores."""
    mascotas = repo.listar_mascotas()
    refugios = repo.listar_refugios()

    assert len(mascotas) == 16
    assert len([m for m in mascotas if m.galeria]) == 1
    assert len(next(m for m in mascotas if m.id == 1).galeria) == 5
    assert sum(len(m.galeria) for m in mascotas) == 5
    assert all(m.galeria == [] for m in mascotas if m.id != 1)

    assert sum(r.adoptadas for r in refugios) == 702
    assert sum(r.en_acogida for r in refugios) == 96
    assert sum(1 for m in mascotas if m.estado == "adoptada") == 2
    assert sum(1 for m in mascotas if m.estado == "en_acogida") == 2


def test_paridad_de_detalle_historia_cuidados_y_cita(repo, seed):
    assert seed.detalles, "El seed no trae detalles editoriales"
    for mascota_id, esperado in seed.detalles.items():
        obtenido = repo.obtener_detalle(mascota_id)
        assert obtenido is not None, f"Falta el detalle de la mascota {mascota_id}"
        assert obtenido.historia == esperado.historia
        assert obtenido.cuidados == esperado.cuidados
        assert obtenido.cita == esperado.cita
        assert obtenido.rasgos == []


def test_mapper_no_inventa_rasgos_ausentes_en_sql_server(repo):
    """El mapper publica solo los rasgos registrados en `mascota_rasgos`."""
    refugios = {refugio.id: refugio for refugio in repo.listar_refugios()}
    mapeadas = {m.id: mascota_out(m, refugios) for m in repo.listar_mascotas()}

    assert len(mapeadas) == 16
    assert [rasgo.texto for rasgo in mapeadas[1].rasgos] == [
        "Juguetona y cariñosa",
        "Tranquila en interiores",
        "Excelente con niños",
        "Sociable con otros perros",
        "Acostumbrada a paseos con correa",
        "Tolerante con gatos (prueba básica OK)",
    ]
    assert mapeadas[12].rasgos == []
    assert sum(len(item.rasgos) for item in mapeadas.values()) == 6


def test_paridad_de_contenido(repo, seed):
    def normalizar(items):
        claves = ("icono", "titulo", "texto", "nota")
        return [{clave: item.get(clave, "") for clave in claves} for item in items]

    obtenido = repo.obtener_contenido()
    assert obtenido.pasos_adopcion == normalizar(seed.contenido.pasos_adopcion)
    assert obtenido.pasos_refugio == normalizar(seed.contenido.pasos_refugio)
    assert obtenido.requisitos == normalizar(seed.contenido.requisitos)
    assert obtenido.faqs == [
        {"pregunta": faq["pregunta"], "respuesta": faq["respuesta"]}
        for faq in seed.contenido.faqs
    ]


def test_paridad_de_solicitudes_demo(repo, seed):
    por_codigo = {solicitud.codigo: solicitud for solicitud in repo.listar_solicitudes()}
    for esperada in seed.solicitudes:
        obtenida = por_codigo.get(esperada.codigo)
        assert obtenida is not None, f"Falta la solicitud {esperada.codigo}"
        assert obtenida.mascota_id == esperada.mascota_id
        assert obtenida.estado == esperada.estado
        assert obtenida.etapa == esperada.etapa
        assert obtenida.creada_en == esperada.creada_en
        assert obtenida.actualizada_en == esperada.actualizada_en

        if esperada.cita is not None:
            assert obtenida.cita is not None
            assert obtenida.cita.fecha == esperada.cita.fecha
            assert obtenida.cita.direccion == esperada.cita.direccion
            assert obtenida.cita.coordinadora == esperada.cita.coordinadora
        else:
            assert obtenida.cita is None

        if esperada.mensaje is not None:
            assert obtenida.mensaje is not None
            assert obtenida.mensaje.texto == esperada.mensaje.texto
            assert obtenida.mensaje.nombre == esperada.mensaje.nombre
        else:
            assert obtenida.mensaje is None


def test_usuarios_demo_por_correo_y_dni(repo, seed):
    for esperado in seed.usuarios:
        por_correo = repo.buscar_usuario_por_email(esperado.email)
        assert por_correo is not None
        assert por_correo.nombre == esperado.nombre
        assert por_correo.rol == esperado.rol
        assert por_correo.dni == esperado.dni
        assert por_correo.refugio_id == esperado.refugio_id

        por_dni = repo.buscar_usuario_por_dni(esperado.dni)
        assert por_dni is not None and por_dni.id == por_correo.id

        assert repo.obtener_usuario(por_correo.id) is not None


def test_registro_y_perfil_con_sql_server(cliente_sql, repo):
    """A-01: el JWT de un registro nace del id real devuelto por SQL Server."""
    sufijo = uuid.uuid4().hex[:8]
    correo = f"registro-{sufijo}@example.com"
    dni = str(uuid.uuid4().int % 90_000_000 + 10_000_000)

    try:
        registro = cliente_sql.post(
            "/api/v1/auth/registro",
            json={
                "nombre": "Regreso Prueba",
                "email": correo,
                "dni": dni,
                "password": "claveSegura1",
            },
        )
        assert registro.status_code == 201, registro.text
        datos = registro.json()
        assert datos["usuario"]["id"] > 0

        perfil = cliente_sql.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {datos['token']}"},
        )
        assert perfil.status_code == 200, perfil.text
        assert perfil.json()["id"] == datos["usuario"]["id"]
    finally:
        with repo.engine.begin() as conexion:
            assert conexion.execute(text("SELECT DB_NAME()")).scalar_one() == "LeonsDB_Test"
            conexion.execute(delete(db.Usuario).where(db.Usuario.email == correo))


def test_registro_publico_no_eleva_roles_con_sql_server(motor, cliente_sql, repo):
    """AUD-01: ni el JWT ni la fila SQL permiten roles de refugio/admin."""
    _confirmar_bd_pruebas(motor)
    antes = _huella_tablas_sql(motor, ("dbo.usuarios",))
    sufijo = uuid.uuid4().hex[:8]
    base = {
        "nombre": "Regreso Seguro",
        "email": f"seguro-{sufijo}@example.com",
        "dni": str(uuid.uuid4().int % 90_000_000 + 10_000_000),
        "password": "claveSegura1",
    }

    refugio = cliente_sql.post(
        "/api/v1/auth/registro",
        json={
            **base,
            "email": f"refugio-{sufijo}@example.com",
            "dni": str(uuid.uuid4().int % 90_000_000 + 10_000_000),
            "rol": "refugio",
            "refugioId": "huellitas-wanka",
        },
    )
    assert refugio.status_code == 403, refugio.text
    assert refugio.json()["code"] == "FORBIDDEN"

    administrador = cliente_sql.post(
        "/api/v1/auth/registro",
        json={
            **base,
            "email": f"admin-{sufijo}@example.com",
            "dni": str(uuid.uuid4().int % 90_000_000 + 10_000_000),
            "rol": "admin",
        },
    )
    assert administrador.status_code == 422, administrador.text
    assert administrador.json()["code"] == "VALIDATION_ERROR"

    usuario_id: int | None = None
    registro = cliente_sql.post(
        "/api/v1/auth/registro",
        json={**base, "rol": "adoptante", "refugioId": "huellitas-wanka"},
    )
    assert registro.status_code == 201, registro.text
    datos = registro.json()
    assert datos["usuario"]["rol"] == "adoptante"
    assert datos["usuario"]["refugioId"] is None
    usuario_id = int(datos["usuario"]["id"])

    try:
        persistido = repo.obtener_usuario(usuario_id)
        assert persistido is not None
        assert persistido.rol == "adoptante"
        assert persistido.refugio_id is None

        headers = {"Authorization": f"Bearer {datos['token']}"}
        alertas = cliente_sql.get("/api/v1/alertas-rescate", headers=headers)
        assert alertas.status_code == 403, alertas.text
        assert alertas.json()["code"] == "FORBIDDEN"

        mascotas = cliente_sql.post(
            "/api/v1/mascotas",
            json={
                "nombre": "Mascota Prueba AUD01",
                "especie": "perro",
                "sexo": "Macho",
                "raza": "Mestizo",
                "edadAnios": 2,
                "tamano": "Mediano",
                "pesoKg": 12.5,
                "distrito": "El Tambo",
                "lugar": "Huancayo",
                "foto": "/assets/prueba.jpg",
                "alt": "Mascota de prueba",
                "descripcion": "Mascota usada solo para verificar permisos.",
                "etiqueta": "Amigable",
                "refugioId": "huellitas-wanka",
            },
            headers=headers,
        )
        assert mascotas.status_code == 403, mascotas.text
        assert mascotas.json()["code"] == "FORBIDDEN"
    finally:
        _confirmar_bd_pruebas(motor)
        with motor.begin() as conexion:
            eliminados = conexion.execute(
                text("DELETE FROM dbo.usuarios WHERE id = :usuario_id"),
                {"usuario_id": usuario_id},
            ).rowcount
            assert eliminados == 1
        logger.info(
            "limpieza_registro_aud01 id=%s antes=%s despues=%s",
            usuario_id,
            antes,
            _huella_tablas_sql(motor, ("dbo.usuarios",)),
        )
        assert _huella_tablas_sql(motor, ("dbo.usuarios",)) == antes


def test_crear_actualizar_y_eliminar_mascota(repo, seed):
    base = seed.mascotas[3]
    sufijo = uuid.uuid4().hex[:8]
    nueva = replace(
        base,
        id=0,
        nombre=f"Prueba {sufijo}",
        nombre_corto=f"P{sufijo}",
        ficha_id="",
        actualizado_dias=0,
        rasgos=base.rasgos[:2],
    )

    creada = repo.crear_mascota(nueva)
    try:
        assert creada.id > 16
        assert creada.ficha_id == ficha_predeterminada(creada.id)
        assert creada.nombre == nueva.nombre
        assert creada.distrito == base.distrito
        assert [rasgo.texto for rasgo in creada.rasgos] == [
            rasgo.texto for rasgo in base.rasgos[:2]
        ]
        assert repo.obtener_mascota(creada.id) is not None

        creada.nombre = f"{nueva.nombre} II"
        actualizada = repo.actualizar_mascota(creada)
        assert actualizada.nombre.endswith(" II")
    finally:
        repo.eliminar_mascota(creada.id)
    assert repo.obtener_mascota(creada.id) is None


def test_ciclo_de_solicitud(repo, motor):
    usuario = repo.buscar_usuario_por_email("demo@leons.pe")
    assert usuario is not None
    mascota = repo.obtener_mascota(12)
    assert mascota is not None and mascota.estado == "disponible"

    ahora = ahora_utc()
    solicitud = Solicitud(
        id=0,
        codigo="",
        usuario_id=usuario.id,
        mascota_id=mascota.id,
        estado="activa",
        etapa=2,
        creada_en=ahora,
        actualizada_en=ahora,
        mensaje=Mensaje(
            iniciales="VQ",
            nombre=usuario.nombre,
            rol="Adoptante",
            texto=f"Mensaje de prueba {uuid.uuid4().hex[:8]}",
            autor_id=usuario.id,
        ),
    )

    # 5.6.3.3B: la fila y sus hijos se eliminan por IDs exactos aunque falle una aserción.
    with _solicitud_temporal_directa_sql(motor, repo, solicitud) as creada:
        assert creada.id > 0
        assert re.fullmatch(r"#SOL-HYO-\d{4}-\d{3}", creada.codigo)
        assert creada.estado == "activa"
        assert creada.mensaje is not None
        assert creada.mensaje.texto == solicitud.mensaje.texto

        cancelada = repo.actualizar_solicitud(
            replace(
                creada,
                estado="cancelada",
                motivo_cancelacion="Motivo de prueba automatizada",
            )
        )
        assert cancelada.estado == "cancelada"
        assert cancelada.motivo_cancelacion == "Motivo de prueba automatizada"


def test_favoritos(repo):
    usuario = repo.buscar_usuario_por_email("demo@leons.pe")
    assert usuario is not None

    if any(f.mascota_id == 5 for f in repo.listar_favoritos(usuario.id)):
        repo.eliminar_favorito(usuario.id, 5)

    repo.crear_favorito(Favorito(usuario_id=usuario.id, mascota_id=5))
    assert 5 in [f.mascota_id for f in repo.listar_favoritos(usuario.id)]
    assert repo.eliminar_favorito(usuario.id, 5) is True
    assert repo.eliminar_favorito(usuario.id, 5) is False


def test_alertas_de_rescate(repo, motor):
    alerta = AlertaRescate(
        id=0,
        nombre="Prueba Integración",
        contacto="+51 999 000 111",
        distrito="El Tambo",
        especie="perro",
        mensaje=f"Alerta de prueba {uuid.uuid4().hex[:8]}",
        creado_en=ahora_utc(),
    )
    # 5.6.3.3B: la alerta se elimina por su ID exacto aunque falle una aserción.
    with _alerta_temporal_sql(motor, repo, alerta) as creada:
        assert creada.id > 0
        assert creada.mensaje == alerta.mensaje
        assert creada.distrito == "El Tambo"
        assert creada.atendida is False
        assert creada.id in [existente.id for existente in repo.listar_alertas()]


def test_resumen_impacto(repo):
    resumen = repo.resumen_impacto()
    # Semántica equivalente a cargar las listas completas.
    disponibles = [m for m in repo.listar_mascotas() if m.estado == "disponible"]
    refugios = repo.listar_refugios()
    por_distrito: dict[str, int] = {}
    for r in refugios:
        por_distrito[r.distrito] = por_distrito.get(r.distrito, 0) + r.adoptadas

    assert resumen["total_mascotas"] == len(disponibles)
    assert resumen["total_perros"] == sum(1 for m in disponibles if m.especie == "perro")
    assert resumen["total_gatos"] == sum(1 for m in disponibles if m.especie == "gato")
    assert resumen["total_refugios"] == len(refugios)
    assert resumen["total_adoptadas"] == sum(r.adoptadas for r in refugios)
    assert resumen["total_en_acogida"] == sum(r.en_acogida for r in refugios)
    assert resumen["total_distritos"] == len({r.distrito for r in refugios})
    assert resumen["adoptadas_por_distrito"] == dict(sorted(por_distrito.items()))


# -- Fase 4.2: paridad de las consultas optimizadas -----------------------


def _coincide_edad(anios: float, grupo: str) -> bool:
    if grupo == "cachorro":
        return anios < 1
    if grupo == "joven":
        return 1 <= anios < 3
    if grupo == "adulto":
        return 3 <= anios <= 7
    if grupo == "senior":
        return anios > 7
    return True


def _referencia_catalogo(mascotas, filtro: FiltroMascotas) -> tuple[list[int], int]:
    """Implementación en Python del catálogo; referencia del pushdown a SQL."""
    texto = (filtro.q or "").strip().lower()

    def incluir(m) -> bool:
        if filtro.estado != "todos" and m.estado != filtro.estado:
            return False
        if texto:
            campos = (m.nombre, m.raza, m.etiqueta, m.lugar)
            if not any(texto in campo.lower() for campo in campos):
                return False
        if filtro.especie and m.especie != filtro.especie:
            return False
        if filtro.distrito and m.distrito.lower() != filtro.distrito.lower():
            return False
        if filtro.tamano and m.tamano != filtro.tamano:
            return False
        if filtro.sexo and m.sexo != filtro.sexo:
            return False
        if filtro.edad and not _coincide_edad(m.edad_anios, filtro.edad):
            return False
        if filtro.refugio_id and m.refugio_id != filtro.refugio_id:
            return False
        if filtro.solo_esterilizados and not m.esterilizado:
            return False
        if filtro.solo_vacunados and not m.vacunado:
            return False
        if filtro.solo_urgentes and not m.urgente:
            return False
        return True

    filtradas = [m for m in mascotas if incluir(m)]
    if filtro.orden == "urgent":
        filtradas.sort(key=lambda m: (not m.urgente, m.id))
    elif filtro.orden == "youngest":
        filtradas.sort(key=lambda m: (m.edad_anios, m.id))
    elif filtro.orden == "oldest":
        filtradas.sort(key=lambda m: (-m.edad_anios, m.id))
    else:
        filtradas.sort(key=lambda m: -m.id)
    inicio = (filtro.page - 1) * filtro.limit
    return [m.id for m in filtradas[inicio : inicio + filtro.limit]], len(filtradas)


def test_buscar_mascotas_paridad_con_python(repo):
    mascotas = repo.listar_mascotas()
    casos = [
        FiltroMascotas(),
        FiltroMascotas(page=2),
        FiltroMascotas(limit=50),
        FiltroMascotas(estado="adoptada"),
        FiltroMascotas(estado="en_acogida"),
        FiltroMascotas(especie="gato", limit=50),
        FiltroMascotas(distrito="El Tambo"),
        FiltroMascotas(distrito="Huancayo Centro"),
        FiltroMascotas(tamano="Grande"),
        FiltroMascotas(sexo="Hembra"),
        FiltroMascotas(edad="cachorro"),
        FiltroMascotas(edad="joven"),
        FiltroMascotas(edad="adulto"),
        FiltroMascotas(edad="senior"),
        FiltroMascotas(q="chaska"),
        FiltroMascotas(q="mestiza"),
        FiltroMascotas(q="HUA"),
        FiltroMascotas(q="%"),
        FiltroMascotas(q="_"),
        FiltroMascotas(q="agustin"),
        FiltroMascotas(orden="urgent"),
        FiltroMascotas(orden="youngest"),
        FiltroMascotas(orden="oldest"),
        FiltroMascotas(solo_urgentes=True),
        FiltroMascotas(solo_vacunados=True),
        FiltroMascotas(solo_esterilizados=True),
        FiltroMascotas(refugio_id="huellitas-wanka", limit=50),
        FiltroMascotas(especie="perro", estado="disponible", orden="oldest", limit=4),
    ]
    for filtro in casos:
        obtenidas, total = repo.buscar_mascotas(filtro)
        esperados, total_esperado = _referencia_catalogo(mascotas, filtro)
        assert total == total_esperado, filtro
        assert [m.id for m in obtenidas] == esperados, filtro


def test_buscar_solicitudes_paridad_con_python(repo):
    usuarios = [
        repo.buscar_usuario_por_email("demo@leons.pe"),
        repo.buscar_usuario_por_email("refugio@leons.pe"),
        repo.buscar_usuario_por_email("admin@leons.pe"),
    ]
    assert all(isinstance(u, Usuario) for u in usuarios)
    todas = repo.listar_solicitudes()
    mascotas = {m.id: m for m in repo.listar_mascotas()}

    def visible(usuario, solicitud) -> bool:
        if usuario.rol == "admin" or solicitud.usuario_id == usuario.id:
            return True
        if usuario.rol != "refugio":
            return False
        mascota = mascotas.get(solicitud.mascota_id)
        return mascota is not None and mascota.refugio_id == usuario.refugio_id

    for usuario in usuarios:
        for estado, incluir in (
            ("todos", False),
            ("todos", True),
            ("activa", False),
            ("cancelada", False),
            ("completada", False),
        ):
            for page, limit in ((1, 20), (2, 20), (1, 2)):
                esperadas = [s for s in todas if visible(usuario, s)]
                if estado != "todos":
                    esperadas = [s for s in esperadas if s.estado == estado]
                elif not incluir:
                    esperadas = [s for s in esperadas if s.estado != "cancelada"]
                esperadas.sort(key=lambda s: (-s.creada_en.timestamp(), -s.id))
                inicio = (page - 1) * limit
                esperados = [s.id for s in esperadas[inicio : inicio + limit]]

                obtenidas, total = repo.buscar_solicitudes(
                    usuario_id=usuario.id,
                    rol=usuario.rol,
                    refugio_id=usuario.refugio_id,
                    estado=estado,
                    incluir_canceladas=incluir,
                    page=page,
                    limit=limit,
                )
                assert total == len(esperadas), (usuario.email, estado, incluir)
                assert [s.id for s in obtenidas] == esperados, (
                    usuario.email,
                    estado,
                    incluir,
                    page,
                    limit,
                )


def test_listado_de_solicitudes_no_es_n_mas_1(repo):
    """P6: el costo en consultas no crece con la cantidad de solicitudes."""
    admin = repo.buscar_usuario_por_email("admin@leons.pe")
    assert isinstance(admin, Usuario)

    contador = {"n": 0}

    def contar(*_args, **_kwargs) -> None:
        contador["n"] += 1

    def consultas(limit: int) -> tuple[int, int]:
        contador["n"] = 0
        event.listen(Engine, "before_cursor_execute", contar)
        try:
            filas, total = repo.buscar_solicitudes(
                usuario_id=admin.id,
                rol=admin.rol,
                refugio_id=admin.refugio_id,
                limit=limit,
            )
        finally:
            event.remove(Engine, "before_cursor_execute", contar)
        return len(filas), total

    filas_veinte, total = consultas(20)
    consultas_veinte = contador["n"]
    filas_una, _ = consultas(1)
    consultas_una = contador["n"]

    assert total >= filas_veinte > filas_una
    # Las tablas hijas se cargan por lotes: mismo número de consultas con 1 o
    # con 20 filas (antes se resolvían 3 consultas por cada solicitud).
    assert consultas_veinte <= consultas_una + 1
    assert consultas_veinte <= 8


# -- A-14/A-15/A-16: caracterización, sin cambios de persistencia ----------


def test_a14_caracteriza_autor_de_mensaje_en_sql(motor, repo):
    """A-14: el repositorio guarda el autor real del último mensaje.

    La auditoría previa afirmaba que `actualizar_solicitud()` siempre usaba
    `solicitud.usuario_id`. Esta prueba verifica el comportamiento actual para
    decidir si el hallazgo sigue vigente; no modifica datos.
    """
    from sqlalchemy import inspect as sa_inspect

    columnas = {c["name"] for c in sa_inspect(motor).get_columns("mensajes")}
    assert "autor_id" in columnas

    # Los mensajes de las solicitudes demo se leen sin escribir.
    for solicitud in repo.listar_solicitudes():
        if solicitud.mensaje is not None:
            assert solicitud.mensaje.nombre
            assert solicitud.mensaje.rol in {"Adoptante", "Coordinación del refugio"}


def test_a15_caracteriza_indice_unico_de_solicitud_activa(motor):
    """A-15: la integridad de la postulación activa se apoya en un índice único.

    No se crea ni modifica ningún objeto de esquema: solo se inspecciona.
    """
    from sqlalchemy import inspect as sa_inspect

    inspector = sa_inspect(motor)
    indices = inspector.get_indexes("solicitudes")
    nombres = {indice.get("name") for indice in indices}
    # D-034: `alembic check` limpio; el índice parcial debe existir.
    assert any("activa" in (nombre or "").lower() for nombre in nombres)


def test_a16_caracteriza_tipo_de_la_columna_fecha_de_cita(motor):
    """A-16: la cita se persiste como DATETIME2, no como texto libre.

    `AgendarCitaRequest.fecha` sigue siendo texto en el contrato; `_parsear_fecha`
    decide cómo convertirlo. Esta prueba solo documenta el tipo real.
    """
    from sqlalchemy import inspect as sa_inspect

    columnas = {
        columna["name"]: columna["type"]
        for columna in sa_inspect(motor).get_columns("citas")
    }
    assert "fecha_hora" in columnas
    assert "DATETIME2" in str(columnas["fecha_hora"]).upper()


# -- A-15: finalización atómica (opción B) ---------------------------------

MASCOTA_A15 = 12
USUARIO_ADOPTANTE_A15 = 1
USUARIO_OTRA_ACTIVA_A15 = 3


def _confirmar_bd_pruebas(motor: Engine) -> None:
    with motor.connect() as conexion:
        assert conexion.execute(text("SELECT DB_NAME()")).scalar_one() == "LeonsDB_Test"


# 5.6.3.3B: huella de las únicas tablas que pueden cambiar en los dos tests
# corregidos. Se compara antes y después de la limpieza para demostrar que no
# aumentan los conteos ni se modifica ningún registro preexistente.
TABLAS_HUELLA_SOLICITUD = (
    "dbo.solicitudes",
    "dbo.mensajes",
    "dbo.solicitud_eventos",
    "dbo.citas",
    "dbo.seguimiento_fotos",
)
TABLAS_HUELLA_ALERTA = ("dbo.alertas_rescate",)
TABLAS_HIJAS_SOLICITUD = (
    "dbo.seguimiento_fotos",
    "dbo.citas",
    "dbo.mensajes",
    "dbo.solicitud_eventos",
)


def _huella_tablas_sql(
    motor: Engine, tablas: tuple[str, ...]
) -> dict[str, dict[str, object]]:
    """Devuelve conteo y hash por tabla usando solo SELECT."""
    _confirmar_bd_pruebas(motor)
    huella: dict[str, dict[str, object]] = {}
    with motor.connect() as conexion:
        for tabla in tablas:
            filas = conexion.execute(
                text(f"SELECT * FROM {tabla} ORDER BY id")
            ).mappings().all()
            digest = hashlib.sha256()
            for fila in filas:
                digest.update(
                    "|".join(
                        "" if valor is None else str(valor) for valor in fila.values()
                    ).encode("utf-8")
                )
            huella[tabla.removeprefix("dbo.")] = {
                "count": len(filas),
                "hash": digest.hexdigest()[:20],
            }
    return huella


@contextmanager
def _solicitud_temporal_directa_sql(
    motor: Engine, repo: SqlServerRepository, solicitud: Solicitud
):
    """Crea una solicitud y elimina solo sus IDs exactos, incluso si falla el test."""
    _confirmar_bd_pruebas(motor)
    antes = _huella_tablas_sql(motor, TABLAS_HUELLA_SOLICITUD)
    creada = repo.crear_solicitud(solicitud)
    try:
        yield creada
    finally:
        _confirmar_bd_pruebas(motor)
        eliminados: dict[str, list[int]] = {}
        with motor.begin() as conexion:
            for tabla in TABLAS_HIJAS_SOLICITUD:
                ids = [
                    int(fila[0])
                    for fila in conexion.execute(
                        text(
                            f"SELECT id FROM {tabla} "
                            "WHERE solicitud_id = :solicitud_id"
                        ),
                        {"solicitud_id": creada.id},
                    ).all()
                ]
                eliminados[tabla] = ids
                for id_hijo in ids:
                    conexion.execute(
                        text(f"DELETE FROM {tabla} WHERE id = :id"), {"id": id_hijo}
                    )
            eliminados["dbo.solicitudes"] = [creada.id]
            conexion.execute(
                text("DELETE FROM dbo.solicitudes WHERE id = :id"), {"id": creada.id}
            )

        despues = _huella_tablas_sql(motor, TABLAS_HUELLA_SOLICITUD)
        logger.info(
            "limpieza_solicitud ids=%s antes=%s despues=%s",
            eliminados,
            antes,
            despues,
        )
        assert despues == antes, (
            "La prueba alteró el baseline de LeonsDB_Test: "
            f"antes={antes} despues={despues}"
        )


@contextmanager
def _alerta_temporal_sql(
    motor: Engine, repo: SqlServerRepository, alerta: AlertaRescate
):
    """Crea una alerta y elimina solo su ID exacto, incluso si falla el test."""
    _confirmar_bd_pruebas(motor)
    antes = _huella_tablas_sql(motor, TABLAS_HUELLA_ALERTA)
    creada = repo.crear_alerta(alerta)
    try:
        yield creada
    finally:
        _confirmar_bd_pruebas(motor)
        eliminados: list[int] = []
        with motor.begin() as conexion:
            existe = conexion.execute(
                text("SELECT id FROM dbo.alertas_rescate WHERE id = :id"),
                {"id": creada.id},
            ).scalar_one_or_none()
            if existe is not None:
                eliminados.append(int(existe))
                conexion.execute(
                    text("DELETE FROM dbo.alertas_rescate WHERE id = :id"),
                    {"id": creada.id},
                )

        despues = _huella_tablas_sql(motor, TABLAS_HUELLA_ALERTA)
        logger.info(
            "limpieza_alerta ids=%s antes=%s despues=%s",
            eliminados,
            antes,
            despues,
        )
        assert despues == antes, (
            "La prueba alteró el baseline de LeonsDB_Test: "
            f"antes={antes} despues={despues}"
        )


MASCOTA_TEMP_SQL = 12


@contextmanager
def _solicitud_temporal_sql(
    motor: Engine, cliente: TestClient, *, mensaje: str | None = None
):
    """Crea una solicitud HTTP real y elimina solo las filas que genera."""
    _confirmar_bd_pruebas(motor)
    adoptante = autenticar(cliente)
    cuerpo: dict[str, object] = {"mascotaId": MASCOTA_TEMP_SQL}
    if mensaje is not None:
        cuerpo["mensaje"] = mensaje
    respuesta = cliente.post("/api/v1/solicitudes", json=cuerpo, headers=adoptante)
    assert respuesta.status_code == 201, respuesta.text
    solicitud_id = int(respuesta.json()["id"])
    try:
        yield solicitud_id, adoptante
    finally:
        _confirmar_bd_pruebas(motor)
        with motor.begin() as conexion:
            for tabla in (
                "dbo.seguimiento_fotos",
                "dbo.citas",
                "dbo.mensajes",
                "dbo.solicitud_eventos",
            ):
                conexion.execute(
                    text(f"DELETE FROM {tabla} WHERE solicitud_id = :solicitud_id"),
                    {"solicitud_id": solicitud_id},
                )
            conexion.execute(
                text("DELETE FROM dbo.solicitudes WHERE id = :solicitud_id"),
                {"solicitud_id": solicitud_id},
            )


@contextmanager
def _adoptante_temporal_sql(motor: Engine, cliente: TestClient):
    """Registra un adoptante solo para verificar un rechazo por permisos."""
    _confirmar_bd_pruebas(motor)
    sufijo = uuid.uuid4().hex[:8]
    respuesta = cliente.post(
        "/api/v1/auth/registro",
        json={
            "nombre": f"Adoptante A14 {sufijo}",
            "email": f"a14-{sufijo}@example.com",
            "dni": str(uuid.uuid4().int % 90_000_000 + 10_000_000),
            "password": "claveSegura1",
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    usuario_id = int(respuesta.json()["usuario"]["id"])
    headers = {"Authorization": f"Bearer {respuesta.json()['token']}"}
    try:
        yield headers
    finally:
        _confirmar_bd_pruebas(motor)
        with motor.begin() as conexion:
            conexion.execute(
                text("DELETE FROM dbo.usuarios WHERE id = :usuario_id"),
                {"usuario_id": usuario_id},
            )


def _ultimo_mensaje_sql(motor: Engine, solicitud_id: int) -> dict[str, object]:
    _confirmar_bd_pruebas(motor)
    with motor.connect() as conexion:
        fila = conexion.execute(
            text(
                """
                SELECT TOP 1 autor_id, texto
                FROM dbo.mensajes
                WHERE solicitud_id = :solicitud_id
                ORDER BY creado_en DESC, id DESC
                """
            ),
            {"solicitud_id": solicitud_id},
        ).mappings().one()
    return dict(fila)


def _citas_sql(motor: Engine, solicitud_id: int) -> list[dict[str, object]]:
    _confirmar_bd_pruebas(motor)
    with motor.connect() as conexion:
        filas = conexion.execute(
            text(
                """
                SELECT fecha_hora, lugar, notas, coordinadora
                FROM dbo.citas
                WHERE solicitud_id = :solicitud_id
                ORDER BY creado_en, id
                """
            ),
            {"solicitud_id": solicitud_id},
        ).mappings().all()
    return [dict(fila) for fila in filas]


# -- A-14: autoría real de mensajes -----------------------------------------

def test_a14_autoria_real_persistida_y_reconstruida(cliente_sql, motor):
    _confirmar_bd_pruebas(motor)
    sufijo = uuid.uuid4().hex[:8]
    texto_adoptante = f"Mensaje del adoptante {sufijo}"

    with _solicitud_temporal_sql(
        motor, cliente_sql, mensaje=texto_adoptante
    ) as (solicitud_id, adoptante):
        persistido = _ultimo_mensaje_sql(motor, solicitud_id)
        assert persistido["autor_id"] == 1
        assert persistido["texto"] == texto_adoptante

        detalle = cliente_sql.get(
            f"/api/v1/solicitudes/{solicitud_id}", headers=adoptante
        ).json()
        assert detalle["mensaje"]["nombre"] == "Valeria Quispe"
        assert detalle["mensaje"]["rol"] == "Adoptante"

        refugio = autenticar(cliente_sql, "refugio@leons.pe", "refugio12345")
        texto_refugio = f"Coordinación del refugio {sufijo}"
        respuesta = cliente_sql.post(
            f"/api/v1/solicitudes/{solicitud_id}/mensajes",
            json={"texto": texto_refugio},
            headers=refugio,
        )
        assert respuesta.status_code == 200, respuesta.text
        persistido = _ultimo_mensaje_sql(motor, solicitud_id)
        assert persistido["autor_id"] == 2
        assert persistido["texto"] == texto_refugio
        detalle = cliente_sql.get(
            f"/api/v1/solicitudes/{solicitud_id}", headers=adoptante
        ).json()
        assert detalle["mensaje"]["nombre"] == "Silvia Mallqui"
        assert detalle["mensaje"]["rol"] == "Coordinación del refugio"

        admin = autenticar(cliente_sql, "admin@leons.pe", "admin12345")
        texto_admin = f"Mensaje del administrador {sufijo}"
        respuesta = cliente_sql.post(
            f"/api/v1/solicitudes/{solicitud_id}/mensajes",
            json={"texto": texto_admin},
            headers=admin,
        )
        assert respuesta.status_code == 200, respuesta.text
        persistido = _ultimo_mensaje_sql(motor, solicitud_id)
        assert persistido["autor_id"] == 3
        assert persistido["texto"] == texto_admin
        detalle = cliente_sql.get(
            f"/api/v1/solicitudes/{solicitud_id}", headers=adoptante
        ).json()
        assert detalle["mensaje"]["nombre"] == "Administrador LeonS"
        assert detalle["mensaje"]["rol"] == "Coordinación del refugio"

        with _adoptante_temporal_sql(motor, cliente_sql) as otro:
            rechazado = cliente_sql.post(
                f"/api/v1/solicitudes/{solicitud_id}/mensajes",
                json={"texto": f"No autorizado {sufijo}"},
                headers=otro,
            )
        assert rechazado.status_code == 403
        assert rechazado.json()["code"] == "FORBIDDEN"
        assert _ultimo_mensaje_sql(motor, solicitud_id)["autor_id"] == 3


# -- A-16: validación estricta de fechas de cita -----------------------------

def test_a16_matriz_de_formatos_de_fecha():
    anio = 2025
    casos = {
        "Sábado 24 Mayo • 10:30 am": datetime(anio, 5, 24, 10, 30),
        "Sábado 24 Mayo · 10:30 am": datetime(anio, 5, 24, 10, 30),
        "24 de mayo 10:30": datetime(anio, 5, 24, 10, 30),
        "24 mayo": datetime(anio, 5, 24, 0, 0),
        "24 mayo 10:30 pm": datetime(anio, 5, 24, 22, 30),
        "12 enero 12:00 am": datetime(anio, 1, 12, 0, 0),
        "1 de enero 00:00": datetime(anio, 1, 1, 0, 0),
        "31 de diciembre 23:59": datetime(anio, 12, 31, 23, 59),
    }
    for texto, esperado in casos.items():
        assert _parsear_fecha(texto, anio) == esperado

    assert _parsear_fecha("29 de febrero 10:30", 2024) == datetime(
        2024, 2, 29, 10, 30
    )

    for texto in (
        "31 de abril 10:30",
        "32 de enero 10:30",
        "29 de febrero 10:30",
        "texto no reconocible",
        "24 de mayo 25:00",
        "24 mayo 10:70",
        "24 mayo 13:00 pm",
        "",
    ):
        with pytest.raises(ValidationError) as error:
            _parsear_fecha(texto, 2026)
        assert error.value.code == "FECHA_CITA_INVALIDA"


def test_a16_fechas_validas_se_persisten_sin_sustitucion(cliente_sql, motor):
    _confirmar_bd_pruebas(motor)
    refugio = autenticar(cliente_sql, "refugio@leons.pe", "refugio12345")

    with _solicitud_temporal_sql(motor, cliente_sql) as (solicitud_id, _):
        textos = (
            "Sábado 24 Mayo • 10:30 am",
            "Sábado 24 Mayo · 11:45 am",
            "24 de mayo 18:15",
        )
        for indice, texto in enumerate(textos):
            respuesta = cliente_sql.post(
                f"/api/v1/solicitudes/{solicitud_id}/citas",
                json={
                    "fecha": texto,
                    "direccion": f"Dirección de prueba {indice}",
                    "coordinadora": "Coordinación de prueba",
                },
                headers=refugio,
            )
            assert respuesta.status_code == 200, respuesta.text
            assert respuesta.json()["cita"]["fecha"] == texto

        filas = _citas_sql(motor, solicitud_id)
        assert len(filas) == len(textos)
        anio = ahora_utc().year
        assert [fila["fecha_hora"] for fila in filas] == [
            datetime(anio, 5, 24, 10, 30),
            datetime(anio, 5, 24, 11, 45),
            datetime(anio, 5, 24, 18, 15),
        ]
        assert [fila["notas"] for fila in filas] == list(textos)


def test_a16_fechas_invalidas_no_escriben(cliente_sql, motor):
    _confirmar_bd_pruebas(motor)
    refugio = autenticar(cliente_sql, "refugio@leons.pe", "refugio12345")

    with _solicitud_temporal_sql(motor, cliente_sql) as (solicitud_id, _):
        assert _citas_sql(motor, solicitud_id) == []

        casos = (
            ("31 de abril 10:30", "FECHA_CITA_INVALIDA"),
            ("30 de febrero 10:30", "FECHA_CITA_INVALIDA"),
            ("texto no reconocible", "FECHA_CITA_INVALIDA"),
            ("", "VALIDATION_ERROR"),
        )
        for texto, codigo in casos:
            respuesta = cliente_sql.post(
                f"/api/v1/solicitudes/{solicitud_id}/citas",
                json={
                    "fecha": texto,
                    "direccion": "Dirección de prueba",
                    "coordinadora": "Coordinación de prueba",
                },
                headers=refugio,
            )
            assert respuesta.status_code == 422, respuesta.text
            assert respuesta.json()["code"] == codigo

        assert _citas_sql(motor, solicitud_id) == []


def _insertar_solicitud_a15(
    motor: Engine,
    *,
    usuario_id: int,
    estado: str = "activa",
    etapa: int = 2,
) -> int:
    codigo = f"#SOL-A15-{uuid.uuid4().hex[:12]}"
    with motor.begin() as conexion:
        solicitud_id = conexion.execute(
            text(
                """
                INSERT INTO dbo.solicitudes
                    (codigo, usuario_id, mascota_id, refugio_id, estado, etapa,
                     creado_en, actualizado_en)
                OUTPUT INSERTED.id
                VALUES
                    (:codigo, :usuario_id, :mascota_id,
                     (SELECT refugio_id FROM dbo.mascotas WHERE id = :mascota_id),
                     :estado, :etapa, SYSUTCDATETIME(), SYSUTCDATETIME())
                """
            ),
            {
                "codigo": codigo,
                "usuario_id": usuario_id,
                "mascota_id": MASCOTA_A15,
                "estado": estado,
                "etapa": etapa,
            },
        ).scalar_one()
    return int(solicitud_id)


def _estado_solicitud_a15(motor: Engine, solicitud_id: int) -> dict[str, object]:
    with motor.connect() as conexion:
        fila = conexion.execute(
            text(
                """
                SELECT estado, etapa
                FROM dbo.solicitudes
                WHERE id = :solicitud_id
                """
            ),
            {"solicitud_id": solicitud_id},
        ).mappings().one()
    return dict(fila)


def _estado_mascota_a15(motor: Engine) -> dict[str, object]:
    with motor.connect() as conexion:
        fila = conexion.execute(
            text(
                """
                SELECT estado, actualizado_en
                FROM dbo.mascotas
                WHERE id = :mascota_id
                """
            ),
            {"mascota_id": MASCOTA_A15},
        ).mappings().one()
    return dict(fila)


def _conteos_hijos_a15(motor: Engine, solicitud_id: int) -> dict[str, int]:
    with motor.connect() as conexion:
        total_eventos = conexion.execute(
            text(
                "SELECT COUNT(*) FROM dbo.solicitud_eventos WHERE solicitud_id = :solicitud_id"
            ),
            {"solicitud_id": solicitud_id},
        ).scalar_one()
        eventos_finales = conexion.execute(
            text(
                """SELECT COUNT(*) FROM dbo.solicitud_eventos
                   WHERE solicitud_id = :solicitud_id AND etapa = 5"""
            ),
            {"solicitud_id": solicitud_id},
        ).scalar_one()
        mensajes = conexion.execute(
            text("SELECT COUNT(*) FROM dbo.mensajes WHERE solicitud_id = :solicitud_id"),
            {"solicitud_id": solicitud_id},
        ).scalar_one()
    return {
        "eventos": int(total_eventos),
        "eventos_finales": int(eventos_finales),
        "mensajes": int(mensajes),
    }


@contextmanager
def _escenario_a15(
    motor: Engine,
    *,
    con_otra_activa: bool = False,
    estado_mascota: str | None = None,
):
    """Crea solo las filas de esta prueba y las elimina al terminar."""
    _confirmar_bd_pruebas(motor)
    estado_original = _estado_mascota_a15(motor)
    solicitud_id = _insertar_solicitud_a15(
        motor, usuario_id=USUARIO_ADOPTANTE_A15
    )
    otra_id: int | None = None
    if con_otra_activa:
        otra_id = _insertar_solicitud_a15(
            motor, usuario_id=USUARIO_OTRA_ACTIVA_A15
        )
    if estado_mascota is not None:
        with motor.begin() as conexion:
            conexion.execute(
                text("UPDATE dbo.mascotas SET estado = :estado WHERE id = :mascota_id"),
                {"estado": estado_mascota, "mascota_id": MASCOTA_A15},
            )

    try:
        yield solicitud_id, otra_id, estado_original
    finally:
        _confirmar_bd_pruebas(motor)
        ids = [valor for valor in (solicitud_id, otra_id) if valor is not None]
        with motor.begin() as conexion:
            for actual_id in ids:
                for tabla in (
                    "dbo.seguimiento_fotos",
                    "dbo.citas",
                    "dbo.mensajes",
                    "dbo.solicitud_eventos",
                ):
                    conexion.execute(
                        text(f"DELETE FROM {tabla} WHERE solicitud_id = :solicitud_id"),
                        {"solicitud_id": actual_id},
                    )
            for actual_id in ids:
                conexion.execute(
                    text("DELETE FROM dbo.solicitudes WHERE id = :solicitud_id"),
                    {"solicitud_id": actual_id},
                )
            conexion.execute(
                text(
                    """UPDATE dbo.mascotas
                       SET estado = :estado, actualizado_en = :actualizado_en
                       WHERE id = :mascota_id"""
                ),
                {
                    "estado": estado_original["estado"],
                    "actualizado_en": estado_original["actualizado_en"],
                    "mascota_id": MASCOTA_A15,
                },
            )


def _solicitud_para_finalizar(
    repo: SqlServerRepository,
    solicitud_id: int,
    texto: str,
    autor: Usuario | None = None,
):
    autor = autor or repo.buscar_usuario_por_email("refugio@leons.pe")
    assert autor is not None
    return replace(
        repo.obtener_solicitud(solicitud_id),
        mensaje=Mensaje(
            iniciales="RF",
            nombre=autor.nombre,
            rol="Adoptante" if autor.rol == "adoptante" else "Coordinación del refugio",
            texto=texto,
            autor_id=autor.id,
        ),
    )


def test_a15_finalizacion_correcta_evento_y_mensaje_unicos(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        texto = f"Nota final {uuid.uuid4().hex[:8]}"
        finalizada = repo.finalizar_solicitud(
            _solicitud_para_finalizar(repo, solicitud_id, texto), refugio
        )
        assert finalizada.estado == "completada"
        assert finalizada.etapa == 5
        assert finalizada.mensaje is not None
        assert finalizada.mensaje.texto == texto
        assert finalizada.mensaje.autor_id == refugio.id
        assert _ultimo_mensaje_sql(motor, solicitud_id)["autor_id"] == refugio.id

        assert _estado_solicitud_a15(motor, solicitud_id) == {
            "estado": "completada",
            "etapa": 5,
        }
        assert _estado_mascota_a15(motor)["estado"] == "adoptada"
        conteos = _conteos_hijos_a15(motor, solicitud_id)
        assert conteos == {"eventos": 1, "eventos_finales": 1, "mensajes": 1}


def test_a15_usUna_sola_transaccion_y_un_commit(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        commits: list[int] = []

        def contar_commit(connection) -> None:
            commits.append(1)

        event.listen(repo.engine, "commit", contar_commit)
        try:
            repo.finalizar_solicitud(
                _solicitud_para_finalizar(repo, solicitud_id, "Nota transacción única"),
                refugio,
            )
        finally:
            event.remove(repo.engine, "commit", contar_commit)

        assert len(commits) == 1
        assert _conteos_hijos_a15(motor, solicitud_id)["eventos_finales"] == 1


def test_a15_fallo_forzado_hace_rollback_completo(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        def fallar(session) -> None:
            raise RuntimeError("fallo forzado antes del commit")

        event.listen(Session, "before_commit", fallar)
        try:
            with pytest.raises(RuntimeError, match="fallo forzado"):
                repo.finalizar_solicitud(
                    _solicitud_para_finalizar(repo, solicitud_id, "Nota que no se guarda"),
                    refugio,
                )
        finally:
            event.remove(Session, "before_commit", fallar)

        assert _estado_solicitud_a15(motor, solicitud_id) == {
            "estado": "activa",
            "etapa": 2,
        }
        assert _estado_mascota_a15(motor)["estado"] == "disponible"
        assert _conteos_hijos_a15(motor, solicitud_id) == {
            "eventos": 0,
            "eventos_finales": 0,
            "mensajes": 0,
        }


def test_a15_fallo_de_commit_no_deja_cambios_parciales(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        def fallar_commit(connection) -> None:
            raise RuntimeError("commit fallido a propósito")

        event.listen(repo.engine, "commit", fallar_commit)
        try:
            with pytest.raises(RuntimeError, match="commit fallido"):
                repo.finalizar_solicitud(
                    _solicitud_para_finalizar(repo, solicitud_id, "Nota sin commit"),
                    refugio,
                )
        finally:
            event.remove(repo.engine, "commit", fallar_commit)

        assert _estado_solicitud_a15(motor, solicitud_id) == {
            "estado": "activa",
            "etapa": 2,
        }
        assert _estado_mascota_a15(motor)["estado"] == "disponible"
        assert _conteos_hijos_a15(motor, solicitud_id) == {
            "eventos": 0,
            "eventos_finales": 0,
            "mensajes": 0,
        }


def test_a15_dos_finalizaciones_concurrentes_son_idempotentes(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        texto = f"Nota concurrente {uuid.uuid4().hex[:8]}"
        solicitudes = [
            _solicitud_para_finalizar(repo, solicitud_id, texto) for _ in range(2)
        ]
        barrera = Barrier(2)

        def finalizar(solicitud):
            barrera.wait(timeout=15)
            return repo.finalizar_solicitud(solicitud, refugio)

        with ThreadPoolExecutor(max_workers=2) as grupo:
            futuros = [grupo.submit(finalizar, solicitud) for solicitud in solicitudes]
            resultados = [futuro.result(timeout=30) for futuro in futuros]

        assert all(item.estado == "completada" and item.etapa == 5 for item in resultados)
        assert _estado_solicitud_a15(motor, solicitud_id) == {
            "estado": "completada",
            "etapa": 5,
        }
        assert _conteos_hijos_a15(motor, solicitud_id) == {
            "eventos": 1,
            "eventos_finales": 1,
            "mensajes": 1,
        }


def test_a15_otra_postulacion_activa_impide_finalizar(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor, con_otra_activa=True) as (solicitud_id, otra_id, _):
        with pytest.raises(ConflictError) as error:
            repo.finalizar_solicitud(
                _solicitud_para_finalizar(repo, solicitud_id, "Nota bloqueada"), refugio
            )
        assert error.value.code == "ADOPCION_EN_CURSO"
        assert error.value.details["solicitudesActivas"] == 1

        assert _estado_solicitud_a15(motor, solicitud_id) == {
            "estado": "activa",
            "etapa": 2,
        }
        assert _estado_mascota_a15(motor)["estado"] == "disponible"
        assert _conteos_hijos_a15(motor, solicitud_id)["eventos"] == 0
        assert otra_id is not None
        assert _estado_solicitud_a15(motor, otra_id)["estado"] == "activa"


def test_a15_solicitud_incompatible_devuelve_409(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor, estado_mascota="en_acogida") as (solicitud_id, _, _):
        with pytest.raises(ConflictError) as error:
            repo.finalizar_solicitud(
                _solicitud_para_finalizar(repo, solicitud_id, "Nota incompatible"),
                refugio,
            )
        assert error.value.code == "MASCOTA_NO_DISPONIBLE"
        assert _estado_solicitud_a15(motor, solicitud_id) == {
            "estado": "activa",
            "etapa": 2,
        }
        assert _estado_mascota_a15(motor)["estado"] == "en_acogida"


def test_a15_repeticion_idempotente_no_duplica_eventos_ni_mensajes(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        texto = f"Nota idempotente {uuid.uuid4().hex[:8]}"
        primera = repo.finalizar_solicitud(
            _solicitud_para_finalizar(repo, solicitud_id, texto), refugio
        )
        conteos_antes = _conteos_hijos_a15(motor, solicitud_id)

        repetida = replace(
            repo.obtener_solicitud(solicitud_id),
            actualizada_en=ahora_utc(),
            mensaje=Mensaje(
                iniciales="RF",
                nombre=refugio.nombre,
                rol="Coordinación del refugio",
                texto=f"{texto}-distinto",
                autor_id=refugio.id,
            ),
        )
        segunda = repo.finalizar_solicitud(repetida, refugio)

        assert segunda.estado == "completada"
        assert segunda.etapa == 5
        assert segunda.actualizada_en == primera.actualizada_en
        assert segunda.mensaje is not None
        assert segunda.mensaje.texto == texto
        assert segunda.mensaje.autor_id == refugio.id
        assert _ultimo_mensaje_sql(motor, solicitud_id)["autor_id"] == refugio.id
        assert _conteos_hijos_a15(motor, solicitud_id) == conteos_antes


def test_a15_rechaza_adoptante_no_autorizado(motor, repo):
    _confirmar_bd_pruebas(motor)
    adoptante = repo.buscar_usuario_por_email("demo@leons.pe")
    assert adoptante is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        with pytest.raises(ForbiddenError):
            repo.finalizar_solicitud(
                _solicitud_para_finalizar(repo, solicitud_id, "Nota no autorizada"),
                adoptante,
            )
        assert _estado_solicitud_a15(motor, solicitud_id) == {
            "estado": "activa",
            "etapa": 2,
        }
        assert _estado_mascota_a15(motor)["estado"] == "disponible"
        assert _conteos_hijos_a15(motor, solicitud_id)["eventos"] == 0


# -- 5.6.3.2D: deadlock 1205 y orden determinista de bloqueos --------------


def _error_1205() -> Exception:
    """Imita la firma que pyodbc/SQLAlchemy exponen para un deadlock 1205."""
    return Exception("(1205) [40001] Transaction was deadlocked on lock resources")


def test_detecta_1205_sin_confundir_otros_dbapi_error():
    from sqlalchemy.exc import DBAPIError

    assert _codigo_transitorio_sqlserver(_error_1205()) == "1205"
    envuelto = DBAPIError("SELECT 1", None, _error_1205())
    assert _codigo_transitorio_sqlserver(envuelto) == "1205"
    otro = DBAPIError("SELECT 1", None, Exception("(2627) restricción única"))
    assert _codigo_transitorio_sqlserver(otro) is None
    assert _codigo_transitorio_sqlserver(RuntimeError("fallo de negocio")) is None


def test_a15_dos_solicitudes_distintas_devuelven_409_sin_deadlock(motor, repo):
    """INC-E2E-01: la causa real del 500 era el COUNT con HOLDLOCK.

    Con el orden mascota -> solicitudes por id, las dos finalizaciones se
    serializan y ambas ven la otra postulación activa: ninguna escribe.
    """
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor, con_otra_activa=True) as (solicitud_id, otra_id, _):
        assert otra_id is not None
        texto = f"Nota concurrente {uuid.uuid4().hex[:8]}"
        solicitudes = [
            _solicitud_para_finalizar(repo, actual_id, texto)
            for actual_id in (solicitud_id, otra_id)
        ]
        barrera = Barrier(2)

        def finalizar(solicitud):
            barrera.wait(timeout=15)
            return repo.finalizar_solicitud(solicitud, refugio)

        with ThreadPoolExecutor(max_workers=2) as grupo:
            futuros = [grupo.submit(finalizar, item) for item in solicitudes]
            resultados = []
            errores = []
            for futuro in futuros:
                try:
                    resultados.append(futuro.result(timeout=30))
                except Exception as exc:  # noqa: BLE001 - se clasifica abajo
                    errores.append(exc)

        assert resultados == [], [str(item) for item in resultados]
        assert len(errores) == 2, errores
        assert all(
            isinstance(error, ConflictError)
            and error.code == "ADOPCION_EN_CURSO"
            and error.details["solicitudesActivas"] == 1
            for error in errores
        ), [(type(error).__name__, str(error)) for error in errores]

        # Ninguna de las dos solicitudes cambió y la mascota sigue disponible.
        for actual_id in (solicitud_id, otra_id):
            assert _estado_solicitud_a15(motor, actual_id) == {
                "estado": "activa",
                "etapa": 2,
            }
            assert _conteos_hijos_a15(motor, actual_id) == {
                "eventos": 0,
                "eventos_finales": 0,
                "mensajes": 0,
            }
        assert _estado_mascota_a15(motor)["estado"] == "disponible"


def test_a15_cancelar_otra_y_finalizar_es_exitoso_e_idempotente(motor, repo):
    """Escenario controlado separado: sin competencia, la finalización funciona."""
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor, con_otra_activa=True) as (solicitud_id, otra_id, _):
        assert otra_id is not None
        with motor.begin() as conexion:
            conexion.execute(
                text(
                    """UPDATE dbo.solicitudes
                       SET estado = 'cancelada',
                           motivo_cancelacion = :motivo,
                           actualizado_en = SYSUTCDATETIME()
                       WHERE id = :solicitud_id"""
                ),
                {"solicitud_id": otra_id, "motivo": "Relevada por otra postulación"},
            )

        texto = f"Nota controlada {uuid.uuid4().hex[:8]}"
        primera = repo.finalizar_solicitud(
            _solicitud_para_finalizar(repo, solicitud_id, texto), refugio
        )
        assert primera.estado == "completada"
        assert primera.etapa == 5
        conteos = _conteos_hijos_a15(motor, solicitud_id)
        assert conteos == {"eventos": 1, "eventos_finales": 1, "mensajes": 1}
        assert _estado_mascota_a15(motor)["estado"] == "adoptada"

        segunda = repo.finalizar_solicitud(
            _solicitud_para_finalizar(repo, solicitud_id, f"{texto}-repetida"), refugio
        )
        assert segunda.estado == "completada"
        assert segunda.mensaje is not None
        assert segunda.mensaje.texto == texto
        assert _conteos_hijos_a15(motor, solicitud_id) == conteos


def test_a15_1205_una_vez_se_reintenta_sin_duplicar(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        intentos: list[int] = []

        def fallar_una_vez(session) -> None:
            intentos.append(1)
            if len(intentos) == 1:
                raise _error_1205()

        event.listen(Session, "before_commit", fallar_una_vez)
        try:
            finalizada = repo.finalizar_solicitud(
                _solicitud_para_finalizar(repo, solicitud_id, "Nota tras reintento"),
                refugio,
            )
        finally:
            event.remove(Session, "before_commit", fallar_una_vez)

        assert finalizada.estado == "completada"
        assert len(intentos) == 2
        assert _conteos_hijos_a15(motor, solicitud_id) == {
            "eventos": 1,
            "eventos_finales": 1,
            "mensajes": 1,
        }


def test_a15_1205_persistente_devuelve_503_controlado_sin_escrituras(motor, repo):
    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        intentos: list[int] = []

        def fallar_siempre(session) -> None:
            intentos.append(1)
            raise _error_1205()

        event.listen(Session, "before_commit", fallar_siempre)
        try:
            with pytest.raises(TransitorioError) as error:
                repo.finalizar_solicitud(
                    _solicitud_para_finalizar(repo, solicitud_id, "Nota sin commit"),
                    refugio,
                )
        finally:
            event.remove(Session, "before_commit", fallar_siempre)

        assert error.value.code == "SERVICIO_NO_DISPONIBLE"
        assert error.value.status_code == 503
        assert "1205" not in str(error.value)
        assert len(intentos) == 2  # un reintento acotado, sin bucle
        assert _estado_solicitud_a15(motor, solicitud_id) == {
            "estado": "activa",
            "etapa": 2,
        }
        assert _estado_mascota_a15(motor)["estado"] == "disponible"
        assert _conteos_hijos_a15(motor, solicitud_id)["eventos"] == 0


def test_a15_dbapi_error_sin_firma_de_deadlock_no_se_traduce(motor, repo):
    """Un DBAPIError cualquiera no debe convertirse en 409 ni en 503."""
    from sqlalchemy.exc import DBAPIError

    _confirmar_bd_pruebas(motor)
    refugio = repo.buscar_usuario_por_email("refugio@leons.pe")
    assert refugio is not None

    with _escenario_a15(motor) as (solicitud_id, _, _):
        def fallar(session) -> None:
            raise DBAPIError("SELECT 1", None, Exception("fallo diverso de base de datos"))

        event.listen(Session, "before_commit", fallar)
        try:
            with pytest.raises(DBAPIError):
                repo.finalizar_solicitud(
                    _solicitud_para_finalizar(repo, solicitud_id, "Nota sin commit"),
                    refugio,
                )
        finally:
            event.remove(Session, "before_commit", fallar)

        assert _estado_solicitud_a15(motor, solicitud_id)["estado"] == "activa"
        assert _estado_mascota_a15(motor)["estado"] == "disponible"


# -- INC-011: estadísticas de mascotas con SQL Server ----------------------


def _stats_esperados_desde_repo(repo: SqlServerRepository) -> dict[str, object]:
    """Deriva los esperados de los datos controlados de LeonsDB_Test."""
    mascotas = repo.listar_mascotas()
    refugios = repo.listar_refugios()
    disponibles = [m for m in mascotas if m.estado == "disponible"]

    por_especie: dict[str, int] = {}
    por_distrito: dict[str, int] = {}
    por_tamano: dict[str, int] = {}
    for mascota in mascotas:
        especie = str(mascota.especie)
        distrito = str(mascota.distrito or "")
        tamano = str(mascota.tamano or "Mediano")
        por_especie[especie] = por_especie.get(especie, 0) + 1
        por_distrito[distrito] = por_distrito.get(distrito, 0) + 1
        por_tamano[tamano] = por_tamano.get(tamano, 0) + 1

    edad_promedio = (
        round(sum(float(m.edad_anios) for m in disponibles) / len(disponibles), 2)
        if disponibles
        else 0.0
    )
    return {
        "total": len(disponibles),
        "total_registradas": len(mascotas),
        "disponibles": len(disponibles),
        # La semántica vigente del repositorio SQL Server cuenta urgentes sobre
        # TODAS las mascotas; no se cambia en esta corrección.
        "adoptadas": sum(1 for m in mascotas if m.estado == "adoptada"),
        "en_acogida": sum(1 for m in mascotas if m.estado == "en_acogida"),
        "urgentes": sum(1 for m in mascotas if m.urgente),
        "total_refugios": len(refugios),
        "edad_promedio": edad_promedio,
        "por_especie": dict(sorted(por_especie.items())),
        "por_distrito": dict(sorted(por_distrito.items())),
        "por_tamano": dict(sorted(por_tamano.items())),
    }


def test_estadisticas_mascotas_derivadas_de_sql_server(repo):
    """INC-011: los agregados coinciden con los datos sembrados en la base de pruebas."""
    esperado = _stats_esperados_desde_repo(repo)
    obtenido = repo.estadisticas_mascotas()

    assert set(obtenido) == set(esperado)
    assert obtenido == esperado


def test_estadisticas_mascotas_no_carga_el_catalogo(repo, monkeypatch):
    """F: las estadísticas se calculan en SQL, sin materializar las mascotas."""

    def prohibido(*_args, **_kwargs):
        raise AssertionError("estadisticas_mascotas no debe cargar el catálogo completo")

    monkeypatch.setattr(repo, "listar_mascotas", prohibido)
    assert repo.estadisticas_mascotas()["total_registradas"] > 0


def test_endpoint_mascotas_stats_con_sql_server(cliente_sql, repo):
    """INC-011: se valida HTTP 200 y el contrato JSON, no solo el repositorio."""
    assert cliente_sql.app.state.container.settings.repos_backend == "sqlserver"
    with cliente_sql.app.state.container.repo.engine.connect() as conexion:
        assert conexion.execute(text("SELECT DB_NAME()")).scalar_one() == "LeonsDB_Test"

    respuesta = cliente_sql.get("/api/v1/mascotas/stats")
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    esperado = _stats_esperados_desde_repo(repo)

    assert set(cuerpo) == {
        "total",
        "totalRegistradas",
        "disponibles",
        "adoptadas",
        "enAcogida",
        "urgentes",
        "totalRefugios",
        "edadPromedio",
        "porEspecie",
        "porDistrito",
        "porTamano",
    }
    claves_enteras = (
        "total",
        "totalRegistradas",
        "disponibles",
        "adoptadas",
        "enAcogida",
        "urgentes",
        "totalRefugios",
    )
    assert all(isinstance(cuerpo[clave], int) for clave in claves_enteras)
    assert isinstance(cuerpo["edadPromedio"], (int, float))
    assert all(isinstance(cuerpo[clave], dict) for clave in ("porEspecie", "porDistrito", "porTamano"))

    assert cuerpo["total"] == esperado["total"]
    assert cuerpo["totalRegistradas"] == esperado["total_registradas"]
    assert cuerpo["disponibles"] == esperado["disponibles"]
    assert cuerpo["adoptadas"] == esperado["adoptadas"]
    assert cuerpo["enAcogida"] == esperado["en_acogida"]
    assert cuerpo["urgentes"] == esperado["urgentes"]
    assert cuerpo["totalRefugios"] == esperado["total_refugios"]
    assert cuerpo["edadPromedio"] == pytest.approx(esperado["edad_promedio"])
    assert cuerpo["porEspecie"] == esperado["por_especie"]
    assert cuerpo["porDistrito"] == esperado["por_distrito"]
    assert cuerpo["porTamano"] == esperado["por_tamano"]


def test_endpoint_impacto_con_sql_server_conserva_valores(cliente_sql, repo):
    """El arreglo de stats no altera el significado de /estadisticas/impacto."""
    respuesta = cliente_sql.get("/api/v1/estadisticas/impacto")
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()

    refugios = repo.listar_refugios()
    disponibles = [m for m in repo.listar_mascotas() if m.estado == "disponible"]
    assert cuerpo["totalAdoptadas"] == sum(r.adoptadas for r in refugios)
    assert cuerpo["totalEnAcogida"] == sum(r.en_acogida for r in refugios)
    assert cuerpo["totalMascotas"] == len(disponibles)
    assert cuerpo["totalRefugios"] == len(refugios)
    assert cuerpo["totalDistritos"] == len({r.distrito for r in refugios})
    assert cuerpo["totalPerros"] == sum(1 for m in disponibles if m.especie == "perro")
    assert cuerpo["totalGatos"] == sum(1 for m in disponibles if m.especie == "gato")


def test_agregados_de_stats_con_conjunto_vacio_y_nulos(repo):
    """D: las mismas expresiones devuelven cero sin filas o con edades nulas."""
    with repo._sesion() as sesion:
        totales = sesion.execute(
            select(
                func.coalesce(func.count(db.Mascota.id), 0),
                func.coalesce(func.sum(case((db.Mascota.estado == "adoptada", 1), else_=0)), 0),
                func.coalesce(func.sum(case((db.Mascota.estado == "en_acogida", 1), else_=0)), 0),
                func.coalesce(func.sum(case((db.Mascota.urgente == True, 1), else_=0)), 0),
            ).where(db.Mascota.id < 0)
        ).one()
        disponibles = sesion.scalar(
            select(func.coalesce(func.count(db.Mascota.id), 0)).where(db.Mascota.id < 0)
        )
        promedio = sesion.scalar(
            select(func.coalesce(func.avg(db.Mascota.edad), 0)).where(db.Mascota.id < 0)
        )
        promedio_nulo = sesion.scalar(
            select(func.coalesce(func.avg(db.Mascota.edad), 0)).where(db.Mascota.edad.is_(None))
        )

    assert tuple(int(valor) for valor in totales) == (0, 0, 0, 0)
    assert int(disponibles) == 0
    assert float(promedio) == 0.0
    assert float(promedio_nulo) == 0.0
