"""Carga `seed.json` (exportado desde Angular) al modelo de dominio."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

from ..domain import (
    Cierre,
    Cita,
    Contenido,
    DetalleMascota,
    EtapaVista,
    Foto,
    Mascota,
    Mensaje,
    Rasgo,
    Refugio,
    SaludItem,
    Solicitud,
    Usuario,
)
from ..security import hash_password

PATRON_PESO = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*kg", re.IGNORECASE)

ESTADOS_SOLICITUD = {"active": "activa", "completed": "completada"}


@dataclass(slots=True)
class SeedData:
    mascotas: list[Mascota] = field(default_factory=list)
    refugios: list[Refugio] = field(default_factory=list)
    contenido: Contenido = field(default_factory=Contenido)
    detalles: dict[int, DetalleMascota] = field(default_factory=dict)
    solicitudes: list[Solicitud] = field(default_factory=list)
    usuarios: list[Usuario] = field(default_factory=list)


def _dias_desde_texto(texto: str) -> int:
    coincidencia = re.search(r"hace\s+(\d+)\s+(d[ií]a|mes|meses|año|años)", texto.lower())
    if not coincidencia:
        return 0
    cantidad = int(coincidencia.group(1))
    unidad = coincidencia.group(2)
    if unidad.startswith("mes"):
        return cantidad * 30
    if unidad.startswith("año"):
        return cantidad * 365
    return cantidad


def _peso_desde_texto(texto: str) -> float:
    coincidencia = PATRON_PESO.search(texto or "")
    return float(coincidencia.group(1)) if coincidencia else 0.0


def _mascota(datos: dict) -> Mascota:
    return Mascota(
        id=int(datos["id"]),
        nombre=datos["nombre"],
        nombre_corto=datos.get("nombreCorto") or datos["nombre"],
        especie=datos["especie"],
        sexo=datos["sexo"],
        raza=datos["raza"],
        edad_anios=float(datos["edadAnios"]),
        tamano=datos["tamano"],
        peso_kg=_peso_desde_texto(datos.get("tamanoTexto", "")),
        distrito=datos["distrito"],
        lugar=datos["lugar"],
        foto=datos["foto"],
        alt=datos["alt"],
        descripcion=datos["descripcion"],
        etiqueta=datos["etiqueta"],
        etiqueta_icono=datos.get("etiquetaIcono", "pets"),
        etiqueta_clase=datos.get("etiquetaClase", "bg-secondary text-on-secondary"),
        esterilizado=bool(datos.get("esterilizado")),
        vacunado=bool(datos.get("vacunado")),
        urgente=bool(datos.get("urgente")),
        refugio_id=datos["refugioId"],
        energia=datos["energia"],
        ficha_id=datos["fichaId"],
        actualizado_dias=_dias_desde_texto(datos.get("actualizado", "")),
        estado=datos.get("estado", "disponible"),
        salud=[SaludItem(texto=item["texto"], ok=bool(item.get("ok"))) for item in datos.get("salud", [])],
        galeria=[Foto(src=foto["src"], alt=foto["alt"]) for foto in datos.get("galeria", [])],
        rasgos=[
            Rasgo(
                icono=rasgo["icono"],
                texto=rasgo["texto"],
                clase=rasgo["clase"],
                icono_clase=rasgo.get("iconoClase", ""),
            )
            for rasgo in datos.get("rasgos", [])
        ],
    )


def _refugio(datos: dict) -> Refugio:
    return Refugio(
        id=datos["id"],
        nombre=datos["nombre"],
        distrito=datos["distrito"],
        direccion=datos["direccion"],
        tipo=datos["tipo"],
        desde=int(datos["desde"]),
        descripcion=datos["descripcion"],
        contacto=datos["contacto"],
        cargo=datos["cargo"],
        telefono=datos["telefono"],
        whatsapp=datos["whatsapp"],
        adoptadas=int(datos.get("adoptadas", 0)),
        en_acogida=int(datos.get("enAcogida", 0)),
        verificado=bool(datos.get("verificado")),
        especies=list(datos.get("especies", [])),
        logo=datos.get("logo"),
    )


def _solicitud(datos: dict) -> Solicitud:
    creada = datetime.fromisoformat(datos["creadaEn"])
    estado = ESTADOS_SOLICITUD.get(datos.get("estado", "active"), "activa")
    cita = datos.get("cita")
    mensaje = datos.get("mensaje")
    cierre = datos.get("cierre")
    etapas = datos.get("etapas") or []
    return Solicitud(
        id=int(datos["id"]),
        codigo=datos["exp"],
        usuario_id=1,
        mascota_id=int(datos["fichaId"]),
        estado=estado,
        etapa=int(datos["paso"]),
        creada_en=creada,
        actualizada_en=creada + timedelta(days=2) if estado == "activa" else creada,
        tiempo_respuesta=datos.get("tiempoRespuesta"),
        whatsapp=datos.get("whatsapp"),
        foto_src=datos.get("fotoSrc"),
        foto_alt=datos.get("fotoAlt"),
        cita=Cita(
            fecha=cita["fecha"],
            direccion=cita["direccion"],
            coordinadora=cita["coordinadora"],
        )
        if cita
        else None,
        mensaje=Mensaje(
            iniciales=mensaje["iniciales"],
            nombre=mensaje["nombre"],
            rol=mensaje["rol"],
            texto=mensaje["texto"],
        )
        if mensaje
        else None,
        cierre=Cierre(
            titulo=cierre["titulo"],
            texto=cierre["texto"],
            control_titulo=cierre["controlTitulo"],
            control_fecha=cierre["controlFecha"],
            control_lugar=cierre["controlLugar"],
        )
        if cierre
        else None,
        etapas_override=[
            EtapaVista(
                titulo=etapa["titulo"],
                detalle=etapa["detalle"],
                destacado=bool(etapa.get("destacado")),
            )
            for etapa in etapas
        ]
        or None,
    )


@lru_cache(maxsize=8)
def _hash_demo(password: str) -> str:
    """Los hashes demo se calculan una sola vez por proceso."""
    return hash_password(password)


DEMO_USERS = [
    {
        "id": 1,
        "nombre": "Valeria Quispe",
        "email": "demo@leons.pe",
        "dni": "70000001",
        "password": "demo12345",
        "rol": "adoptante",
        "distrito": "El Tambo",
        "telefono": "+51 999 111 222",
        "refugio_id": None,
    },
    {
        "id": 2,
        "nombre": "Silvia Mallqui",
        "email": "refugio@leons.pe",
        "dni": "70000002",
        "password": "refugio12345",
        "rol": "refugio",
        "distrito": "El Tambo",
        "telefono": "+51 964 123 456",
        "refugio_id": "huellitas-wanka",
    },
    {
        "id": 3,
        "nombre": "Administrador LeonS",
        "email": "admin@leons.pe",
        "dni": "70000003",
        "password": "admin12345",
        "rol": "admin",
        "distrito": "Huancayo Centro",
        "telefono": None,
        "refugio_id": None,
    },
]


def cargar_seed(ruta: Path) -> SeedData:
    if not ruta.exists():
        raise RuntimeError(
            f"No existe el seed en {ruta}. Genera el archivo con "
            "`Leons/scripts/export-seed.ts` (ver Backend/README.md)."
        )

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    contenido = datos.get("contenido", {})
    detalles = {
        int(llave): DetalleMascota(
            historia=valor.get("historia", []),
            cuidados=valor.get("cuidados", []),
            rasgos=[
                Rasgo(
                    icono=rasgo["icono"],
                    texto=rasgo["texto"],
                    clase=rasgo["clase"],
                    icono_clase=rasgo.get("iconoClase", ""),
                )
                for rasgo in valor.get("rasgos", [])
            ],
            cita=valor.get("cita"),
        )
        for llave, valor in datos.get("detalles", {}).items()
    }

    usuarios = [
        Usuario(
            id=usuario["id"],
            nombre=usuario["nombre"],
            email=usuario["email"],
            dni=usuario["dni"],
            telefono=usuario.get("telefono"),
            distrito=usuario.get("distrito"),
            rol=usuario["rol"],
            refugio_id=usuario.get("refugio_id"),
            password_hash=_hash_demo(usuario["password"]),
            creado_en=datetime(2025, 1, 1, 9, 0, 0),
        )
        for usuario in DEMO_USERS
    ]

    return SeedData(
        mascotas=[_mascota(mascota) for mascota in datos.get("mascotas", [])],
        refugios=[_refugio(refugio) for refugio in datos.get("refugios", [])],
        contenido=Contenido(
            pasos_adopcion=contenido.get("pasosAdopcion", []),
            pasos_refugio=contenido.get("pasosRefugio", []),
            faqs=contenido.get("faqs", []),
            requisitos=contenido.get("requisitos", []),
        ),
        detalles=detalles,
        solicitudes=[_solicitud(solicitud) for solicitud in datos.get("solicitudesDemo", [])],
        usuarios=usuarios,
    )
