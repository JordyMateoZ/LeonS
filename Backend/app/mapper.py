"""Mapas de presentación derivados: el dominio no guarda clases CSS."""

from __future__ import annotations

import math
from datetime import datetime

from app.domain import AlertaRescate, Contenido, EstadoMascota, Mascota, Refugio, Solicitud

RASGO_BASE = (
    "inline-flex items-center gap-1.5 font-label-md text-label-md px-4 py-2.5 rounded-full "
)

RASGOS_POR_ESPECIE: dict[str, list[dict[str, str]]] = {
    "perro": [
        {"icono": "toys", "texto": "Juguetón y cariñoso"},
        {"icono": "chair", "texto": "Tranquilo en interiores"},
        {"icono": "family_restroom", "texto": "Excelente con niños"},
        {"icono": "group", "texto": "Sociable con otros perros"},
        {"icono": "nordic_walking", "texto": "Acostumbrado a paseos con correa"},
    ],
    "gato": [
        {"icono": "favorite", "texto": "Cariñoso y ronroneador"},
        {"icono": "chair", "texto": "Disfruta espacios tranquilos"},
        {"icono": "group", "texto": "Sociable con otros gatos"},
        {"icono": "cleaning_services", "texto": "Limpio con su arenero"},
        {"icono": "apartment", "texto": "Se adapta a departamento"},
    ],
}

ESTADO_INFO: dict[EstadoMascota, dict[str, str]] = {
    "disponible": {
        "etiqueta": "Disponible",
        "icono": "favorite",
        "clase": "bg-secondary text-on-secondary",
    },
    "adoptada": {
        "etiqueta": "Adoptada",
        "icono": "verified",
        "clase": "bg-primary text-on-primary",
    },
    "en_acogida": {
        "etiqueta": "En acogida",
        "icono": "home",
        "clase": "bg-surface-container text-on-surface-variant",
    },
}


def _rasgo_dto(rasgo: dict[str, str], destacado: bool = False) -> dict[str, str]:
    return {
        "icono": rasgo["icono"],
        "texto": rasgo["texto"],
        "clase": RASGO_BASE
        + (
            "bg-primary-fixed text-on-primary-fixed shadow-sm"
            if destacado
            else "bg-surface-container text-on-surface"
        ),
        "iconoClase": "" if destacado else "text-secondary",
    }


def rasgos_de(mascota: Mascota) -> list[dict[str, str]]:
    fuente = (
        [{"icono": r.icono, "texto": r.texto} for r in mascota.rasgos]
        if mascota.rasgos
        else RASGOS_POR_ESPECIE[mascota.especie]
    )
    return [_rasgo_dto(rasgo, indice % 2 == 0) for indice, rasgo in enumerate(fuente)]


def to_mascota_dto(mascota: Mascota) -> dict:
    datos = mascota.model_dump(by_alias=True, mode="json")
    datos["badgeClase"] = (
        "text-primary bg-primary-fixed"
        if mascota.especie == "perro"
        else "text-secondary bg-secondary-fixed"
    )
    datos["etiquetaClase"] = (
        "bg-primary text-on-primary" if mascota.urgente else "bg-secondary text-on-secondary"
    )
    datos["estadoInfo"] = ESTADO_INFO[mascota.estado]
    datos["rasgos"] = rasgos_de(mascota)
    return datos


def to_refugio_dto(refugio: Refugio) -> dict:
    datos = refugio.model_dump(by_alias=True, mode="json")
    datos["whatsappUrl"] = f"https://wa.me/{refugio.whatsapp}"
    datos["iniciales"] = "".join(
        palabra[0].upper() for palabra in refugio.nombre.split()[:2] if palabra
    )
    return datos


def to_alerta_dto(alerta: AlertaRescate) -> dict:
    datos = alerta.model_dump(by_alias=True, mode="json")
    digits = "".join(caracter for caracter in alerta.telefono if caracter.isdigit())
    datos["whatsappUrl"] = f"https://wa.me/{digits}"
    return datos


