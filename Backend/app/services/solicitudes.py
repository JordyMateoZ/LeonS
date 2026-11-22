"""Solicitudes de adopción: creación, etapas, citas, mensajes y seguimiento."""

from __future__ import annotations

from ..adapters.pdf import construir_pdf
from ..adapters.storage import LocalStorage
from ..domain import (
    Cita,
    Foto,
    Mascota,
    Mensaje,
    Repositorio,
    Solicitud,
    Usuario,
    ahora_utc,
)
from ..errors import ConflictError, ForbiddenError, NotFoundError
from ..schemas import AgendarCitaRequest, CrearSolicitudRequest


def _iniciales(nombre: str) -> str:
    partes = [parte for parte in nombre.split() if parte]
    return "".join(parte[0].upper() for parte in partes[:2]) or "LS"


def _mensaje_autenticado(usuario: Usuario, texto: str) -> Mensaje:
    """Construye un mensaje con la identidad real del usuario autenticado."""
    rol = "Adoptante" if usuario.rol == "adoptante" else "Coordinación del refugio"
    return Mensaje(
        iniciales=_iniciales(usuario.nombre),
        nombre=usuario.nombre,
        rol=rol,
        texto=texto,
        autor_id=usuario.id,
    )


def _mascota(repo: Repositorio, mascota_id: int) -> Mascota:
    mascota = repo.obtener_mascota(mascota_id)
    if mascota is None:
        raise NotFoundError("Mascota no encontrada.", {"mascotaId": mascota_id})
    return mascota


def puede_ver(repo: Repositorio, usuario: Usuario, solicitud: Solicitud) -> bool:
    if usuario.rol == "admin":
        return True
    if solicitud.usuario_id == usuario.id:
        return True
    if usuario.rol == "refugio":
        mascota = repo.obtener_mascota(solicitud.mascota_id)
        return mascota is not None and mascota.refugio_id == usuario.refugio_id
    return False


def _exigir_lectura(repo: Repositorio, usuario: Usuario, solicitud: Solicitud) -> None:
    if not puede_ver(repo, usuario, solicitud):
        raise ForbiddenError("No puedes acceder a esta solicitud.")


def _exigir_refugio(repo: Repositorio, usuario: Usuario, solicitud: Solicitud) -> None:
    if usuario.rol == "admin":
        return
    mascota = repo.obtener_mascota(solicitud.mascota_id)
    if usuario.rol != "refugio" or mascota is None or mascota.refugio_id != usuario.refugio_id:
        raise ForbiddenError("Solo el refugio de la mascota puede gestionar esta solicitud.")


def listar(
    repo: Repositorio,
    usuario: Usuario,
    *,
    estado: str = "todos",
    incluir_canceladas: bool = False,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Solicitud], int]:
    """Filtrado, orden y paginación delegados al repositorio (Fase 4.2, P6).

    El repositorio aplica la misma regla de visibilidad que `puede_ver`, pero
    en una sola consulta: el admin ve todo, cada usuario ve las suyas y un
    refugio ve las solicitudes de sus mascotas.
    """
    return repo.buscar_solicitudes(
        usuario_id=usuario.id,
        rol=usuario.rol,
        refugio_id=usuario.refugio_id,
        estado=estado,
        incluir_canceladas=incluir_canceladas,
        page=page,
        limit=limit,
    )


def obtener(repo: Repositorio, usuario: Usuario, solicitud_id: int) -> Solicitud:
    solicitud = repo.obtener_solicitud(solicitud_id)
    if solicitud is None:
        raise NotFoundError("Solicitud no encontrada.", {"solicitudId": solicitud_id})
    _exigir_lectura(repo, usuario, solicitud)
    return solicitud


def crear(
    repo: Repositorio, usuario: Usuario, datos: CrearSolicitudRequest
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

    ahora = ahora_utc()
    solicitud = Solicitud(
        id=0,
        codigo="",
        usuario_id=usuario.id,
        mascota_id=mascota.id,
        estado="activa",
        etapa=2,
        creada_en=ahora,
        actualizada_en=ahora,
        foto_src=mascota.foto,
        foto_alt=mascota.alt,
        mensaje=_mensaje_autenticado(usuario, datos.mensaje)
        if datos.mensaje
        else None,
    )
    return repo.crear_solicitud(solicitud)


def cancelar(
    repo: Repositorio, usuario: Usuario, solicitud_id: int, motivo: str
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
    return repo.actualizar_solicitud(solicitud)


def cambiar_etapa(
    repo: Repositorio,
    usuario: Usuario,
    solicitud_id: int,
    etapa: int,
    nota: str | None = None,
) -> Solicitud:
    # A-15: la etapa final delega en una operación atómica del repositorio.
    # El servicio no carga la mascota ni escribe por separado: el repositorio
    # revalida permisos, estados y ausencia de otras postulaciones activas.
    if etapa >= 5:
        # Comando mínimo: `id`, `actualizada_en` y, si hay nota, el mensaje.
        # La fila real y el autor se validan dentro de la única sesión del
        # repositorio; aquí no se abre una lectura previa ni se carga la mascota.
        ahora = ahora_utc()
        solicitud = Solicitud(
            id=solicitud_id,
            codigo="",
            usuario_id=0,
            mascota_id=0,
            estado="activa",
            etapa=2,
            creada_en=ahora,
            actualizada_en=ahora,
            mensaje=_mensaje_autenticado(usuario, nota) if nota else None,
        )
        return repo.finalizar_solicitud(solicitud, usuario)

    solicitud = obtener(repo, usuario, solicitud_id)
    _exigir_refugio(repo, usuario, solicitud)
    if solicitud.estado == "cancelada":
        raise ConflictError("SOLICITUD_CANCELADA", "La postulación fue cancelada.")

    solicitud.etapa = etapa
    solicitud.actualizada_en = ahora_utc()
    solicitud.estado = "activa"

    if nota:
        solicitud.mensaje = _mensaje_autenticado(usuario, nota)

    return repo.actualizar_solicitud(solicitud)


def agendar_cita(
    repo: Repositorio, usuario: Usuario, solicitud_id: int, datos: AgendarCitaRequest
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
    return repo.actualizar_solicitud(solicitud)


def enviar_mensaje(
    repo: Repositorio, usuario: Usuario, solicitud_id: int, texto: str
) -> Solicitud:
    solicitud = obtener(repo, usuario, solicitud_id)
    if solicitud.estado == "cancelada":
        raise ConflictError("SOLICITUD_CANCELADA", "La postulación fue cancelada.")

    solicitud.mensaje = _mensaje_autenticado(usuario, texto)
    solicitud.actualizada_en = ahora_utc()
    return repo.actualizar_solicitud(solicitud)


def registrar_seguimiento(
    repo: Repositorio,
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
    return repo.actualizar_solicitud(solicitud)


def documentos(
    repo: Repositorio, usuario: Usuario, solicitud_id: int
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
