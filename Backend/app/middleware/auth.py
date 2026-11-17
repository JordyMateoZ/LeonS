from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, Request

from app.config import settings
from app.container import Dependencies, get_dependencies
from app.domain import Role, Usuario
from app.errors import ForbiddenError, UnauthorizedError

Deps = Annotated[Dependencies, Depends(get_dependencies)]


def firmar_token(usuario: Usuario) -> str:
    expiracion = datetime.now(timezone.utc) + settings.jwt_expiration
    payload = {
        "sub": usuario.id,
        "email": usuario.email,
        "rol": usuario.rol,
        "exp": expiracion,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


async def _usuario_desde_request(request: Request, deps: Dependencies, obligatorio: bool) -> Usuario | None:
    cabecera = request.headers.get("authorization", "")
    partes = cabecera.split()
    if not partes:
        if obligatorio:
            raise UnauthorizedError("Se requiere un token Bearer")
        return None
    if len(partes) != 2 or partes[0].lower() != "bearer":
        raise UnauthorizedError("Se requiere un token Bearer")

    try:
        payload = jwt.decode(partes[1], settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token inválido o expirado") from exc

    usuario_id = payload.get("sub")
    if not isinstance(usuario_id, str):
        raise UnauthorizedError("Token inválido")

    usuario = await deps.repos.usuarios.find_by_id(usuario_id)
    if not usuario or not usuario.activo:
        raise UnauthorizedError("La cuenta no está activa")
    return usuario


async def get_current_user(request: Request, deps: Deps) -> Usuario:
    usuario = await _usuario_desde_request(request, deps, obligatorio=True)
    if usuario is None:  # pragma: no cover - defensa de tipos
        raise UnauthorizedError()
    return usuario


async def get_optional_user(request: Request, deps: Deps) -> Usuario | None:
    return await _usuario_desde_request(request, deps, obligatorio=False)


AuthUser = Annotated[Usuario, Depends(get_current_user)]
OptionalAuthUser = Annotated[Usuario | None, Depends(get_optional_user)]


def require_roles(*roles: Role):
    async def dependency(usuario: AuthUser) -> Usuario:
        if usuario.rol not in roles:
            raise ForbiddenError()
        return usuario

    return dependency
