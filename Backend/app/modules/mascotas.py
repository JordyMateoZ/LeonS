from __future__ import annotations

import random
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query
from pydantic import Field

from app.domain import (
    DomainModel,
    Especie,
    EstadoMascota,
    Foto,
    Mascota,
    MascotaFiltros,
    SaludItem,
    Tamano,
)
from app.errors import NotFoundError
from app.middleware.auth import Deps, require_roles
from app.mapper import to_detalle_mascota, to_mascota_dto

router = APIRouter(prefix="/mascotas", tags=["mascotas"])


class CrearMascotaRequest(DomainModel):
    nombre: str = Field(min_length=2, max_length=80)
    especie: Especie
    sexo: Literal["Macho", "Hembra"]
    raza: str = Field(min_length=2, max_length=80)
    edad_anios: float = Field(ge=0, le=30)
    tamano: Tamano
    distrito: str = Field(min_length=2, max_length=80)
    lugar: str = Field(min_length=2, max_length=120)
    foto: str = Field(min_length=5, max_length=800)
    alt: str = Field(min_length=5, max_length=240)
    descripcion: str = Field(min_length=20, max_length=1500)
    energia: str = Field(min_length=2, max_length=60)
    refugio_id: str = Field(min_length=2, max_length=100)
    urgente: bool = False
    esterilizado: bool = False
    vacunado: bool = False
    etiqueta: str | None = Field(default=None, min_length=2, max_length=80)


@router.get("")
async def listar_mascotas(
    deps: Deps,
    especie: Especie | None = None,
    tamano: Tamano | None = None,
    distrito: str | None = None,
    estado: EstadoMascota | None = None,
    refugio_id: str | None = Query(default=None, alias="refugioId"),
    energia: str | None = None,
    urgente: bool | None = None,
    q: str | None = None,
    orden: Literal["recientes", "nombre", "edad_asc", "edad_desc"] = "recientes",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=100),
    todos: bool | None = None,
) -> dict:
    filtros = MascotaFiltros(
        page=page,
        limit=limit,
        especie=especie,
        tamano=tamano,
        distrito=distrito,
        estado=estado if estado is not None else (None if todos else "disponible"),
        refugio_id=refugio_id,
        energia=energia,
        urgente=urgente,
        q=q,
        orden=orden,
    )
    pagina = await deps.repos.mascotas.list(filtros)
    return {
        "data": [to_mascota_dto(m) for m in pagina.items],
        "meta": {
            "page": pagina.page,
            "limit": pagina.limit,
            "total": pagina.total,
            "totalPages": pagina.total_pages,
            "filters": {
                "especie": filtros.especie,
                "tamano": filtros.tamano,
                "distrito": filtros.distrito,
                "estado": filtros.estado,
                "refugioId": filtros.refugio_id,
                "energia": filtros.energia,
                "urgente": filtros.urgente,
                "q": filtros.q,
                "orden": filtros.orden,
            },
        },
    }


@router.get("/destacadas")
async def destacadas(
    deps: Deps,
    limit: int = Query(default=4, ge=1, le=20),
) -> dict:
    mascotas = []
    for mascota_id in (1, 2, 3, 4):
        mascota = await deps.repos.mascotas.find_by_id(mascota_id)
        if mascota and mascota.estado == "disponible":
            mascotas.append(mascota)
    return {"data": [to_mascota_dto(m) for m in mascotas[:limit]]}


@router.get("/stats")
async def stats(deps: Deps) -> dict:
    return {"data": (await deps.repos.mascotas.stats()).model_dump(by_alias=True, mode="json")}


@router.post("", status_code=201)
async def crear_mascota(
    body: CrearMascotaRequest,
    deps: Deps,
    _: object = Depends(require_roles("shelter", "admin")),
) -> dict:
    refugio = await deps.repos.refugios.find_by_id(body.refugio_id)
    if not refugio:
        raise NotFoundError("Refugio")

    anio = datetime.now().year
    genero = (
        ("Perra" if body.sexo == "Hembra" else "Perro")
        if body.especie == "perro"
        else ("Gata" if body.sexo == "Hembra" else "Gato")
    )
    tamano_texto = (
        f"{body.tamano} • "
        f"{'5 kg' if body.tamano == 'Pequeño' else '14 kg' if body.tamano == 'Mediano' else '28 kg'}"
    )
    salud: list[SaludItem] = []
    if body.esterilizado:
        salud.append(SaludItem(texto="Esterilizado/a", ok=True))
    if body.vacunado:
        salud.append(SaludItem(texto="Vacunas al día", ok=True))

    mascota = Mascota(
        id=0,
        ficha_id=f"LS-HYO-{anio}-{random.randint(1000, 9999)}",
        nombre=body.nombre,
        nombre_corto=body.nombre.split()[0],
        especie=body.especie,
        sexo=body.sexo,
        genero_texto=genero,
        raza=body.raza,
        edad_texto=f"{body.edad_anios} años",
        edad_anios=body.edad_anios,
        tamano=body.tamano,
        tamano_texto=tamano_texto,
        distrito=body.distrito,
        lugar=body.lugar,
        foto=body.foto,
        alt=body.alt,
        descripcion=body.descripcion,
        etiqueta=body.etiqueta or "Nueva ficha",
        etiqueta_icono="favorite" if body.urgente else "pets",
        salud=salud,
        esterilizado=body.esterilizado,
        vacunado=body.vacunado,
        urgente=body.urgente,
        refugio=refugio.nombre,
        refugio_id=refugio.id,
        energia=body.energia,
        actualizado="recién publicada",
        estado="disponible",
        galeria=[Foto(src=body.foto, alt=body.alt)],
        rasgos=[],
    )
    creada = await deps.repos.mascotas.create(mascota)
    return {"data": to_mascota_dto(creada)}


@router.get("/{mascota_id}/detalle")
async def detalle(deps: Deps, mascota_id: int = Path(gt=0)) -> dict:
    mascota = await deps.repos.mascotas.find_by_id(mascota_id)
    if not mascota:
        raise NotFoundError("Mascota")
    return {"data": to_detalle_mascota(mascota)}


@router.get("/{mascota_id}/similares")
async def similares(
    deps: Deps,
    mascota_id: int = Path(gt=0),
    limit: int = Query(default=3, ge=1, le=20),
) -> dict:
    mascota = await deps.repos.mascotas.find_by_id(mascota_id)
    if not mascota:
        raise NotFoundError("Mascota")
    encontradas = await deps.repos.mascotas.find_similares(mascota_id, limit)
    return {"data": [to_mascota_dto(m) for m in encontradas]}


@router.get("/{mascota_id}")
async def por_id(deps: Deps, mascota_id: int = Path(gt=0)) -> dict:
    mascota = await deps.repos.mascotas.find_by_id(mascota_id)
    if not mascota:
        raise NotFoundError("Mascota")
    return {"data": to_mascota_dto(mascota)}
