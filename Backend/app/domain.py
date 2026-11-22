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


FICHAS_SEMILLA = 16


def ficha_predeterminada(mascota_id: int) -> str:
    """`fichaId` derivado del id (D-023); nunca se persiste.

    La semilla usa cuatro dígitos (`LS-HYO-0482`…`LS-HYO-0497`); las altas
    nuevas arrancan en 5000 para no colisionar con ese rango.
    """
    base = 481 if mascota_id <= FICHAS_SEMILLA else 5000
    return f"LS-HYO-{base + mascota_id:04d}"


def codigo_solicitud(solicitud_id: int, anio: int) -> str:
    """Código legible de la postulación; depende del id definitivo (D-025)."""
    return f"#SOL-HYO-{anio}-{solicitud_id:03d}"


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
    # A-14: identidad real del usuario autenticado que creó el mensaje.
    # No forma parte del contrato JSON; el mapper no lo expone.
    autor_id: int | None = None


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
    activo: bool = True
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


@dataclass(slots=True)
class FiltroMascotas:
    """Criterios del catálogo (Fase 4.2, P1).

    El repositorio devuelve solo la página pedida y el total de coincidencias.
    El repositorio en memoria lo resuelve en Python y el de SQL Server empuja
    filtros, orden y paginación a la consulta, con la misma semántica.
    """

    q: str | None = None
    especie: str | None = None
    distrito: str | None = None
    tamano: str | None = None
    edad: str | None = None
    sexo: str | None = None
    refugio_id: str | None = None
    estado: str = "todos"
    orden: Literal["recent", "urgent", "youngest", "oldest"] = "recent"
    solo_esterilizados: bool = False
    solo_vacunados: bool = False
    solo_urgentes: bool = False
    page: int = 1
    limit: int = 8


class Repositorio(Protocol):
    """Contrato que deben cumplir los repositorios (memoria y SQL Server).

    `MemoryRepository` lo implementa en las fases 0–3 y `SqlServerRepository`
    en la Fase 6. Los servicios dependen de este protocolo, no de una clase
    concreta.

    Las operaciones `crear_*` insertan y devuelven la entidad con el id
    definitivo (D-025). El repositorio ignora el `id` que traiga la entidad
    (se envía `0`) y, en el caso de las solicitudes, también el `codigo`
    (se envía vacío): ambos se generan al insertar. Las operaciones
    `actualizar_*` exigen una entidad ya persistida.
    """

    # -- Catálogo ---------------------------------------------------------
    def listar_mascotas(self) -> list[Mascota]: ...

    def buscar_mascotas(self, filtro: FiltroMascotas) -> tuple[list[Mascota], int]: ...

    def obtener_mascota(self, mascota_id: int) -> Mascota | None: ...

    def crear_mascota(self, mascota: Mascota) -> Mascota: ...

    def actualizar_mascota(self, mascota: Mascota) -> Mascota: ...

    def eliminar_mascota(self, mascota_id: int) -> None: ...

    # -- Refugios ---------------------------------------------------------
    def listar_refugios(self) -> list[Refugio]: ...

    def obtener_refugio(self, refugio_id: str) -> Refugio | None: ...

    # -- Contenido --------------------------------------------------------
    def obtener_contenido(self) -> Contenido: ...

    def obtener_detalle(self, mascota_id: int) -> DetalleMascota | None: ...

    # -- Estadísticas -----------------------------------------------------
    def resumen_impacto(self) -> dict[str, object]: ...

    # -- Catálogo optimizado --------------------------------------------
    def listar_mascotas_por_ids(self, ids: list[int]) -> list[Mascota]: ...
    def listar_mascotas_de_refugio(self, refugio_id: str, *, estado: str = "todos") -> list[Mascota]: ...
    def estadisticas_mascotas(self) -> dict[str, object]: ...

    # -- Usuarios ---------------------------------------------------------
    def obtener_usuario(self, usuario_id: int) -> Usuario | None: ...

    def buscar_usuario_por_email(self, email: str) -> Usuario | None: ...

    def buscar_usuario_por_dni(self, dni: str) -> Usuario | None: ...

    def listar_usuarios(self) -> list[Usuario]: ...

    def crear_usuario(self, usuario: Usuario) -> Usuario: ...

    # -- Solicitudes ------------------------------------------------------
    def listar_solicitudes(self) -> list[Solicitud]: ...

    def buscar_solicitudes(
        self,
        *,
        usuario_id: int,
        rol: str,
        refugio_id: str | None,
        estado: str = "todos",
        incluir_canceladas: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Solicitud], int]:
        """Solicitudes visibles para un usuario, ya filtradas y paginadas.

        Reproduce `services.solicitudes.puede_ver`: el admin ve todo, cada
        usuario ve las suyas y un refugio ve las de sus mascotas. La
        comparación la hace el repositorio (Fase 4.2, P6) para no recorrer
        todas las solicitudes ni resolver la mascota una por una.
        """
        ...

    def obtener_solicitud(self, solicitud_id: int) -> Solicitud | None: ...

    def crear_solicitud(self, solicitud: Solicitud) -> Solicitud: ...

    def actualizar_solicitud(self, solicitud: Solicitud) -> Solicitud: ...

    def finalizar_solicitud(self, solicitud: Solicitud, usuario: Usuario) -> Solicitud:
        """Finaliza una adopción en una sola transacción.

        Revalida permisos, solicitud, mascota, ausencia de otras postulaciones
        activas y estado vigente de la mascota. Una solicitud ya completada y
        coherente se devuelve sin escribir (idempotencia).
        """
        ...

    # -- Favoritos --------------------------------------------------------
    def listar_favoritos(self, usuario_id: int) -> list[Favorito]: ...

    def listar_favoritos_mascotas(self, usuario_id: int) -> list[Mascota]: ...

    def crear_favorito(self, favorito: Favorito) -> Favorito: ...

    def eliminar_favorito(self, usuario_id: int, mascota_id: int) -> bool: ...

    # -- Alertas ----------------------------------------------------------
    def listar_alertas(self) -> list[AlertaRescate]: ...

    def crear_alerta(self, alerta: AlertaRescate) -> AlertaRescate: ...
