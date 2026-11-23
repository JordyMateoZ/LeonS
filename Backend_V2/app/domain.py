"""Modelo de dominio de LeonS.

Entidades en español, sin dependencias de HTTP ni de SQLAlchemy. Los DTO
(camelCase) viven en `schemas.py` y se construyen en `mapper.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Protocol

Especie = Literal["perro", "gato"]
EstadoMascota = Literal["disponible", "adoptada", "en_acogida"]
Rol = Literal["adoptante", "refugio", "admin"]
EstadoSolicitud = Literal["activa", "cancelada", "completada"]


def ahora_utc() -> datetime:
    """UTC sin tzinfo: es el formato que se guardará en DATETIME2."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(slots=True)
class SaludItem:
    texto: str
    ok: bool


@dataclass(slots=True)
class Foto:
    src: str
    alt: str


@dataclass(slots=True)
class Rasgo:
    icono: str
    texto: str
    clase: str
    icono_clase: str = ""


@dataclass(slots=True)
class Cita:
    fecha: str
    direccion: str
    coordinadora: str


@dataclass(slots=True)
class Mensaje:
    iniciales: str
    nombre: str
    rol: str
    texto: str


@dataclass(slots=True)
class Cierre:
    titulo: str
    texto: str
    control_titulo: str
    control_fecha: str
    control_lugar: str


@dataclass(slots=True)
class EtapaVista:
    titulo: str
    detalle: str
    destacado: bool = False


@dataclass(slots=True)
class Refugio:
    id: str
    nombre: str
    distrito: str
    direccion: str
    tipo: str
    desde: int
    descripcion: str
    contacto: str
    cargo: str
    telefono: str
    whatsapp: str
    adoptadas: int
    en_acogida: int
    verificado: bool
    especies: list[Especie] = field(default_factory=list)
    logo: str | None = None


@dataclass(slots=True)
class Mascota:
    id: int
    nombre: str
    nombre_corto: str
    especie: Especie
    sexo: Literal["Macho", "Hembra"]
    raza: str
    edad_anios: float
    tamano: Literal["Pequeño", "Mediano", "Grande"]
    peso_kg: float
    distrito: str
    lugar: str
    foto: str
    alt: str
    descripcion: str
    etiqueta: str
    etiqueta_icono: str
    etiqueta_clase: str
    esterilizado: bool
    vacunado: bool
    urgente: bool
    refugio_id: str
    energia: str
    ficha_id: str
    actualizado_dias: int
    estado: EstadoMascota = "disponible"
    salud: list[SaludItem] = field(default_factory=list)
    galeria: list[Foto] = field(default_factory=list)
    rasgos: list[Rasgo] = field(default_factory=list)


@dataclass(slots=True)
class DetalleMascota:
    """Datos especiales por mascota exportados desde `detalle.data.ts`."""

    historia: list[str] = field(default_factory=list)
    cuidados: list[dict[str, str]] = field(default_factory=list)
    rasgos: list[Rasgo] = field(default_factory=list)
    cita: dict[str, str] | None = None


@dataclass(slots=True)
class Usuario:
    id: int
    nombre: str
    email: str
    password_hash: str
    rol: Rol
    dni: str | None = None
    telefono: str | None = None
    distrito: str | None = None
    refugio_id: str | None = None
    google_id: str | None = None
    creado_en: datetime = field(default_factory=ahora_utc)


@dataclass(slots=True)
class Solicitud:
    id: int
    codigo: str
    usuario_id: int
    mascota_id: int
    estado: EstadoSolicitud = "activa"
    etapa: int = 2
    creada_en: datetime = field(default_factory=ahora_utc)
    actualizada_en: datetime = field(default_factory=ahora_utc)
    motivo_cancelacion: str | None = None
    cita: Cita | None = None
    mensaje: Mensaje | None = None
    cierre: Cierre | None = None
    tiempo_respuesta: str | None = None
    whatsapp: str | None = None
    foto_src: str | None = None
    foto_alt: str | None = None
    etapas_override: list[EtapaVista] | None = None
    seguimiento: list[Foto] = field(default_factory=list)


@dataclass(slots=True)
class Favorito:
    usuario_id: int
    mascota_id: int
    creado_en: datetime = field(default_factory=ahora_utc)


@dataclass(slots=True)
class AlertaRescate:
    id: int
    nombre: str
    contacto: str
    distrito: str | None = None
    especie: str | None = None
    mensaje: str | None = None
    atendida: bool = False
    creado_en: datetime = field(default_factory=ahora_utc)


@dataclass(slots=True)
class Contenido:
    pasos_adopcion: list[dict[str, str]] = field(default_factory=list)
    pasos_refugio: list[dict[str, str]] = field(default_factory=list)
    faqs: list[dict[str, str]] = field(default_factory=list)
    requisitos: list[dict[str, str]] = field(default_factory=list)


class RepositorioProtocol(Protocol):
    """Contrato que deben cumplir los repositorios (memoria y SQL Server)."""

    def listar_mascotas(self) -> list[Mascota]: ...

    def obtener_mascota(self, mascota_id: int) -> Mascota | None: ...

    def guardar_mascota(self, mascota: Mascota) -> Mascota: ...

    def eliminar_mascota(self, mascota_id: int) -> None: ...

    def listar_refugios(self) -> list[Refugio]: ...

    def obtener_refugio(self, refugio_id: str) -> Refugio | None: ...

    def obtener_contenido(self) -> Contenido: ...

    def obtener_detalle(self, mascota_id: int) -> DetalleMascota | None: ...

    def obtener_usuario(self, usuario_id: int) -> Usuario | None: ...

    def buscar_usuario_por_email(self, email: str) -> Usuario | None: ...

    def buscar_usuario_por_dni(self, dni: str) -> Usuario | None: ...

    def crear_usuario(self, usuario: Usuario) -> Usuario: ...

    def listar_solicitudes(self) -> list[Solicitud]: ...

    def obtener_solicitud(self, solicitud_id: int) -> Solicitud | None: ...

    def crear_solicitud(self, solicitud: Solicitud) -> Solicitud: ...

    def guardar_solicitud(self, solicitud: Solicitud) -> Solicitud: ...

    def listar_favoritos(self, usuario_id: int) -> list[Favorito]: ...

    def crear_favorito(self, favorito: Favorito) -> Favorito: ...

    def eliminar_favorito(self, usuario_id: int, mascota_id: int) -> bool: ...

    def listar_alertas(self) -> list[AlertaRescate]: ...

    def crear_alerta(self, alerta: AlertaRescate) -> AlertaRescate: ...
