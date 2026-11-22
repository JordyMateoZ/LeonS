"""Catálogo de mascotas: filtros, paginación, estadísticas y CRUD."""

from __future__ import annotations

from typing import Literal

from ..domain import FiltroMascotas, Mascota, Repositorio, SaludItem, Usuario
from ..errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from ..schemas import MascotaCreate, MascotaUpdate


def listar(
    repo: Repositorio,
    *,
    q: str | None = None,
    especie: str | None = None,
    distrito: str | None = None,
    tamano: str | None = None,
    edad: str | None = None,
    sexo: str | None = None,
    refugio_id: str | None = None,
    estado: str = "todos",
    orden: Literal["recent", "urgent", "youngest", "oldest"] = "recent",
    solo_esterilizados: bool = False,
    solo_vacunados: bool = False,
    solo_urgentes: bool = False,
    page: int = 1,
    limit: int = 8,
) -> tuple[list[Mascota], int]:
    """Filtros, orden y paginación delegados al repositorio (Fase 4.2, P1).

    El repositorio en memoria los resuelve en Python y el de SQL Server en la
    consulta; el resultado es equivalente en ambos casos.
    """
    return repo.buscar_mascotas(
        FiltroMascotas(
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
    )


def destacadas(repo: Repositorio, ids: list[int]) -> list[Mascota]:
    return repo.listar_mascotas_por_ids(ids)


def obtener(repo: Repositorio, mascota_id: int) -> Mascota:
    mascota = repo.obtener_mascota(mascota_id)
    if mascota is None:
        raise NotFoundError("Mascota no encontrada.", {"mascotaId": mascota_id})
    return mascota


def _validar_refugio(repo: Repositorio, refugio_id: str) -> None:
    if repo.obtener_refugio(refugio_id) is None:
        raise ValidationError(
            "REFUGIO_INVALIDO",
            "El refugio indicado no existe.",
            {"refugioId": refugio_id},
        )


def _autorizar_refugio(usuario: Usuario, refugio_id: str) -> None:
    if usuario.rol == "refugio" and usuario.refugio_id != refugio_id:
        raise ForbiddenError("Solo puedes administrar las mascotas de tu refugio.")


def crear(repo: Repositorio, usuario: Usuario, datos: MascotaCreate) -> Mascota:
    _validar_refugio(repo, datos.refugio_id)
    _autorizar_refugio(usuario, datos.refugio_id)
    mascota = Mascota(
        id=0,
        nombre=datos.nombre,
        nombre_corto=datos.nombre_corto or datos.nombre,
        especie=datos.especie,
        sexo=datos.sexo,
        raza=datos.raza,
        edad_anios=datos.edad_anios,
        tamano=datos.tamano,
        peso_kg=datos.peso_kg,
        distrito=datos.distrito,
        lugar=datos.lugar,
        foto=datos.foto,
        alt=datos.alt,
        descripcion=datos.descripcion,
        etiqueta=datos.etiqueta,
        etiqueta_icono=datos.etiqueta_icono,
        etiqueta_clase=(
            "bg-primary text-on-primary" if datos.urgente else "bg-secondary text-on-secondary"
        ),
        esterilizado=datos.esterilizado,
        vacunado=datos.vacunado,
        urgente=datos.urgente,
        refugio_id=datos.refugio_id,
        energia=datos.energia,
        ficha_id="",
        actualizado_dias=0,
        estado=datos.estado,
        salud=[SaludItem(texto=item.texto, ok=item.ok) for item in datos.salud],
    )
    return repo.crear_mascota(mascota)


def actualizar(
    repo: Repositorio,
    usuario: Usuario,
    mascota_id: int,
    datos: MascotaUpdate,
) -> Mascota:
    mascota = obtener(repo, mascota_id)
    _autorizar_refugio(usuario, mascota.refugio_id)

    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    if "refugio_id" in cambios:
        _validar_refugio(repo, cambios["refugio_id"])
        _autorizar_refugio(usuario, cambios["refugio_id"])
    if "salud" in cambios:
        mascota.salud = [
            SaludItem(texto=item["texto"], ok=item["ok"])
            for item in cambios.pop("salud")
        ]
    for campo, valor in cambios.items():
        setattr(mascota, campo, valor)
    mascota.actualizado_dias = 0
    return repo.actualizar_mascota(mascota)


def eliminar(repo: Repositorio, mascota_id: int) -> None:
    obtener(repo, mascota_id)
    if any(solicitud.mascota_id == mascota_id for solicitud in repo.listar_solicitudes()):
        raise ConflictError(
            "MASCOTA_CON_SOLICITUDES",
            "No se puede eliminar una mascota con solicitudes registradas.",
            {"mascotaId": mascota_id},
        )
    repo.eliminar_mascota(mascota_id)
