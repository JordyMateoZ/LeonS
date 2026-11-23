"""Limitador de peticiones en memoria (ventana deslizante)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from ..errors import AppError


class RateLimiter:
    def __init__(self, maximo: int, ventana_segundos: int) -> None:
        self.maximo = max(1, maximo)
        self.ventana = max(1, ventana_segundos)
        self._eventos: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def consumir(self, clave: str) -> None:
        ahora = time.monotonic()
        with self._lock:
            eventos = self._eventos[clave]
            while eventos and ahora - eventos[0] > self.ventana:
                eventos.popleft()
            if len(eventos) >= self.maximo:
                espera = max(1, round(self.ventana - (ahora - eventos[0])))
                raise AppError(
                    "RATE_LIMIT",
                    "Demasiadas solicitudes. Intenta de nuevo en unos segundos.",
                    429,
                    {"reintentarEnSegundos": espera},
                )
            eventos.append(ahora)
