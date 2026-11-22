"""Contenido editorial y estadísticas de impacto."""

from __future__ import annotations

from ..domain import Contenido, Repositorio


def obtener_contenido(repo: Repositorio) -> Contenido:
    return repo.obtener_contenido()


def pasos(repo: Repositorio, tipo: str) -> list[dict[str, str]]:
    contenido = repo.obtener_contenido()
    return contenido.pasos_refugio if tipo == "refugio" else contenido.pasos_adopcion


def faqs(repo: Repositorio) -> list[dict[str, str]]:
    return repo.obtener_contenido().faqs
