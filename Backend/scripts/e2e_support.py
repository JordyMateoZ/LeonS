"""Soporte controlado para las pruebas E2E con persistencia (5.6.3.2B).

Reglas de esta herramienta:

* Solo escribe en la conexión derivada de `DB_TEST_URL` y exige
  `SELECT DB_NAME() = 'LeonsDB_Test'` antes de cada escritura y limpieza.
* `DB_URL` se usa únicamente para comprobaciones READ ONLY de no contaminación.
* Toda fila temporal se registra en un manifiesto y se borra por id exacto.
* No ejecuta migraciones, seeds, `DROP`, `TRUNCATE` ni borrados por rango.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import insert, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import models as db  # noqa: E402
from app.db.session import crear_engine  # noqa: E402
from app.security import hash_password  # noqa: E402

TEST_DB = "LeonsDB_Test"
MAIN_DB = "LeonsDB"

TABLAS = (
    "migraciones",
    "usuarios",
    "refugios",
    "refugio_especies",
    "mascotas",
    "mascota_salud",
    "mascota_fotos",
    "mascota_rasgos",
    "mascota_historia",
    "mascota_cuidados",
    "solicitudes",
    "solicitud_eventos",
    "citas",
    "mensajes",
    "seguimiento_fotos",
    "favoritos",
    "alertas_rescate",
    "contenido_pasos",
    "contenido_faqs",
    "distritos",
)

HijasMascota = (
    db.MascotaSalud,
    db.MascotaFoto,
    db.MascotaRasgo,
    db.MascotaHistoria,
    db.MascotaCuidado,
)

# Orden explícito para que la huella sea estable antes y después de borrar.
ORDEN = {
    "migraciones": "id",
    "usuarios": "id",
    "refugios": "id",
    "refugio_especies": "refugio_id, especie",
    "mascotas": "id",
    "mascota_salud": "id",
    "mascota_fotos": "id",
    "mascota_rasgos": "id",
    "mascota_historia": "id",
    "mascota_cuidados": "id",
    "solicitudes": "id",
    "solicitud_eventos": "id",
    "citas": "id",
    "mensajes": "id",
    "seguimiento_fotos": "id",
    "favoritos": "usuario_id, mascota_id",
    "alertas_rescate": "id",
    "contenido_pasos": "id",
    "contenido_faqs": "id",
    "distritos": "id",
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def _json(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "as_tuple"):
        return float(value) if value is not None else None
    if isinstance(value, (list, tuple)):
        return [_json(v) for v in value]
    if isinstance(value, dict):
        return {k: _json(v) for k, v in value.items()}
    return value


def _impresion(value: Any) -> None:
    print(json.dumps(_json(value), ensure_ascii=False, default=str))


def _motores() -> tuple[Any, Any]:
    ajustes = get_settings()
    return crear_engine(ajustes.db_test_url), crear_engine(ajustes.db_url)


def _nombre(engine: Any) -> str:
    with engine.connect() as conexion:
        return str(conexion.execute(text("SELECT DB_NAME()")).scalar_one())


def _exigir_pruebas(engine: Any) -> str:
    nombre = _nombre(engine)
    if nombre != TEST_DB:
        raise RuntimeError(
            f"Fail-closed: se exige {TEST_DB!r}; la conexión de pruebas apunta a {nombre!r}."
        )
    return nombre


def _exigir_principal(engine: Any) -> str:
    nombre = _nombre(engine)
    if nombre != MAIN_DB:
        raise RuntimeError(
            f"Fail-closed de no contaminación: se esperaba {MAIN_DB!r}, se obtuvo {nombre!r}."
        )
    return nombre


def _leer(manifest: Path) -> dict[str, Any]:
    return json.loads(manifest.read_text(encoding="utf-8"))


def _escribir(manifest: Path, datos: dict[str, Any]) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def _registrar(manifest: Path, kind: str, **datos: Any) -> None:
    contenido = _leer(manifest)
    contenido.setdefault("records", {}).setdefault(kind, []).append(_json(datos))
    _escribir(manifest, contenido)


def _huella(engine: Any) -> dict[str, Any]:
    resultado: dict[str, Any] = {}
    with engine.connect() as conexion:
        for tabla in TABLAS:
            try:
                filas = conexion.execute(
                    text(f"SELECT * FROM dbo.{tabla} ORDER BY {ORDEN[tabla]}")
                ).mappings().all()
            except Exception:  # tabla técnica o no presente en esta base
                continue
            digest = hashlib.sha256()
            for fila in filas:
                digest.update(
                    "|".join("" if v is None else str(v) for v in fila.values()).encode("utf-8")
                )
            resultado[tabla] = {"count": len(filas), "hash": digest.hexdigest()[:20]}
        resultado["alembic"] = str(
            conexion.execute(text("SELECT version_num FROM dbo.alembic_version")).scalar_one()
        )
    return resultado


def _conteos(engine: Any) -> dict[str, int]:
    with engine.connect() as conexion:
        return {
            tabla: int(conexion.execute(text(f"SELECT COUNT(*) FROM dbo.{tabla}")).scalar_one())
            for tabla in TABLAS
        }


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    pruebas, principal = _motores()
    nombre_pruebas = _exigir_pruebas(pruebas)
    nombre_principal = _exigir_principal(principal)
    with pruebas.connect() as conexion:
        distritos_iniciales = [
            int(f[0])
            for f in conexion.execute(text("SELECT id FROM dbo.distritos ORDER BY id")).all()
        ]
    datos = {
        "run_id": args.run_id,
        "creado_en": datetime.now(timezone.utc).isoformat(),
        "db_pruebas": nombre_pruebas,
        "db_principal": nombre_principal,
        "status": "open",
        "baseline": _huella(pruebas),
        "baseline_principal_counts": _conteos(principal),
        "baseline_distrito_ids": distritos_iniciales,
        "guards": [],
        "records": {},
        "cleanup": None,
    }
    _escribir(manifest, datos)
    pruebas.dispose()
    principal.dispose()
    _impresion(
        {
            "run_id": args.run_id,
            "db_pruebas": nombre_pruebas,
            "db_principal": nombre_principal,
            "tablas": len(datos["baseline"]),
        }
    )


def cmd_guard(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    datos = _leer(manifest)
    if datos.get("status") != "open":
        raise RuntimeError(f"Fail-closed: el manifiesto está {datos.get('status')!r}.")
    pruebas, principal = _motores()
    nombre = _exigir_pruebas(pruebas)
    _exigir_principal(principal)
    datos.setdefault("guards", []).append(
        {"operacion": args.operation, "db": nombre, "en": datetime.now(timezone.utc).isoformat()}
    )
    _escribir(manifest, datos)
    pruebas.dispose()
    principal.dispose()
    _impresion({"ok": True, "db": nombre, "operacion": args.operation})


def cmd_verify_marker(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    datos = _leer(manifest)
    if datos.get("status") != "open":
        raise RuntimeError("Fail-closed: manifiesto cerrado.")
    pruebas, principal = _motores()
    _exigir_pruebas(pruebas)
    _exigir_principal(principal)
    with pruebas.connect() as conexion:
        en_pruebas = int(
            conexion.execute(
                text("SELECT COUNT(*) FROM dbo.usuarios WHERE email = :e"), {"e": args.email}
            ).scalar_one()
        )
    with principal.connect() as conexion:  # solo lectura
        en_principal = int(
            conexion.execute(
                text("SELECT COUNT(*) FROM dbo.usuarios WHERE email = :e"), {"e": args.email}
            ).scalar_one()
        )
    pruebas.dispose()
    principal.dispose()
    ok = en_pruebas == 1 and en_principal == 0
    if not ok:
        raise RuntimeError(
            f"Fail-closed: marcador API en pruebas={en_pruebas}, en principal={en_principal}."
        )
    _impresion({"ok": True, "marcador_en": TEST_DB, "ausente_en": MAIN_DB})


def cmd_identifiers(args: argparse.Namespace) -> None:
    pruebas, principal = _motores()
    _exigir_pruebas(pruebas)
    _exigir_principal(principal)
    usados: set[str] = set()
    dnis: set[str] = set()
    for engine in (pruebas, principal):
        with engine.connect() as conexion:
            usados.update(
                str(f[0]) for f in conexion.execute(text("SELECT email FROM dbo.usuarios")).all()
            )
            dnis.update(
                str(f[0])
                for f in conexion.execute(text("SELECT dni FROM dbo.usuarios WHERE dni IS NOT NULL")).all()
            )
    semilla = args.seed
    salida = []
    indice = 0
    while len(salida) < args.count:
        indice += 1
        digest = hashlib.sha256(f"{semilla}:{indice}".encode("utf-8")).hexdigest()
        email = f"e2e-{digest[:12]}@example.com"
        dni = str(int(digest[12:20], 16) % 90_000_000 + 10_000_000)
        if email in usados or dni in dnis:
            continue
        usados.add(email)
        dnis.add(dni)
        salida.append({"email": email, "dni": dni})
    pruebas.dispose()
    principal.dispose()
    _impresion(salida)


def cmd_choose_source(args: argparse.Namespace) -> None:
    pruebas, _ = _motores()
    _exigir_pruebas(pruebas)
    with pruebas.connect() as conexion:
        fila = conexion.execute(
            text(
                """
                SELECT TOP (1) m.id, m.nombre, m.refugio_id
                FROM dbo.mascotas m
                WHERE m.estado = 'disponible'
                  AND NOT EXISTS (
                      SELECT 1 FROM dbo.solicitudes s
                      WHERE s.mascota_id = m.id AND s.estado = 'activa'
                  )
                ORDER BY m.id
                """
            )
        ).mappings().first()
    pruebas.dispose()
    if fila is None:
        raise RuntimeError("No hay mascota disponible sin solicitud activa para clonar.")
    _impresion(dict(fila))


def cmd_track_solicitudes(args: argparse.Namespace) -> None:
    """Registra solicitudes creadas por usuarios/mascotas del manifiesto.

    El filtro usa únicamente ids exactos del manifiesto: no hay búsquedas por
    rangos ni limpiezas globales.
    """
    manifest = Path(args.manifest)
    datos = _leer(manifest)
    if datos.get("status") != "open":
        raise RuntimeError("Fail-closed: manifiesto cerrado.")
    registros = datos.get("records", {})
    users = [int(r["id"]) for r in registros.get("users", []) if "id" in r]
    mascotas = [int(r["id"]) for r in registros.get("mascotas", []) if "id" in r]
    if not users or not mascotas:
        raise RuntimeError("Fail-closed: faltan usuarios o mascotas en el manifiesto.")
    pruebas, _ = _motores()
    _exigir_pruebas(pruebas)
    condiciones = [
        f"usuario_id IN ({','.join(map(str, users))})",
        f"mascota_id IN ({','.join(map(str, mascotas))})",
    ]
    with pruebas.connect() as conexion:
        filas = conexion.execute(
            text(
                "SELECT id, codigo, usuario_id, mascota_id, estado "
                f"FROM dbo.solicitudes WHERE {' OR '.join(condiciones)} ORDER BY id"
            )
        ).mappings().all()
    ya_registradas = {
        int(r["id"]) for r in registros.get("solicitudes", []) if "id" in r
    }
    añadidas = 0
    for fila in filas:
        if int(fila["id"]) in ya_registradas:
            continue
        _registrar(
            manifest,
            "solicitudes",
            id=int(fila["id"]),
            codigo=str(fila["codigo"]),
            usuario_id=int(fila["usuario_id"]),
            mascota_id=int(fila["mascota_id"]),
            estado_inicial=str(fila["estado"]),
        )
        añadidas += 1
    pruebas.dispose()
    _impresion({"registradas": len(filas), "añadidas": añadidas})


def cmd_create_role_users(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    datos = _leer(manifest)
    if datos.get("status") != "open":
        raise RuntimeError("Fail-closed: manifiesto cerrado.")
    pruebas, _ = _motores()
    _exigir_pruebas(pruebas)
    ahora = datetime.now(timezone.utc)
    creados = {}
    with Session(pruebas) as sesion, sesion.begin():
        for rol, email, dni, refugio_id in (
            ("refugio", args.email_refugio, args.dni_refugio, args.refugio_id),
            ("admin", args.email_admin, args.dni_admin, None),
        ):
            fila = db.Usuario(
                nombres=f"E2E {rol.title()} {args.run_id}"[:120],
                apellidos="Prueba",
                email=email,
                dni=dni,
                password_hash=hash_password(args.password),
                rol=rol,
                telefono="900000000",
                activo=True,
                refugio_id=refugio_id,
                creado_en=ahora,
            )
            sesion.add(fila)
            sesion.flush()
            creados[rol] = {"id": int(fila.id), "email": email, "rol": rol}
    for info in creados.values():
        _registrar(manifest, "users", **info)
    pruebas.dispose()
    _impresion(creados)


def cmd_create_adoptantes(args: argparse.Namespace) -> None:
    """Crea adoptantes de fixture, sin pasar por el registro público.

    Se usa para las cuentas auxiliares: así el registro público se prueba una
    sola vez y no se agota el límite de 5 registros/minuto por IP.
    """
    manifest = Path(args.manifest)
    datos = _leer(manifest)
    if datos.get("status") != "open":
        raise RuntimeError("Fail-closed: manifiesto cerrado.")
    correos = json.loads(args.correos)
    dnis = json.loads(args.dnis)
    if not isinstance(correos, list) or not isinstance(dnis, list) or len(correos) != len(dnis) or not correos:
        raise RuntimeError("Fail-closed: correos y dnis deben ser listas del mismo tamaño.")
    pruebas, _ = _motores()
    _exigir_pruebas(pruebas)
    ahora = datetime.now(timezone.utc)
    creados = []
    with Session(pruebas) as sesion, sesion.begin():
        for indice, (email, dni) in enumerate(zip(correos, dnis)):
            fila = db.Usuario(
                nombres=f"E2E Adoptante {args.run_id} {indice}"[:120],
                apellidos="Prueba",
                email=str(email),
                dni=str(dni),
                password_hash=hash_password(args.password),
                rol="adoptante",
                telefono="900000001",
                activo=True,
                refugio_id=None,
                creado_en=ahora,
            )
            sesion.add(fila)
            sesion.flush()
            creados.append({"id": int(fila.id), "email": str(email), "rol": "adoptante"})
    for info in creados:
        _registrar(manifest, "users", **info)
    pruebas.dispose()
    _impresion(creados)


def cmd_track_distritos(args: argparse.Namespace) -> None:
    """Registra distritos creados por el registro público de este run."""
    manifest = Path(args.manifest)
    datos = _leer(manifest)
    if datos.get("status") != "open":
        raise RuntimeError("Fail-closed: manifiesto cerrado.")
    base_ids = {int(x) for x in datos.get("baseline_distrito_ids", [])}
    registros = datos.get("records", {})
    users = [int(r["id"]) for r in registros.get("users", []) if "id" in r]
    pruebas, _ = _motores()
    _exigir_pruebas(pruebas)
    with pruebas.connect() as conexion:
        actuales = [
            int(f[0])
            for f in conexion.execute(text("SELECT id FROM dbo.distritos ORDER BY id")).all()
        ]
        nuevos = [identificador for identificador in actuales if identificador not in base_ids]
        referidos: list[int] = []
        if nuevos and users:
            marcas = ",".join(map(str, nuevos))
            ids_usuarios = ",".join(map(str, users))
            referidos = [
                int(f[0])
                for f in conexion.execute(
                    text(
                        f"SELECT DISTINCT distrito_id FROM dbo.usuarios "
                        f"WHERE id IN ({ids_usuarios}) AND distrito_id IN ({marcas})"
                    )
                ).all()
                if f[0] is not None
            ]
    ya_registrados = {
        int(r["id"]) for r in registros.get("distritos", []) if "id" in r
    }
    añadidos = 0
    for identificador in referidos:
        if identificador in ya_registrados:
            continue
        _registrar(manifest, "distritos", id=identificador)
        añadidos += 1
    pruebas.dispose()
    _impresion({"nuevos": len(nuevos), "referidos": len(referidos), "añadidos": añadidos})


def cmd_create_mascota(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    datos = _leer(manifest)
    if datos.get("status") != "open":
        raise RuntimeError("Fail-closed: manifiesto cerrado.")
    pruebas, _ = _motores()
    _exigir_pruebas(pruebas)
    with pruebas.begin() as conexion:
        tabla = db.Mascota.__table__
        original = conexion.execute(
            select(tabla).where(tabla.c.id == args.source_id)
        ).mappings().one()
        valores = dict(original)
        valores.pop("id", None)
        valores.update(
            {
                "nombre": args.nombre[:80],
                "nombre_corto": f"E2E-{args.run_id[-6:]}"[:40],
                "estado": "disponible",
                "destacada": False,
                "urgente": False,
                "creado_en": datetime.now(timezone.utc),
                "actualizado_en": None,
            }
        )
        if args.foto_principal:
            valores["foto_principal"] = args.foto_principal
        nuevo = conexion.execute(insert(tabla).values(**valores))
        mascota_id = int(nuevo.inserted_primary_key[0])
        for modelo in HijasMascota:
            hija = modelo.__table__
            filas = conexion.execute(
                select(hija).where(hija.c.mascota_id == args.source_id)
            ).mappings().all()
            for fila in filas:
                valores_hija = dict(fila)
                valores_hija.pop("id", None)
                valores_hija["mascota_id"] = mascota_id
                conexion.execute(insert(hija).values(**valores_hija))
    _registrar(
        manifest,
        "mascotas",
        id=mascota_id,
        nombre=args.nombre[:80],
        refugio_id=str(original["refugio_id"]),
        source_id=args.source_id,
    )
    pruebas.dispose()
    _impresion(
        {
            "id": mascota_id,
            "nombre": args.nombre[:80],
            "refugio_id": str(original["refugio_id"]),
        }
    )


def cmd_inspect(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    datos = _leer(manifest)
    pruebas, principal = _motores()
    _exigir_pruebas(pruebas)
    _exigir_principal(principal)
    registros = datos.get("records", {})
    users = [int(r["id"]) for r in registros.get("users", []) if "id" in r]
    mascotas = [int(r["id"]) for r in registros.get("mascotas", []) if "id" in r]
    sols = [int(r["id"]) for r in registros.get("solicitudes", []) if "id" in r]
    salida: dict[str, Any] = {"db": TEST_DB}
    with pruebas.connect() as conexion:
        def filtros(columna: str, valores: list[int]) -> str:
            return ",".join(str(v) for v in valores) if valores else "NULL"

        salida["usuarios"] = [
            dict(f)
            for f in conexion.execute(
                text(f"SELECT id, email, rol, refugio_id, activo FROM dbo.usuarios WHERE id IN ({filtros('id', users)})")
            ).mappings().all()
        ] if users else []
        salida["mascotas"] = [
            dict(f)
            for f in conexion.execute(
                text(f"SELECT id, nombre, refugio_id, estado FROM dbo.mascotas WHERE id IN ({filtros('id', mascotas)})")
            ).mappings().all()
        ] if mascotas else []
        salida["solicitudes"] = [
            dict(f)
            for f in conexion.execute(
                text(
                    f"SELECT id, codigo, usuario_id, mascota_id, estado, etapa, motivo_cancelacion "
                    f"FROM dbo.solicitudes WHERE id IN ({filtros('id', sols)})"
                )
            ).mappings().all()
        ] if sols else []
        for tabla in ("mensajes", "citas", "solicitud_eventos"):
            salida[tabla] = (
                [
                    dict(f)
                    for f in conexion.execute(
                        text(f"SELECT * FROM dbo.{tabla} WHERE solicitud_id IN ({filtros('id', sols)}) ORDER BY id")
                    ).mappings().all()
                ]
                if sols
                else []
            )
        conditions = []
        if users:
            conditions.append(f"usuario_id IN ({filtros('id', users)})")
        if mascotas:
            conditions.append(f"mascota_id IN ({filtros('id', mascotas)})")
        salida["favoritos"] = (
            [
                dict(f)
                for f in conexion.execute(
                    text(f"SELECT usuario_id, mascota_id, creado_en FROM dbo.favoritos WHERE {' OR '.join(conditions)}")
                ).mappings().all()
            ]
            if conditions
            else []
        )
    pruebas.dispose()
    principal.dispose()
    _impresion(salida)


def cmd_rollback_fixture(args: argparse.Namespace) -> None:
    """Fixture SQL aislada: inserción y rollback forzado; verifica que nada persista."""
    manifest = Path(args.manifest)
    if _leer(manifest).get("status") != "open":
        raise RuntimeError("Fail-closed: manifiesto cerrado.")
    pruebas, _ = _motores()
    _exigir_pruebas(pruebas)
    sello = f"ROLLBACK-{args.run_id}-{datetime.now(timezone.utc).timestamp():.0f}"
    try:
        with pruebas.begin() as conexion:
            conexion.execute(
                insert(db.Mensaje).values(
                    solicitud_id=args.solicitud_id,
                    autor_id=args.autor_id,
                    texto=sello,
                    creado_en=datetime.now(timezone.utc),
                )
            )
            raise RuntimeError("Fallo simulado antes del commit")
    except RuntimeError as error:
        if "Fallo simulado" not in str(error):
            raise
    with pruebas.connect() as conexion:
        persistidas = int(
            conexion.execute(
                text("SELECT COUNT(*) FROM dbo.mensajes WHERE texto = :s"), {"s": sello}
            ).scalar_one()
        )
    pruebas.dispose()
    if persistidas:
        raise RuntimeError("Fail: la fila del rollback persistió.")
    _impresion({"ok": True, "rollback_verificado": True, "filas_persistidas": 0})


def cmd_cleanup(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    datos = _leer(manifest)
    if datos.get("status") != "open":
        _impresion({"ok": True, "omitido": datos.get("status")})
        return
    pruebas, principal = _motores()
    nombre = _exigir_pruebas(pruebas)
    _exigir_principal(principal)
    registros = datos.get("records", {})
    users = [int(r["id"]) for r in registros.get("users", []) if "id" in r]
    mascotas = [int(r["id"]) for r in registros.get("mascotas", []) if "id" in r]
    sols = [int(r["id"]) for r in registros.get("solicitudes", []) if "id" in r]
    distritos = [int(r["id"]) for r in registros.get("distritos", []) if "id" in r]
    borrados: dict[str, int] = {}
    with pruebas.begin() as conexion:
        def borrar(tabla: str, columna: str, valores: list[int]) -> None:
            if not valores:
                return
            resultado = conexion.execute(
                text(f"DELETE FROM dbo.{tabla} WHERE {columna} IN ({','.join(map(str, valores))})")
            )
            borrados[tabla] = borrados.get(tabla, 0) + (resultado.rowcount or 0)

        for tabla in (
            "seguimiento_fotos",
            "citas",
            "mensajes",
            "solicitud_eventos",
        ):
            borrar(tabla, "solicitud_id", sols)
        for tabla in (
            "mascota_salud",
            "mascota_fotos",
            "mascota_rasgos",
            "mascota_historia",
            "mascota_cuidados",
        ):
            borrar(tabla, "mascota_id", mascotas)
        if users:
            resultado = conexion.execute(
                text(
                    f"DELETE FROM dbo.favoritos WHERE usuario_id IN ({','.join(map(str, users))})"
                )
            )
            borrados["favoritos"] = resultado.rowcount or 0
        if mascotas:
            resultado = conexion.execute(
                text(
                    f"DELETE FROM dbo.favoritos WHERE mascota_id IN ({','.join(map(str, mascotas))})"
                )
            )
            borrados["favoritos"] = borrados.get("favoritos", 0) + (resultado.rowcount or 0)
        borrar("solicitudes", "id", sols)
        borrar("mascotas", "id", mascotas)
        borrar("usuarios", "id", users)
        # Los distritos se borran al final: solo los creados por este run y
        # referidos por sus usuarios, nunca un distrito preexistente.
        borrar("distritos", "id", distritos)

    archivos = 0
    for ruta in registros.get("files", []):
        archivo = Path(str(ruta["path"]))
        if archivo.is_file():
            archivo.unlink()
            archivos += 1

    final = _huella(pruebas)
    final_principal = _conteos(principal)
    baseline = datos.get("baseline", {})
    baseline_principal = datos.get("baseline_principal_counts", {})
    coinciden = final == baseline
    principal_intacta = final_principal == baseline_principal
    datos["cleanup"] = {
        "en": datetime.now(timezone.utc).isoformat(),
        "db": nombre,
        "borrados": borrados,
        "archivos_borrados": archivos,
        "coincide_con_baseline": coinciden,
        "leonsdb_intacta": principal_intacta,
        "final": final,
        "final_principal_counts": final_principal,
    }
    datos["status"] = "closed" if coinciden and principal_intacta else "cleanup_failed"
    _escribir(manifest, datos)
    pruebas.dispose()
    principal.dispose()
    if not coinciden:
        raise RuntimeError("La limpieza no restauró LeonsDB_Test; revisar manifest.")
    if not principal_intacta:
        raise RuntimeError("LeonsDB cambió respecto al baseline; revisar manifest.")
    _impresion({"ok": True, "db": nombre, "borrados": borrados, "baseline": "restaurado"})


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Soporte E2E controlado de LeonS.")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("init")
    p.add_argument("--manifest", required=True)
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("guard")
    p.add_argument("--manifest", required=True)
    p.add_argument("--operation", required=True)
    p.set_defaults(func=cmd_guard)

    p = sub.add_parser("verify-marker")
    p.add_argument("--manifest", required=True)
    p.add_argument("--email", required=True)
    p.set_defaults(func=cmd_verify_marker)

    p = sub.add_parser("identifiers")
    p.add_argument("--manifest", required=True)
    p.add_argument("--seed", required=True)
    p.add_argument("--count", type=int, default=4)
    p.set_defaults(func=cmd_identifiers)

    p = sub.add_parser("choose-source")
    p.set_defaults(func=cmd_choose_source)

    p = sub.add_parser("track-solicitudes")
    p.add_argument("--manifest", required=True)
    p.set_defaults(func=cmd_track_solicitudes)

    p = sub.add_parser("track-distritos")
    p.add_argument("--manifest", required=True)
    p.set_defaults(func=cmd_track_distritos)

    p = sub.add_parser("create-adoptantes")
    p.add_argument("--manifest", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--correos", required=True, help="JSON con la lista de correos")
    p.add_argument("--dnis", required=True, help="JSON con la lista de DNIs")
    p.add_argument("--password", required=True)
    p.set_defaults(func=cmd_create_adoptantes)

    p = sub.add_parser("create-role-users")
    p.add_argument("--manifest", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--refugio-id", required=True)
    p.add_argument("--email-refugio", required=True)
    p.add_argument("--dni-refugio", required=True)
    p.add_argument("--email-admin", required=True)
    p.add_argument("--dni-admin", required=True)
    p.add_argument("--password", required=True)
    p.set_defaults(func=cmd_create_role_users)

    p = sub.add_parser("create-mascota")
    p.add_argument("--manifest", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--source-id", type=int, required=True)
    p.add_argument("--nombre", required=True)
    p.add_argument("--foto-principal", default=None)
    p.set_defaults(func=cmd_create_mascota)

    p = sub.add_parser("inspect")
    p.add_argument("--manifest", required=True)
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("rollback-fixture")
    p.add_argument("--manifest", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--solicitud-id", type=int, required=True)
    p.add_argument("--autor-id", type=int, required=True)
    p.set_defaults(func=cmd_rollback_fixture)

    p = sub.add_parser("cleanup")
    p.add_argument("--manifest", required=True)
    p.set_defaults(func=cmd_cleanup)

    return parser


def main() -> int:
    args = construir_parser().parse_args()
    try:
        args.func(args)
    except Exception as error:  # noqa: BLE001 - se reporta sin secretos
        print(f"ERROR E2E_SUPPORT: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
