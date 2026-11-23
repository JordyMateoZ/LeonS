"""Punto de entrada: `uv run uvicorn app.main:app --reload --port 8000`."""

from __future__ import annotations

import logging

import uvicorn

from .app import create_app

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
