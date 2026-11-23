from typing import Literal

from fastapi import APIRouter, Depends, Query, status

from ..container import Container
from ..dependencies import get_container, require_roles
from ..domain import Usuario
from ..errors import NotFoundError
from ..mapper import (
    detalle_out,
    mascota_out,
    page_mascotas,
    similares,
    stats_mascotas,
)
from ..schemas import (
    DetalleMascotaOut,
    MascotaCreate,
    MascotaOut,
    MascotaStats,
    MascotaUpdate,
    PageMascotas,
)
from ..services import catalogo

router = APIRouter(prefix="/mascotas", tags=["mascotas"])


def _refugios(container: Container) -> dict:
    return {refugio.id: refugio for refugio in container.repo.listar_refugios()}


@router.get("", response_model=PageMascotas)
def listar(
    container: Container = Depends(get_container),
    page: int = Query(1, ge=1),
    limit: int = Query(8, ge=1, le=50),
    q: str | None = None,
    especie: Literal["perro", "gato"] | None = None,
    distrito: str | None = None,
    tamano: Literal["Pequeño", "Mediano", "Grande"] | None = None,
    edad: Literal["cachorro", "joven", "adulto", "senior"] | None = None,
    sexo: Literal["Macho", "Hembra"] | None = None,
    refugio_id: str | None = Query(None, alias="refugioId"),
    estado: Literal["todos", "disponible", "adoptada", "en_acogida"] = "todos",
    orden: Literal["recent", "urgent", "youngest", "oldest"] = "recent",
    solo_esterilizados: bool = Query(False, alias="soloEsterilizados"),
    solo_vacunados: bool = Query(False, alias="soloVacunados"),
    solo_urgentes: bool = Query(False, alias="soloUrgentes"),
) -> PageMascotas:
    mascotas, total = catalogo.listar(
        container.repo,
        q=q,
        especie=especie,
        distrito=distrito,
        tamano=tamano,
        edad=edad,
        sexo=sexo,
        refugio_id=refugio_id,
        estado=estado,
        orden=orden,
        solo_esterilizados=solo_esterilizados,
        solo_vacunados=solo_vacunados,
        solo_urgentes=solo_urgentes,
        page=page,
        limit=limit,
    )
    refugios = _refugios(container)
    return page_mascotas(
        [mascota_out(mascota, refugios) for mascota in mascotas], page, limit, total
    )


@router.get("/destacadas", response_model=list[MascotaOut])
def destacadas(
    container: Container = Depends(get_container),
    ids: str = Query("1,2,3,4", description="Ids separados por coma"),
) -> list[MascotaOut]:
    try:
        lista = [int(valor) for valor in ids.split(",") if valor.strip()]
    except ValueError:
        lista = [1, 2, 3, 4]
    refugios = _refugios(container)
    return [mascota_out(m, refugios) for m in catalogo.destacadas(container.repo, lista)]


@router.get("/stats", response_model=MascotaStats)
def stats(container: Container = Depends(get_container)) -> MascotaStats:
    return stats_mascotas(
        container.repo.listar_mascotas(), len(container.repo.listar_refugios())
    )


@router.get("/{mascota_id}", response_model=MascotaOut)
def obtener(mascota_id: int, container: Container = Depends(get_container)) -> MascotaOut:
    mascota = catalogo.obtener(container.repo, mascota_id)
    return mascota_out(mascota, _refugios(container))


@router.get("/{mascota_id}/detalle", response_model=DetalleMascotaOut)
def detalle(mascota_id: int, container: Container = Depends(get_container)) -> DetalleMascotaOut:
    mascota = catalogo.obtener(container.repo, mascota_id)
    refugio = container.repo.obtener_refugio(mascota.refugio_id)
    if refugio is None:
        raise NotFoundError("El refugio de la mascota no existe.", {"refugioId": mascota.refugio_id})
    return detalle_out(
        mascota,
        refugio,
        container.repo.obtener_contenido(),
        container.repo.obtener_detalle(mascota_id),
        container.repo.listar_mascotas(),
        _refugios(container),
    )


@router.get("/{mascota_id}/similares", response_model=list[MascotaOut])
def mascotas_similares(
    mascota_id: int,
    container: Container = Depends(get_container),
    limite: int = Query(3, ge=1, le=10),
) -> list[MascotaOut]:
    mascota = catalogo.obtener(container.repo, mascota_id)
    refugios = _refugios(container)
    return [
        mascota_out(otra, refugios)
        for otra in similares(mascota, container.repo.listar_mascotas(), limite)
    ]


@router.post("", response_model=MascotaOut, status_code=status.HTTP_201_CREATED)
def crear(
    datos: MascotaCreate,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(require_roles("admin", "refugio")),
) -> MascotaOut:
    mascota = catalogo.crear(container.repo, usuario, datos)
    return mascota_out(mascota, _refugios(container))


@router.patch("/{mascota_id}", response_model=MascotaOut)
def actualizar(
    mascota_id: int,
    datos: MascotaUpdate,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(require_roles("admin", "refugio")),
) -> MascotaOut:
    mascota = catalogo.actualizar(container.repo, usuario, mascota_id, datos)
    return mascota_out(mascota, _refugios(container))


@router.delete("/{mascota_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    mascota_id: int,
    container: Container = Depends(get_container),
    _: Usuario = Depends(require_roles("admin")),
) -> None:
    catalogo.eliminar(container.repo, mascota_id)
