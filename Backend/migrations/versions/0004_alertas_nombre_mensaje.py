"""Agrega `nombre` y `mensaje` a `alertas_rescate` (D-026).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-18

El contrato de alertas de rescate pide `nombre` obligatorio y `mensaje`
opcional, pero la tabla solo tenía `contacto` y `descripcion`. Esta
revisión es **aditiva**: no borra ni renombra columnas y no copia
`contacto` en `nombre` (los datos personales se mantienen separados).

Para bases con filas, `nombre` se agrega como NULL, se rellena con cadena
vacía (no se inventa un nombre) y luego se marca NOT NULL. En `LeonsDB` y
`LeonsDB_Test` la tabla está vacía, así que el relleno no afecta a nadie.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "alertas_rescate",
        sa.Column("nombre", sa.Unicode(length=120), nullable=True),
    )
    op.execute("UPDATE alertas_rescate SET nombre = N'' WHERE nombre IS NULL")
    op.alter_column(
        "alertas_rescate",
        "nombre",
        existing_type=mssql.NVARCHAR(length=120),
        nullable=False,
    )
    op.add_column(
        "alertas_rescate",
        sa.Column("mensaje", mssql.NVARCHAR(length=1000), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("alertas_rescate", "mensaje")
    op.drop_column("alertas_rescate", "nombre")
