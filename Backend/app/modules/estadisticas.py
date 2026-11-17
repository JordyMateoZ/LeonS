from __future__ import annotations

import asyncio

from fastapi import APIRouter

from app.domain import MascotaFiltros
from app.middleware.auth import Deps
from app.mapper import to_impacto

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


@router.get("/impacto")
async def impacto(deps: Deps) -> dict:
    refugios, solicitudes, mascotas = await asyncio.gather(
        deps.repos.refugios.list(),
        deps.repos.solicitudes.list_all(),
        deps.repos.mascotas.list(MascotaFiltros(page=1, limit=100)),
    )
    return {"data": to_impacto(refugios, solicitudes, mascotas.items)}
