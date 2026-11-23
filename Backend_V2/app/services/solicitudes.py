"""Solicitudes de adopción: creación, etapas, citas, mensajes y seguimiento."""

from __future__ import annotations

from ..adapters.pdf import construir_pdf
from ..adapters.storage import LocalStorage
from ..domain import Cita, Foto, Mascota, Mensaje, Solicitud, Usuario, ahora_utc
from ..errors import ConflictError, ForbiddenError, NotFoundError
from ..repositories.memory import MemoryRepository
from ..schemas import AgendarCitaRequest, CrearSolicitudRequest


def _iniciales(nombre: str) -> str:
    partes = [parte for parte in nombre.split() if parte]
    return "".join(parte[0].upper() for parte in partes[:2]) or "LS"


def _mascota(repo: MemoryRepository, mascota_id: int) -> Mascota:
    mascota = repo.obtener_mascota(mascota_id)
    if mascota is None:
        raise NotFoundError("Mascota no encontrada.", {"mascotaId": mascota_id})
    return mascota


def puede_ver(repo: MemoryRepository, usuario: Usuario, solicitud: Solicitud) -> bool:
    if usuario.rol == "admin":
        return True
    if solicitud.usuario_id == usuario.id:
        return True
    if usuario.rol == "refugio":
        mascota = repo.obtener_mascota(solicitud.mascota_id)
        return mascota is not None and mascota.refugio_id == usuario.refugio_id
    return False


def _exigir_lectura(repo: MemoryRepository, usuario: Usuario, solicitud: Solicitud) -> None:
    if not puede_ver(repo, usuario, solicitud):
        raise ForbiddenError("No puedes acceder a esta solicitud.")


def _exigir_refugio(repo: MemoryRepository, usuario: Usuario, solicitud: Solicitud) -> None:
    if usuario.rol == "admin":
        return
    mascota = repo.obtener_mascota(solicitud.mascota_id)
    if usuario.rol != "refugio" or mascota is None or mascota.refugio_id != usuario.refugio_id:
        raise ForbiddenError("Solo el refugio de la mascota puede gestionar esta solicitud.")


def listar(
    repo: MemoryRepository,
    usuario: Usuario,
    *,
    estado: str = "todos",
    incluir_canceladas: bool = False,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Solicitud], int]:
    solicitudes = [s for s in repo.listar_solicitudes() if puede_ver(repo, usuario, s)]
    if estado != "todos":
        solicitudes = [s for s in solicitudes if s.estado == estado]
    elif not incluir_canceladas:
        solicitudes = [s for s in solicitudes if s.estado != "cancelada"]

    solicitudes.sort(key=lambda s: (-s.creada_en.timestamp(), -s.id))
    total = len(solicitudes)
    inicio = (page - 1) * limit
    return solicitudes[inicio : inicio + limit], total


def obtener(repo: MemoryRepository, usuario: Usuario, solicitud_id: int) -> Solicitud:
    solicitud = repo.obtener_solicitud(solicitud_id)
    if solicitud is None:
        raise NotFoundError("Solicitud no encontrada.", {"solicitudId": solicitud_id})
    _exigir_lectura(repo, usuario, solicitud)
    return solicitud


def crear(
    repo: MemoryRepository, usuario: Usuario, datos: CrearSolicitudRequest
) -> Solicitud:
    mascota = _mascota(repo, datos.mascota_id)
    if mascota.estado != "disponible":
        raise ConflictError(
            "MASCOTA_NO_DISPONIBLE",
            "Esta mascota no está disponible para adopción.",
            {"mascotaId": mascota.id, "estado": mascota.estado},
        )

    duplicada = next(
        (
            solicitud
            for solicitud in repo.listar_solicitudes()
            if solicitud.usuario_id == usuario.id
            and solicitud.mascota_id == mascota.id
            and solicitud.estado == "activa"
        ),
        None,
    )
    if duplicada is not None:
        raise ConflictError(
            "SOLICITUD_DUPLICADA",
            "Ya tienes una postulación activa para esta mascota.",
            {"solicitudId": duplicada.id, "codigo": duplicada.codigo},
        )

    solicitud_id = repo.siguiente_solicitud_id()
    ahora = ahora_utc()
    solicitud = Solicitud(
        id=solicitud_id,
        codigo=f"#SOL-HYO-{ahora.year}-{solicitud_id:03d}",
        usuario_id=usuario.id,
        mascota_id=mascota.id,
        estado="activa",
        etapa=2,
        creada_en=ahora,
        actualizada_en=ahora,
        foto_src=mascota.foto,
        foto_alt=mascota.alt,
        mensaje=Mensaje(
            iniciales=_iniciales(usuario.nombre),
            nombre=usuario.nombre,
            rol="Adoptante",
            texto=datos.mensaje,
        )
        if datos.mensaje
        else None,
    )
    return repo.crear_solicitud(solicitud)


def cancelar(
    repo: MemoryRepository, usuario: Usuario, solicitud_id: int, motivo: str
) -> Solicitud:
    solicitud = obtener(repo, usuario, solicitud_id)
    if usuario.rol != "admin" and solicitud.usuario_id != usuario.id:
        raise ForbiddenError("Solo el adoptante puede cancelar su postulación.")
    if solicitud.estado != "activa":
        raise ConflictError(
            "SOLICITUD_NO_ACTIVA",
            "Solo se puede cancelar una postulación activa.",
            {"estado": solicitud.estado},
        )
    solicitud.estado = "cancelada"
    solicitud.motivo_cancelacion = motivo
    solicitud.actualizada_en = ahora_utc()
    return repo.guardar_solicitud(solicitud)


