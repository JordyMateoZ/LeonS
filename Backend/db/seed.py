"""Siembra idempotente de SQL Server para la Fase 6.

Uso:

    cd Backend
    uv run python db/seed.py

El script lee `app/data/seed.json` (exportado desde Angular) y lo inserta sin
duplicar filas:

* busca por clave natural (`id` del refugio, `email` del usuario, `codigo` de
  la solicitud, `orden` del contenido) y **no sobrescribe** lo que ya existe;
* preserva los ids 1–16 de las mascotas con `IDENTITY_INSERT`, la única
  excepción permitida a D-025, y ajusta el contador con `DBCC CHECKIDENT`;
* abre una sola transacción: si algo falla, la base queda como estaba.

Salvaguarda: por defecto solo siembra bases cuyo nombre termina en `_Test`.
Para una base distinta hace falta `--force` y una razón explícita.
"""

from __future__ import annotations

import argparse
import sys
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
if str(RAIZ_BACKEND) not in sys.path:
    sys.path.insert(0, str(RAIZ_BACKEND))

from sqlalchemy import func, insert, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.data.loader import SeedData, cargar_seed
from app.db import models as db
from app.db.session import crear_engine, crear_fabrica
from app.domain import ahora_utc
from app.repositories.sqlserver import _parsear_fecha

SUFIJO_PERMITIDO = "_Test"


@contextmanager
def _identity_insert(sesion: Session, tabla: str):
    """Activa `IDENTITY_INSERT` para una sola tabla dentro de la transacción."""
    sesion.execute(text(f"SET IDENTITY_INSERT {tabla} ON"))
    try:
        yield
    finally:
        sesion.execute(text(f"SET IDENTITY_INSERT {tabla} OFF"))


def _existe(sesion: Session, modelo: Any, **filtros: Any) -> bool:
    return (
        sesion.scalar(select(func.count()).select_from(modelo).filter_by(**filtros))
        or 0
    ) > 0


def _resolver_distritos(sesion: Session, nombres: set[str]) -> dict[str, int]:
    for nombre in sorted(nombre for nombre in nombres if nombre):
        if not _existe(sesion, db.Distrito, nombre=nombre):
            sesion.execute(insert(db.Distrito).values(nombre=nombre))
    sesion.flush()
    return {
        fila.nombre: fila.id for fila in sesion.scalars(select(db.Distrito))
    }


def _sembrar_refugios(
    sesion: Session, refugios: list, distritos: dict[str, int]
) -> dict[str, int]:
    nuevos = existentes = 0
    for posicion, refugio in enumerate(refugios, start=1):
        fila = sesion.get(db.Refugio, refugio.id)
        if fila is None:
            sesion.execute(
                insert(db.Refugio).values(
                    id=refugio.id,
                    nombre=refugio.nombre,
                    orden=posicion,
                    descripcion=refugio.descripcion or None,
                    distrito_id=distritos.get(refugio.distrito),
                    direccion=refugio.direccion or None,
                    telefono=refugio.telefono or None,
                    whatsapp=refugio.whatsapp or None,
                    adoptadas_historicas=refugio.adoptadas,
                    en_acogida_actual=refugio.en_acogida,
                    contacto=refugio.contacto or None,
                    cargo=refugio.cargo or None,
                    tipo=refugio.tipo or None,
                    desde=refugio.desde or None,
                    verificado=refugio.verificado,
                    logo=refugio.logo,
                    creado_en=ahora_utc(),
                )
            )
            nuevos += 1
        else:
            existentes += 1
            # D-035: rellena el orden editorial en bases ya sembradas y nunca
            # sobrescribe uno ajustado a mano.
            if fila.orden is None:
                sesion.execute(
                    db.Refugio.__table__.update()
                    .where(db.Refugio.id == refugio.id)
                    .values(orden=posicion)
                )
        for especie in refugio.especies:
            if not _existe(
                sesion, db.RefugioEspecie, refugio_id=refugio.id, especie=especie
            ):
                sesion.execute(
                    insert(db.RefugioEspecie).values(
                        refugio_id=refugio.id, especie=especie
                    )
                )
    sesion.flush()
    return {"refugios": nuevos, "refugios_existentes": existentes}


