"""Exporta `db/schema.sql` desde los modelos SQLAlchemy (Fase 5).

Uso:

    uv run python db/export_schema.py

El archivo resultante es la representación legible y reproducible del
esquema final: 20 tablas, sus restricciones e índices, en orden de
dependencias. No se conecta a SQL Server.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
if str(RAIZ_BACKEND) not in sys.path:
    sys.path.insert(0, str(RAIZ_BACKEND))

from sqlalchemy.dialects import mssql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db import models  # noqa: F401  (registra las 20 tablas)
from app.db.base import Base

DESTINO = Path(__file__).resolve().parent / "schema.sql"

CABECERA = """\
-- ============================================================================
-- LeonS — Esquema de base de datos (SQL Server 2019+)
-- Generado desde los modelos SQLAlchemy 2.0 con: uv run python db/export_schema.py
-- No editar a mano: cambia el modelo y regenera este archivo.
--
-- Base: LeonsDB (producción local) / LeonsDB_Test (pruebas)
-- Collation: Modern_Spanish_CI_AI
--
-- Aplicación recomendada (no destructiva):
--   cd Backend
--   uv run alembic -x target=test upgrade head
--   uv run alembic -x target=main upgrade head
--
-- El esquema se compone de 20 tablas de dominio. Alembic mantiene su
-- propia tabla `alembic_version`, que no forma parte del modelo.
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

"""

PIE = """
-- ============================================================================
-- Fin del esquema. 20 tablas de dominio.
-- ============================================================================
"""


def generar() -> str:
    dialecto = mssql.dialect()
    partes = [CABECERA]

    for tabla in Base.metadata.sorted_tables:
        partes.append(f"-- {tabla.name} " + "-" * (70 - len(tabla.name)) + "\n")
        partes.append(str(CreateTable(tabla).compile(dialect=dialecto)).strip() + ";\nGO\n\n")
        for indice in tabla.indexes:
            partes.append(
                str(CreateIndex(indice).compile(dialect=dialecto)).strip() + ";\nGO\n\n"
            )

    partes.append(PIE)
    return "".join(partes)


if __name__ == "__main__":
    DESTINO.write_text(generar(), encoding="utf-8")
    print(f"Escrito {DESTINO} ({DESTINO.stat().st_size} bytes)")
