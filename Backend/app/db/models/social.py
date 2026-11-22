"""Favoritos y alertas de rescate."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
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


class Favorito(Base):
    __tablename__ = "favoritos"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    mascota_id: Mapped[int] = mapped_column(
        ForeignKey("mascotas.id", ondelete="CASCADE"), primary_key=True
    )
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )

    __table_args__ = (Index("IX_favoritos_mascota", "mascota_id"),)


class AlertaRescate(Base):
    __tablename__ = "alertas_rescate"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    nombre: Mapped[str] = mapped_column(Unicode(120), nullable=False)
    especie: Mapped[str | None] = mapped_column(Unicode(20))
    descripcion: Mapped[str] = mapped_column(Unicode(1000), nullable=False)
    ubicacion: Mapped[str | None] = mapped_column(Unicode(250))
    distrito_id: Mapped[int | None] = mapped_column(ForeignKey("distritos.id"))
    contacto: Mapped[str | None] = mapped_column(Unicode(100))
    mensaje: Mapped[str | None] = mapped_column(Unicode(1000))
    estado: Mapped[str] = mapped_column(
        Unicode(20), nullable=False, server_default=text("N'nueva'")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )

    distrito = relationship("Distrito", back_populates="alertas")
    usuario = relationship("Usuario")

    __table_args__ = (
        CheckConstraint(
            "especie IS NULL OR especie IN ('perro', 'gato')", name="especie"
        ),
        CheckConstraint("estado IN ('nueva', 'atendida', 'cerrada')", name="estado"),
        Index("IX_alertas_rescate_fecha", "creado_en"),
    )
