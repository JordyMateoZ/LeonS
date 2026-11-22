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
    FiltroMascotas,
    Mascota,
    Refugio,
    Solicitud,
    Usuario,
    codigo_solicitud,
    ficha_predeterminada,
)
from ..errors import ConflictError, ForbiddenError, NotFoundError


def _siguiente_id(entidades: list) -> int:
    return max((entidad.id for entidad in entidades), default=0) + 1


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

    def buscar_mascotas(self, filtro: FiltroMascotas) -> tuple[list[Mascota], int]:
        texto = (filtro.q or "").strip().lower()

        def incluir(mascota: Mascota) -> bool:
            if filtro.estado != "todos" and mascota.estado != filtro.estado:
                return False
            if texto:
                campos = (mascota.nombre, mascota.raza, mascota.etiqueta, mascota.lugar)
                if not any(texto in campo.lower() for campo in campos):
                    return False
            if filtro.especie and mascota.especie != filtro.especie:
                return False
            if filtro.distrito and mascota.distrito.lower() != filtro.distrito.lower():
                return False
            if filtro.tamano and mascota.tamano != filtro.tamano:
                return False
            if filtro.sexo and mascota.sexo != filtro.sexo:
                return False
            if filtro.edad and not _coincide_edad(mascota.edad_anios, filtro.edad):
                return False
            if filtro.refugio_id and mascota.refugio_id != filtro.refugio_id:
                return False
            if filtro.solo_esterilizados and not mascota.esterilizado:
                return False
            if filtro.solo_vacunados and not mascota.vacunado:
                return False
            if filtro.solo_urgentes and not mascota.urgente:
                return False
            return True

        filtradas = [mascota for mascota in self.mascotas if incluir(mascota)]

        if filtro.orden == "urgent":
            filtradas.sort(key=lambda m: (not m.urgente, m.id))
        elif filtro.orden == "youngest":
            filtradas.sort(key=lambda m: (m.edad_anios, m.id))
        elif filtro.orden == "oldest":
            filtradas.sort(key=lambda m: (-m.edad_anios, m.id))
        else:
            filtradas.sort(key=lambda m: -m.id)

        total = len(filtradas)
        inicio = (filtro.page - 1) * filtro.limit
        return filtradas[inicio : inicio + filtro.limit], total

    def obtener_mascota(self, mascota_id: int) -> Mascota | None:
        return next((m for m in self.mascotas if m.id == mascota_id), None)

    def crear_mascota(self, mascota: Mascota) -> Mascota:
        mascota.id = _siguiente_id(self.mascotas)
        mascota.ficha_id = ficha_predeterminada(mascota.id)
        self.mascotas.append(mascota)
        return mascota

    def actualizar_mascota(self, mascota: Mascota) -> Mascota:
        for indice, actual in enumerate(self.mascotas):
            if actual.id == mascota.id:
                mascota.ficha_id = ficha_predeterminada(mascota.id)
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

    def resumen_impacto(self) -> dict[str, object]:
        disponibles = [m for m in self.mascotas if m.estado == "disponible"]
        por_distrito: dict[str, int] = {}
        for refugio in self.refugios.values():
            por_distrito[refugio.distrito] = por_distrito.get(refugio.distrito, 0) + refugio.adoptadas
        return {
            "total_mascotas": len(disponibles),
            "total_perros": sum(1 for m in disponibles if m.especie == "perro"),
            "total_gatos": sum(1 for m in disponibles if m.especie == "gato"),
            "total_refugios": len(self.refugios),
            "total_adoptadas": sum(r.adoptadas for r in self.refugios.values()),
            "total_en_acogida": sum(r.en_acogida for r in self.refugios.values()),
            "total_distritos": len({r.distrito for r in self.refugios.values()}),
            "adoptadas_por_distrito": dict(sorted(por_distrito.items())),
        }

    def listar_mascotas_por_ids(self, ids: list[int]) -> list[Mascota]:
        por_id = {m.id: m for m in self.mascotas}
        return [por_id[mascota_id] for mascota_id in ids if mascota_id in por_id]

    def listar_mascotas_de_refugio(self, refugio_id: str, *, estado: str = "todos") -> list[Mascota]:
        resultado = [m for m in self.mascotas if m.refugio_id == refugio_id]
        if estado != "todos":
            resultado = [m for m in resultado if m.estado == estado]
        return sorted(resultado, key=lambda m: m.id)

    def estadisticas_mascotas(self) -> dict[str, object]:
        total_registradas = len(self.mascotas)
        disponibles = [m for m in self.mascotas if m.estado == "disponible"]
        total = len(disponibles)
        por_especie: dict[str, int] = {}
        for m in self.mascotas:
            por_especie[m.especie] = por_especie.get(m.especie, 0) + 1
        por_especie = dict(sorted(por_especie.items()))
        # por_distrito: contar mascotas por valor de mascota.distrito (como el old mapper.stats_mascotas)
        por_distrito: dict[str, int] = {}
        for m in self.mascotas:
            d = m.distrito or ""
            por_distrito[d] = por_distrito.get(d, 0) + 1
        por_distrito = dict(sorted(por_distrito.items()))
        edad_promedio = round(
            sum(m.edad_anios for m in disponibles) / total, 2
        ) if total else 0.0
        por_tamano: dict[str, int] = {}
        for m in self.mascotas:
            por_tamano[m.tamano] = por_tamano.get(m.tamano, 0) + 1
        por_tamano = dict(sorted(por_tamano.items()))
        return {
            "total": total,
            "total_registradas": total_registradas,
            "disponibles": total,
            "adoptadas": sum(1 for m in self.mascotas if m.estado == "adoptada"),
            "en_acogida": sum(1 for m in self.mascotas if m.estado == "en_acogida"),
            "urgentes": sum(1 for m in disponibles if m.urgente),
            "total_refugios": len(self.refugios),
            "edad_promedio": edad_promedio,
            "por_especie": por_especie,
            "por_distrito": por_distrito,
            "por_tamano": por_tamano,
        }

    # -- Usuarios ---------------------------------------------------------
    def obtener_usuario(self, usuario_id: int) -> Usuario | None:
        return next((u for u in self.usuarios if u.id == usuario_id), None)

    def buscar_usuario_por_email(self, email: str) -> Usuario | None:
        email = email.strip().lower()
        return next((u for u in self.usuarios if u.email.lower() == email), None)

    def buscar_usuario_por_dni(self, dni: str) -> Usuario | None:
        return next((u for u in self.usuarios if u.dni == dni), None)

    def listar_usuarios(self) -> list[Usuario]:
        return list(self.usuarios)

    def crear_usuario(self, usuario: Usuario) -> Usuario:
        usuario.id = _siguiente_id(self.usuarios)
        self.usuarios.append(usuario)
        return usuario

    # -- Solicitudes ------------------------------------------------------
    def listar_solicitudes(self) -> list[Solicitud]:
        return list(self.solicitudes)

    def buscar_solicitudes(
        self,
        *,
        usuario_id: int,
        rol: str,
        refugio_id: str | None,
        estado: str = "todos",
        incluir_canceladas: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Solicitud], int]:
        mascotas = {mascota.id: mascota for mascota in self.mascotas}

        def visible(solicitud: Solicitud) -> bool:
            if rol == "admin" or solicitud.usuario_id == usuario_id:
                return True
            if rol != "refugio":
                return False
            mascota = mascotas.get(solicitud.mascota_id)
            return mascota is not None and mascota.refugio_id == refugio_id

        solicitudes = [s for s in self.solicitudes if visible(s)]
        if estado != "todos":
            solicitudes = [s for s in solicitudes if s.estado == estado]
        elif not incluir_canceladas:
            solicitudes = [s for s in solicitudes if s.estado != "cancelada"]

        solicitudes.sort(key=lambda s: (-s.creada_en.timestamp(), -s.id))
        total = len(solicitudes)
        inicio = (page - 1) * limit
        return solicitudes[inicio : inicio + limit], total

    def obtener_solicitud(self, solicitud_id: int) -> Solicitud | None:
        return next((s for s in self.solicitudes if s.id == solicitud_id), None)

    def crear_solicitud(self, solicitud: Solicitud) -> Solicitud:
        solicitud.id = _siguiente_id(self.solicitudes)
        solicitud.codigo = codigo_solicitud(solicitud.id, solicitud.creada_en.year)
        self.solicitudes.append(solicitud)
        return solicitud

    def actualizar_solicitud(self, solicitud: Solicitud) -> Solicitud:
        for indice, actual in enumerate(self.solicitudes):
            if actual.id == solicitud.id:
                self.solicitudes[indice] = solicitud
                return solicitud
        self.solicitudes.append(solicitud)
        return solicitud

    def finalizar_solicitud(self, solicitud: Solicitud, usuario: Usuario) -> Solicitud:
        """Paridad en memoria de la finalización atómica de A-15."""
        actual = self.obtener_solicitud(solicitud.id)
        if actual is None:
            raise NotFoundError(
                "Solicitud no encontrada.", {"solicitudId": solicitud.id}
            )
        mascota = next((m for m in self.mascotas if m.id == actual.mascota_id), None)
        if mascota is None:
            raise NotFoundError(
                "Mascota no encontrada.", {"mascotaId": actual.mascota_id}
            )

        if usuario.rol not in {"refugio", "admin"}:
            raise ForbiddenError(
                "Solo el refugio o un administrador puede finalizar una adopción."
            )
        if usuario.rol == "refugio" and usuario.refugio_id != mascota.refugio_id:
            raise ForbiddenError(
                "Solo el refugio de la mascota puede finalizar esta adopción."
            )

        if actual.estado == "cancelada":
            raise ConflictError(
                "SOLICITUD_CANCELADA", "La postulación fue cancelada."
            )

        otras_activas = [
            item
            for item in self.solicitudes
            if item.mascota_id == actual.mascota_id
            and item.id != actual.id
            and item.estado == "activa"
        ]
        if otras_activas:
            raise ConflictError(
                "ADOPCION_EN_CURSO",
                "Existen otras postulaciones activas para esta mascota; "
                "resuélvelas antes de finalizar la adopción.",
                {
                    "mascotaId": actual.mascota_id,
                    "solicitudesActivas": len(otras_activas),
                },
            )

        if actual.estado == "completada" and actual.etapa >= 5:
            if mascota.estado != "adoptada":
                raise ConflictError(
                    "SOLICITUD_INCONSISTENTE",
                    "La solicitud está completada pero la mascota no está adoptada.",
                    {"mascotaId": actual.mascota_id},
                )
            return actual

        if actual.etapa >= 5:
            raise ConflictError(
                "SOLICITUD_INCONSISTENTE",
                "La solicitud está en etapa final pero no está completada.",
                {"solicitudId": actual.id},
            )

        if mascota.estado != "disponible":
            raise ConflictError(
                "MASCOTA_NO_DISPONIBLE",
                "Esta mascota ya no está disponible para adopción.",
                {"mascotaId": mascota.id, "estado": mascota.estado},
            )

        mascota.estado = "adoptada"
        actual.etapa = 5
        actual.estado = "completada"
        actual.actualizada_en = solicitud.actualizada_en or actual.actualizada_en
        if solicitud.mensaje is not None:
            actual.mensaje = solicitud.mensaje
        return actual

    # -- Favoritos --------------------------------------------------------
    def listar_favoritos(self, usuario_id: int) -> list[Favorito]:
        return [f for f in self.favoritos if f.usuario_id == usuario_id]

    def listar_favoritos_mascotas(self, usuario_id: int) -> list[Mascota]:
        ids = {f.mascota_id for f in self.favoritos if f.usuario_id == usuario_id}
        return [m for m in self.mascotas if m.id in ids]

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

    def crear_alerta(self, alerta: AlertaRescate) -> AlertaRescate:
        alerta.id = _siguiente_id(self.alertas)
        self.alertas.append(alerta)
        return alerta
