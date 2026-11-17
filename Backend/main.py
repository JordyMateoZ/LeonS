"""Punto de entrada para: uv run uvicorn Backend.main:app

Se ejecuta desde la raíz del workspace. El paquete interno `app` vive en
`Backend/app`, así que se añade `Backend/` al `sys.path` para que los imports
`from app...` sigan funcionando sin cambios.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.app import app  # noqa: E402

__all__ = ["app"]
