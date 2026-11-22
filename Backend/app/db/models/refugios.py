"""Refugios y sus especies admitidas."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Integer,
    SmallInteger,
    Unicode,
    text,
)
from sqlalchemy.dialects.mssql import DATETIME2, NVARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Refugio(Base):
    __tablename__ = "refugios"

    id: Mapped[str] = mapped_column(Unicode(60), primary_key=True)
    nombre: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    # Orden editorial del listado (D-035). `NULL` = al final, por nombre.
    orden: Mapped[int | None] = mapped_column(SmallInteger)
    descripcion: Mapped[str | None] = mapped_column(NVARCHAR(None))
    distrito_id: Mapped[int | None] = mapped_column(ForeignKey("distritos.id"))
    direccion: Mapped[str | None] = mapped_column(Unicode(250))
    telefono: Mapped[str | None] = mapped_column(Unicode(30))
    whatsapp: Mapped[str | None] = mapped_column(Unicode(30))
    email: Mapped[str | None] = mapped_column(Unicode(180))
    adoptadas_historicas: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    en_acogida_actual: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )

    # Columnas del contrato JSON (delta 0002).
    contacto: Mapped[str | None] = mapped_column(Unicode(120))
    cargo: Mapped[str | None] = mapped_column(Unicode(120))
    tipo: Mapped[str | None] = mapped_column(Unicode(20))
    desde: Mapped[int | None] = mapped_column(SmallInteger)
    verificado: Mapped[bool] = mapped_column(nullable=False, server_default=text("1"))
    logo: Mapped[str | None] = mapped_column(Unicode(500))

    distrito = relationship("Distrito", back_populates="refugios")
    mascotas = relationship("Mascota", back_populates="refugio")
    especies = relationship(
        "RefugioEspecie", back_populates="refugio", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "adoptadas_historicas >= 0 AND en_acogida_actual >= 0",
            name="contadores",
        ),
        CheckConstraint(
            "tipo IS NULL OR tipo IN ('constituido', 'independiente')", name="tipo"
        ),
        Index("IX_refugios_distrito", "distrito_id"),
    )


class RefugioEspecie(Base):
    __tablename__ = "refugio_especies"

    refugio_id: Mapped[str] = mapped_column(
        ForeignKey("refugios.id", ondelete="CASCADE"), primary_key=True
    )
    especie: Mapped[str] = mapped_column(Unicode(20), primary_key=True)

    refugio = relationship("Refugio", back_populates="especies")

    __table_args__ = (CheckConstraint("especie IN ('perro', 'gato')", name="especie"),)
