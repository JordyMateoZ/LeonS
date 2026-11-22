"""Punto de entrada: `uv run uvicorn app.main:app --reload --port 8000`."""

from __future__ import annotations

import logging

import uvicorn

from .app import create_app
from .e2e import verificar_base_e2e

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# Fail-closed solo en el proceso E2E (E2E_EXPECT_DB). En desarrollo normal no
# hace nada, así que el servidor de :8000 conserva su comportamiento.
verificar_base_e2e()

app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