HISTORIAS_ESPECIALES: dict[int, list[str]] = {
    1: [
        "Chaska fue encontrada en noviembre cerca de la ribera del Río Shullcas, en El Tambo. Estaba protegiendo con valentía a sus cuatro cachorritos bajo un cobertizo precario de calamina, buscando abrigo contra las heladas nocturnas del valle.",
        "Gracias a una alerta ciudadana coordinada con la red de voluntarias de Albergue Huellitas Wanka, Chaska y su camada fueron puestas a salvo. Sus pequeños ya fueron adoptados en hogares responsables y ahora le toca a ella encontrar a su propia familia.",
        "Busca una familia comprometida en el Valle del Mantaro que comprenda que un perro no es una alarma de azotea ni un vigilante de garaje, sino un miembro más del hogar.",
    ]
}

CITAS_ESPECIALES: dict[int, dict[str, str]] = {
    1: {
        "texto": "Chaska es de esas perritas que te miran con absoluta gratitud. Le encanta apoyar suavemente su hocico en tu regazo mientras descansas. No ladra sin motivo, duerme en su manta y se porta como una dama en casa.",
        "autor": "Lic. Silvia Mallqui, Coordinadora de Acogida",
    }
}

CUIDADOS_ESPECIALES: dict[int, list[dict[str, str]]] = {
    1: [
        {"icono": "check", "titulo": "Esterilizada Certificada", "texto": "Campaña Municipal El Tambo (ene 2025). Cirugía limpia y cicatrización completada."},
        {"icono": "vaccines", "titulo": "Vacunas al Día", "texto": "Séxtuple canina y antirrábica vigentes. Carnet físico original listo para entrega."},
        {"icono": "verified", "titulo": "Desparasitación Completa", "texto": "Protección interna y externa al día. Tratamiento aplicado hace 15 días."},
        {"icono": "fitness_center", "titulo": "Condición Física Óptima", "texto": "Recuperada de desnutrición. Peso ideal de 14 kg, pelaje brillante y excelente capacidad respiratoria para la altura."},
    ]
}

REQUISITOS = [
    {
        "icono": "home_work",
        "titulo": "Vivienda con cerco perimétrico seguro:",
        "texto": "Casa con portón cerrado o departamento propio / alquilado pet-friendly en Huancayo, El Tambo, Chilca o zonas aledañas.",
    },
    {
        "icono": "roofing",
        "titulo": "Sin cadenas ni techos desprotegidos:",
        "texto": "Compromiso firmado de no mantener a la mascota a la intemperie, amarrada ni en azoteas expuestas al frío o la lluvia.",
    },
    {
        "icono": "handshake",
        "titulo": "Visita previa y seguimiento respetuoso:",
        "texto": "Conocer a la mascota en persona y permitir seguimiento virtual fotográfico a los 1, 3 y 6 meses de integración.",
    },
    {
        "icono": "badge",
        "titulo": "Documentación básica ciudadana:",
        "texto": "DNI original de la persona mayor de edad titular y copia de recibo de servicios (luz o agua) para acreditar domicilio.",
    },
]

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _icono_para(texto: str) -> str:
    t = texto.casefold()
    if "esteriliz" in t:
        return "check"
    if "vacun" in t:
        return "vaccines"
    if "desparasit" in t:
        return "verified"
    if "test felino" in t:
        return "science"
    if "compromiso" in t:
        return "schedule"
    return "health_and_safety"


def _texto_para(texto: str) -> str:
    t = texto.casefold()
    if "esteriliz" in t:
        return "Procedimiento certificado y recuperación completada."
    if "vacun" in t:
        return "Esquema de vacunas vigente y carnet listo para entrega."
    if "desparasit" in t:
        return "Protección interna y externa al día."
    if "test felino" in t:
        return "Resultado negativo en las pruebas felinas realizadas."
    if "compromiso" in t:
        return "Se entrega con compromiso formal de esterilización gratuita."
    return "Revisión veterinaria y cuidados al día."


