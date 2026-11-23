from typing import Literal

from fastapi import APIRouter, Depends, Query

from ..container import Container
from ..dependencies import get_container
from ..errors import NotFoundError
from ..mapper import mascota_out, refugio_detalle, refugio_out
from ..schemas import MascotaOut, RefugioDetalleOut, RefugioOut

router = APIRouter(prefix="/refugios", tags=["refugios"])


def _refugios(container: Container) -> dict:
    return {refugio.id: refugio for refugio in container.repo.listar_refugios()}


@router.get("", response_model=list[RefugioOut])
def listar(
    container: Container = Depends(get_container),
    distrito: str | None = None,
    especie: Literal["perro", "gato"] | None = None,
    verificado: bool | None = None,
) -> list[RefugioOut]:
    refugios = container.repo.listar_refugios()
    if distrito:
        refugios = [r for r in refugios if r.distrito.lower() == distrito.lower()]
    if especie:
        refugios = [r for r in refugios if especie in r.especies]
    if verificado is not None:
        refugios = [r for r in refugios if r.verificado is verificado]
    return [refugio_out(refugio) for refugio in refugios]


@router.get("/{refugio_id}", response_model=RefugioDetalleOut)
def detalle(refugio_id: str, container: Container = Depends(get_container)) -> RefugioDetalleOut:
    refugio = container.repo.obtener_refugio(refugio_id)
    if refugio is None:
        raise NotFoundError("Refugio no encontrado.", {"refugioId": refugio_id})
    return refugio_detalle(
        refugio, container.repo.listar_mascotas(), _refugios(container)
    )


@router.get("/{refugio_id}/mascotas", response_model=list[MascotaOut])
def mascotas(
    refugio_id: str,
    container: Container = Depends(get_container),
    estado: Literal["todos", "disponible", "adoptada", "en_acogida"] = "todos",
) -> list[MascotaOut]:
    refugio = container.repo.obtener_refugio(refugio_id)
    if refugio is None:
        raise NotFoundError("Refugio no encontrado.", {"refugioId": refugio_id})
    refugios = _refugios(container)
    lista = [
        mascota
        for mascota in container.repo.listar_mascotas()
        if mascota.refugio_id == refugio_id and (estado == "todos" or mascota.estado == estado)
    ]
    return [mascota_out(mascota, refugios) for mascota in lista]
