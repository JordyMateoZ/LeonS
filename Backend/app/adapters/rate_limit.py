from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from app.config import settings
from app.errors import AppError


class RateLimiter:
    """Limitador en memoria, sustituible por Redis cuando el backend escale."""

    def __init__(self, max_solicitudes: int, mensaje: str) -> None:
        self.max_solicitudes = max_solicitudes
        self.mensaje = mensaje
        self.ventana = settings.rate_limit_window_ms / 1000
        self._intentos: defaultdict[str, list[float]] = defaultdict(list)
        self._bloqueo = asyncio.Lock()

    async def verificar(self, clave: str) -> None:
        ahora = time.monotonic()
        async with self._bloqueo:
            recientes = [
                momento
                for momento in self._intentos[clave]
                if ahora - momento < self.ventana
            ]
            if len(recientes) >= self.max_solicitudes:
                raise AppError(
                    429,
                    "RATE_LIMITED",
                    self.mensaje,
                    {"limite": self.max_solicitudes, "ventanaMs": settings.rate_limit_window_ms},
                )
            recientes.append(ahora)
            self._intentos[clave] = recientes
