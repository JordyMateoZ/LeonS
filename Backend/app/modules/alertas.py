from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import EmailStr, Field

from app.domain import AlertaRescate, DomainModel, Especie, Literal
from app.middleware.auth import Deps, require_roles
from app.middleware.rate_limit import limitar_alertas
from app.mapper import to_alerta_dto
from app.repositories import ahora_iso, nuevo_id

router = APIRouter(prefix="/alertas-rescate", tags=["alertas-rescate"])


class AlertaRequest(DomainModel):
    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr
    telefono: str = Field(min_length=9, max_length=30)
    distrito: str = Field(min_length=2, max_length=80)
    direccion: str = Field(min_length=4, max_length=200)
    descripcion: str = Field(min_length=15, max_length=1200)
    especie: Especie | Literal["otro"]
    cantidad: int = Field(default=1, ge=1, le=50)
    urgente: bool = False


@router.post("", status_code=201)
async def crear_alerta(
    body: AlertaRequest,
    deps: Deps,
    _: None = Depends(limitar_alertas),
) -> dict:
    alerta = AlertaRescate(
        id=nuevo_id(),
        nombre=body.nombre,
        email=str(body.email).casefold(),
        telefono=body.telefono,
        distrito=body.distrito,
        direccion=body.direccion,
        descripcion=body.descripcion,
        especie=body.especie,
        cantidad=body.cantidad,
        urgente=body.urgente,
        creado_en=ahora_iso(),
        atendida=False,
    )
    await deps.repos.alertas.create(alerta)
    await deps.notificaciones.whatsapp(
        "+51 999 999 999",
        f"Alerta de rescate en {alerta.distrito}: {alerta.descripcion[:120]}",
    )

    datos = to_alerta_dto(alerta)
    datos["mensaje"] = "Gracias. La red de refugios fue notificada."
    return {"data": datos}


@router.get("")
async def listar_alertas(
    deps: Deps,
    _: object = Depends(require_roles("admin", "shelter")),
) -> dict:
    alertas = await deps.repos.alertas.list()
    return {"data": [to_alerta_dto(a) for a in alertas]}
