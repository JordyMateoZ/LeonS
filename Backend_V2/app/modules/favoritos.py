from fastapi import APIRouter, Depends, Query, status

from ..container import Container
from ..dependencies import get_container, get_current_user
from ..domain import Usuario
from ..mapper import mascota_out
from ..schemas import FavoritoRequest, FavoritosOut
from ..services import social

router = APIRouter(prefix="/favoritos", tags=["favoritos"])


def _salida(container: Container, usuario: Usuario) -> FavoritosOut:
    refugios = {refugio.id: refugio for refugio in container.repo.listar_refugios()}
    mascotas = social.listar_favoritos(container.repo, usuario)
    return FavoritosOut(
        ids=[mascota.id for mascota in mascotas],
        mascotas=[mascota_out(mascota, refugios) for mascota in mascotas],
    )


@router.get("", response_model=FavoritosOut)
def listar(
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> FavoritosOut:
    return _salida(container, usuario)


@router.post("", response_model=FavoritosOut, status_code=status.HTTP_201_CREATED)
def agregar(
    datos: FavoritoRequest,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> FavoritosOut:
    social.agregar_favorito(container.repo, usuario, datos.mascota_id)
    return _salida(container, usuario)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def quitar_por_query(
    mascota_id: int = Query(..., alias="mascotaId"),
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> None:
    social.quitar_favorito(container.repo, usuario, mascota_id)


@router.delete("/{mascota_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar(
    mascota_id: int,
    container: Container = Depends(get_container),
    usuario: Usuario = Depends(get_current_user),
) -> None:
    social.quitar_favorito(container.repo, usuario, mascota_id)
