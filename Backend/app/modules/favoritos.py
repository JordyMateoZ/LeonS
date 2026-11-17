from __future__ import annotations

from fastapi import APIRouter, Response
from pydantic import Field

from app.domain import DomainModel, Favorito
from app.errors import ConflictError, NotFoundError
from app.middleware.auth import AuthUser, Deps
from app.mapper import to_mascota_dto
from app.repositories import ahora_iso

router = APIRouter(prefix="/favoritos", tags=["favoritos"])


class MascotaIdRequest(DomainModel):
    mascota_id: int = Field(gt=0)


@router.get("")
async def listar(usuario: AuthUser, deps: Deps) -> dict:
    favoritos = await deps.repos.favoritos.list_by_usuario(usuario.id)
    mascotas = []
    for favorito in favoritos:
        mascota = await deps.repos.mascotas.find_by_id(favorito.mascota_id)
        if mascota:
            mascotas.append(to_mascota_dto(mascota))
    return {"data": mascotas, "meta": {"total": len(favoritos)}}


@router.get("/{mascota_id}/estado")
async def estado(usuario: AuthUser, deps: Deps, mascota_id: int) -> dict:
    favorito = await deps.repos.favoritos.find(usuario.id, mascota_id)
    return {"data": {"favorito": bool(favorito)}}


@router.post("", status_code=201)
async def agregar(body: MascotaIdRequest, usuario: AuthUser, deps: Deps) -> dict:
    mascota = await deps.repos.mascotas.find_by_id(body.mascota_id)
    if not mascota:
        raise NotFoundError("Mascota")
    if await deps.repos.favoritos.find(usuario.id, body.mascota_id):
        raise ConflictError("Esta mascota ya está en tus favoritos")

    favorito = await deps.repos.favoritos.add(
        Favorito(
            usuario_id=usuario.id,
            mascota_id=body.mascota_id,
            creado_en=ahora_iso(),
        )
    )
    return {
        "data": {
            "favorito": favorito.model_dump(by_alias=True, mode="json"),
            "mascota": to_mascota_dto(mascota),
        }
    }


@router.delete("/{mascota_id}", status_code=204)
async def eliminar(usuario: AuthUser, deps: Deps, mascota_id: int) -> Response:
    eliminado = await deps.repos.favoritos.remove(usuario.id, mascota_id)
    if not eliminado:
        raise NotFoundError("Favorito")
    return Response(status_code=204)
