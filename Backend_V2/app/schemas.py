"""DTO de entrada y salida. JSON en camelCase para calzar con Angular."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


def to_camel(texto: str) -> str:
    partes = texto.split("_")
    return partes[0] + "".join(parte.title() for parte in partes[1:])


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        str_strip_whitespace=True,
    )


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------


class SaludItemOut(BaseSchema):
    texto: str
    ok: bool


class FotoOut(BaseSchema):
    src: str
    alt: str


class RasgoOut(BaseSchema):
    icono: str
    texto: str
    clase: str
    icono_clase: str


class MascotaOut(BaseSchema):
    id: int
    nombre: str
    nombre_corto: str
    especie: Literal["perro", "gato"]
    sexo: Literal["Macho", "Hembra"]
    genero_texto: str
    badge_clase: str
    raza: str
    edad_texto: str
    edad_anios: float
    tamano: Literal["Pequeño", "Mediano", "Grande"]
    tamano_texto: str
    distrito: str
    lugar: str
    foto: str
    alt: str
    descripcion: str
    etiqueta: str
    etiqueta_icono: str
    etiqueta_clase: str
    salud: list[SaludItemOut]
    esterilizado: bool
    vacunado: bool
    urgente: bool
    refugio: str
    refugio_id: str
    energia: str
    ficha_id: str
    actualizado: str
    estado: Literal["disponible", "adoptada", "en_acogida"]
    galeria: list[FotoOut]
    rasgos: list[RasgoOut]


class PageMascotas(BaseSchema):
    items: list[MascotaOut]
    page: int
    limit: int
    total: int
    total_pages: int


class MascotaCreate(BaseSchema):
    nombre: str = Field(min_length=2, max_length=80)
    nombre_corto: str | None = Field(default=None, max_length=40)
    especie: Literal["perro", "gato"]
    sexo: Literal["Macho", "Hembra"]
    raza: str = Field(min_length=2, max_length=80)
    edad_anios: float = Field(ge=0, le=30)
    tamano: Literal["Pequeño", "Mediano", "Grande"]
    peso_kg: float = Field(gt=0, le=120)
    distrito: str = Field(min_length=2, max_length=80)
    lugar: str = Field(min_length=2, max_length=120)
    foto: str = Field(min_length=4, max_length=1000)
    alt: str = Field(min_length=4, max_length=300)
    descripcion: str = Field(min_length=10, max_length=1000)
    etiqueta: str = Field(min_length=2, max_length=60)
    etiqueta_icono: str = "pets"
    energia: str = Field(min_length=2, max_length=40)
    refugio_id: str = Field(min_length=2, max_length=60)
    esterilizado: bool = False
    vacunado: bool = False
    urgente: bool = False
    estado: Literal["disponible", "adoptada", "en_acogida"] = "disponible"
    salud: list[SaludItemOut] = Field(default_factory=list)


class MascotaUpdate(BaseSchema):
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    nombre_corto: str | None = Field(default=None, max_length=40)
    especie: Literal["perro", "gato"] | None = None
    sexo: Literal["Macho", "Hembra"] | None = None
    raza: str | None = Field(default=None, min_length=2, max_length=80)
    edad_anios: float | None = Field(default=None, ge=0, le=30)
    tamano: Literal["Pequeño", "Mediano", "Grande"] | None = None
    peso_kg: float | None = Field(default=None, gt=0, le=120)
    distrito: str | None = Field(default=None, min_length=2, max_length=80)
    lugar: str | None = Field(default=None, min_length=2, max_length=120)
    foto: str | None = Field(default=None, min_length=4, max_length=1000)
    alt: str | None = Field(default=None, min_length=4, max_length=300)
    descripcion: str | None = Field(default=None, min_length=10, max_length=1000)
    etiqueta: str | None = Field(default=None, min_length=2, max_length=60)
    etiqueta_icono: str | None = None
    energia: str | None = Field(default=None, min_length=2, max_length=40)
    refugio_id: str | None = Field(default=None, min_length=2, max_length=60)
    esterilizado: bool | None = None
    vacunado: bool | None = None
    urgente: bool | None = None
    estado: Literal["disponible", "adoptada", "en_acogida"] | None = None
    salud: list[SaludItemOut] | None = None


class MascotaStats(BaseSchema):
    total: int
    total_registradas: int
    disponibles: int
    adoptadas: int
    en_acogida: int
    urgentes: int
    total_refugios: int
    edad_promedio: float
    por_especie: dict[str, int]
    por_distrito: dict[str, int]
    por_tamano: dict[str, int]


# ---------------------------------------------------------------------------
# Refugios
# ---------------------------------------------------------------------------


class RefugioOut(BaseSchema):
    id: str
    nombre: str
    distrito: str
    desde: int
    descripcion: str
    contacto: str
    cargo: str
    telefono: str
    whatsapp: str
    logo: str | None
    adoptadas: int
    en_acogida: int
    verificado: bool
    especies: list[Literal["perro", "gato"]]
    direccion: str
    tipo: Literal["constituido", "independiente"]


class ResumenRefugioOut(BaseSchema):
    total: int
    disponibles: int
    adoptadas: int
    en_acogida: int


class RefugioDetalleOut(BaseSchema):
    refugio: RefugioOut
    resumen: ResumenRefugioOut
    mascotas: list[MascotaOut]


# ---------------------------------------------------------------------------
# Detalle de mascota y contenido
# ---------------------------------------------------------------------------


class CuidadoOut(BaseSchema):
    icono: str
    titulo: str
    texto: str


class RequisitoOut(BaseSchema):
    icono: str
    titulo: str
    texto: str


class PreguntaOut(BaseSchema):
    pregunta: str
    respuesta: str


class CitaDetalleOut(BaseSchema):
    texto: str
    autor: str


class DetalleMascotaOut(BaseSchema):
    mascota: MascotaOut
    refugio: RefugioOut
    historia: list[str]
    cuidados: list[CuidadoOut]
    requisitos: list[RequisitoOut]
    preguntas: list[PreguntaOut]
    cita: CitaDetalleOut | None
    galeria: list[FotoOut]
    similares: list[MascotaOut]


class PasoOut(BaseSchema):
    icono: str
    titulo: str
    texto: str
    nota: str


class FaqOut(BaseSchema):
    pregunta: str
    respuesta: str


class ContenidoOut(BaseSchema):
    pasos_adopcion: list[PasoOut]
    pasos_refugio: list[PasoOut]
    faqs: list[FaqOut]
    requisitos: list[RequisitoOut]


class ImpactoOut(BaseSchema):
    total_adoptadas: int
    total_refugios: int
    total_en_acogida: int
    total_distritos: int
    total_mascotas: int
    total_perros: int
    total_gatos: int
    adoptadas_por_distrito: dict[str, int]


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------


class RegistroRequest(BaseSchema):
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    dni: str = Field(pattern=r"^\d{8}$")
    password: str = Field(min_length=8, max_length=72)
    telefono: str | None = Field(default=None, max_length=30)
    distrito: str | None = Field(default=None, max_length=80)
    rol: Literal["adoptante", "refugio"] = "adoptante"
    refugio_id: str | None = Field(default=None, max_length=60)


class LoginRequest(BaseSchema):
    password: str = Field(min_length=1, max_length=72)
    identificador: str | None = None
    email: str | None = None
    dni: str | None = None


class GoogleRequest(BaseSchema):
    id_token: str = Field(min_length=10)


class RecuperarRequest(BaseSchema):
    email: EmailStr


class UsuarioOut(BaseSchema):
    id: int
    nombre: str
    email: str
    dni: str | None
    telefono: str | None
    distrito: str | None
    rol: Literal["adoptante", "refugio", "admin"]
    refugio_id: str | None
    creado_en: datetime


class AuthResponse(BaseSchema):
    usuario: UsuarioOut
    token: str
    token_type: str = "Bearer"


class MensajeOut(BaseSchema):
    mensaje: str


# ---------------------------------------------------------------------------
# Solicitudes
# ---------------------------------------------------------------------------


class CitaOut(BaseSchema):
    fecha: str
    direccion: str
    coordinadora: str


class MensajeSolicitudOut(BaseSchema):
    iniciales: str
    nombre: str
    rol: str
    texto: str


class CierreOut(BaseSchema):
    titulo: str
    texto: str
    control_titulo: str
    control_fecha: str
    control_lugar: str


class EtapaOut(BaseSchema):
    titulo: str
    detalle: str
    destacado: bool


class SeguimientoFotoOut(BaseSchema):
    src: str
    alt: str
    creada_en: datetime | None = None


class SolicitudOut(BaseSchema):
    id: int
    estado: Literal["active", "completed", "cancelled"]
    nombre: str
    ficha_id: int
    foto_src: str
    foto_alt: str
    chip_texto: str
    chip_clase: str
    refugio: str
    lugar: str
    exp: str
    fecha_texto: str
    badge_texto: str
    badge_clase: str
    punto_clase: str
    paso_texto: str
    paso_texto_clase: str
    header_clase: str
    icono_mini: str
    icono_mini_clase: str
    paso: int
    barra_clase: str
    etapas: list[EtapaOut]
    cita: CitaOut | None
    mensaje: MensajeSolicitudOut | None
    tiempo_respuesta: str | None
    whatsapp: str | None
    cierre: CierreOut | None
    motivo_cancelacion: str | None
    fotos_seguimiento: list[SeguimientoFotoOut]
    creada_en: datetime


class PageSolicitudes(BaseSchema):
    items: list[SolicitudOut]
    page: int
    limit: int
    total: int
    total_pages: int


class CrearSolicitudRequest(BaseSchema):
    mascota_id: int = Field(gt=0)
    mensaje: str | None = Field(default=None, max_length=1000)
    telefono: str | None = Field(default=None, max_length=30)


class CancelarSolicitudRequest(BaseSchema):
    motivo: str = Field(default="No especificado", min_length=3, max_length=300)


class CambiarEtapaRequest(BaseSchema):
    etapa: int = Field(ge=1, le=5)
    nota: str | None = Field(default=None, max_length=500)


class AgendarCitaRequest(BaseSchema):
    fecha: str = Field(min_length=4, max_length=120)
    direccion: str = Field(min_length=4, max_length=200)
    coordinadora: str = Field(min_length=2, max_length=120)


class EnviarMensajeRequest(BaseSchema):
    texto: str = Field(min_length=2, max_length=1000)


# ---------------------------------------------------------------------------
# Favoritos y alertas
# ---------------------------------------------------------------------------


class FavoritoRequest(BaseSchema):
    mascota_id: int = Field(gt=0)


class FavoritosOut(BaseSchema):
    ids: list[int]
    mascotas: list[MascotaOut]


class AlertaRequest(BaseSchema):
    nombre: str = Field(min_length=2, max_length=120)
    contacto: str = Field(min_length=5, max_length=120)
    distrito: str | None = Field(default=None, max_length=80)
    especie: str | None = Field(default=None, max_length=40)
    mensaje: str | None = Field(default=None, max_length=1000)


class AlertaOut(BaseSchema):
    id: int
    nombre: str
    contacto: str
    distrito: str | None
    especie: str | None
    mensaje: str | None
    atendida: bool
    creado_en: datetime


class PageAlertas(BaseSchema):
    items: list[AlertaOut]
    total: int


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------


class ErrorOut(BaseSchema):
    code: str
    message: str
    details: Any | None = None
