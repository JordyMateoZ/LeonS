from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Response, UploadFile
from pydantic import Field, model_validator

from app.adapters import generar_pdf
from app.domain import (
    CitaSolicitud,
    DomainModel,
    MensajeSolicitud,
    SeguimientoFoto,
    Solicitud,
    Solicitante,
)
from app.errors import AppError, ConflictError, ForbiddenError, NotFoundError
from app.middleware.auth import (
    AuthUser,
    Deps,
    OptionalAuthUser,
    require_roles,
)
from app.mapper import to_solicitud_dto
from app.repositories import ahora_iso

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])

MAX_IMAGEN_BYTES = 5 * 1024 * 1024
MAX_IMAGENES = 5


class SolicitanteRequest(DomainModel):
    nombre: str = Field(min_length=3, max_length=100)
    telefono: str = Field(min_length=9, max_length=30)
    distrito: str = Field(min_length=2, max_length=80)
    vivienda: str = Field(min_length=5, max_length=200)
    acepta_compromiso: bool
    email: str | None = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    dni: str | None = Field(default=None, pattern=r"^\d{8}$")


class CrearSolicitudRequest(DomainModel):
    mascota_id: int = Field(gt=0)
    solicitante: SolicitanteRequest

    @model_validator(mode="after")
    def compromiso_requerido(self) -> "CrearSolicitudRequest":
        if not self.solicitante.acepta_compromiso:
            raise ValueError("Debes aceptar el compromiso de tenencia responsable")
        return self


class CancelarRequest(DomainModel):
    motivo: str = Field(min_length=5, max_length=500)


class ActualizarSolicitudRequest(DomainModel):
    estado: str | None = None
    paso: int | None = Field(default=None, ge=1, le=5)
    cita: CitaSolicitud | None = None
    mensaje: MensajeSolicitud | None = None

    @model_validator(mode="after")
    def al_menos_un_campo(self) -> "ActualizarSolicitudRequest":
        if not any(
            valor is not None
            for valor in (self.estado, self.paso, self.cita, self.mensaje)
        ):
            raise ValueError("Debes enviar al menos un campo")
        return self


async def enriquecer(deps, solicitud: Solicitud) -> dict:
    mascota = await deps.repos.mascotas.find_by_id(solicitud.mascota_id)
    refugio = await deps.repos.refugios.find_by_id(mascota.refugio_id) if mascota else None
    return to_solicitud_dto(solicitud, mascota=mascota, refugio=refugio)


async def autorizada(deps, usuario: AuthUser, solicitud_id: int) -> Solicitud:
    solicitud = await deps.repos.solicitudes.find_by_id(solicitud_id)
    if not solicitud:
        raise NotFoundError("Solicitud")

    correo_usuario = (usuario.email or "").casefold()
    correo_solicitante = (solicitud.solicitante.email or "").casefold()
    mismo_correo = bool(correo_usuario and correo_usuario == correo_solicitante)
    if usuario.rol != "admin" and solicitud.usuario_id != usuario.id and not mismo_correo:
        raise ForbiddenError("Esta solicitud no te pertenece")
    return solicitud


