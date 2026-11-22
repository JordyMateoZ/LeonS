"""Contenido editorial: pasos y preguntas frecuentes.

Los requisitos comparten `contenido_pasos` con el discriminador
`tipo='requisito'`, para no crear una tabla 19 fuera del modelo aprobado.
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Identity, SmallInteger, Unicode, text
from sqlalchemy.dialects.mssql import NVARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base

TIPOS_CONTENIDO = ("adopcion", "refugio", "requisito")


class ContenidoPaso(Base):
    __tablename__ = "contenido_pasos"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False, unique=True)
    titulo: Mapped[str] = mapped_column(Unicode(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(NVARCHAR(None))
    tipo: Mapped[str] = mapped_column(
        Unicode(20), nullable=False, server_default=text("N'adopcion'")
    )
    icono: Mapped[str | None] = mapped_column(Unicode(40))
    nota: Mapped[str | None] = mapped_column(Unicode(300))

    __table_args__ = (
        CheckConstraint("tipo IN ('adopcion', 'refugio', 'requisito')", name="tipo"),
    )


class ContenidoFaq(Base):
    __tablename__ = "contenido_faqs"

    id: Mapped[int] = mapped_column(Identity(1, 1), primary_key=True)
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False, unique=True)
    pregunta: Mapped[str] = mapped_column(Unicode(300), nullable=False)
    respuesta: Mapped[str] = mapped_column(NVARCHAR(None), nullable=False)