def to_detalle_mascota(mascota: Mascota) -> dict:
    rescatado = "rescatada" if mascota.sexo == "Hembra" else "rescatado"
    historia = HISTORIAS_ESPECIALES.get(mascota.id) or [
        f"{mascota.nombre} fue {rescatado} en {mascota.lugar} y desde entonces recibe atención veterinaria y mucho cariño en {mascota.refugio}.",
        f"Hoy vive en un hogar de acogida temporal, donde se está recuperando y aprendiendo rutinas de convivencia. Su temperamento es {mascota.energia.casefold()} y ya comparte espacio con otras mascotas.",
        "Busca una familia responsable en el Valle del Mantaro que le ofrezca un hogar seguro, alimentación adecuada, atención veterinaria y seguimiento post-adopción.",
    ]

    cuidados = CUIDADOS_ESPECIALES.get(mascota.id) or [
        {
            "icono": _icono_para(item.texto),
            "titulo": item.texto,
            "texto": _texto_para(item.texto),
        }
        for item in mascota.salud
    ] + [
        {
            "icono": "fitness_center",
            "titulo": "Condición física óptima",
            "texto": "Peso adecuado, pelaje sano y evaluación veterinaria satisfactoria.",
        }
    ]

    respuesta: dict = {
        "fichaId": mascota.ficha_id,
        "historia": historia,
        "rasgos": rasgos_de(mascota),
        "cuidados": cuidados,
        "requisitos": REQUISITOS,
        "preguntas": [
            {
                "pregunta": f"¿Puedo conocer a {mascota.nombre} antes de decidir?",
                "respuesta": f"¡Por supuesto! Coordinamos una visita al hogar temporal para conocer a {mascota.nombre} y confirmar la compatibilidad antes de firmar el acta.",
            },
            {
                "pregunta": "¿Cómo es el proceso de entrega?",
                "respuesta": f"Una vez aprobada tu solicitud, una voluntaria de {mascota.refugio} te acompaña en la entrega con el carnet de salud y los implementos básicos de {mascota.nombre}.",
            },
            {
                "pregunta": "¿Si vivo en otro distrito del Valle puedo postular?",
                "respuesta": "Sí, recibimos postulaciones de todo el Valle del Mantaro. La única condición es que podamos coordinar la visita de verificación previa.",
            },
        ],
    }
    if mascota.id in CITAS_ESPECIALES:
        respuesta["cita"] = CITAS_ESPECIALES[mascota.id]
    return respuesta


def _fecha_legible(iso: str) -> str:
    try:
        fecha = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return "Fecha por confirmar"
    return f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


TITULOS_ETAPAS = [
    "Enviada",
    "Revisión de Ficha",
    "Entrevista / Visita",
    "Aprobación",
    "Adopción Feliz",
]


def _etapas(solicitud: Solicitud) -> list[dict]:
    if solicitud.estado in {"completed", "cancelled"}:
        return []
    etapas = []
    for indice, titulo in enumerate(TITULOS_ETAPAS, start=1):
        if indice < solicitud.paso:
            detalle = "Completado"
        elif indice == solicitud.paso:
            detalle = "¡Agendada!" if solicitud.cita else "En curso"
        else:
            detalle = "Pendiente"
        etapa = {"titulo": f"{indice}. {titulo}", "detalle": detalle}
        if indice == solicitud.paso - 1:
            etapa["destacado"] = True
        etapas.append(etapa)
    return etapas


def _badge_de_paso(paso: int) -> str:
    if paso >= 5:
        return "Adopción Feliz"
    if paso == 4:
        return "Aprobación Pendiente"
    if paso == 3:
        return "Visita Programada"
    return "En Revisión Inicial"


def _cierre_generico(solicitud: Solicitud) -> dict:
    return {
        "titulo": f"¡{solicitud.nombre} ya es parte de tu familia!",
        "texto": "Gracias por abrir tu corazón y brindarle un hogar cálido en el Valle del Mantaro. Tu contrato de adopción digital y certificado veterinario están disponibles en tu perfil.",
        "controlTitulo": "Control Veterinario Trimestral",
        "controlFecha": "Próximo control",
        "controlLugar": "Veterinaria aliada",
    }


