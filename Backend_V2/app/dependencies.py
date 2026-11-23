"""Dependencias de FastAPI: contenedor, usuario actual y roles."""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings
from .container import Container
from .domain import Rol, Usuario
from .errors import ForbiddenError, UnauthorizedError
from .repositories.memory import MemoryRepository
from .security import leer_token

bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_repo(container: Container = Depends(get_container)) -> MemoryRepository:
    return container.repo


def get_app_settings(container: Container = Depends(get_container)) -> Settings:
    return container.settings


def _resolver_usuario(
    credentials: HTTPAuthorizationCredentials | None, container: Container
) -> Usuario:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Falta el token Bearer.")
    payload = leer_token(credentials.credentials, container.settings)
    try:
        usuario_id = int(payload.get("sub", "0"))
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Token inválido.") from exc
    usuario = container.repo.obtener_usuario(usuario_id)
    if usuario is None:
        raise UnauthorizedError("El usuario del token ya no existe.")
    return usuario


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    container: Container = Depends(get_container),
) -> Usuario:
    return _resolver_usuario(credentials, container)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    container: Container = Depends(get_container),
) -> Usuario | None:
    if credentials is None:
        return None
    return _resolver_usuario(credentials, container)


def require_roles(*roles: Rol) -> Callable[..., Usuario]:
    def dependencia(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in roles:
            raise ForbiddenError("Tu rol no tiene permisos para esta acción.")
        return usuario

    return dependencia
