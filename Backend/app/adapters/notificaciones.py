from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger("leons.integraciones")


class NotificacionesAdapter(Protocol):
    async def correo(self, destinatario: str, asunto: str, cuerpo: str) -> None: ...
    async def whatsapp(self, numero: str, mensaje: str) -> None: ...


class LogNotificacionesAdapter(NotificacionesAdapter):
    """En desarrollo solo registra la intención; se sustituye por proveedores reales."""

    async def correo(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        logger.info("[mail] -> %s | %s | %s", destinatario, asunto, cuerpo)

    async def whatsapp(self, numero: str, mensaje: str) -> None:
        logger.info("[whatsapp] -> %s | %s", numero, mensaje)
