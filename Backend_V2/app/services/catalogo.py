"""Catálogo de mascotas: filtros, paginación, estadísticas y CRUD."""

from __future__ import annotations

from typing import Literal

from ..domain import Mascota, SaludItem, Usuario
from ..errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from ..repositories.memory import MemoryRepository
from ..schemas import MascotaCreate, MascotaUpdate


def _coincide_edad(anios: float, grupo: str) -> bool:
    if grupo == "cachorro":
        return anios < 1
    if grupo == "joven":
        return 1 <= anios < 3
    if grupo == "adulto":
        return 3 <= anios <= 7
    if grupo == "senior":
        return anios > 7
    return True


def listar(
    repo: MemoryRepository,
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
    texto = (q or "").strip().lower()

    def incluir(mascota: Mascota) -> bool:
        if estado != "todos" and mascota.estado != estado:
            return False
        if texto:
            campos = (mascota.nombre, mascota.raza, mascota.etiqueta, mascota.lugar)
            if not any(texto in campo.lower() for campo in campos):
                return False
        if especie and mascota.especie != especie:
            return False
        if distrito and mascota.distrito.lower() != distrito.lower():
            return False
        if tamano and mascota.tamano != tamano:
            return False
        if sexo and mascota.sexo != sexo:
            return False
        if edad and not _coincide_edad(mascota.edad_anios, edad):
            return False
        if refugio_id and mascota.refugio_id != refugio_id:
            return False
        if solo_esterilizados and not mascota.esterilizado:
            return False
        if solo_vacunados and not mascota.vacunado:
            return False
        if solo_urgentes and not mascota.urgente:
            return False
        return True

    filtradas = [mascota for mascota in repo.listar_mascotas() if incluir(mascota)]

    if orden == "urgent":
        filtradas.sort(key=lambda m: (not m.urgente, m.id))
    elif orden == "youngest":
        filtradas.sort(key=lambda m: (m.edad_anios, m.id))
    elif orden == "oldest":
        filtradas.sort(key=lambda m: (-m.edad_anios, m.id))
    else:
        filtradas.sort(key=lambda m: -m.id)

    total = len(filtradas)
    inicio = (page - 1) * limit
    return filtradas[inicio : inicio + limit], total


def destacadas(repo: MemoryRepository, ids: list[int]) -> list[Mascota]:
    por_id = {mascota.id: mascota for mascota in repo.listar_mascotas()}
    return [por_id[mascota_id] for mascota_id in ids if mascota_id in por_id]


def obtener(repo: MemoryRepository, mascota_id: int) -> Mascota:
    mascota = repo.obtener_mascota(mascota_id)
    if mascota is None:
        raise NotFoundError("Mascota no encontrada.", {"mascotaId": mascota_id})
    return mascota


def _validar_refugio(repo: MemoryRepository, refugio_id: str) -> None:
    if repo.obtener_refugio(refugio_id) is None:
        raise ValidationError(
            "REFUGIO_INVALIDO",
            "El refugio indicado no existe.",
            {"refugioId": refugio_id},
        )


def _autorizar_refugio(usuario: Usuario, refugio_id: str) -> None:
    if usuario.rol == "refugio" and usuario.refugio_id != refugio_id:
        raise ForbiddenError("Solo puedes administrar las mascotas de tu refugio.")


def crear(repo: MemoryRepository, usuario: Usuario, datos: MascotaCreate) -> Mascota:
    _validar_refugio(repo, datos.refugio_id)
    _autorizar_refugio(usuario, datos.refugio_id)
    mascota_id = repo.siguiente_mascota_id()
    mascota = Mascota(
        id=mascota_id,
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
        ficha_id=f"LS-HYO-{5000 + mascota_id}",
        actualizado_dias=0,
        estado=datos.estado,
        salud=[SaludItem(texto=item.texto, ok=item.ok) for item in datos.salud],
    )
    return repo.guardar_mascota(mascota)


def actualizar(
    repo: MemoryRepository,
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
    return repo.guardar_mascota(mascota)


def eliminar(repo: MemoryRepository, mascota_id: int) -> None:
    obtener(repo, mascota_id)
    if any(solicitud.mascota_id == mascota_id for solicitud in repo.listar_solicitudes()):
        raise ConflictError(
            "MASCOTA_CON_SOLICITUDES",
            "No se puede eliminar una mascota con solicitudes registradas.",
            {"mascotaId": mascota_id},
        )
    repo.eliminar_mascota(mascota_id)
