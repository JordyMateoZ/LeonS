"""Notificaciones. En esta fase solo registra en el log."""

from __future__ import annotations

import logging

logger = logging.getLogger("leons.notificaciones")


class LogNotifier:
    def enviar(self, destino: str, asunto: str, cuerpo: str) -> None:
        logger.info("Notificación simulada a %s: %s — %s", destino, asunto, cuerpo)
