"""Usuarios de la plataforma y sus credenciales."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Unicode,
    text,
)
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    nombres: Mapped[str] = mapped_column(Unicode(120), nullable=False)
    apellidos: Mapped[str | None] = mapped_column(Unicode(120))
    email: Mapped[str] = mapped_column(Unicode(180), nullable=False, unique=True)
    dni: Mapped[str | None] = mapped_column(CHAR(8))
    password_hash: Mapped[str | None] = mapped_column(Unicode(255))
    google_id: Mapped[str | None] = mapped_column(Unicode(100))
    rol: Mapped[str] = mapped_column(
        Unicode(20), nullable=False, server_default=text("N'adoptante'")
    )
    telefono: Mapped[str | None] = mapped_column(Unicode(30))
    distrito_id: Mapped[int | None] = mapped_column(ForeignKey("distritos.id"))
    refugio_id: Mapped[str | None] = mapped_column(ForeignKey("refugios.id"))
    activo: Mapped[bool] = mapped_column(nullable=False, server_default=text("1"))
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )
    actualizado_en: Mapped[datetime | None] = mapped_column(DATETIME2)

    distrito = relationship("Distrito", back_populates="usuarios")
    refugio = relationship("Refugio")

    __table_args__ = (
        CheckConstraint("rol IN ('adoptante', 'refugio', 'admin')", name="rol"),
        CheckConstraint("dni IS NULL OR NOT dni LIKE '%[^0-9]%'", name="dni"),
        # Índices únicos filtrados: permiten varios NULL (Google y DNI opcional).
        Index(
            "UX_usuarios_dni",
            "dni",
            unique=True,
            mssql_where=text("dni IS NOT NULL"),
        ),
        Index(
            "UX_usuarios_google",
            "google_id",
            unique=True,
            mssql_where=text("google_id IS NOT NULL"),
        ),
    )
