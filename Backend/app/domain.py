"""Modelo de dominio: sin clases CSS y con contratos async listos para SQL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

Role = Literal["adopter", "shelter", "admin"]
Especie = Literal["perro", "gato"]
Tamano = Literal["Pequeño", "Mediano", "Grande"]
Sexo = Literal["Macho", "Hembra"]
EstadoMascota = Literal["disponible", "adoptada", "en_acogida"]
EstadoSolicitud = Literal["active", "completed", "cancelled"]


class DomainModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class Usuario(DomainModel):
    id: str
    nombre: str
    apellido: str | None = None
    email: str
    dni: str
    password_hash: str
    rol: Role
    telefono: str | None = None
    distrito: str | None = None
    terminos_aceptados: bool
    google_id: str | None = None
    activo: bool
    creado_en: str
    actualizado_en: str


class SaludItem(DomainModel):
    texto: str
    ok: bool


class Foto(DomainModel):
    src: str
    alt: str


class Rasgo(DomainModel):
    icono: str
    texto: str


class Mascota(DomainModel):
    id: int
    ficha_id: str
    nombre: str
    nombre_corto: str
    especie: Especie
    sexo: Sexo
    genero_texto: str
    raza: str
    edad_texto: str
    edad_anios: float
    tamano: Tamano
    tamano_texto: str
    distrito: str
    lugar: str
    foto: str
    alt: str
    descripcion: str
    etiqueta: str
    etiqueta_icono: str
    salud: list[SaludItem]
    esterilizado: bool
    vacunado: bool
    urgente: bool
    refugio: str
    refugio_id: str
    energia: str
    actualizado: str
    estado: EstadoMascota
    galeria: list[Foto] = []
    rasgos: list[Rasgo] = []


class Refugio(DomainModel):
    id: str
    nombre: str
    distrito: str
    direccion: str
    tipo: Literal["constituido", "independiente"]
    desde: int
    descripcion: str
    contacto: str
    cargo: str
    telefono: str
    whatsapp: str
    logo: str | None = None
    adoptadas: int
    en_acogida: int
    verificado: bool
    especies: list[Especie]


class Solicitante(DomainModel):
    nombre: str
    telefono: str
    distrito: str
    vivienda: str
    acepta_compromiso: bool
    email: str | None = None
    dni: str | None = None


class Etapa(DomainModel):
    titulo: str
    detalle: str
    destacado: bool | None = None


class CitaSolicitud(DomainModel):
    fecha: str
    direccion: str
    coordinadora: str


class MensajeSolicitud(DomainModel):
    iniciales: str
    nombre: str
    rol: str
    texto: str


class CierreSolicitud(DomainModel):
    titulo: str
    texto: str
    control_titulo: str
    control_fecha: str
    control_lugar: str


class SeguimientoFoto(DomainModel):
    id: str
    nombre: str
    url: str
    mime_type: str
    tamanio: int
    creado_en: str


class Solicitud(DomainModel):
    id: int
    estado: EstadoSolicitud
    paso: int
    mascota_id: int
    ficha_id: int | str
    nombre: str
    refugio: str
    lugar: str
    exp: str
    solicitante: Solicitante
    usuario_id: str | None = None
    creada_en: str
    actualizada_en: str
    tiempo_respuesta: str | None = None
    whatsapp: str | None = None
    cita: CitaSolicitud | None = None
    mensaje: MensajeSolicitud | None = None
    cierre: CierreSolicitud | None = None
    motivo_cancelacion: str | None = None
    fotos_seguimiento: list[SeguimientoFoto] = []


class Favorito(DomainModel):
    usuario_id: str
    mascota_id: int
    creado_en: str


class AlertaRescate(DomainModel):
    id: str
    nombre: str
    email: str
    telefono: str
    distrito: str
    direccion: str
    descripcion: str
    especie: Especie | Literal["otro"]
    cantidad: int
    urgente: bool
    creado_en: str
    atendida: bool


class PasoContenido(DomainModel):
    icono: str
    titulo: str
    texto: str
    nota: str


class PreguntaFrecuente(DomainModel):
    pregunta: str
    respuesta: str


class Contenido(DomainModel):
    pasos_adopcion: list[PasoContenido]
    pasos_refugio: list[PasoContenido]
    faqs: list[PreguntaFrecuente]


class SeedData(DomainModel):
    mascotas: list[Mascota]
    refugios: list[Refugio]
    solicitudes: list[Solicitud]
    contenido: Contenido


@dataclass
class MascotaFiltros:
    page: int = 1
    limit: int = 12
    especie: Especie | None = None
    tamano: Tamano | None = None
    distrito: str | None = None
    estado: EstadoMascota | None = None
    refugio_id: str | None = None
    energia: str | None = None
    urgente: bool | None = None
    q: str | None = None
    orden: Literal["recientes", "nombre", "edad_asc", "edad_desc"] = "recientes"


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
    total_pages: int


class MascotaStats(BaseModel):
    total: int
    disponibles: int
    adoptadas: int
    en_acogida: int
    urgentes: int
    por_especie: dict[Especie, int]
    por_distrito: list[dict[str, object]]


class UsuarioRepo(Protocol):
    async def find_by_id(self, usuario_id: str) -> Usuario | None: ...
    async def find_by_email(self, email: str) -> Usuario | None: ...
    async def find_by_dni(self, dni: str) -> Usuario | None: ...
    async def find_by_google_id(self, google_id: str) -> Usuario | None: ...
    async def create(self, usuario: Usuario) -> Usuario: ...
    async def update(self, usuario: Usuario) -> Usuario: ...


class MascotaRepo(Protocol):
    async def list(self, filtros: MascotaFiltros) -> Page[Mascota]: ...
    async def find_by_id(self, mascota_id: int) -> Mascota | None: ...
    async def find_by_ficha_id(self, ficha_id: str) -> Mascota | None: ...
    async def find_similares(self, mascota_id: int, limit: int) -> list[Mascota]: ...
    async def stats(self) -> MascotaStats: ...
    async def create(self, mascota: Mascota) -> Mascota: ...
    def snapshot(self) -> list[Mascota]: ...


class RefugioRepo(Protocol):
    async def list(
        self,
        distrito: str | None = None,
        especie: Especie | None = None,
        q: str | None = None,
    ) -> list[Refugio]: ...
    async def find_by_id(self, refugio_id: str) -> Refugio | None: ...
    async def find_mascotas(self, refugio_id: str) -> list[Mascota]: ...


class SolicitudRepo(Protocol):
    async def list_by_usuario(self, usuario_id: str) -> list[Solicitud]: ...
    async def list_all(self) -> list[Solicitud]: ...
    async def find_by_id(self, solicitud_id: int) -> Solicitud | None: ...
    async def exists_active(
        self, mascota_id: int, solicitante: Solicitante, usuario_id: str | None = None
    ) -> bool: ...
    async def create(self, solicitud: Solicitud) -> Solicitud: ...
    async def update(self, solicitud: Solicitud) -> Solicitud: ...
    async def next_id(self) -> int: ...


class FavoritoRepo(Protocol):
    async def list_by_usuario(self, usuario_id: str) -> list[Favorito]: ...
    async def find(self, usuario_id: str, mascota_id: int) -> Favorito | None: ...
    async def add(self, favorito: Favorito) -> Favorito: ...
    async def remove(self, usuario_id: str, mascota_id: int) -> bool: ...


class AlertaRepo(Protocol):
    async def create(self, alerta: AlertaRescate) -> AlertaRescate: ...
    async def list(self) -> list[AlertaRescate]: ...


class ContenidoRepo(Protocol):
    async def get(self) -> Contenido: ...


class Repositorios(Protocol):
    usuarios: UsuarioRepo
    mascotas: MascotaRepo
    refugios: RefugioRepo
    solicitudes: SolicitudRepo
    favoritos: FavoritoRepo
    alertas: AlertaRepo
    contenido: ContenidoRepo
