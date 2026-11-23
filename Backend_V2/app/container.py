"""Inyección de dependencias: repositorio, almacenamiento y adaptadores."""

from __future__ import annotations

from dataclasses import dataclass

from .adapters.notifications import LogNotifier
from .adapters.rate_limit import RateLimiter
from .adapters.storage import LocalStorage
from .config import Settings
from .data.loader import cargar_seed
from .repositories.memory import MemoryRepository


@dataclass(slots=True)
class Container:
    settings: Settings
    repo: MemoryRepository
    storage: LocalStorage
    limiter: RateLimiter
    notifier: LogNotifier


def build_container(settings: Settings) -> Container:
    if settings.repos_backend != "memory":
        raise RuntimeError(
            "REPOS_BACKEND=sqlserver todavía no está implementado: "
            "corresponde a la Fase 6 del AGENTS.md."
        )

    seed = cargar_seed(settings.seed_path)
    return Container(
        settings=settings,
        repo=MemoryRepository(seed),
        storage=LocalStorage(settings.uploads_dir),
        limiter=RateLimiter(settings.rate_limit_alerts_max, settings.rate_limit_window_seconds),
        notifier=LogNotifier(),
    )