def _sembrar_usuarios(
    sesion: Session, usuarios: list, distritos: dict[str, int]
) -> tuple[dict[int, int], dict[str, int]]:
    """Devuelve el mapa id del seed → id real y el resumen de la siembra."""
    mapa: dict[int, int] = {}
    nuevos = existentes = 0
    for usuario in usuarios:
        fila = sesion.scalar(
            select(db.Usuario).where(
                func.lower(db.Usuario.email) == usuario.email.strip().lower()
            )
        )
        if fila is not None:
            mapa[usuario.id] = fila.id
            existentes += 1
            continue

        valores = {
            "nombres": usuario.nombre,
            "email": usuario.email,
            "dni": usuario.dni,
            "password_hash": usuario.password_hash,
            "rol": usuario.rol,
            "telefono": usuario.telefono,
            "distrito_id": distritos.get(usuario.distrito or ""),
            "refugio_id": usuario.refugio_id,
            "creado_en": usuario.creado_en,
        }
        if sesion.get(db.Usuario, usuario.id) is None:
            with _identity_insert(sesion, "usuarios"):
                sesion.execute(insert(db.Usuario).values(id=usuario.id, **valores))
                sesion.flush()
            mapa[usuario.id] = usuario.id
        else:
            sesion.execute(insert(db.Usuario).values(**valores))
            sesion.flush()
            mapa[usuario.id] = int(
                sesion.scalar(
                    select(db.Usuario.id).where(
                        func.lower(db.Usuario.email) == usuario.email.strip().lower()
                    )
                )
            )
        nuevos += 1
    return mapa, {"usuarios": nuevos, "usuarios_existentes": existentes}


def _sembrar_mascotas(
    sesion: Session, mascotas: list, detalles: dict, distritos: dict[str, int]
) -> dict[str, int]:
    nuevos = existentes = 0
    for mascota in mascotas:
        fila = sesion.get(db.Mascota, mascota.id)
        if fila is not None:
            if fila.nombre != mascota.nombre:
                raise RuntimeError(
                    f"El id {mascota.id} ya lo ocupa {fila.nombre!r} y el seed "
                    f"espera {mascota.nombre!r}. Revisa la base antes de sembrar."
                )
            # Backfill acotado de D-032: solo rellena NULL, nunca sobrescribe.
            cambios = {
                columna: valor
                for columna, valor in (
                    ("vacunado", mascota.vacunado),
                    ("esterilizado", mascota.esterilizado),
                )
                if getattr(fila, columna) is None
            }
            if cambios:
                sesion.execute(
                    db.Mascota.__table__.update()
                    .where(db.Mascota.id == mascota.id)
                    .values(**cambios)
                )
            existentes += 1
            continue

        with _identity_insert(sesion, "mascotas"):
            sesion.execute(
                insert(db.Mascota).values(
                    id=mascota.id,
                    refugio_id=mascota.refugio_id,
                    nombre=mascota.nombre,
                    nombre_corto=mascota.nombre_corto or None,
                    especie=mascota.especie,
                    raza=mascota.raza or None,
                    sexo=mascota.sexo,
                    edad=mascota.edad_anios,
                    tamano=mascota.tamano,
                    descripcion=mascota.descripcion or None,
                    estado=mascota.estado,
                    destacada=False,
                    foto_principal=mascota.foto or None,
                    creado_en=ahora_utc(),
                    actualizado_en=ahora_utc()
                    - timedelta(days=mascota.actualizado_dias),
                    peso_kg=mascota.peso_kg,
                    lugar=mascota.lugar or None,
                    etiqueta=mascota.etiqueta or None,
                    etiqueta_icono=mascota.etiqueta_icono or None,
                    energia=mascota.energia or None,
                    urgente=mascota.urgente,
                    vacunado=mascota.vacunado,
                    esterilizado=mascota.esterilizado,
                    foto_alt=mascota.alt or None,
                    distrito_id=distritos.get(mascota.distrito),
                    etiqueta_clase=mascota.etiqueta_clase or None,
                )
            )
            sesion.flush()

        for indice, item in enumerate(mascota.salud):
            sesion.execute(
                insert(db.MascotaSalud).values(
                    mascota_id=mascota.id,
                    orden=indice,
                    texto=item.texto,
                    ok=item.ok,
                )
            )
        for indice, foto in enumerate(mascota.galeria):
            sesion.execute(
                insert(db.MascotaFoto).values(
                    mascota_id=mascota.id,
                    orden=indice,
                    url=foto.src,
                    alt=foto.alt or None,
                )
            )
        for indice, rasgo in enumerate(mascota.rasgos):
            sesion.execute(
                insert(db.MascotaRasgo).values(
                    mascota_id=mascota.id,
                    orden=indice,
                    rasgo=rasgo.texto,
                    icono=rasgo.icono or None,
                    clase=rasgo.clase or None,
                    icono_clase=rasgo.icono_clase or None,
                )
            )

        detalle = detalles.get(mascota.id)
        if detalle is not None:
            for indice, texto_historia in enumerate(detalle.historia):
                sesion.execute(
                    insert(db.MascotaHistoria).values(
                        mascota_id=mascota.id,
                        orden=indice,
                        texto=texto_historia,
                    )
                )
            for indice, cuidado in enumerate(detalle.cuidados):
                sesion.execute(
                    insert(db.MascotaCuidado).values(
                        mascota_id=mascota.id,
                        orden=indice,
                        icono=cuidado["icono"],
                        titulo=cuidado["titulo"],
                        texto=cuidado["texto"],
                    )
                )
            if detalle.cita:
                sesion.execute(
                    db.Mascota.__table__.update()
                    .where(db.Mascota.id == mascota.id)
                    .values(
                        cita_texto=detalle.cita.get("texto"),
                        cita_autor=detalle.cita.get("autor"),
                    )
                )

        sesion.flush()
        nuevos += 1
    return {"mascotas": nuevos, "mascotas_existentes": existentes}


