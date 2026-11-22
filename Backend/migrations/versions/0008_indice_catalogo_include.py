"""Alinea `IX_mascotas_catalogo` con el índice real de `LeonsDB`.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-18

`LeonsDB` se creó a mano con `INCLUDE (destacada, nombre)` en el índice del
catálogo; los modelos y `0001` no lo declaraban. Para que `alembic check`
pueda quedar limpio cuando `LeonsDB` se marque y se migre (D-027), el modelo
adopta la definición real y esta revisión recrea el índice con el mismo
`INCLUDE`. No cambia datos ni columnas.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("IX_mascotas_catalogo", table_name="mascotas")
    op.create_index(
        "IX_mascotas_catalogo",
        "mascotas",
        ["estado", "especie"],
        unique=False,
        mssql_include=["destacada", "nombre"],
    )


def downgrade() -> None:
    op.drop_index("IX_mascotas_catalogo", table_name="mascotas")
    op.create_index(
        "IX_mascotas_catalogo",
        "mascotas",
        ["estado", "especie"],
        unique=False,
    )
