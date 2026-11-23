"""Contenido editorial y estadísticas de impacto."""

from __future__ import annotations

from ..domain import Contenido
from ..repositories.memory import MemoryRepository


def obtener_contenido(repo: MemoryRepository) -> Contenido:
    return repo.obtener_contenido()


def pasos(repo: MemoryRepository, tipo: str) -> list[dict[str, str]]:
    contenido = repo.obtener_contenido()
    return contenido.pasos_refugio if tipo == "refugio" else contenido.pasos_adopcion


def faqs(repo: MemoryRepository) -> list[dict[str, str]]:
    return repo.obtener_contenido().faqs