def cambiar_etapa(
    repo: MemoryRepository,
    usuario: Usuario,
    solicitud_id: int,
    etapa: int,
    nota: str | None = None,
) -> Solicitud:
    solicitud = obtener(repo, usuario, solicitud_id)
    _exigir_refugio(repo, usuario, solicitud)
    if solicitud.estado == "cancelada":
        raise ConflictError("SOLICITUD_CANCELADA", "La postulación fue cancelada.")

    solicitud.etapa = etapa
    solicitud.actualizada_en = ahora_utc()
    solicitud.estado = "completada" if etapa >= 5 else "activa"

    if nota:
        solicitud.mensaje = Mensaje(
            iniciales=_iniciales(usuario.nombre),
            nombre=usuario.nombre,
            rol="Coordinación del refugio",
            texto=nota,
        )

    mascota = _mascota(repo, solicitud.mascota_id)
    if etapa >= 5:
        mascota.estado = "adoptada"
        repo.guardar_mascota(mascota)

    return repo.guardar_solicitud(solicitud)


def agendar_cita(
    repo: MemoryRepository, usuario: Usuario, solicitud_id: int, datos: AgendarCitaRequest
) -> Solicitud:
    solicitud = obtener(repo, usuario, solicitud_id)
    _exigir_refugio(repo, usuario, solicitud)
    if solicitud.estado == "cancelada":
        raise ConflictError("SOLICITUD_CANCELADA", "La postulación fue cancelada.")

    solicitud.cita = Cita(
        fecha=datos.fecha,
        direccion=datos.direccion,
        coordinadora=datos.coordinadora,
    )
    solicitud.etapa = max(3, solicitud.etapa)
    solicitud.actualizada_en = ahora_utc()
    return repo.guardar_solicitud(solicitud)


def enviar_mensaje(
    repo: MemoryRepository, usuario: Usuario, solicitud_id: int, texto: str
) -> Solicitud:
    solicitud = obtener(repo, usuario, solicitud_id)
    if solicitud.estado == "cancelada":
        raise ConflictError("SOLICITUD_CANCELADA", "La postulación fue cancelada.")

    rol = "Coordinación del refugio" if usuario.rol in {"refugio", "admin"} else "Adoptante"
    solicitud.mensaje = Mensaje(
        iniciales=_iniciales(usuario.nombre),
        nombre=usuario.nombre,
        rol=rol,
        texto=texto,
    )
    solicitud.actualizada_en = ahora_utc()
    return repo.guardar_solicitud(solicitud)


def registrar_seguimiento(
    repo: MemoryRepository,
    usuario: Usuario,
    solicitud_id: int,
    storage: LocalStorage,
    *,
    nombre_archivo: str | None,
    content_type: str | None,
    contenido: bytes,
    nota: str | None = None,
) -> Solicitud:
    solicitud = obtener(repo, usuario, solicitud_id)
    if solicitud.estado == "cancelada":
        raise ConflictError("SOLICITUD_CANCELADA", "La postulación fue cancelada.")

    url = storage.guardar_imagen(nombre_archivo, content_type, contenido)
    mascota = _mascota(repo, solicitud.mascota_id)
    solicitud.seguimiento.append(
        Foto(src=url, alt=nota or f"Seguimiento fotográfico de {mascota.nombre}")
    )
    solicitud.actualizada_en = ahora_utc()
    return repo.guardar_solicitud(solicitud)


def documentos(
    repo: MemoryRepository, usuario: Usuario, solicitud_id: int
) -> tuple[bytes, str]:
    solicitud = obtener(repo, usuario, solicitud_id)
    mascota = _mascota(repo, solicitud.mascota_id)
    refugio = repo.obtener_refugio(mascota.refugio_id)
    adoptante = repo.obtener_usuario(solicitud.usuario_id)

    lineas = [
        "Plataforma de adopción responsable — Huancayo, Valle del Mantaro",
        "",
        f"Código de postulación: {solicitud.codigo}",
        f"Mascota: {mascota.nombre} ({mascota.ficha_id})",
        f"Refugio: {refugio.nombre if refugio else mascota.refugio_id}",
        f"Adoptante: {adoptante.nombre if adoptante else solicitud.usuario_id}",
        f"Etapa actual: {solicitud.etapa} de 5",
        f"Estado: {solicitud.estado}",
        f"Fecha de envío: {solicitud.creada_en.date().isoformat()}",
    ]
    if solicitud.motivo_cancelacion:
        lineas.append(f"Motivo de cancelación: {solicitud.motivo_cancelacion}")
    lineas += [
        "",
        "Este documento es una constancia digital del proceso de adopción.",
        "LeonS no cobra por la adopción de ninguna mascota.",
    ]
    nombre = f"constancia-{solicitud.codigo.replace('#', '').replace('/', '-')}.pdf"
    return construir_pdf("LeonS — Constancia de postulación", lineas), nombre
