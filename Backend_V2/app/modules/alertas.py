from fastapi import APIRouter, Depends, Query, Request, status

from ..container import Container
from ..dependencies import get_container, require_roles
from ..domain import Usuario
from ..mapper import alerta_out
from ..schemas import AlertaOut, AlertaRequest, PageAlertas
from ..services import social

router = APIRouter(prefix="/alertas-rescate", tags=["alertas"])


@router.post("", response_model=AlertaOut, status_code=status.HTTP_201_CREATED)
def crear(
    datos: AlertaRequest,
    request: Request,
    container: Container = Depends(get_container),
) -> AlertaOut:
    ip = request.client.host if request.client else "desconocido"
    container.limiter.consumir(f"alertas:{ip}")
    alerta = social.crear_alerta(container.repo, datos)
    container.notifier.enviar(
        alerta.contacto,
        "Alerta de rescate registrada",
        f"{alerta.nombre} reportó una mascota en {alerta.distrito or 'Huancayo'}.",
    )
    return alerta_out(alerta)


@router.get("", response_model=PageAlertas)
def listar(
    container: Container = Depends(get_container),
    _: Usuario = Depends(require_roles("admin", "refugio")),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> PageAlertas:
    alertas, total = social.listar_alertas(container.repo, page=page, limit=limit)
    return PageAlertas(items=[alerta_out(alerta) for alerta in alertas], total=total)
