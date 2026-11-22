"""Modelos SQLAlchemy 2.0 de LeonS.

Un módulo por agregado. Los campos de presentación (badges, chips, textos
relativos, etapas) **no** se persisten: los calcula `app/mapper.py`.
"""

from __future__ import annotations

from ..base import Base
from .catalogos import Distrito, Migracion
from .contenido import ContenidoFaq, ContenidoPaso
from .mascotas import (
    Mascota,
    MascotaCuidado,
    MascotaFoto,
    MascotaHistoria,
    MascotaRasgo,
    MascotaSalud,
)
from .refugios import Refugio, RefugioEspecie
from .social import AlertaRescate, Favorito
from .solicitudes import (
    Cita,
    Mensaje,
    SeguimientoFoto,
    Solicitud,
    SolicitudEvento,
)
from .usuarios import Usuario

__all__ = [
    "AlertaRescate",
    "Base",
    "Cita",
    "ContenidoFaq",
    "ContenidoPaso",
    "Distrito",
    "Favorito",
    "Mascota",
    "MascotaCuidado",
    "MascotaFoto",
    "MascotaHistoria",
    "MascotaRasgo",
    "MascotaSalud",
    "Mensaje",
    "Migracion",
    "Refugio",
    "RefugioEspecie",
    "SeguimientoFoto",
    "Solicitud",
    "SolicitudEvento",
    "Usuario",
]
