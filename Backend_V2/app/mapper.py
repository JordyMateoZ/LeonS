"""Dominio → DTO.

Aquí viven los campos de presentación (badge, chips, textos relativos y
etapas). No se guardan en la base de datos: se calculan en cada respuesta.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .domain import (
    AlertaRescate,
    Cierre,
    Contenido,
    DetalleMascota,
    Foto,
    Mascota,
    Refugio,
    Rasgo,
    Solicitud,
    Usuario,
)
from .schemas import (
    AlertaOut,
    CierreOut,
    CitaDetalleOut,
    CitaOut,
    ContenidoOut,
    CuidadoOut,
    DetalleMascotaOut,
    EtapaOut,
    FaqOut,
    FotoOut,
    ImpactoOut,
    MascotaOut,
    MascotaStats,
    MensajeSolicitudOut,
    PageMascotas,
    PageSolicitudes,
    PasoOut,
    PreguntaOut,
    RasgoOut,
    RefugioDetalleOut,
    RefugioOut,
    RequisitoOut,
    ResumenRefugioOut,
    SaludItemOut,
    SeguimientoFotoOut,
    SolicitudOut,
    UsuarioOut,
)

MESES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

HEADER_SOLICITUD_ACTIVA = (
    "from-surface-container-lowest via-surface-container-low/40 to-surface-container-lowest"
)
HEADER_SOLICITUD_CERRADA = (
    "from-secondary-fixed/20 via-surface-container-lowest to-surface-container-lowest"
)

BADGE_PERRO = "text-primary bg-primary-fixed"
BADGE_GATO = "text-secondary bg-secondary-fixed"
ETQ_SECUNDARIA = "bg-secondary text-on-secondary"

RASGO_BASE = "inline-flex items-center gap-1.5 font-label-md text-label-md px-4 py-2.5 rounded-full "

RASGOS_POR_ESPECIE: dict[str, list[Rasgo]] = {
    "perro": [
        Rasgo("toys", "Juguetón y cariñoso", RASGO_BASE + "bg-primary-fixed text-on-primary-fixed shadow-sm"),
        Rasgo("chair", "Tranquilo en interiores", RASGO_BASE + "bg-surface-container text-on-surface", "text-secondary"),
        Rasgo("family_restroom", "Excelente con niños", RASGO_BASE + "bg-secondary-container text-on-secondary-container shadow-sm"),
        Rasgo("group", "Sociable con otros perros", RASGO_BASE + "bg-surface-container text-on-surface", "text-primary"),
        Rasgo("nordic_walking", "Acostumbrado a paseos con correa", RASGO_BASE + "bg-surface-container text-on-surface", "text-secondary"),
    ],
    "gato": [
        Rasgo("favorite", "Cariñoso y ronroneador", RASGO_BASE + "bg-primary-fixed text-on-primary-fixed shadow-sm"),
        Rasgo("chair", "Disfruta espacios tranquilos", RASGO_BASE + "bg-surface-container text-on-surface", "text-secondary"),
        Rasgo("group", "Sociable con otros gatos", RASGO_BASE + "bg-surface-container text-on-surface", "text-primary"),
        Rasgo("cleaning_services", "Limpio con su arenero", RASGO_BASE + "bg-secondary-container text-on-secondary-container shadow-sm"),
        Rasgo("apartment", "Se adapta a departamento", RASGO_BASE + "bg-surface-container text-on-surface", "text-secondary"),
    ],
}

ETAPAS_TITULOS = [
    "Enviada",
    "Revisión de Ficha",
    "Entrevista / Visita",
    "Aprobación",
    "Adopción Feliz",
]

ICONOS_SALUD = {
    "esteriliz": "check",
    "vacun": "vaccines",
    "desparasit": "verified",
    "test felino": "science",
    "compromiso": "schedule",
}

TEXTOS_SALUD = {
    "esteriliz": "Procedimiento certificado y recuperación completada.",
    "vacun": "Esquema de vacunas vigente y carnet listo para entrega.",
    "desparasit": "Protección interna y externa al día.",
    "test felino": "Resultado negativo en las pruebas felinas realizadas.",
    "compromiso": "Se entrega con compromiso formal de esterilización gratuita.",
}


# ---------------------------------------------------------------------------
# Campos de presentación
# ---------------------------------------------------------------------------


def genero_texto(especie: str, sexo: str) -> str:
    if especie == "gato":
        return "Gata" if sexo == "Hembra" else "Gato"
    return "Perra" if sexo == "Hembra" else "Perro"


def badge_especie(especie: str) -> str:
    return BADGE_GATO if especie == "gato" else BADGE_PERRO


def edad_texto(anios: float) -> str:
    if anios < 1:
        meses = max(1, round(anios * 12))
        return f"{meses} meses" if meses != 1 else "1 mes"
    if float(anios).is_integer():
        valor = int(anios)
        return "1 año" if valor == 1 else f"{valor} años"
    return f"{anios:g} años"


def tamano_texto(tamano: str, peso_kg: float, sexo: str) -> str:
    adjetivo = tamano
    if sexo == "Hembra" and tamano in {"Pequeño", "Mediano"}:
        adjetivo = f"{tamano[:-1]}a"
    return f"{adjetivo} • {peso_kg:g} kg"


def actualizado_texto(dias: int) -> str:
    if dias <= 0:
        return "hoy"
    if dias == 1:
        return "hace 1 día"
    if dias < 30:
        return f"hace {dias} días"
    meses = max(1, round(dias / 30))
    return "hace 1 mes" if meses == 1 else f"hace {meses} meses"


def _fecha_larga(momento: datetime) -> str:
    return f"{momento.day} de {MESES[momento.month - 1]}, {momento.year}"


def _fecha_corta(momento: datetime) -> str:
    return f"{momento.day} {MESES_CORTOS[momento.month - 1]}"


def _sumar_meses(momento: datetime, meses: int) -> datetime:
    total = momento.month - 1 + meses
    anio = momento.year + total // 12
    mes = total % 12 + 1
    return momento.replace(year=anio, month=mes, day=1)


# ---------------------------------------------------------------------------
# Mascotas y refugios
# ---------------------------------------------------------------------------


def mascota_out(mascota: Mascota, refugios: dict[str, Refugio]) -> MascotaOut:
    refugio = refugios.get(mascota.refugio_id)
    galeria = mascota.galeria or [Foto(mascota.foto, mascota.alt)]
    rasgos = mascota.rasgos or RASGOS_POR_ESPECIE.get(mascota.especie, [])
    return MascotaOut(
        id=mascota.id,
        nombre=mascota.nombre,
        nombre_corto=mascota.nombre_corto or mascota.nombre,
        especie=mascota.especie,
        sexo=mascota.sexo,
        genero_texto=genero_texto(mascota.especie, mascota.sexo),
        badge_clase=badge_especie(mascota.especie),
        raza=mascota.raza,
        edad_texto=edad_texto(mascota.edad_anios),
        edad_anios=mascota.edad_anios,
        tamano=mascota.tamano,
        tamano_texto=tamano_texto(mascota.tamano, mascota.peso_kg, mascota.sexo),
        distrito=mascota.distrito,
        lugar=mascota.lugar,
        foto=mascota.foto,
        alt=mascota.alt,
        descripcion=mascota.descripcion,
        etiqueta=mascota.etiqueta,
        etiqueta_icono=mascota.etiqueta_icono,
        etiqueta_clase=mascota.etiqueta_clase,
        salud=[SaludItemOut(texto=item.texto, ok=item.ok) for item in mascota.salud],
        esterilizado=mascota.esterilizado,
        vacunado=mascota.vacunado,
        urgente=mascota.urgente,
        refugio=refugio.nombre if refugio else mascota.refugio_id,
        refugio_id=mascota.refugio_id,
        energia=mascota.energia,
        ficha_id=mascota.ficha_id,
        actualizado=actualizado_texto(mascota.actualizado_dias),
        estado=mascota.estado,
        galeria=[FotoOut(src=foto.src, alt=foto.alt) for foto in galeria],
        rasgos=[
            RasgoOut(
                icono=rasgo.icono,
                texto=rasgo.texto,
                clase=rasgo.clase,
                icono_clase=rasgo.icono_clase,
            )
            for rasgo in rasgos
        ],
    )


def refugio_out(refugio: Refugio) -> RefugioOut:
    return RefugioOut(
        id=refugio.id,
        nombre=refugio.nombre,
        distrito=refugio.distrito,
        desde=refugio.desde,
        descripcion=refugio.descripcion,
        contacto=refugio.contacto,
        cargo=refugio.cargo,
        telefono=refugio.telefono,
        whatsapp=refugio.whatsapp,
        logo=refugio.logo,
        adoptadas=refugio.adoptadas,
        en_acogida=refugio.en_acogida,
        verificado=refugio.verificado,
        especies=refugio.especies,
        direccion=refugio.direccion,
        tipo=refugio.tipo,
    )


def resumen_refugio(refugio: Refugio, mascotas: Iterable[Mascota]) -> ResumenRefugioOut:
    propias = [m for m in mascotas if m.refugio_id == refugio.id]
    return ResumenRefugioOut(
        total=len(propias),
        disponibles=sum(1 for m in propias if m.estado == "disponible"),
        adoptadas=sum(1 for m in propias if m.estado == "adoptada"),
        en_acogida=sum(1 for m in propias if m.estado == "en_acogida"),
    )


def page_mascotas(items: list[MascotaOut], page: int, limit: int, total: int) -> PageMascotas:
    total_pages = max(1, -(-total // limit))
    return PageMascotas(items=items, page=page, limit=limit, total=total, total_pages=total_pages)


def refugio_detalle(
    refugio: Refugio,
    mascotas: list[Mascota],
    refugios: dict[str, Refugio],
) -> RefugioDetalleOut:
    return RefugioDetalleOut(
        refugio=refugio_out(refugio),
        resumen=resumen_refugio(refugio, mascotas),
        mascotas=[mascota_out(m, refugios) for m in mascotas if m.refugio_id == refugio.id],
    )


def similares(mascota: Mascota, todas: Iterable[Mascota], limite: int = 3) -> list[Mascota]:
    def puntaje(otra: Mascota) -> int:
        return (2 if otra.especie == mascota.especie else 0) + (
            1 if otra.distrito == mascota.distrito else 0
        )

    candidatas = [
        otra
        for otra in todas
        if otra.id != mascota.id and otra.estado == "disponible"
    ]
    candidatas.sort(key=puntaje, reverse=True)
    return candidatas[:limite]


def _cuidados(mascota: Mascota, detalle: DetalleMascota | None) -> list[CuidadoOut]:
    if detalle and detalle.cuidados:
        return [CuidadoOut(**cuidado) for cuidado in detalle.cuidados]

    cuidados: list[CuidadoOut] = []
    for item in mascota.salud:
        clave = item.texto.lower()
        icono = next((valor for llave, valor in ICONOS_SALUD.items() if llave in clave), "health_and_safety")
        texto = next((valor for llave, valor in TEXTOS_SALUD.items() if llave in clave), "Revisión veterinaria y cuidados al día.")
        cuidados.append(CuidadoOut(icono=icono, titulo=item.texto, texto=texto))
    cuidados.append(
        CuidadoOut(
            icono="fitness_center",
            titulo="Condición física óptima",
            texto="Peso adecuado, pelaje sano y evaluación veterinaria satisfactoria.",
        )
    )
    return cuidados


def _historia(mascota: Mascota, refugio: Refugio | None, detalle: DetalleMascota | None) -> list[str]:
    if detalle and detalle.historia:
        return detalle.historia
    rescatado = "rescatada" if mascota.sexo == "Hembra" else "rescatado"
    nombre_refugio = refugio.nombre if refugio else mascota.refugio_id
    return [
        f"{mascota.nombre} fue {rescatado} en {mascota.lugar} y desde entonces recibe atención veterinaria y mucho cariño en {nombre_refugio}.",
        f"Hoy vive en un hogar de acogida temporal, donde se está recuperando y aprendiendo rutinas de convivencia. Su temperamento es {mascota.energia.lower()} y ya comparte espacio con otras mascotas.",
        "Busca una familia responsable en el Valle del Mantaro que le ofrezca un hogar seguro, alimentación adecuada, atención veterinaria y seguimiento post-adopción.",
    ]


def _preguntas(mascota: Mascota, refugio: Refugio | None) -> list[PreguntaOut]:
    nombre_refugio = refugio.nombre if refugio else "el refugio"
    return [
        PreguntaOut(
            pregunta=f"¿Puedo conocer a {mascota.nombre} antes de decidir?",
            respuesta=f"¡Por supuesto! Coordinamos una visita al hogar temporal para conocer a {mascota.nombre} y confirmar la compatibilidad antes de firmar el acta.",
        ),
        PreguntaOut(
            pregunta="¿Cómo es el proceso de entrega?",
            respuesta=f"Una vez aprobada tu solicitud, una voluntaria de {nombre_refugio} te acompaña en la entrega con el carnet de salud y los implementos básicos de {mascota.nombre}.",
        ),
        PreguntaOut(
            pregunta="¿Si vivo en otro distrito del Valle puedo postular?",
            respuesta="Sí, recibimos postulaciones de todo el Valle del Mantaro. La única condición es que podamos coordinar la visita de verificación previa.",
        ),
    ]


def detalle_out(
    mascota: Mascota,
    refugio: Refugio,
    contenido: Contenido,
    detalle: DetalleMascota | None,
    todas: list[Mascota],
    refugios: dict[str, Refugio],
) -> DetalleMascotaOut:
    return DetalleMascotaOut(
        mascota=mascota_out(mascota, refugios),
        refugio=refugio_out(refugio),
        historia=_historia(mascota, refugio, detalle),
        cuidados=_cuidados(mascota, detalle),
        requisitos=[RequisitoOut(**requisito) for requisito in contenido.requisitos],
        preguntas=_preguntas(mascota, refugio),
        cita=CitaDetalleOut(**detalle.cita) if detalle and detalle.cita else None,
        galeria=[FotoOut(src=foto.src, alt=foto.alt) for foto in (mascota.galeria or [Foto(mascota.foto, mascota.alt)])],
        similares=[mascota_out(m, refugios) for m in similares(mascota, todas)],
    )


def contenido_out(contenido: Contenido) -> ContenidoOut:
    return ContenidoOut(
        pasos_adopcion=[PasoOut(**paso) for paso in contenido.pasos_adopcion],
        pasos_refugio=[PasoOut(**paso) for paso in contenido.pasos_refugio],
        faqs=[FaqOut(**faq) for faq in contenido.faqs],
        requisitos=[RequisitoOut(**requisito) for requisito in contenido.requisitos],
    )


# ---------------------------------------------------------------------------
# Estadísticas
# ---------------------------------------------------------------------------


def stats_mascotas(mascotas: list[Mascota], total_refugios: int) -> MascotaStats:
    def contar(campo: str) -> dict[str, int]:
        resultado: dict[str, int] = {}
        for mascota in mascotas:
            valor = getattr(mascota, campo)
            resultado[valor] = resultado.get(valor, 0) + 1
        return dict(sorted(resultado.items()))

    disponibles = [m for m in mascotas if m.estado == "disponible"]
    return MascotaStats(
        total=len(disponibles),
        total_registradas=len(mascotas),
        disponibles=len(disponibles),
        adoptadas=sum(1 for m in mascotas if m.estado == "adoptada"),
        en_acogida=sum(1 for m in mascotas if m.estado == "en_acogida"),
        urgentes=sum(1 for m in disponibles if m.urgente),
        total_refugios=total_refugios,
        edad_promedio=round(sum(m.edad_anios for m in mascotas) / len(mascotas), 2) if mascotas else 0.0,
        por_especie=contar("especie"),
        por_distrito=contar("distrito"),
        por_tamano=contar("tamano"),
    )


def impacto_out(mascotas: list[Mascota], refugios: list[Refugio]) -> ImpactoOut:
    disponibles = [m for m in mascotas if m.estado == "disponible"]
    por_distrito: dict[str, int] = {}
    for refugio in refugios:
        por_distrito[refugio.distrito] = por_distrito.get(refugio.distrito, 0) + refugio.adoptadas
    return ImpactoOut(
        total_adoptadas=sum(r.adoptadas for r in refugios),
        total_refugios=len(refugios),
        total_en_acogida=sum(r.en_acogida for r in refugios),
        total_distritos=len({r.distrito for r in refugios}),
        total_mascotas=len(disponibles),
        total_perros=sum(1 for m in disponibles if m.especie == "perro"),
        total_gatos=sum(1 for m in disponibles if m.especie == "gato"),
        adoptadas_por_distrito=dict(sorted(por_distrito.items())),
    )


# ---------------------------------------------------------------------------
# Usuarios y solicitudes
# ---------------------------------------------------------------------------


def usuario_out(usuario: Usuario) -> UsuarioOut:
    return UsuarioOut(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        dni=usuario.dni,
        telefono=usuario.telefono,
        distrito=usuario.distrito,
        rol=usuario.rol,
        refugio_id=usuario.refugio_id,
        creado_en=usuario.creado_en,
    )


def alerta_out(alerta: AlertaRescate) -> AlertaOut:
    return AlertaOut(
        id=alerta.id,
        nombre=alerta.nombre,
        contacto=alerta.contacto,
        distrito=alerta.distrito,
        especie=alerta.especie,
        mensaje=alerta.mensaje,
        atendida=alerta.atendida,
        creado_en=alerta.creado_en,
    )


def _etapas(solicitud: Solicitud) -> list[EtapaOut]:
    if solicitud.estado == "completada":
        return []
    if solicitud.etapas_override:
        return [EtapaOut(titulo=e.titulo, detalle=e.detalle, destacado=e.destacado) for e in solicitud.etapas_override]

    etapas: list[EtapaOut] = []
    for indice, titulo in enumerate(ETAPAS_TITULOS, start=1):
        if indice == 1:
            detalle = _fecha_corta(solicitud.creada_en)
        elif indice < solicitud.etapa:
            detalle = "Completado"
        elif indice == solicitud.etapa:
            if solicitud.cita and indice == 3:
                detalle = "¡Agendada!"
            elif indice == 2:
                detalle = "En revisión"
            elif indice == 4:
                detalle = "En evaluación"
            else:
                detalle = "En curso"
        else:
            detalle = "Pendiente"
        etapas.append(EtapaOut(titulo=f"{indice}. {titulo}", detalle=detalle, destacado=indice == solicitud.etapa))
    return etapas


def solicitud_out(
    solicitud: Solicitud,
    mascota: Mascota,
    refugio: Refugio | None,
    usuario: Usuario | None = None,
) -> SolicitudOut:
    paso = solicitud.etapa
    completada = solicitud.estado == "completada"
    cancelada = solicitud.estado == "cancelada"
    estado = "completed" if completada else "cancelled" if cancelada else "active"

    if completada:
        badge_texto = "Adopción Concluida"
        badge_clase = "bg-secondary text-on-secondary"
    elif cancelada:
        badge_texto = "Postulación cancelada"
        badge_clase = "bg-surface-container text-on-surface-variant"
    elif paso >= 3:
        badge_texto = "Visita Programada"
        badge_clase = "bg-secondary-fixed text-secondary"
    else:
        badge_texto = "En Revisión Inicial"
        badge_clase = "bg-primary-fixed text-primary"

    if completada or cancelada:
        punto_clase = ""
    elif paso >= 3:
        punto_clase = "bg-secondary animate-ping"
    else:
        punto_clase = "bg-primary animate-pulse"

    whatsapp = f"https://wa.me/{refugio.whatsapp}" if refugio and refugio.whatsapp else None
    if solicitud.mensaje:
        mensaje = MensajeSolicitudOut(
            iniciales=solicitud.mensaje.iniciales,
            nombre=solicitud.mensaje.nombre,
            rol=solicitud.mensaje.rol,
            texto=solicitud.mensaje.texto,
        )
    else:
        mensaje = None

    cierre: CierreOut | None = None
    if solicitud.cierre:
        cierre = CierreOut(
            titulo=solicitud.cierre.titulo,
            texto=solicitud.cierre.texto,
            control_titulo=solicitud.cierre.control_titulo,
            control_fecha=solicitud.cierre.control_fecha,
            control_lugar=solicitud.cierre.control_lugar,
        )
    elif completada:
        control = _sumar_meses(solicitud.actualizada_en or solicitud.creada_en, 3)
        cierre = CierreOut(
            titulo=f"¡{mascota.nombre} ya es parte de tu familia!",
            texto=(
                "Gracias por abrir tu corazón y brindarle un hogar cálido en el Valle del Mantaro. "
                "Tu contrato de adopción digital y certificado veterinario están disponibles en tu perfil."
            ),
            control_titulo="Control Veterinario Trimestral",
            control_fecha=f"{MESES[control.month - 1]} {control.year}",
            control_lugar=refugio.nombre if refugio else "Veterinaria aliada",
        )

    fecha_texto = (
        f"Adopción concretada: {_fecha_larga(solicitud.actualizada_en or solicitud.creada_en)}"
        if completada
        else f"Enviada el {_fecha_larga(solicitud.creada_en)}"
    )

    return SolicitudOut(
        id=solicitud.id,
        estado=estado,
        nombre=mascota.nombre,
        ficha_id=mascota.id,
        foto_src=solicitud.foto_src or mascota.foto,
        foto_alt=solicitud.foto_alt or mascota.alt,
        chip_texto="¡Adoptado en Casa!" if completada else f"{edad_texto(mascota.edad_anios)} • {mascota.sexo}",
        chip_clase=(
            "bg-secondary-fixed text-secondary font-bold"
            if completada
            else "bg-surface-container text-on-surface-variant"
        ),
        refugio=refugio.nombre if refugio else mascota.refugio_id,
        lugar=mascota.lugar,
        exp=solicitud.codigo,
        fecha_texto=fecha_texto,
        badge_texto=badge_texto,
        badge_clase=badge_clase,
        punto_clase=punto_clase,
        paso_texto="Proceso finalizado" if completada else f"Paso {paso} de 5",
        paso_texto_clase="text-secondary" if (completada or paso >= 3) else "text-primary",
        header_clase=HEADER_SOLICITUD_CERRADA if completada else HEADER_SOLICITUD_ACTIVA,
        icono_mini="verified" if completada else "pets",
        icono_mini_clase=(
            "bg-secondary text-on-secondary"
            if completada
            else "bg-surface-container-lowest text-primary"
        ),
        paso=paso,
        barra_clase="bg-secondary" if (completada or paso >= 3) else "bg-primary",
        etapas=_etapas(solicitud),
        cita=CitaOut(
            fecha=solicitud.cita.fecha,
            direccion=solicitud.cita.direccion,
            coordinadora=solicitud.cita.coordinadora,
        )
        if solicitud.cita
        else None,
        mensaje=mensaje,
        tiempo_respuesta=(
            solicitud.tiempo_respuesta
            if solicitud.tiempo_respuesta is not None
            else ("24 a 48 horas" if (estado == "active" and paso <= 2 and not mensaje) else None)
        ),
        whatsapp=solicitud.whatsapp if solicitud.whatsapp is not None else whatsapp,
        cierre=cierre,
        motivo_cancelacion=solicitud.motivo_cancelacion,
        fotos_seguimiento=[
            SeguimientoFotoOut(src=foto.src, alt=foto.alt) for foto in solicitud.seguimiento
        ],
        creada_en=solicitud.creada_en,
    )


def page_solicitudes(
    items: list[SolicitudOut], page: int, limit: int, total: int
) -> PageSolicitudes:
    return PageSolicitudes(
        items=items,
        page=page,
        limit=limit,
        total=total,
        total_pages=max(1, -(-total // limit)),
    )
