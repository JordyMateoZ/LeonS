"""Distrito, presentación y detalle de mascota (D-029 y D-030).

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-18

Migración **aditiva**: solo agrega columnas y dos tablas hijas.
No modifica ni elimina datos existentes.

* D-029: `mascotas.distrito_id`, `mascotas.etiqueta_clase` y las columnas
  visuales de `mascota_rasgos`.
* D-030: `mascota_historia`, `mascota_cuidados` y la cita editorial de la
  ficha en `mascotas.cita_texto` / `mascotas.cita_autor`.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("mascotas", sa.Column("distrito_id", sa.Integer(), nullable=True))
    op.add_column(
        "mascotas", sa.Column("etiqueta_clase", sa.Unicode(length=80), nullable=True)
    )
    op.add_column(
        "mascotas", sa.Column("cita_texto", sa.Unicode(length=500), nullable=True)
    )
    op.add_column(
        "mascotas", sa.Column("cita_autor", sa.Unicode(length=120), nullable=True)
    )
    op.create_foreign_key(
        "FK_mascotas_distritos", "mascotas", "distritos", ["distrito_id"], ["id"]
    )

    op.add_column(
        "mascota_rasgos", sa.Column("icono", sa.Unicode(length=40), nullable=True)
    )
    op.add_column(
        "mascota_rasgos", sa.Column("clase", sa.Unicode(length=80), nullable=True)
    )
    op.add_column(
        "mascota_rasgos", sa.Column("icono_clase", sa.Unicode(length=40), nullable=True)
    )

    op.create_table(
        "mascota_historia",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("mascota_id", sa.Integer(), nullable=False),
        sa.Column("orden", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("texto", mssql.NVARCHAR(length=None), nullable=False),
        sa.ForeignKeyConstraint(
            ["mascota_id"],
            ["mascotas.id"],
            name="FK_mascota_historia_mascotas",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="PK_mascota_historia"),
    )
    op.create_index(
        "IX_mascota_historia_mascota",
        "mascota_historia",
        ["mascota_id", "orden"],
        unique=False,
    )

    op.create_table(
        "mascota_cuidados",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("mascota_id", sa.Integer(), nullable=False),
        sa.Column("orden", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("icono", sa.Unicode(length=40), nullable=False),
        sa.Column("titulo", sa.Unicode(length=120), nullable=False),
        sa.Column("texto", mssql.NVARCHAR(length=None), nullable=False),
        sa.ForeignKeyConstraint(
            ["mascota_id"],
            ["mascotas.id"],
            name="FK_mascota_cuidados_mascotas",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="PK_mascota_cuidados"),
    )
    op.create_index(
        "IX_mascota_cuidados_mascota",
        "mascota_cuidados",
        ["mascota_id", "orden"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("IX_mascota_cuidados_mascota", table_name="mascota_cuidados")
    op.drop_table("mascota_cuidados")
    op.drop_index("IX_mascota_historia_mascota", table_name="mascota_historia")
    op.drop_table("mascota_historia")
    op.drop_column("mascota_rasgos", "icono_clase")
    op.drop_column("mascota_rasgos", "clase")
    op.drop_column("mascota_rasgos", "icono")
    op.drop_constraint("FK_mascotas_distritos", "mascotas", type_="foreignkey")
    op.drop_column("mascotas", "cita_autor")
    op.drop_column("mascotas", "cita_texto")
    op.drop_column("mascotas", "etiqueta_clase")
    op.drop_column("mascotas", "distrito_id")
