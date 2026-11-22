"""Columnas y restricciones que el contrato JSON necesita (aditiva).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-18

Motivo: `mapper.py` y los DTO camelCase usan campos de catálogo que el
esquema inicial no guardaba (`pesoKg`, `energia`, `etiqueta`, `contacto`,
`tipo`, `verificado`, etc.). Esta revisión **solo agrega**; no borra ni
renombra nada.

Reparto de `contenido_pasos.orden` (único global):

* 1–4  pasos de adopción
* 5–7  pasos para refugios
* 8–11 requisitos de adopción (`tipo='requisito'`)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -- mascotas: campos del catálogo ------------------------------------
    op.add_column("mascotas", sa.Column("nombre_corto", sa.Unicode(40), nullable=True))
    op.add_column("mascotas", sa.Column("peso_kg", sa.Numeric(4, 1), nullable=True))
    op.add_column("mascotas", sa.Column("lugar", sa.Unicode(120), nullable=True))
    op.add_column("mascotas", sa.Column("etiqueta", sa.Unicode(60), nullable=True))
    op.add_column("mascotas", sa.Column("etiqueta_icono", sa.Unicode(40), nullable=True))
    op.add_column("mascotas", sa.Column("energia", sa.Unicode(40), nullable=True))
    op.add_column(
        "mascotas",
        sa.Column("urgente", sa.Boolean(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column("mascotas", sa.Column("foto_alt", sa.Unicode(300), nullable=True))
    op.create_check_constraint(
        "CK_mascotas_sexo",
        "mascotas",
        "sexo IS NULL OR sexo IN ('Macho', 'Hembra')",
    )
    op.create_check_constraint(
        "CK_mascotas_tamano",
        "mascotas",
        "tamano IS NULL OR tamano IN ('Pequeño', 'Mediano', 'Grande')",
    )

    # -- tablas hijas de mascotas -----------------------------------------
    op.add_column("mascota_salud", sa.Column("ok", sa.Boolean(), server_default=sa.text("1"), nullable=False))
    op.add_column("mascota_fotos", sa.Column("alt", sa.Unicode(300), nullable=True))

    # -- refugios: datos editoriales y de contacto ------------------------
    op.add_column("refugios", sa.Column("contacto", sa.Unicode(120), nullable=True))
    op.add_column("refugios", sa.Column("cargo", sa.Unicode(120), nullable=True))
    op.add_column("refugios", sa.Column("tipo", sa.Unicode(20), nullable=True))
    op.add_column("refugios", sa.Column("desde", sa.SmallInteger(), nullable=True))
    op.add_column(
        "refugios",
        sa.Column("verificado", sa.Boolean(), server_default=sa.text("1"), nullable=False),
    )
    op.add_column("refugios", sa.Column("logo", sa.Unicode(500), nullable=True))
    op.create_check_constraint(
        "CK_refugios_tipo",
        "refugios",
        "tipo IS NULL OR tipo IN ('constituido', 'independiente')",
    )

    # -- citas: coordinadora que atiende la visita ------------------------
    op.add_column("citas", sa.Column("coordinadora", sa.Unicode(120), nullable=True))

    # -- contenido: separar pasos de adopción, refugio y requisitos -------
    op.add_column(
        "contenido_pasos",
        sa.Column(
            "tipo",
            sa.Unicode(20),
            server_default=sa.text("N'adopcion'"),
            nullable=False,
        ),
    )
    op.add_column("contenido_pasos", sa.Column("icono", sa.Unicode(40), nullable=True))
    op.add_column("contenido_pasos", sa.Column("nota", sa.Unicode(300), nullable=True))
    op.create_check_constraint(
        "CK_contenido_pasos_tipo",
        "contenido_pasos",
        "tipo IN ('adopcion', 'refugio', 'requisito')",
    )


def downgrade() -> None:
    op.drop_constraint("CK_contenido_pasos_tipo", "contenido_pasos", type_="check")
    op.drop_column("contenido_pasos", "nota")
    op.drop_column("contenido_pasos", "icono")
    op.drop_column("contenido_pasos", "tipo")

    op.drop_column("citas", "coordinadora")

    op.drop_constraint("CK_refugios_tipo", "refugios", type_="check")
    op.drop_column("refugios", "logo")
    op.drop_column("refugios", "verificado")
    op.drop_column("refugios", "desde")
    op.drop_column("refugios", "tipo")
    op.drop_column("refugios", "cargo")
    op.drop_column("refugios", "contacto")

    op.drop_column("mascota_fotos", "alt")
    op.drop_column("mascota_salud", "ok")

    op.drop_constraint("CK_mascotas_tamano", "mascotas", type_="check")
    op.drop_constraint("CK_mascotas_sexo", "mascotas", type_="check")
    op.drop_column("mascotas", "foto_alt")
    op.drop_column("mascotas", "urgente")
    op.drop_column("mascotas", "energia")
    op.drop_column("mascotas", "etiqueta_icono")
    op.drop_column("mascotas", "etiqueta")
    op.drop_column("mascotas", "lugar")
    op.drop_column("mascotas", "peso_kg")
    op.drop_column("mascotas", "nombre_corto")
