"""Solicitudes de adopción y su trazabilidad."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Unicode,
    text,
)
from sqlalchemy.dialects.mssql import DATETIME2, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Solicitud(Base):
    __tablename__ = "solicitudes"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    codigo: Mapped[str] = mapped_column(Unicode(30), nullable=False, unique=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    mascota_id: Mapped[int] = mapped_column(ForeignKey("mascotas.id"), nullable=False)
    refugio_id: Mapped[str] = mapped_column(ForeignKey("refugios.id"), nullable=False)
    estado: Mapped[str] = mapped_column(
        Unicode(20), nullable=False, server_default=text("N'activa'")
    )
    etapa: Mapped[int] = mapped_column(
        TINYINT, nullable=False, server_default=text("2")
    )
    motivo_cancelacion: Mapped[str | None] = mapped_column(Unicode(500))
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )
    actualizado_en: Mapped[datetime | None] = mapped_column(DATETIME2)

    usuario = relationship("Usuario")
    mascota = relationship("Mascota")
    refugio = relationship("Refugio")
    eventos = relationship(
        "SolicitudEvento", back_populates="solicitud", cascade="all, delete-orphan"
    )
    citas = relationship("Cita", back_populates="solicitud", cascade="all, delete-orphan")
    mensajes = relationship(
        "Mensaje", back_populates="solicitud", cascade="all, delete-orphan"
    )
    seguimiento = relationship(
        "SeguimientoFoto", back_populates="solicitud", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "estado IN ('activa', 'cancelada', 'completada')", name="estado"
        ),
        CheckConstraint("etapa BETWEEN 1 AND 5", name="etapa"),
        CheckConstraint(
            "estado <> 'cancelada' OR motivo_cancelacion IS NOT NULL", name="motivo"
        ),
        Index("IX_solicitudes_mascota", "mascota_id"),
        Index("IX_solicitudes_refugio", "refugio_id", "estado", "etapa"),
        Index("IX_solicitudes_usuario", "usuario_id", "creado_en"),
        # Una sola postulación activa por usuario y mascota.
        Index(
            "UX_solicitudes_activa",
            "usuario_id",
            "mascota_id",
            unique=True,
            mssql_where=text("estado = 'activa'"),
        ),
    )


class SolicitudEvento(Base):
    __tablename__ = "solicitud_eventos"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes.id", ondelete="CASCADE"), nullable=False
    )
    etapa: Mapped[int] = mapped_column(TINYINT, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Unicode(300))
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )

    solicitud = relationship("Solicitud", back_populates="eventos")

    __table_args__ = (
        CheckConstraint("etapa BETWEEN 1 AND 5", name="etapa"),
        Index("IX_solicitud_eventos_solicitud", "solicitud_id", "creado_en"),
    )


class Cita(Base):
    __tablename__ = "citas"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes.id", ondelete="CASCADE"), nullable=False
    )
    fecha_hora: Mapped[datetime] = mapped_column(DATETIME2, nullable=False)
    lugar: Mapped[str | None] = mapped_column(Unicode(200))
    notas: Mapped[str | None] = mapped_column(Unicode(500))
    coordinadora: Mapped[str | None] = mapped_column(Unicode(120))
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )

    solicitud = relationship("Solicitud", back_populates="citas")

    __table_args__ = (Index("IX_citas_solicitud", "solicitud_id", "fecha_hora"),)


class Mensaje(Base):
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes.id", ondelete="CASCADE"), nullable=False
    )
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    texto: Mapped[str] = mapped_column(Unicode(2000), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )

    solicitud = relationship("Solicitud", back_populates="mensajes")
    autor = relationship("Usuario")

    __table_args__ = (Index("IX_mensajes_solicitud", "solicitud_id", "creado_en"),)


class SeguimientoFoto(Base):
    __tablename__ = "seguimiento_fotos"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes.id", ondelete="CASCADE"), nullable=False
    )
    mes: Mapped[int] = mapped_column(TINYINT, nullable=False)
    archivo: Mapped[str] = mapped_column(Unicode(300), nullable=False)
    mime: Mapped[str] = mapped_column(Unicode(50), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    comentario: Mapped[str | None] = mapped_column(Unicode(500))
    creado_en: Mapped[datetime] = mapped_column(
        DATETIME2, nullable=False, server_default=text("sysutcdatetime()")
    )

    solicitud = relationship("Solicitud", back_populates="seguimiento")

    __table_args__ = (
        CheckConstraint("mes IN (1, 3, 6)", name="mes"),
        CheckConstraint("tamano_bytes > 0", name="tamano"),
        Index("IX_seguimiento_fotos_solicitud", "solicitud_id", "mes"),
    )
