"""Amplía `mascota_rasgos.clase` para las clases Tailwind del seed.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-18

El seed exportado desde Angular guarda en `rasgo.clase` la lista completa de
utilidades Tailwind del chip (hasta 146 caracteres), pero `0005` la creó como
`NVARCHAR(80)`. Esta revisión **solo amplía** la columna a `NVARCHAR(200)`;
no borra ni reescribe datos.

El resto de columnas nuevas de `0005` ya tienen longitud suficiente para el
seed (verificado campo por campo antes de sembrar).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "mascota_rasgos",
        "clase",
        existing_type=mssql.NVARCHAR(length=80),
        type_=mssql.NVARCHAR(length=200),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "mascota_rasgos",
        "clase",
        existing_type=mssql.NVARCHAR(length=200),
        type_=mssql.NVARCHAR(length=80),
        existing_nullable=True,
    )
