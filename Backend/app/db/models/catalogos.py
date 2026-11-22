"""Catálogos: distritos y migraciones."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Identity, Unicode, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Distrito(Base):
    __tablename__ = "distritos"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    nombre: Mapped[str] = mapped_column(Unicode(80), nullable=False, unique=True)
    provincia: Mapped[str | None] = mapped_column(Unicode(80))

    refugios = relationship("Refugio", back_populates="distrito")
    usuarios = relationship("Usuario", back_populates="distrito")
    alertas = relationship("AlertaRescate", back_populates="distrito")


class Migracion(Base):
    """Registro funcional de migraciones del equipo (no es `alembic_version`)."""

    __tablename__ = "migraciones"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    nombre: Mapped[str] = mapped_column(Unicode(100), nullable=False, unique=True)
    aplicada_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )
