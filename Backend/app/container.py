"""Inyección de dependencias: repositorio, almacenamiento y adaptadores."""

from __future__ import annotations

from dataclasses import dataclass

from .adapters.notifications import LogNotifier
from .adapters.rate_limit import RateLimiter
from .adapters.storage import LocalStorage
from .config import Settings
from .domain import Repositorio


@dataclass(slots=True)
class Container:
    settings: Settings
    repo: Repositorio
    storage: LocalStorage
    limiter: RateLimiter
    limiter_auth: RateLimiter
    limiter_register: RateLimiter
    notifier: LogNotifier


def build_container(settings: Settings) -> Container:
    if settings.repos_backend == "sqlserver":
        from .repositories.sqlserver import SqlServerRepository

        repo: Repositorio = SqlServerRepository(settings.db_url, settings.uploads_dir)
    else:
        from .data.loader import cargar_seed
        from .repositories.memory import MemoryRepository

        seed = cargar_seed(settings.seed_path)
        repo = MemoryRepository(seed)

    return Container(
        settings=settings,
        repo=repo,
        storage=LocalStorage(settings.uploads_dir),
        limiter=RateLimiter(settings.rate_limit_alerts_max, settings.rate_limit_window_seconds),
        limiter_auth=RateLimiter(settings.rate_limit_auth_max, settings.rate_limit_auth_window_seconds),
        limiter_register=RateLimiter(settings.rate_limit_register_max, settings.rate_limit_register_window_seconds),
        notifier=LogNotifier(),
    )