def to_solicitud_dto(
    solicitud: Solicitud,
    mascota: Mascota | None = None,
    refugio: Refugio | None = None,
) -> dict:
    datos = solicitud.model_dump(by_alias=True, mode="json")
    avanzada = solicitud.paso >= 3
    final = solicitud.estado != "active"
    whatsapp = solicitud.whatsapp or (
        f"https://wa.me/{refugio.whatsapp}" if refugio else None
    )

    datos.update(
        {
            "fotoSrc": mascota.foto if mascota else "",
            "fotoAlt": mascota.alt if mascota else f"Foto de {solicitud.nombre}",
            "chipTexto": (
                f"{mascota.edad_texto} • {mascota.sexo}"
                if mascota
                else "¡Adoptado en Casa!"
                if solicitud.estado == "completed"
                else "Ficha en revisión"
            ),
            "chipClase": (
                "bg-secondary-fixed text-secondary font-bold"
                if solicitud.estado == "completed"
                else "bg-surface-container text-on-surface-variant"
            ),
            "fechaTexto": (
                f"Adopción concretada: {_fecha_legible(solicitud.actualizada_en)}"
                if solicitud.estado == "completed"
                else f"Enviada el {_fecha_legible(solicitud.creada_en)}"
            ),
            "badgeTexto": (
                "Solicitud Cancelada"
                if solicitud.estado == "cancelled"
                else "Adopción Concluida"
                if solicitud.estado == "completed"
                else _badge_de_paso(solicitud.paso)
            ),
            "badgeClase": (
                "bg-secondary text-on-secondary"
                if final
                else "bg-secondary-fixed text-secondary"
                if avanzada
                else "bg-primary-fixed text-primary"
            ),
            "puntoClase": (
                "" if final else "bg-secondary animate-ping" if avanzada else "bg-primary animate-pulse"
            ),
            "pasoTexto": "Proceso finalizado" if final else f"Paso {solicitud.paso} de 5",
            "pasoTextoClase": "text-secondary" if final or avanzada else "text-primary",
            "headerClase": (
                "from-secondary-fixed/20 via-surface-container-lowest to-surface-container-lowest"
                if final
                else "from-surface-container-lowest via-surface-container-low/40 to-surface-container-lowest"
            ),
            "iconoMini": "verified" if final else "pets",
            "iconoMiniClase": (
                "bg-secondary text-on-secondary"
                if final
                else "bg-surface-container-lowest text-primary"
            ),
            "barraClase": "bg-secondary",
            "etapas": _etapas(solicitud),
        }
    )
    if solicitud.estado == "completed" and not solicitud.cierre:
        datos["cierre"] = _cierre_generico(solicitud)
    if whatsapp:
        datos["whatsapp"] = whatsapp
    return datos


def to_contenido_dto(contenido: Contenido) -> dict:
    return contenido.model_dump(by_alias=True, mode="json")


def to_impacto(refugios: list[Refugio], solicitudes: list[Solicitud], mascotas: list[Mascota]) -> dict:
    distritos = {r.distrito for r in refugios}
    perros = sum(1 for m in mascotas if m.especie == "perro")
    gatos = len(mascotas) - perros
    total = len(mascotas) or 1
    pct_perros = math.floor((perros / total) * 100 + 0.5)

    return {
        "kpis": {
            "adoptadas": sum(r.adoptadas for r in refugios),
            "refugios": len(refugios),
            "enAcogida": sum(r.en_acogida for r in refugios),
            "distritos": len(distritos),
            "mascotasEnCatalogo": len(mascotas),
            "solicitudesActivas": sum(1 for s in solicitudes if s.estado == "active"),
        },
        "serieMensual": [
            {"mes": "Ene", "valor": 45},
            {"mes": "Feb", "valor": 58},
            {"mes": "Mar", "valor": 62},
            {"mes": "Abr", "valor": 74},
            {"mes": "May", "valor": 92},
            {"mes": "Jun", "valor": 97},
        ],
        "porEspecie": [
            {"nombre": "Caninos", "total": perros, "porcentaje": pct_perros},
            {"nombre": "Felinos", "total": gatos, "porcentaje": 100 - pct_perros},
        ],
        "porDistrito": [
            {
                "distrito": distrito,
                "total": sum(1 for r in refugios if r.distrito == distrito),
            }
            for distrito in sorted(distritos)
        ],
    }