@router.post("", status_code=201)
async def crear_solicitud(
    body: CrearSolicitudRequest,
    deps: Deps,
    usuario: OptionalAuthUser,
) -> dict:
    mascota = await deps.repos.mascotas.find_by_id(body.mascota_id)
    if not mascota:
        raise NotFoundError("Mascota")
    if mascota.estado != "disponible":
        raise ConflictError("Esta mascota ya no está disponible para adopción")

    datos_solicitante = body.solicitante.model_dump()
    if usuario and not datos_solicitante.get("email"):
        datos_solicitante["email"] = usuario.email
    solicitante = Solicitante(**datos_solicitante)

    if await deps.repos.solicitudes.exists_active(
        body.mascota_id, solicitante, usuario.id if usuario else None
    ):
        raise ConflictError(
            "Ya tienes una solicitud activa para esta mascota",
            {"mascotaId": body.mascota_id},
        )

    identificador = await deps.repos.solicitudes.next_id()
    fecha = ahora_iso()
    solicitud = Solicitud(
        id=identificador,
        estado="active",
        paso=2,
        mascota_id=mascota.id,
        ficha_id=mascota.id,
        nombre=mascota.nombre,
        refugio=mascota.refugio,
        lugar=mascota.lugar,
        exp=f"#SOL-HYO-{datetime.now().year}-{identificador:03d}",
        solicitante=solicitante,
        usuario_id=usuario.id if usuario else None,
        creada_en=fecha,
        actualizada_en=fecha,
        tiempo_respuesta="24 a 48 horas",
        fotos_seguimiento=[],
    )
    creada = await deps.repos.solicitudes.create(solicitud)

    refugio = await deps.repos.refugios.find_by_id(mascota.refugio_id)
    if refugio and refugio.whatsapp:
        await deps.notificaciones.whatsapp(
            refugio.whatsapp,
            f"Nueva solicitud {creada.exp} para {mascota.nombre}",
        )
    if solicitante.email:
        await deps.notificaciones.correo(
            solicitante.email,
            f"Recibimos tu solicitud {creada.exp}",
            "El refugio responderá entre 24 y 48 horas.",
        )

    return {"data": await enriquecer(deps, creada)}


@router.get("")
async def listar_solicitudes(usuario: AuthUser, deps: Deps) -> dict:
    solicitudes = await deps.repos.solicitudes.list_by_usuario(usuario.id)
    return {
        "data": [await enriquecer(deps, s) for s in solicitudes],
        "meta": {"total": len(solicitudes)},
    }


@router.get("/{solicitud_id}")
async def por_id(usuario: AuthUser, deps: Deps, solicitud_id: int) -> dict:
    solicitud = await autorizada(deps, usuario, solicitud_id)
    return {"data": await enriquecer(deps, solicitud)}


@router.post("/{solicitud_id}/cancelar")
async def cancelar(
    body: CancelarRequest,
    usuario: AuthUser,
    deps: Deps,
    solicitud_id: int,
) -> dict:
    solicitud = await autorizada(deps, usuario, solicitud_id)
    if solicitud.estado != "active":
        raise ConflictError("Solo se puede cancelar una solicitud activa")

    cancelada = solicitud.model_copy(
        update={
            "estado": "cancelled",
            "motivo_cancelacion": body.motivo,
            "actualizada_en": ahora_iso(),
        }
    )
    await deps.repos.solicitudes.update(cancelada)
    return {"data": await enriquecer(deps, cancelada)}


@router.patch("/{solicitud_id}")
async def actualizar(
    body: ActualizarSolicitudRequest,
    deps: Deps,
    solicitud_id: int,
    _: object = Depends(require_roles("admin", "shelter")),
) -> dict:
    solicitud = await deps.repos.solicitudes.find_by_id(solicitud_id)
    if not solicitud:
        raise NotFoundError("Solicitud")

    cambios = body.model_dump(exclude_unset=True)
    cambios["actualizada_en"] = ahora_iso()
    actualizada = solicitud.model_copy(update=cambios)
    await deps.repos.solicitudes.update(actualizada)
    return {"data": await enriquecer(deps, actualizada)}


def _respuesta_pdf(nombre: str, pdf: bytes) -> Response:
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{nombre}"'},
    )


@router.get("/{solicitud_id}/documentos/carnet")
async def carnet(usuario: AuthUser, deps: Deps, solicitud_id: int) -> Response:
    solicitud = await autorizada(deps, usuario, solicitud_id)
    mascota = await deps.repos.mascotas.find_by_id(solicitud.mascota_id)
    pdf = generar_pdf(
        "Carnet de salud - LeonS Huancayo",
        [
            f"Expediente: {solicitud.exp}",
            f"Mascota: {solicitud.nombre}",
            f"Ficha: {mascota.ficha_id if mascota else solicitud.ficha_id}",
            f"Refugio: {solicitud.refugio}",
            f"Titular: {solicitud.solicitante.nombre}",
            f"Vacunado: {'Sí' if mascota and mascota.vacunado else 'Pendiente'}",
            f"Esterilizado/a: {'Sí' if mascota and mascota.esterilizado else 'Pendiente'}",
            "Documento generado digitalmente para seguimiento post-adopción.",
        ],
    )
    return _respuesta_pdf(f"carnet-{solicitud.id}.pdf", pdf)


