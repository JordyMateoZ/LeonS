"""Guard de arranque de producción contra cuentas de demostración (AUD-02).

Solo actúa cuando ``APP_ENV=production`` y ``REPOS_BACKEND=sqlserver``. Consulta,
sin modificar datos, si la base contiene alguno de los correos demo definidos en
``app/data/loader.py`` (D-016). Si hay coincidencias —o si la verificación no
puede completarse— aborta el arranque con un mensaje genérico: no revela correos,
hashes, contraseñas, JWT ni cadenas de conexión.

Esta protección **no reemplaza** la rotación o eliminación controlada de
credenciales conocidas antes de un despliegue real; solo impide reutilizar
silenciosamente una base sembrada para demostración.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy import bindparam, text

from .config import Settings
from .data.loader import DEMO_USERS

logger = logging.getLogger("leons")

MENSAJE_CUENTAS_DEMO = (
    "La base contiene cuentas de demostración; arranque de producción rechazado."
)
MENSAJE_VERIFICACION_FALLIDA = (
    "No se pudo verificar la ausencia de cuentas de demostración; "
    "arranque de producción rechazado."
)


def correos_demo() -> tuple[str, ...]:
    """Devuelve los marcadores existentes, normalizados, sin secretos."""
    return tuple(str(usuario["email"]).strip().lower() for usuario in DEMO_USERS)


def contar_cuentas_demo(motor) -> int:
    """Cuenta cuentas demo con una consulta parametrizada de alcance mínimo."""
    consulta = text(
        "SELECT COUNT(*) FROM dbo.usuarios WHERE LOWER(email) IN :correos"
    ).bindparams(bindparam("correos", expanding=True))
    with motor.connect() as conexion:
        total = conexion.execute(consulta, {"correos": correos_demo()}).scalar_one()
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise TypeError("Resultado inesperado al verificar cuentas de demostración.")
    return total


def verificar_arranque_produccion(
    settings: Settings, *, contador: Callable[[], int] | None = None
) -> None:
    """Fail-closed en producción; inactivo en desarrollo y pruebas.

    ``contador`` permite probar el guard con stubs sin base de datos. En la app
    real se omite y se construye un motor a partir de ``settings.db_url``.
    """
    if settings.app_env != "production" or settings.repos_backend != "sqlserver":
        return

    try:
        if contador is not None:
            total = contador()
        else:
            from .db.session import crear_engine

            motor = crear_engine(settings.db_url)
            try:
                total = contar_cuentas_demo(motor)
            finally:
                motor.dispose()
    except Exception:
        # Se registra el hecho sin motivos, URLs ni datos de las cuentas.
        logger.error("No se pudo verificar cuentas demo en el arranque de producción.")
        raise RuntimeError(MENSAJE_VERIFICACION_FALLIDA) from None

    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise RuntimeError(MENSAJE_VERIFICACION_FALLIDA)
    if total > 0:
        logger.error("Se detectaron cuentas demo en el arranque de producción.")
        raise RuntimeError(MENSAJE_CUENTAS_DEMO)

    logger.info("Verificación de cuentas demo de producción completada.")
