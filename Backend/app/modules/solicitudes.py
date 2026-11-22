from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status

from ..container import Container
from ..dependencies import get_container, get_current_user, require_roles
from ..domain import Mascota, Refugio, Solicitud, Usuario
from ..errors import NotFoundError
from ..mapper import page_solicitudes, solicitud_out
from ..schemas import (
    AgendarCitaRequest,
    CambiarEtapaRequest,
    CancelarSolicitudRequest,
    CrearSolicitudRequest,
    EnviarMensajeRequest,
    PageSolicitudes,
    SolicitudOut,
)
from ..services import solicitudes as solicitudes_service

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])


class _CacheRelaciones:
    """Carga por lotes de mascotas, refugios y usuarios para evitar N+1 (P2)."""

    def __init__(self, container: Container) -> None:
        self.mascotas: dict[int, Mascota | None] = {
            m.id: m for m in container.repo.listar_mascotas()
        }
        self.refugios: dict[str, Refugio | None] = {
            r.id: r for r in container.repo.listar_refugios()
        }
        self.usuarios: dict[int, Usuario | None] = {
            u.id: u for u in container.repo.listar_usuarios()
        }


def _out(
    cache: _CacheRelaciones,
    solicitud: Solicitud,
) -> SolicitudOut:
    mascota = cache.mascotas.get(solicitud.mascota_id)
    if mascota is None:
        raise NotFoundError("La mascota de la solicitud ya no existe.")
    refugio = cache.refugios.get(mascota.refugio_id)
    usuario = cache.usuarios.get(solicitud.usuario_id)
    return solicitud_out(solicitud, mascota, refugio, usuario)


@router.get("", response_model=PageSolicitudes)
def listar(
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
    estado: Literal["todos", "activa", "cancelada", "completada"] = "todos",
    incluir_canceladas: bool = Query(False, alias="incluirCanceladas"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> PageSolicitudes:
    solicitudes, total = solicitudes_service.listar(
        container.repo,
        usuario,
        estado=estado,
        incluir_canceladas=incluir_canceladas,
        page=page,
        limit=limit,
    )
    cache = _CacheRelaciones(container)
    return page_solicitudes(
        [_out(cache, solicitud) for solicitud in solicitudes], page, limit, total
    )


@router.post("", response_model=SolicitudOut, status_code=status.HTTP_201_CREATED)
def crear(
    datos: CrearSolicitudRequest,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(require_roles("adoptante")),
) -> SolicitudOut:
    solicitud = solicitudes_service.crear(container.repo, usuario, datos)
    return _out(_CacheRelaciones(container), solicitud)


@router.get("/{solicitud_id}", response_model=SolicitudOut)
def obtener(
    solicitud_id: int,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> SolicitudOut:
    return _out(_CacheRelaciones(container), solicitudes_service.obtener(container.repo, usuario, solicitud_id))


@router.patch("/{solicitud_id}/cancelar", response_model=SolicitudOut)
def cancelar(
    solicitud_id: int,
    datos: CancelarSolicitudRequest | None = None,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> SolicitudOut:
    motivo = datos.motivo if datos else "No especificado"
    solicitud = solicitudes_service.cancelar(container.repo, usuario, solicitud_id, motivo)
    return _out(_CacheRelaciones(container), solicitud)


@router.patch("/{solicitud_id}/etapa", response_model=SolicitudOut)
def cambiar_etapa(
    solicitud_id: int,
    datos: CambiarEtapaRequest,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> SolicitudOut:
    solicitud = solicitudes_service.cambiar_etapa(
        container.repo, usuario, solicitud_id, datos.etapa, datos.nota
    )
    return _out(_CacheRelaciones(container), solicitud)


@router.post("/{solicitud_id}/citas", response_model=SolicitudOut)
def agendar_cita(
    solicitud_id: int,
    datos: AgendarCitaRequest,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> SolicitudOut:
    solicitud = solicitudes_service.agendar_cita(container.repo, usuario, solicitud_id, datos)
    return _out(_CacheRelaciones(container), solicitud)


@router.post("/{solicitud_id}/mensajes", response_model=SolicitudOut)
def enviar_mensaje(
    solicitud_id: int,
    datos: EnviarMensajeRequest,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> SolicitudOut:
    solicitud = solicitudes_service.enviar_mensaje(
        container.repo, usuario, solicitud_id, datos.texto
    )
    return _out(_CacheRelaciones(container), solicitud)


@router.post(
    "/{solicitud_id}/seguimiento",
    response_model=SolicitudOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_seguimiento(
    solicitud_id: int,
    archivo: UploadFile = File(...),
    nota: str | None = Form(None),
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> SolicitudOut:
    contenido = archivo.file.read()
    solicitud = solicitudes_service.registrar_seguimiento(
        container.repo,
        usuario,
        solicitud_id,
        container.storage,
        nombre_archivo=archivo.filename,
        content_type=archivo.content_type,
        contenido=contenido,
        nota=nota,
    )
    return _out(_CacheRelaciones(container), solicitud)


@router.get("/{solicitud_id}/documentos")
def documentos(
    solicitud_id: int,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    contenido, nombre = solicitudes_service.documentos(
        container.repo, usuario, solicitud_id
    )
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
