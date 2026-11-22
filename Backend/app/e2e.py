"""Fail-closed del entorno E2E.

Cuando el proceso lleva `E2E_EXPECT_DB`, la API solo puede arrancar si la
**conexión efectiva** (la que usa el repositorio, derivada de `Settings.db_url`)
responde `SELECT DB_NAME() = 'LeonsDB_Test'`. No se confía en el texto de la URL.

Sin esa variable el comportamiento es exactamente el anterior, así que el
servidor de desarrollo no se ve afectado.
"""

from __future__ import annotations

import os

from sqlalchemy import text

from .config import Settings, get_settings
from .db.session import crear_engine

BASE_E2E = "LeonsDB_Test"
_VALORES_ACTIVOS = frozenset({"1", "true", "yes", "si", BASE_E2E.lower()})


def e2e_activo() -> bool:
    """Indica si este proceso está declarado como entorno E2E."""
    return os.getenv("E2E_EXPECT_DB", "").strip().lower() in _VALORES_ACTIVOS


def verificar_base_e2e(settings: Settings | None = None) -> str | None:
    """Devuelve la base efectiva si es E2E y es la correcta; si no, aborta.

    El error no incluye la cadena de conexión: puede contener credenciales.
    """
    if not e2e_activo():
        return None
    efectiva = settings or get_settings()
    motor = crear_engine(efectiva.db_url)
    try:
        with motor.connect() as conexion:
            nombre = conexion.execute(text("SELECT DB_NAME()")).scalar_one()
    finally:
        motor.dispose()
    if nombre != BASE_E2E:
        raise RuntimeError(
            f"E2E fail-closed: la conexión efectiva apunta a {nombre!r}; "
            f"se exige {BASE_E2E!r}. No se inicia la API."
        )
    return nombre


def main() -> int:
    """Comprobación aislada: solo consulta `DB_NAME()` y termina; nunca sirve tráfico."""
    import argparse

    parser = argparse.ArgumentParser(description="Verifica el fail-closed de base E2E.")
    parser.add_argument(
        "--usar-url",
        choices=("actual", "main", "test"),
        default="actual",
        help="Qué URL de .env usar como DB_URL para la comprobación.",
    )
    args = parser.parse_args()

    base = get_settings()
    if args.usar_url == "main":
        os.environ["DB_URL"] = base.db_url
    elif args.usar_url == "test":
        os.environ["DB_URL"] = base.db_test_url
    os.environ["E2E_EXPECT_DB"] = BASE_E2E
    get_settings.cache_clear()

    try:
        nombre = verificar_base_e2e()
    except Exception as error:  # noqa: BLE001 - se reporta sin exponer la URL
        print(f"FALLO fail-closed: {error}")
        return 1
    print(f"OK fail-closed: SELECT DB_NAME() = {nombre}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
