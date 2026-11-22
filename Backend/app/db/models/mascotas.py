"""Mascotas y sus tablas hijas (salud, fotos y rasgos)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    SmallInteger,
    Unicode,
    text,
)
from sqlalchemy.dialects.mssql import DATETIME2, NVARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Mascota(Base):
    __tablename__ = "mascotas"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    refugio_id: Mapped[str] = mapped_column(ForeignKey("refugios.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(Unicode(80), nullable=False)
    especie: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    raza: Mapped[str | None] = mapped_column(Unicode(100))
    sexo: Mapped[str | None] = mapped_column(Unicode(20))
    edad: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    tamano: Mapped[str | None] = mapped_column(Unicode(20))
    descripcion: Mapped[str | None] = mapped_column(NVARCHAR(None))
    estado: Mapped[str] = mapped_column(
        Unicode(20), nullable=False, server_default=text("N'disponible'")
    )
    destacada: Mapped[bool] = mapped_column(nullable=False, server_default=text("0"))
    foto_principal: Mapped[str | None] = mapped_column(Unicode(500))
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )
    actualizado_en: Mapped[datetime | None] = mapped_column(DATETIME2)

    # Columnas del contrato JSON (delta 0002).
    nombre_corto: Mapped[str | None] = mapped_column(Unicode(40))
    peso_kg: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    lugar: Mapped[str | None] = mapped_column(Unicode(120))
    etiqueta: Mapped[str | None] = mapped_column(Unicode(60))
    etiqueta_icono: Mapped[str | None] = mapped_column(Unicode(40))
    energia: Mapped[str | None] = mapped_column(Unicode(40))
    urgente: Mapped[bool] = mapped_column(nullable=False, server_default=text("0"))
    foto_alt: Mapped[str | None] = mapped_column(Unicode(300))

    # Banderas editoriales (D-032). NULL = derivar de `mascota_salud.texto`.
    vacunado: Mapped[bool | None] = mapped_column()
    esterilizado: Mapped[bool | None] = mapped_column()

    # Columnas de la Fase 6 (D-029 y D-030).
    distrito_id: Mapped[int | None] = mapped_column(ForeignKey("distritos.id"))
    etiqueta_clase: Mapped[str | None] = mapped_column(Unicode(80))
    cita_texto: Mapped[str | None] = mapped_column(Unicode(500))
    cita_autor: Mapped[str | None] = mapped_column(Unicode(120))

    refugio = relationship("Refugio", back_populates="mascotas")
    salud = relationship(
        "MascotaSalud",
        back_populates="mascota",
        cascade="all, delete-orphan",
        order_by="MascotaSalud.orden",
    )
    fotos = relationship(
        "MascotaFoto",
        back_populates="mascota",
        cascade="all, delete-orphan",
        order_by="MascotaFoto.orden",
    )
    rasgos = relationship(
        "MascotaRasgo",
        back_populates="mascota",
        cascade="all, delete-orphan",
        order_by="MascotaRasgo.orden",
    )
    historia = relationship(
        "MascotaHistoria",
        back_populates="mascota",
        cascade="all, delete-orphan",
        order_by="MascotaHistoria.orden",
    )
    cuidados = relationship(
        "MascotaCuidado",
        back_populates="mascota",
        cascade="all, delete-orphan",
        order_by="MascotaCuidado.orden",
    )

    __table_args__ = (
        CheckConstraint("especie IN ('perro', 'gato')", name="especie"),
        CheckConstraint(
            "estado IN ('disponible', 'adoptada', 'en_acogida')", name="estado"
        ),
        CheckConstraint("edad IS NULL OR edad >= 0", name="edad"),
        CheckConstraint("sexo IS NULL OR sexo IN ('Macho', 'Hembra')", name="sexo"),
        CheckConstraint(
            "tamano IS NULL OR tamano IN ('Pequeño', 'Mediano', 'Grande')",
            name="tamano",
        ),
        Index(
            "IX_mascotas_catalogo",
            "estado",
            "especie",
            mssql_include=["destacada", "nombre"],
        ),
        Index("IX_mascotas_refugio", "refugio_id"),
    )


class MascotaSalud(Base):
    __tablename__ = "mascota_salud"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    mascota_id: Mapped[int] = mapped_column(
        ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False
    )
    orden: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    texto: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    ok: Mapped[bool] = mapped_column(nullable=False, server_default=text("1"))

    mascota = relationship("Mascota", back_populates="salud")

    __table_args__ = (Index("IX_mascota_salud_mascota", "mascota_id", "orden"),)


class MascotaFoto(Base):
    __tablename__ = "mascota_fotos"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    mascota_id: Mapped[int] = mapped_column(
        ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False
    )
    orden: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    url: Mapped[str] = mapped_column(Unicode(500), nullable=False)
    alt: Mapped[str | None] = mapped_column(Unicode(300))

    mascota = relationship("Mascota", back_populates="fotos")

    __table_args__ = (Index("IX_mascota_fotos_mascota", "mascota_id", "orden"),)


class MascotaRasgo(Base):
    __tablename__ = "mascota_rasgos"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    mascota_id: Mapped[int] = mapped_column(
        ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False
    )
    orden: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    rasgo: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    icono: Mapped[str | None] = mapped_column(Unicode(40))
    clase: Mapped[str | None] = mapped_column(Unicode(200))
    icono_clase: Mapped[str | None] = mapped_column(Unicode(40))

    mascota = relationship("Mascota", back_populates="rasgos")

    __table_args__ = (Index("IX_mascota_rasgos_mascota", "mascota_id", "orden"),)


class MascotaHistoria(Base):
    """Párrafos de la historia editorial de la ficha (D-030)."""

    __tablename__ = "mascota_historia"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    mascota_id: Mapped[int] = mapped_column(
        ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False
    )
    orden: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    texto: Mapped[str] = mapped_column(NVARCHAR(None), nullable=False)

    mascota = relationship("Mascota", back_populates="historia")

    __table_args__ = (Index("IX_mascota_historia_mascota", "mascota_id", "orden"),)


class MascotaCuidado(Base):
    """Cuidados mostrados en la ficha de la mascota (D-030)."""

    __tablename__ = "mascota_cuidados"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    mascota_id: Mapped[int] = mapped_column(
        ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False
    )
    orden: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    icono: Mapped[str] = mapped_column(Unicode(40), nullable=False)
    titulo: Mapped[str] = mapped_column(Unicode(120), nullable=False)
    texto: Mapped[str] = mapped_column(NVARCHAR(None), nullable=False)

    mascota = relationship("Mascota", back_populates="cuidados")

    __table_args__ = (Index("IX_mascota_cuidados_mascota", "mascota_id", "orden"),)
