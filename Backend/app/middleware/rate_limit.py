from __future__ import annotations

from fastapi import Request

from app.middleware.auth import Deps


def _clave(request: Request, prefijo: str) -> str:
    host = request.client.host if request.client else "desconocido"
    return f"{prefijo}:{host}"


async def limitar_auth(request: Request, deps: Deps) -> None:
    await deps.auth_limiter.verificar(_clave(request, "auth"))


async def limitar_alertas(request: Request, deps: Deps) -> None:
    await deps.alertas_limiter.verificar(_clave(request, "alertas"))
