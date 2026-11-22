"""Persiste `vacunado` y `esterilizado` de la mascota (D-032).

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-18

D-028 asumía que ambas banderas se podían derivar de `mascota_salud.texto`,
pero el seed tiene un caso que no lo cumple: Misha (id 15) está marcada como
vacunada y su lista de salud solo menciona esterilización y un test felino.

Esta revisión **solo agrega** dos columnas `BIT NULL`:

* `NULL` → el repositorio deriva la bandera de `mascota_salud.texto`
  (comportamiento de D-028, útil para altas cargadas por la API);
* `0/1` → valor editorial explícito, que es lo que siembra `db/seed.py`.

No modifica filas existentes.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("mascotas", sa.Column("vacunado", sa.Boolean(), nullable=True))
    op.add_column("mascotas", sa.Column("esterilizado", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("mascotas", "esterilizado")
    op.drop_column("mascotas", "vacunado")
