"""Agrega `refugios.orden` para preservar el orden editorial del listado.

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-18

La página `refugios` pinta el array del API en el orden en que llega, y ese
orden es el de `refugios.data.ts`. `MemoryRepository` lo conserva porque
devuelve el seed en orden; sin una columna explícita, el repositorio SQL solo
podía ordenar por `nombre` o por la PK (slug), y el listado cambiaba.

Esta revisión **solo agrega** una columna `SMALLINT NULL`:

* `NULL` → el refugio va al final, ordenado por `nombre`;
* `1..n` → posición editorial, la que siembra `db/seed.py`.

No modifica filas existentes: el seed rellena los `NULL`.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("refugios", sa.Column("orden", sa.SmallInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("refugios", "orden")
