"""Repositorio en memoria para las fases 0–3.

No conoce HTTP. La Fase 6 añade `sqlserver.py` con el mismo contrato.
"""

from __future__ import annotations

from ..data.loader import SeedData
from ..domain import (
    AlertaRescate,
    Contenido,
    DetalleMascota,
    Favorito,
    Mascota,
    Refugio,
    Solicitud,
    Usuario,
)


class MemoryRepository:
    def __init__(self, seed: SeedData) -> None:
        self.refugios: dict[str, Refugio] = {refugio.id: refugio for refugio in seed.refugios}
        self.mascotas: list[Mascota] = list(seed.mascotas)
        self.detalles: dict[int, DetalleMascota] = dict(seed.detalles)
        self.contenido: Contenido = seed.contenido
        self.usuarios: list[Usuario] = list(seed.usuarios)
        self.solicitudes: list[Solicitud] = list(seed.solicitudes)
        self.favoritos: list[Favorito] = []
        self.alertas: list[AlertaRescate] = []

    # -- Catálogo ---------------------------------------------------------
    def listar_mascotas(self) -> list[Mascota]:
        return list(self.mascotas)

    def obtener_mascota(self, mascota_id: int) -> Mascota | None:
        return next((m for m in self.mascotas if m.id == mascota_id), None)

    def siguiente_mascota_id(self) -> int:
        return max((m.id for m in self.mascotas), default=0) + 1

    def guardar_mascota(self, mascota: Mascota) -> Mascota:
        for indice, actual in enumerate(self.mascotas):
            if actual.id == mascota.id:
                self.mascotas[indice] = mascota
                return mascota
        self.mascotas.append(mascota)
        return mascota

    def eliminar_mascota(self, mascota_id: int) -> None:
        self.mascotas = [m for m in self.mascotas if m.id != mascota_id]
        self.favoritos = [f for f in self.favoritos if f.mascota_id != mascota_id]

    # -- Refugios ---------------------------------------------------------
    def listar_refugios(self) -> list[Refugio]:
        return list(self.refugios.values())

    def obtener_refugio(self, refugio_id: str) -> Refugio | None:
        return self.refugios.get(refugio_id)

    # -- Contenido --------------------------------------------------------
    def obtener_contenido(self) -> Contenido:
        return self.contenido

    def obtener_detalle(self, mascota_id: int) -> DetalleMascota | None:
        return self.detalles.get(mascota_id)

    # -- Usuarios ---------------------------------------------------------
    def obtener_usuario(self, usuario_id: int) -> Usuario | None:
        return next((u for u in self.usuarios if u.id == usuario_id), None)

    def buscar_usuario_por_email(self, email: str) -> Usuario | None:
        email = email.strip().lower()
        return next((u for u in self.usuarios if u.email.lower() == email), None)

    def buscar_usuario_por_dni(self, dni: str) -> Usuario | None:
        return next((u for u in self.usuarios if u.dni == dni), None)

    def siguiente_usuario_id(self) -> int:
        return max((u.id for u in self.usuarios), default=0) + 1

    def crear_usuario(self, usuario: Usuario) -> Usuario:
        self.usuarios.append(usuario)
        return usuario

    # -- Solicitudes ------------------------------------------------------
    def listar_solicitudes(self) -> list[Solicitud]:
        return list(self.solicitudes)

    def obtener_solicitud(self, solicitud_id: int) -> Solicitud | None:
        return next((s for s in self.solicitudes if s.id == solicitud_id), None)

    def siguiente_solicitud_id(self) -> int:
        return max((s.id for s in self.solicitudes), default=0) + 1

    def crear_solicitud(self, solicitud: Solicitud) -> Solicitud:
        self.solicitudes.append(solicitud)
        return solicitud

    def guardar_solicitud(self, solicitud: Solicitud) -> Solicitud:
        for indice, actual in enumerate(self.solicitudes):
            if actual.id == solicitud.id:
                self.solicitudes[indice] = solicitud
                return solicitud
        self.solicitudes.append(solicitud)
        return solicitud

    # -- Favoritos --------------------------------------------------------
    def listar_favoritos(self, usuario_id: int) -> list[Favorito]:
        return [f for f in self.favoritos if f.usuario_id == usuario_id]

    def crear_favorito(self, favorito: Favorito) -> Favorito:
        self.favoritos.append(favorito)
        return favorito

    def eliminar_favorito(self, usuario_id: int, mascota_id: int) -> bool:
        antes = len(self.favoritos)
        self.favoritos = [
            f
            for f in self.favoritos
            if not (f.usuario_id == usuario_id and f.mascota_id == mascota_id)
        ]
        return len(self.favoritos) != antes

    # -- Alertas ----------------------------------------------------------
    def listar_alertas(self) -> list[AlertaRescate]:
        return list(self.alertas)

    def siguiente_alerta_id(self) -> int:
        return max((a.id for a in self.alertas), default=0) + 1

    def crear_alerta(self, alerta: AlertaRescate) -> AlertaRescate:
        self.alertas.append(alerta)
        return alerta
