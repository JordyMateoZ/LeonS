from __future__ import annotations

from fastapi import APIRouter

from app.middleware.auth import Deps
from app.mapper import to_contenido_dto

router = APIRouter(prefix="/contenido", tags=["contenido"])


@router.get("")
async def contenido_completo(deps: Deps) -> dict:
    return {"data": to_contenido_dto(await deps.repos.contenido.get())}


@router.get("/pasos")
async def pasos(deps: Deps) -> dict:
    contenido = to_contenido_dto(await deps.repos.contenido.get())
    return {
        "data": {
            "adopcion": contenido["pasosAdopcion"],
            "refugio": contenido["pasosRefugio"],
        }
    }


@router.get("/faqs")
async def faqs(deps: Deps) -> dict:
    contenido = to_contenido_dto(await deps.repos.contenido.get())
    return {"data": contenido["faqs"]}
