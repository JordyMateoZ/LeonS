from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request

from app.adapters import (
    LocalStorageAdapter,
    LogNotificacionesAdapter,
    NotificacionesAdapter,
    StorageAdapter,
)
from app.adapters.rate_limit import RateLimiter
from app.config import settings
from app.domain import Repositorios
from app.repositories import crear_repositorios


@dataclass
class Dependencies:
    repos: Repositorios
    storage: StorageAdapter
    notificaciones: NotificacionesAdapter
    auth_limiter: RateLimiter
    alertas_limiter: RateLimiter


def create_dependencies(overrides: dict[str, Any] | None = None) -> Dependencies:
    valores = overrides or {}
    return Dependencies(
        repos=valores.get("repos") or crear_repositorios(),
        storage=valores.get("storage") or LocalStorageAdapter(),
        notificaciones=valores.get("notificaciones") or LogNotificacionesAdapter(),
        auth_limiter=valores.get("auth_limiter")
        or RateLimiter(
            settings.rate_limit_auth_max,
            "Demasiados intentos. Intenta nuevamente en unos minutos.",
        ),
        alertas_limiter=valores.get("alertas_limiter")
        or RateLimiter(
            settings.rate_limit_alerts_max,
            "Demasiadas alertas enviadas. Intenta nuevamente en unos minutos.",
        ),
    )


def get_dependencies(request: Request) -> Dependencies:
    return request.app.state.deps