def _sembrar_contenido(sesion: Session, contenido) -> dict[str, int]:
    grupos = (
        ("adopcion", contenido.pasos_adopcion, 1),
        ("refugio", contenido.pasos_refugio, 5),
        ("requisito", contenido.requisitos, 8),
    )
    pasos = 0
    for tipo, items, inicio in grupos:
        for desplazamiento, item in enumerate(items):
            orden = inicio + desplazamiento
            if _existe(sesion, db.ContenidoPaso, orden=orden):
                continue
            sesion.execute(
                insert(db.ContenidoPaso).values(
                    orden=orden,
                    titulo=item["titulo"],
                    descripcion=item.get("texto") or None,
                    tipo=tipo,
                    icono=item.get("icono") or None,
                    nota=item.get("nota") or None,
                )
            )
            pasos += 1

    faqs = 0
    for orden, faq in enumerate(contenido.faqs, start=1):
        if _existe(sesion, db.ContenidoFaq, orden=orden):
            continue
        sesion.execute(
            insert(db.ContenidoFaq).values(
                orden=orden,
                pregunta=faq["pregunta"],
                respuesta=faq["respuesta"],
            )
        )
        faqs += 1

    sesion.flush()
    return {"contenido_pasos": pasos, "contenido_faqs": faqs}


def _autor_del_mensaje(
    sesion: Session, mascota: db.Mascota, usuario_id: int
) -> int:
    """El mensaje demo lo firma la coordinadora del refugio, no el adoptante."""
    coordinadora = sesion.scalar(
        select(db.Usuario.id)
        .where(
            db.Usuario.refugio_id == mascota.refugio_id,
            db.Usuario.rol.in_(("refugio", "admin")),
        )
        .order_by(db.Usuario.id)
    )
    return int(coordinadora or usuario_id)


