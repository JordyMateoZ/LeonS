from __future__ import annotations

import copy
import re
import uuid
from datetime import datetime, timezone

import bcrypt

from app.data import load_seed
from app.domain import (
    AlertaRepo,
    AlertaRescate,
    Contenido,
    ContenidoRepo,
    Favorito,
    FavoritoRepo,
    Mascota,
    MascotaFiltros,
    MascotaRepo,
    MascotaStats,
    Page,
    RefugioRepo,
    Repositorios,
    Solicitud,
    SolicitudRepo,
    Solicitante,
    Usuario,
    UsuarioRepo,
)


def ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, hash_almacenado: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_almacenado.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def normalizar(texto: str | None) -> str:
    return (texto or "").strip().casefold()


def mismo_solicitante(a: Solicitante, b: Solicitante) -> bool:
    email = normalizar(a.email)
    dni = normalizar(a.dni)
    telefono = re.sub(r"\D", "", a.telefono or "")
    nombre = normalizar(a.nombre)

    if email and email == normalizar(b.email):
        return True
    if dni and dni == normalizar(b.dni):
        return True
    if telefono and telefono == re.sub(r"\D", "", b.telefono or ""):
        return True
    return bool(nombre and nombre == normalizar(b.nombre))


class UsuariosMemoria(UsuarioRepo):
    def __init__(self) -> None:
        fecha = ahora_iso()
        comun = {
            "nombre": "Familia",
            "apellido": "Adoptiva",
            "password_hash": hash_password("demo1234"),
            "rol": "adopter",
            "telefono": "+51 900 000 000",
            "distrito": "El Tambo",
            "terminos_aceptados": True,
            "activo": True,
            "creado_en": fecha,
            "actualizado_en": fecha,
        }
        self._usuarios: dict[str, Usuario] = {
            "demo-user": Usuario(
                id="demo-user", email="demo@leons.pe", dni="00000001", **comun
            ),
            "admin-user": Usuario(
                id="admin-user",
                nombre="Coordinación",
                apellido="LeonS",
                email="admin@leons.pe",
                dni="00000002",
                password_hash=hash_password("admin1234"),
                rol="admin",
                telefono=comun["telefono"],
                distrito=comun["distrito"],
                terminos_aceptados=True,
                activo=True,
                creado_en=fecha,
                actualizado_en=fecha,
            ),
        }

    async def find_by_id(self, usuario_id: str) -> Usuario | None:
        usuario = self._usuarios.get(usuario_id)
        return copy.deepcopy(usuario) if usuario else None

    async def find_by_email(self, email: str) -> Usuario | None:
        buscado = normalizar(email)
        usuario = next(
            (u for u in self._usuarios.values() if normalizar(u.email) == buscado), None
        )
        return copy.deepcopy(usuario) if usuario else None

    async def find_by_dni(self, dni: str) -> Usuario | None:
        usuario = next((u for u in self._usuarios.values() if u.dni == dni.strip()), None)
        return copy.deepcopy(usuario) if usuario else None

    async def find_by_google_id(self, google_id: str) -> Usuario | None:
        usuario = next((u for u in self._usuarios.values() if u.google_id == google_id), None)
        return copy.deepcopy(usuario) if usuario else None

    async def create(self, usuario: Usuario) -> Usuario:
        self._usuarios[usuario.id] = copy.deepcopy(usuario)
        return copy.deepcopy(usuario)

    async def update(self, usuario: Usuario) -> Usuario:
        self._usuarios[usuario.id] = copy.deepcopy(usuario)
        return copy.deepcopy(usuario)