@router.get("/{solicitud_id}/documentos/contrato")
async def contrato(usuario: AuthUser, deps: Deps, solicitud_id: int) -> Response:
    solicitud = await autorizada(deps, usuario, solicitud_id)
    pdf = generar_pdf(
        "Acta de tenencia responsable - LeonS",
        [
            f"Expediente: {solicitud.exp}",
            f"Adoptante: {solicitud.solicitante.nombre}",
            f"DNI: {solicitud.solicitante.dni or 'Registrado en plataforma'}",
            f"Mascota: {solicitud.nombre}",
            f"Refugio: {solicitud.refugio}",
            "Me comprometo a brindar alimento, agua, abrigo y atención veterinaria.",
            "Me comprometo a no abandonar, regalar ni mantener al animal amarrado.",
            "Acepto el seguimiento fotográfico a los 1, 3 y 6 meses.",
            f"Aceptado: {'Sí' if solicitud.solicitante.acepta_compromiso else 'No'}",
        ],
    )
    return _respuesta_pdf(f"contrato-{solicitud.id}.pdf", pdf)


@router.get("/{solicitud_id}/seguimiento")
async def listar_seguimiento(usuario: AuthUser, deps: Deps, solicitud_id: int) -> dict:
    solicitud = await autorizada(deps, usuario, solicitud_id)
    return {
        "data": [f.model_dump(by_alias=True, mode="json") for f in solicitud.fotos_seguimiento]
    }


@router.post("/{solicitud_id}/seguimiento/fotos", status_code=201)
async def subir_fotos(
    usuario: AuthUser,
    deps: Deps,
    solicitud_id: int,
    fotos: list[UploadFile] = File(default=None, alias="fotos"),
) -> dict:
    solicitud = await autorizada(deps, usuario, solicitud_id)
    if not fotos:
        raise AppError(400, "SIN_ARCHIVOS", 'Envía al menos una imagen en el campo "fotos"')
    if len(fotos) > MAX_IMAGENES:
        raise AppError(400, "DEMASIADAS_IMAGENES", "Máximo 5 imágenes por envío")

    for foto in fotos:
        if not (foto.content_type or "").startswith("image/"):
            raise AppError(400, "SOLO_IMAGENES", "Solo se permiten archivos de imagen")
        contenido = await foto.read()
        if len(contenido) > MAX_IMAGEN_BYTES:
            raise AppError(400, "ARCHIVO_GRANDE", "La imagen supera el tamaño permitido")
        await foto.seek(0)

    guardadas = []
    ahora = ahora_iso()
    nuevas: list[SeguimientoFoto] = []
    for indice, foto in enumerate(fotos):
        guardada = await deps.storage.guardar(foto, f"seguimiento-{solicitud_id}")
        guardadas.append(guardada)
        nuevas.append(
            SeguimientoFoto(
                id=f"{solicitud_id}-{int(datetime.now(timezone.utc).timestamp())}-{indice}",
                nombre=guardada.nombre,
                url=guardada.url,
                mime_type=guardada.mime_type,
                tamanio=guardada.tamanio,
                creado_en=ahora,
            )
        )

    actualizada = solicitud.model_copy(
        update={
            "fotos_seguimiento": [*solicitud.fotos_seguimiento, *nuevas],
            "actualizada_en": ahora_iso(),
        }
    )
    await deps.repos.solicitudes.update(actualizada)
    return {"data": [f.model_dump(by_alias=True, mode="json") for f in nuevas]}
