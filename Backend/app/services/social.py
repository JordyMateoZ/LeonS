"""Favoritos y alertas de rescate."""

from __future__ import annotations

from ..domain import AlertaRescate, Favorito, Mascota, Repositorio, Usuario
from ..errors import ConflictError, NotFoundError
from ..schemas import AlertaRequest


def listar_favoritos(repo: Repositorio, usuario: Usuario) -> list[Mascota]:
    return repo.listar_favoritos_mascotas(usuario.id)


def agregar_favorito(repo: Repositorio, usuario: Usuario, mascota_id: int) -> Mascota:
    mascota = repo.obtener_mascota(mascota_id)
    if mascota is None:
        raise NotFoundError("Mascota no encontrada.", {"mascotaId": mascota_id})
    if any(f.mascota_id == mascota_id for f in repo.listar_favoritos(usuario.id)):
        raise ConflictError(
            "FAVORITO_DUPLICADO",
            "La mascota ya está en tus favoritos.",
            {"mascotaId": mascota_id},
        )
    repo.crear_favorito(Favorito(usuario_id=usuario.id, mascota_id=mascota_id))
    return mascota


def quitar_favorito(repo: Repositorio, usuario: Usuario, mascota_id: int) -> None:
    if not repo.eliminar_favorito(usuario.id, mascota_id):
        raise NotFoundError("La mascota no está en tus favoritos.", {"mascotaId": mascota_id})


def crear_alerta(repo: Repositorio, datos: AlertaRequest) -> AlertaRescate:
    alerta = AlertaRescate(
        id=0,
        nombre=datos.nombre,
        contacto=datos.contacto,
        distrito=datos.distrito,
        especie=datos.especie,
        mensaje=datos.mensaje,
    )
    return repo.crear_alerta(alerta)


def listar_alertas(
    repo: Repositorio, *, page: int = 1, limit: int = 20
) -> tuple[list[AlertaRescate], int]:
    alertas = sorted(repo.listar_alertas(), key=lambda a: (-a.creado_en.timestamp(), -a.id))
    total = len(alertas)
    inicio = (page - 1) * limit
    return alertas[inicio : inicio + limit], total
