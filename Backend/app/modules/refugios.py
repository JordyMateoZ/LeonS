from __future__ import annotations

from fastapi import APIRouter

from app.domain import Especie, Refugio
from app.errors import NotFoundError
from app.middleware.auth import Deps
from app.mapper import to_mascota_dto, to_refugio_dto

router = APIRouter(prefix="/refugios", tags=["refugios"])


async def con_resumen(deps, refugio_id: str) -> tuple[Refugio, dict]:
    refugio = await deps.repos.refugios.find_by_id(refugio_id)
    if not refugio:
        raise NotFoundError("Refugio")
    mascotas = await deps.repos.refugios.find_mascotas(refugio_id)
    datos = to_refugio_dto(refugio)
    datos["resumen"] = {
        "total": len(mascotas),
        "disponibles": sum(1 for m in mascotas if m.estado == "disponible"),
        "adoptadas": sum(1 for m in mascotas if m.estado == "adoptada"),
        "enAcogida": sum(1 for m in mascotas if m.estado == "en_acogida"),
    }
    return refugio, datos


@router.get("")
async def listar_refugios(
    deps: Deps,
    distrito: str | None = None,
    especie: Especie | None = None,
    q: str | None = None,
) -> dict:
    refugios = await deps.repos.refugios.list(distrito=distrito, especie=especie, q=q)
    resultados = []
    for refugio in refugios:
        _, datos = await con_resumen(deps, refugio.id)
        resultados.append(datos)
    return {"data": resultados}


@router.get("/{refugio_id}/mascotas")
async def mascotas_del_refugio(deps: Deps, refugio_id: str) -> dict:
    await con_resumen(deps, refugio_id)
    mascotas = await deps.repos.refugios.find_mascotas(refugio_id)
    return {"data": [to_mascota_dto(m) for m in mascotas]}


@router.get("/{refugio_id}")
async def por_id(deps: Deps, refugio_id: str) -> dict:
    _, datos = await con_resumen(deps, refugio_id)
    return {"data": datos}
