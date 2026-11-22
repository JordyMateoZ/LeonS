"""Normaliza NTEXT a NVARCHAR(MAX) en las columnas de texto largo.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-18

La primera versión de `0001` declaró `UnicodeText`, que el dialecto de
SQL Server traduce a `NTEXT` (tipo obsoleto). `LeonsDB` usa
`NVARCHAR(MAX)` y el contrato necesita tildes con la collation
`Modern_Spanish_CI_AI`, así que esta revisión alinea los entornos ya
migrados. En una instalación nueva el cambio es idempotente.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "contenido_faqs",
        "respuesta",
        existing_type=mssql.NTEXT(),
        type_=mssql.NVARCHAR(length=None),
        existing_nullable=False,
    )
    op.alter_column(
        "contenido_pasos",
        "descripcion",
        existing_type=mssql.NTEXT(),
        type_=mssql.NVARCHAR(length=None),
        existing_nullable=True,
    )
    op.alter_column(
        "refugios",
        "descripcion",
        existing_type=mssql.NTEXT(),
        type_=mssql.NVARCHAR(length=None),
        existing_nullable=True,
    )
    op.alter_column(
        "mascotas",
        "descripcion",
        existing_type=mssql.NTEXT(),
        type_=mssql.NVARCHAR(length=None),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "mascotas",
        "descripcion",
        existing_type=mssql.NVARCHAR(length=None),
        type_=mssql.NTEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "refugios",
        "descripcion",
        existing_type=mssql.NVARCHAR(length=None),
        type_=mssql.NTEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "contenido_pasos",
        "descripcion",
        existing_type=mssql.NVARCHAR(length=None),
        type_=mssql.NTEXT(),
        existing_nullable=True,
    )
    op.alter_column(
        "contenido_faqs",
        "respuesta",
        existing_type=mssql.NVARCHAR(length=None),
        type_=mssql.NTEXT(),
        existing_nullable=False,
    )
