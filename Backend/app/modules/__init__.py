from .alertas import router as alertas_router
from .auth import router as auth_router
from .contenido import router as contenido_router
from .estadisticas import router as estadisticas_router
from .favoritos import router as favoritos_router
from .mascotas import router as mascotas_router
from .refugios import router as refugios_router
from .solicitudes import router as solicitudes_router

__all__ = [
    "alertas_router",
    "auth_router",
    "contenido_router",
    "estadisticas_router",
    "favoritos_router",
    "mascotas_router",
    "refugios_router",
    "solicitudes_router",
]