class MascotasMemoria(MascotaRepo):
    def __init__(self, mascotas: list[Mascota]) -> None:
        self._mascotas = copy.deepcopy(mascotas)

    def snapshot(self) -> list[Mascota]:
        """Solo para composición interna de repositorios en memoria."""
        return self._mascotas

    async def list(self, filtros: MascotaFiltros) -> Page[Mascota]:
        pagina = max(1, filtros.page)
        limite = min(100, max(1, filtros.limit))
        q = normalizar(filtros.q)

        items = [
            m
            for m in self._mascotas
            if (filtros.especie is None or m.especie == filtros.especie)
            and (filtros.tamano is None or m.tamano == filtros.tamano)
            and (filtros.estado is None or m.estado == filtros.estado)
            and (filtros.refugio_id is None or m.refugio_id == filtros.refugio_id)
            and (filtros.distrito is None or normalizar(m.distrito) == normalizar(filtros.distrito))
            and (filtros.energia is None or normalizar(m.energia) == normalizar(filtros.energia))
            and (filtros.urgente is None or m.urgente == filtros.urgente)
            and (
                not q
                or q
                in normalizar(
                    " ".join(
                        [
                            m.nombre,
                            m.raza,
                            m.distrito,
                            m.refugio,
                            m.ficha_id,
                            m.descripcion,
                        ]
                    )
                )
            )
        ]

        if filtros.orden == "nombre":
            items.sort(key=lambda m: m.nombre.casefold())
        elif filtros.orden == "edad_asc":
            items.sort(key=lambda m: m.edad_anios)
        elif filtros.orden == "edad_desc":
            items.sort(key=lambda m: -m.edad_anios)
        else:
            items.sort(key=lambda m: -m.id)

        total = len(items)
        inicio = (pagina - 1) * limite
        return Page(
            items=copy.deepcopy(items[inicio : inicio + limite]),
            total=total,
            page=pagina,
            limit=limite,
            total_pages=max(1, (total + limite - 1) // limite),
        )

    async def find_by_id(self, mascota_id: int) -> Mascota | None:
        mascota = next((m for m in self._mascotas if m.id == mascota_id), None)
        return copy.deepcopy(mascota) if mascota else None

    async def find_by_ficha_id(self, ficha_id: str) -> Mascota | None:
        mascota = next((m for m in self._mascotas if m.ficha_id == ficha_id), None)
        return copy.deepcopy(mascota) if mascota else None

    async def find_similares(self, mascota_id: int, limit: int) -> list[Mascota]:
        origen = await self.find_by_id(mascota_id)
        if not origen:
            return []

        puntuados = []
        for mascota in self._mascotas:
            if mascota.id == mascota_id or mascota.estado != "disponible":
                continue
            score = (
                (4 if mascota.especie == origen.especie else 0)
                + (2 if mascota.tamano == origen.tamano else 0)
                + (2 if mascota.distrito == origen.distrito else 0)
                + (1 if mascota.energia == origen.energia else 0)
            )
            if score > 0:
                puntuados.append((score, mascota))

        puntuados.sort(key=lambda tupla: (-tupla[0], -tupla[1].id))
        return copy.deepcopy([m for _, m in puntuados[:limit]])

    async def stats(self) -> MascotaStats:
        distritos: dict[str, int] = {}
        for mascota in self._mascotas:
            distritos[mascota.distrito] = distritos.get(mascota.distrito, 0) + 1

        return MascotaStats(
            total=len(self._mascotas),
            disponibles=sum(1 for m in self._mascotas if m.estado == "disponible"),
            adoptadas=sum(1 for m in self._mascotas if m.estado == "adoptada"),
            en_acogida=sum(1 for m in self._mascotas if m.estado == "en_acogida"),
            urgentes=sum(1 for m in self._mascotas if m.urgente),
            por_especie={
                "perro": sum(1 for m in self._mascotas if m.especie == "perro"),
                "gato": sum(1 for m in self._mascotas if m.especie == "gato"),
            },
            por_distrito=[
                {"distrito": distrito, "total": total}
                for distrito, total in sorted(
                    distritos.items(), key=lambda item: (-item[1], item[0])
                )
            ],
        )

    async def create(self, mascota: Mascota) -> Mascota:
        nueva = mascota.model_copy(update={"id": max((m.id for m in self._mascotas), default=0) + 1})
        self._mascotas.append(copy.deepcopy(nueva))
        return copy.deepcopy(nueva)


class RefugiosMemoria(RefugioRepo):
    def __init__(self, refugios: list, mascotas: MascotasMemoria) -> None:
        from app.domain import Refugio

        self._refugios: list[Refugio] = copy.deepcopy(refugios)
        self._mascotas = mascotas

    async def list(
        self,
        distrito: str | None = None,
        especie: str | None = None,
        q: str | None = None,
    ) -> list:
        busqueda = normalizar(q)
        return copy.deepcopy(
            [
                r
                for r in self._refugios
                if (distrito is None or normalizar(r.distrito) == normalizar(distrito))
                and (especie is None or especie in r.especies)
                and (
                    not busqueda
                    or busqueda
                    in normalizar(" ".join([r.nombre, r.distrito, r.descripcion, r.contacto]))
                )
            ]
        )

    async def find_by_id(self, refugio_id: str) -> object | None:
        refugio = next((r for r in self._refugios if r.id == refugio_id), None)
        return copy.deepcopy(refugio) if refugio else None

    async def find_mascotas(self, refugio_id: str) -> list[Mascota]:
        return copy.deepcopy([m for m in self._mascotas.snapshot() if m.refugio_id == refugio_id])


class SolicitudesMemoria(SolicitudRepo):
    def __init__(
        self,
        solicitudes: list[Solicitud],
        mascotas: MascotaRepo,
        refugios: RefugioRepo,
    ) -> None:
        self._solicitudes = copy.deepcopy(solicitudes)
        self._mascotas = mascotas
        self._refugios = refugios

    async def list_by_usuario(self, usuario_id: str) -> list[Solicitud]:
        return copy.deepcopy([s for s in self._solicitudes if s.usuario_id == usuario_id])

    async def list_all(self) -> list[Solicitud]:
        return copy.deepcopy(self._solicitudes)

    async def find_by_id(self, solicitud_id: int) -> Solicitud | None:
        solicitud = next((s for s in self._solicitudes if s.id == solicitud_id), None)
        return copy.deepcopy(solicitud) if solicitud else None

    async def exists_active(
        self, mascota_id: int, solicitante: Solicitante, usuario_id: str | None = None
    ) -> bool:
        for solicitud in self._solicitudes:
            if solicitud.mascota_id != mascota_id or solicitud.estado != "active":
                continue
            if usuario_id and solicitud.usuario_id == usuario_id:
                return True
            if mismo_solicitante(solicitud.solicitante, solicitante):
                return True
        return False

    async def create(self, solicitud: Solicitud) -> Solicitud:
        attributes = await self._atributos_de(solicitud.mascota_id)
        completa = solicitud.model_copy(
            update={
                "nombre": attributes["nombre"] if attributes else solicitud.nombre,
                "refugio": attributes["refugio"] if attributes else solicitud.refugio,
                "lugar": attributes["lugar"] if attributes else solicitud.lugar,
                "whatsapp": solicitud.whatsapp
                or (attributes.get("whatsapp") if attributes else None),
            }
        )
        self._solicitudes.append(copy.deepcopy(completa))
        return copy.deepcopy(completa)

    async def update(self, solicitud: Solicitud) -> Solicitud:
        for indice, actual in enumerate(self._solicitudes):
            if actual.id == solicitud.id:
                self._solicitudes[indice] = copy.deepcopy(solicitud)
                return copy.deepcopy(solicitud)
        raise LookupError("Solicitud no encontrada al actualizar")

    async def next_id(self) -> int:
        return max((s.id for s in self._solicitudes), default=0) + 1

    async def _atributos_de(self, mascota_id: int) -> dict[str, str] | None:
        mascota = await self._mascotas.find_by_id(mascota_id)
        if not mascota:
            return None
        refugio = await self._refugios.find_by_id(mascota.refugio_id)
        atributos = {
            "nombre": mascota.nombre,
            "refugio": mascota.refugio,
            "lugar": mascota.lugar,
        }
        if refugio and getattr(refugio, "whatsapp", None):
            atributos["whatsapp"] = f"https://wa.me/{refugio.whatsapp}"
        return atributos


class FavoritosMemoria(FavoritoRepo):
    def __init__(self) -> None:
        self._favoritos: list[Favorito] = []

    async def list_by_usuario(self, usuario_id: str) -> list[Favorito]:
        return copy.deepcopy([f for f in self._favoritos if f.usuario_id == usuario_id])

    async def find(self, usuario_id: str, mascota_id: int) -> Favorito | None:
        favorito = next(
            (
                f
                for f in self._favoritos
                if f.usuario_id == usuario_id and f.mascota_id == mascota_id
            ),
            None,
        )
        return copy.deepcopy(favorito) if favorito else None

    async def add(self, favorito: Favorito) -> Favorito:
        self._favoritos.append(copy.deepcopy(favorito))
        return copy.deepcopy(favorito)

    async def remove(self, usuario_id: str, mascota_id: int) -> bool:
        for indice, favorito in enumerate(self._favoritos):
            if favorito.usuario_id == usuario_id and favorito.mascota_id == mascota_id:
                self._favoritos.pop(indice)
                return True
        return False


class AlertasMemoria(AlertaRepo):
    def __init__(self) -> None:
        self._alertas: list[AlertaRescate] = []

    async def create(self, alerta: AlertaRescate) -> AlertaRescate:
        self._alertas.append(copy.deepcopy(alerta))
        return copy.deepcopy(alerta)

    async def list(self) -> list[AlertaRescate]:
        return copy.deepcopy(self._alertas)


class ContenidoMemoria(ContenidoRepo):
    def __init__(self, contenido: Contenido) -> None:
        self._contenido = copy.deepcopy(contenido)

    async def get(self) -> Contenido:
        return copy.deepcopy(self._contenido)


def crear_repositorios() -> Repositorios:
    """Fábrica actual: memoria. Cambiar por una implementación SQL en el futuro."""
    from types import SimpleNamespace

    seed = load_seed()
    usuarios = UsuariosMemoria()
    mascotas = MascotasMemoria(seed.mascotas)
    refugios = RefugiosMemoria(seed.refugios, mascotas)
    solicitudes = SolicitudesMemoria(seed.solicitudes, mascotas, refugios)

    return SimpleNamespace(
        usuarios=usuarios,
        mascotas=mascotas,
        refugios=refugios,
        solicitudes=solicitudes,
        favoritos=FavoritosMemoria(),
        alertas=AlertasMemoria(),
        contenido=ContenidoMemoria(seed.contenido),
    )


def nuevo_id() -> str:
    return str(uuid.uuid4())
