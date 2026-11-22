"""Capa de base de datos (SQLAlchemy 2.0 + Alembic).

La Fase 5 solo define modelos y migraciones; la sesión y el repositorio
SQL Server se implementan en la Fase 6.
"""

from __future__ import annotations

from .base import Base

__all__ = ["Base"]