def _sembrar_solicitudes(
    sesion: Session, solicitudes: list, mapa_usuarios: dict[int, int]
) -> dict[str, int]:
    nuevas = existentes = 0
    for solicitud in solicitudes:
        if _existe(sesion, db.Solicitud, codigo=solicitud.codigo):
            existentes += 1
            continue

        mascota = sesion.get(db.Mascota, solicitud.mascota_id)
        if mascota is None:
            raise RuntimeError(
                f"La solicitud {solicitud.codigo} apunta a la mascota "
                f"{solicitud.mascota_id}, que no existe en la base."
            )
        usuario_id = mapa_usuarios.get(solicitud.usuario_id, solicitud.usuario_id)

        fila = db.Solicitud(
            codigo=solicitud.codigo,
            usuario_id=usuario_id,
            mascota_id=mascota.id,
            refugio_id=mascota.refugio_id,
            estado=solicitud.estado,
            etapa=solicitud.etapa,
            motivo_cancelacion=solicitud.motivo_cancelacion,
            creado_en=solicitud.creada_en,
            actualizado_en=solicitud.actualizada_en,
        )
        sesion.add(fila)
        sesion.flush()

        if solicitud.mensaje is not None:
            sesion.execute(
                insert(db.Mensaje).values(
                    solicitud_id=fila.id,
                    autor_id=_autor_del_mensaje(sesion, mascota, usuario_id),
                    texto=solicitud.mensaje.texto,
                    creado_en=solicitud.creada_en,
                )
            )
        if solicitud.cita is not None:
            sesion.execute(
                insert(db.Cita).values(
                    solicitud_id=fila.id,
                    fecha_hora=_parsear_fecha(
                        solicitud.cita.fecha, solicitud.creada_en.year
                    ),
                    lugar=solicitud.cita.direccion or None,
                    # `notas` conserva el texto original del contrato.
                    notas=solicitud.cita.fecha or None,
                    coordinadora=solicitud.cita.coordinadora or None,
                    creado_en=solicitud.creada_en,
                )
            )
        sesion.execute(
            insert(db.SolicitudEvento).values(
                solicitud_id=fila.id,
                etapa=solicitud.etapa,
                creado_en=solicitud.creada_en,
            )
        )
        nuevas += 1
    sesion.flush()
    return {"solicitudes": nuevas, "solicitudes_existentes": existentes}


def _ajustar_identidad_mascotas(sesion: Session) -> None:
    maximo = sesion.scalar(select(func.max(db.Mascota.id))) or 0
    if maximo:
        sesion.execute(text(f"DBCC CHECKIDENT ('mascotas', RESEED, {int(maximo)})"))


def sembrar(engine: Engine, datos: SeedData, *, forzar: bool = False) -> dict[str, int]:
    """Inserta el seed de forma idempotente y devuelve el resumen."""
    with engine.connect() as conexion:
        nombre_base = conexion.execute(text("SELECT DB_NAME()")).scalar_one()
    if not forzar and not str(nombre_base).endswith(SUFIJO_PERMITIDO):
        raise RuntimeError(
            f"Siembra bloqueada: {nombre_base} no termina en {SUFIJO_PERMITIDO}. "
            "Usa --force solo si sabes lo que haces."
        )

    sesion = crear_fabrica(engine)()
    resumen: dict[str, int] = {}
    try:
        nombres_distrito = {
            *(refugio.distrito for refugio in datos.refugios if refugio.distrito),
            *(mascota.distrito for mascota in datos.mascotas if mascota.distrito),
            *(usuario.distrito for usuario in datos.usuarios if usuario.distrito),
        }
        distritos = _resolver_distritos(sesion, nombres_distrito)
        resumen.update(_sembrar_refugios(sesion, datos.refugios, distritos))
        mapa_usuarios, resumen_usuarios = _sembrar_usuarios(
            sesion, datos.usuarios, distritos
        )
        resumen.update(resumen_usuarios)
        resumen.update(
            _sembrar_mascotas(sesion, datos.mascotas, datos.detalles, distritos)
        )
        resumen.update(_sembrar_contenido(sesion, datos.contenido))
        resumen.update(_sembrar_solicitudes(sesion, datos.solicitudes, mapa_usuarios))
        _ajustar_identidad_mascotas(sesion)
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()
    return resumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Siembra idempotente de LeonS.")
    parser.add_argument(
        "--url",
        default="",
        help="URL de SQLAlchemy. Por defecto usa DB_TEST_URL.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Permite sembrar una base que no termine en _Test.",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    url = args.url or settings.db_test_url
    if not url:
        print(
            "Falta DB_TEST_URL en Backend/.env. Revisa Backend/.env.example.",
            file=sys.stderr,
        )
        return 2

    engine = crear_engine(url)
    try:
        resumen = sembrar(engine, cargar_seed(settings.seed_path), forzar=args.force)
    finally:
        engine.dispose()

    print("Siembra completada:")
    for clave in sorted(resumen):
        print(f"  {clave}: {resumen[clave]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
