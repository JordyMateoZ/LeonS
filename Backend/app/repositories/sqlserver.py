"""Repositorio SQL Server de la Fase 6.

Implementa el protocolo `Repositorio` sin conocer HTTP. Las reglas de
presentación siguen viviendo en `app/mapper.py`; aquí solo se traduce entre
filas y el modelo de dominio.

Decisiones aplicadas:

* D-025: `crear_*` inserta y devuelve la entidad con el id que generó
  SQL Server. Las solicitudes insertan un `codigo` temporal y lo reemplazan
  por el definitivo dentro de la misma transacción.
* D-028: los `NULL` no se rellenan con texto inventado; cuando el contrato
  exige un valor se aplica un valor por defecto documentado.
* D-029/D-030: distrito propio, `etiqueta_clase`, iconos de rasgo, historia,
  cuidados y cita de la ficha.
"""

from __future__ import annotations

import logging
import mimetypes
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import and_, case, collate, delete, exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, selectinload, sessionmaker

from ..db import models as db
from ..db.session import crear_engine, crear_fabrica
from ..domain import (
    AlertaRescate,
    Cita,
    Contenido,
    DetalleMascota,
    Favorito,
    FiltroMascotas,
    Foto,
    Mascota,
    Mensaje,
    Rasgo,
    Refugio,
    SaludItem,
    Solicitud,
    Usuario,
    ahora_utc,
    codigo_solicitud,
    ficha_predeterminada,
)
from ..errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    TransitorioError,
    ValidationError,
)

logger = logging.getLogger(__name__)

ESTERILIZADO = re.compile(r"esterilizad[oa]", re.IGNORECASE)
VACUNADO = re.compile(r"vacunad[oa]|vacunas", re.IGNORECASE)

# Un solo reintento: suficiente para la víctima de un deadlock 1205 y acotado
# para no convertir una incidencia de BD en un bucle de escrituras.
REINTENTOS_DEADLOCK = 1

# La base usa `Modern_Spanish_CI_AI`; la búsqueda del catálogo replica el
# `in` de Python sobre `str.lower()`, que distingue tildes (Fase 4.2, P1).
COLACION_BUSQUEDA = "Modern_Spanish_CI_AS"


def _codigo_transitorio_sqlserver(exc: BaseException) -> str | None:
    """Detecta deadlock 1205 / timeout de bloqueo 1222 sin mapear otros DBAPIError.

    SQLAlchemy envuelve al `pyodbc.Error` original en `DBAPIError.orig`; se
    inspeccionan ambos para no depender de una sola capa.
    """
    orig = getattr(exc, "orig", None)
    candidatos = [exc] if orig is None else [exc, orig]
    textos = []
    for candidato in candidatos:
        textos.append(str(candidato))
        args = getattr(candidato, "args", ())
        textos.extend(str(arg) for arg in args)
    texto = " ".join(textos).lower()
    if "(1205)" in texto or "deadlocked" in texto or "deadlock victim" in texto:
        return "1205"
    if "(1222)" in texto or "lock timeout" in texto:
        return "1222"
    return None


def _escapar_like(texto: str) -> str:
    """Escapa los comodines de `LIKE` con la cláusula `ESCAPE '\\'`."""
    return (
        texto.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("[", "\\[")
    )

# Orden editorial de `especies` en el contrato (ver `refugios.data.ts`).
_ORDEN_ESPECIE = {"perro": 0, "gato": 1}

MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)

MESES_NUMERO = {nombre: indice + 1 for indice, nombre in enumerate(MESES)}

# A-16: formatos admitidos por el contrato. El día y el mes son
# obligatorios; el prefijo de día de la semana es decorativo y la hora es
# opcional. Se aceptan los separadores `•`, `·`, `,` y `-`, además de espacio.
FECHA_CITA_PATRON = re.compile(
    r"""^\s*
    (?:(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+)?
    (\d{1,2})\s*(?:de\s+)?([a-záéíóúñÁÉÍÓÚÑ]+)\.?
    (?:\s*(?:[•·,\-]\s*)?(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?)?)?
    \s*$""",
    re.IGNORECASE | re.VERBOSE,
)

# `CK_seguimiento_fotos_mes` solo admite los controles de 1, 3 y 6 meses.
MESES_SEGUIMIENTO = (1, 3, 6)


def _iniciales(nombre: str) -> str:
    partes = [parte for parte in nombre.split() if parte]
    return "".join(parte[0] for parte in partes[:2]).upper() or "LS"


def _texto_fecha(fecha: datetime) -> str:
    return f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


def _autor_id_mensaje(mensaje: Mensaje) -> int:
    """Devuelve el autor autenticado; nunca infiere al adoptante (A-14)."""
    if mensaje.autor_id is None:
        raise ValidationError(
            "AUTOR_MENSAJE_REQUERIDO",
            "El mensaje no tiene un autor autenticado identificado.",
        )
    return mensaje.autor_id


def _parsear_fecha(texto: str, anio: int | None = None) -> datetime:
    """Convierte estrictamente el texto de una cita a `DATETIME2` (A-16).

    Formatos admitidos (sin cambiar el tipo `str` del contrato):
    `24 mayo`, `24 de mayo`, `Sábado 24 Mayo • 10:30 am` y su variante con
    `·`. La hora puede omitirse (00:00) o expresarse en 24 h; el sufijo
    `am`/`pm` se interpreta como reloj de 12 h. El año ausente se toma del
    contexto (`anio`, o el año UTC vigente) porque el formato documentado no
    lo incluye. Cualquier fecha inexistente o texto no reconocido se rechaza:
    nunca se sustituye por `ahora_utc()`.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ValidationError(
            "FECHA_CITA_INVALIDA",
            "La fecha de la cita es obligatoria y debe ser un texto válido.",
        )

    coincidencia = FECHA_CITA_PATRON.match(texto)
    if coincidencia is None:
        raise ValidationError(
            "FECHA_CITA_INVALIDA",
            "La fecha de la cita no usa un formato reconocido.",
            {"fecha": texto[:120]},
        )

    dia = int(coincidencia.group(1))
    mes = MESES_NUMERO.get(coincidencia.group(2).lower())
    if mes is None:
        raise ValidationError(
            "FECHA_CITA_INVALIDA",
            "El mes de la cita no es válido.",
            {"fecha": texto[:120]},
        )

    hora = int(coincidencia.group(3) or 0)
    minuto = int(coincidencia.group(4) or 0)
    meridiano = coincidencia.group(5)
    if meridiano:
        if not 1 <= hora <= 12:
            raise ValidationError(
                "FECHA_CITA_INVALIDA",
                "La hora con am/pm debe estar entre 1 y 12.",
                {"fecha": texto[:120]},
            )
        hora = hora % 12 + (12 if meridiano.lower().startswith("p") else 0)
    elif not 0 <= hora <= 23:
        raise ValidationError(
            "FECHA_CITA_INVALIDA",
            "La hora de la cita no es válida.",
            {"fecha": texto[:120]},
        )

    if not 0 <= minuto <= 59:
        raise ValidationError(
            "FECHA_CITA_INVALIDA",
            "Los minutos de la cita no son válidos.",
            {"fecha": texto[:120]},
        )

    try:
        return datetime(anio or ahora_utc().year, mes, dia, hora, minuto)
    except ValueError as error:
        raise ValidationError(
            "FECHA_CITA_INVALIDA",
            "La fecha de la cita no existe en el calendario.",
            {"fecha": texto[:120]},
        ) from error


def _decimal(valor: float | None) -> Decimal | None:
    if valor is None:
        return None
    return Decimal(str(valor))


class SqlServerRepository:
    """Implementación del protocolo `Repositorio` sobre SQL Server."""

    def __init__(self, url: str, uploads_dir: Path | None = None) -> None:
        self.engine = crear_engine(url)
        self._fabrica: sessionmaker[Session] = crear_fabrica(self.engine)
        self._uploads = uploads_dir

    # -- Infraestructura --------------------------------------------------
    @contextmanager
    def _sesion(self) -> Iterator[Session]:
        sesion = self._fabrica()
        try:
            yield sesion
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()

    def _mapa_distritos(self, sesion: Session) -> dict[int, str]:
        return {
            distrito.id: distrito.nombre
            for distrito in sesion.scalars(select(db.Distrito))
        }

    def _id_distrito(self, sesion: Session, nombre: str | None) -> int | None:
        if not nombre:
            return None
        existente = sesion.scalar(
            select(db.Distrito).where(db.Distrito.nombre == nombre)
        )
        if existente is not None:
            return existente.id
        nuevo = db.Distrito(nombre=nombre)
        sesion.add(nuevo)
        sesion.flush()
        return nuevo.id

    def _mapa_usuarios(self, sesion: Session) -> dict[int, db.Usuario]:
        return {usuario.id: usuario for usuario in sesion.scalars(select(db.Usuario))}

    # -- Traducción fila → dominio ---------------------------------------
    def _mascota(self, fila: db.Mascota, distritos: dict[int, str]) -> Mascota:
        salud = [SaludItem(texto=item.texto, ok=bool(item.ok)) for item in fila.salud]
        distrito = distritos.get(fila.distrito_id or 0, "")
        if not distrito and fila.refugio is not None and fila.refugio.distrito is not None:
            distrito = fila.refugio.distrito.nombre
        # D-032: la columna manda; si es NULL se deriva de `mascota_salud`.
        esterilizado = (
            bool(fila.esterilizado)
            if fila.esterilizado is not None
            else any(ESTERILIZADO.search(item.texto) for item in salud)
        )
        vacunado = (
            bool(fila.vacunado)
            if fila.vacunado is not None
            else any(VACUNADO.search(item.texto) for item in salud)
        )
        return Mascota(
            id=fila.id,
            nombre=fila.nombre,
            nombre_corto=fila.nombre_corto or fila.nombre,
            especie=fila.especie,
            sexo=fila.sexo or "Macho",
            raza=fila.raza or "",
            edad_anios=float(fila.edad) if fila.edad is not None else 0.0,
            tamano=fila.tamano or "Mediano",
            peso_kg=float(fila.peso_kg) if fila.peso_kg is not None else 0.0,
            distrito=distrito,
            lugar=fila.lugar or "",
            foto=fila.foto_principal or "",
            alt=fila.foto_alt or "",
            descripcion=fila.descripcion or "",
            etiqueta=fila.etiqueta or "",
            etiqueta_icono=fila.etiqueta_icono or "pets",
            etiqueta_clase=fila.etiqueta_clase
            or (
                "bg-primary text-on-primary"
                if fila.urgente
                else "bg-secondary text-on-secondary"
            ),
            esterilizado=esterilizado,
            vacunado=vacunado,
            urgente=bool(fila.urgente),
            refugio_id=fila.refugio_id,
            energia=fila.energia or "",
            ficha_id=ficha_predeterminada(fila.id),
            actualizado_dias=max(
                0, (ahora_utc() - (fila.actualizado_en or fila.creado_en)).days
            ),
            estado=fila.estado,
            salud=salud,
            galeria=[Foto(src=foto.url, alt=foto.alt or "") for foto in fila.fotos],
            rasgos=[
                Rasgo(
                    icono=rasgo.icono or "pets",
                    texto=rasgo.rasgo,
                    clase=rasgo.clase or "",
                    icono_clase=rasgo.icono_clase or "",
                )
                for rasgo in fila.rasgos
            ],
        )

    def _refugio(self, fila: db.Refugio, distritos: dict[int, str]) -> Refugio:
        return Refugio(
            id=fila.id,
            nombre=fila.nombre,
            distrito=distritos.get(fila.distrito_id or 0, ""),
            direccion=fila.direccion or "",
            tipo=fila.tipo or "constituido",
            desde=fila.desde or 0,
            descripcion=fila.descripcion or "",
            contacto=fila.contacto or "",
            cargo=fila.cargo or "",
            telefono=fila.telefono or "",
            whatsapp=fila.whatsapp or "",
            adoptadas=fila.adoptadas_historicas,
            en_acogida=fila.en_acogida_actual,
            verificado=bool(fila.verificado),
            # El contrato publica `perro` antes que `gato`; la PK de
            # `refugio_especies` los devuelve en orden alfabético.
            especies=sorted(
                (item.especie for item in fila.especies),
                key=lambda especie: _ORDEN_ESPECIE.get(especie, 9),
            ),
            logo=fila.logo,
        )

    def _usuario(self, fila: db.Usuario, distritos: dict[int, str]) -> Usuario:
        return Usuario(
            id=fila.id,
            nombre=fila.nombres,
            email=fila.email,
            password_hash=fila.password_hash or "",
            rol=fila.rol,
            dni=fila.dni,
            telefono=fila.telefono,
            distrito=distritos.get(fila.distrito_id or 0),
            refugio_id=fila.refugio_id,
            google_id=fila.google_id,
            activo=bool(fila.activo) if fila.activo is not None else True,
            creado_en=fila.creado_en,
        )

    def _solicitud(
        self, fila: db.Solicitud, usuarios: dict[int, db.Usuario]
    ) -> Solicitud:
        citas = sorted(fila.citas, key=lambda cita: (cita.creado_en, cita.id))
        mensajes = sorted(fila.mensajes, key=lambda m: (m.creado_en, m.id))
        seguimiento = sorted(fila.seguimiento, key=lambda f: (f.mes, f.id))

        mensaje = None
        if mensajes:
            ultimo = mensajes[-1]
            autor = usuarios.get(ultimo.autor_id)
            rol = (
                "Coordinación del refugio"
                if autor is not None and autor.rol in {"refugio", "admin"}
                else "Adoptante"
            )
            mensaje = Mensaje(
                iniciales=_iniciales(autor.nombres if autor else "LeonS"),
                nombre=autor.nombres if autor else "LeonS",
                rol=rol,
                texto=ultimo.texto,
                autor_id=ultimo.autor_id,
            )

        cita = None
        if citas:
            ultima = citas[-1]
            cita = Cita(
                fecha=ultima.notas or _texto_fecha(ultima.fecha_hora),
                direccion=ultima.lugar or "",
                coordinadora=ultima.coordinadora or "",
            )

        return Solicitud(
            id=fila.id,
            codigo=fila.codigo,
            usuario_id=fila.usuario_id,
            mascota_id=fila.mascota_id,
            estado=fila.estado,
            etapa=fila.etapa,
            creada_en=fila.creado_en,
            actualizada_en=fila.actualizado_en or fila.creado_en,
            motivo_cancelacion=fila.motivo_cancelacion,
            cita=cita,
            mensaje=mensaje,
            seguimiento=[
                Foto(src=item.archivo, alt=item.comentario or "") for item in seguimiento
            ],
        )

    def _alerta(self, fila: db.AlertaRescate, distritos: dict[int, str]) -> AlertaRescate:
        return AlertaRescate(
            id=fila.id,
            nombre=fila.nombre,
            contacto=fila.contacto or "",
            distrito=distritos.get(fila.distrito_id or 0),
            especie=fila.especie,
            mensaje=fila.mensaje
            if fila.mensaje is not None
            else (fila.descripcion or None),
            atendida=fila.estado != "nueva",
            creado_en=fila.creado_en,
        )

    # -- Catálogo ---------------------------------------------------------
    def _opciones_mascota(self):
        return (
            selectinload(db.Mascota.salud),
            selectinload(db.Mascota.fotos),
            selectinload(db.Mascota.rasgos),
            selectinload(db.Mascota.refugio).selectinload(db.Refugio.distrito),
        )

    def listar_mascotas(self) -> list[Mascota]:
        with self._sesion() as sesion:
            distritos = self._mapa_distritos(sesion)
            filas = sesion.scalars(
                select(db.Mascota)
                .options(*self._opciones_mascota())
                .order_by(db.Mascota.id)
            ).all()
            return [self._mascota(fila, distritos) for fila in filas]

    def buscar_mascotas(self, filtro: FiltroMascotas) -> tuple[list[Mascota], int]:
        """Filtros, orden y paginación en SQL (Fase 4.2, P1).

        La consulta pagina en el servidor y trae el total con `COUNT(*) OVER ()`
        en lugar de materializar el catálogo entero para descartar la mayor
        parte en Python. Solo la página pedida carga sus tablas hijas.
        """
        distrito_mascota = aliased(db.Distrito)
        distrito_refugio = aliased(db.Distrito)
        # `_mascota()` toma el distrito de la mascota y, si falta, del refugio.
        distrito_efectivo = func.coalesce(
            func.nullif(distrito_mascota.nombre, ""), distrito_refugio.nombre, ""
        )
        # `_mascota()` convierte `edad` NULL en 0.0.
        edad = func.coalesce(db.Mascota.edad, 0)

        def bandera_derivada(columna, *patrones):
            """Columna si está definida; si es NULL, se deriva de `mascota_salud`."""
            derivada = exists(
                select(1).where(
                    db.MascotaSalud.mascota_id == db.Mascota.id,
                    or_(*(db.MascotaSalud.texto.like(patron) for patron in patrones)),
                )
            )
            return or_(columna == True, and_(columna.is_(None), derivada))  # noqa: E712

        condiciones = []
        if filtro.estado != "todos":
            condiciones.append(db.Mascota.estado == filtro.estado)

        texto = (filtro.q or "").strip()
        if texto:
            patron = f"%{_escapar_like(texto)}%"
            condiciones.append(
                or_(
                    *(
                        collate(columna, COLACION_BUSQUEDA).like(patron, "\\")
                        for columna in (
                            db.Mascota.nombre,
                            db.Mascota.raza,
                            db.Mascota.etiqueta,
                            db.Mascota.lugar,
                        )
                    )
                )
            )

        if filtro.especie:
            condiciones.append(db.Mascota.especie == filtro.especie)
        if filtro.distrito:
            condiciones.append(
                collate(distrito_efectivo, COLACION_BUSQUEDA) == filtro.distrito
            )
        if filtro.tamano:
            condiciones.append(db.Mascota.tamano == filtro.tamano)
        if filtro.sexo:
            condiciones.append(db.Mascota.sexo == filtro.sexo)
        if filtro.edad == "cachorro":
            condiciones.append(edad < 1)
        elif filtro.edad == "joven":
            condiciones.append(and_(edad >= 1, edad < 3))
        elif filtro.edad == "adulto":
            condiciones.append(and_(edad >= 3, edad <= 7))
        elif filtro.edad == "senior":
            condiciones.append(edad > 7)
        if filtro.refugio_id:
            condiciones.append(db.Mascota.refugio_id == filtro.refugio_id)
        if filtro.solo_esterilizados:
            condiciones.append(
                bandera_derivada(db.Mascota.esterilizado, "%esterilizad%")
            )
        if filtro.solo_vacunados:
            condiciones.append(
                bandera_derivada(
                    db.Mascota.vacunado, "%vacunad%", "%vacunas%"
                )
            )
        if filtro.solo_urgentes:
            condiciones.append(db.Mascota.urgente == True)  # noqa: E712

        if filtro.orden == "urgent":
            orden = (db.Mascota.urgente.desc(), db.Mascota.id.asc())
        elif filtro.orden == "youngest":
            orden = (edad.asc(), db.Mascota.id.asc())
        elif filtro.orden == "oldest":
            orden = (edad.desc(), db.Mascota.id.asc())
        else:
            orden = (db.Mascota.id.desc(),)

        base = (
            select(db.Mascota.id)
            .join(db.Refugio, db.Mascota.refugio_id == db.Refugio.id)
            .outerjoin(distrito_mascota, db.Mascota.distrito_id == distrito_mascota.id)
            .outerjoin(distrito_refugio, db.Refugio.distrito_id == distrito_refugio.id)
            .where(*condiciones)
        )
        # `COUNT(*) OVER ()` evita una consulta extra de total; los joins son
        # 1:1 (refugio y distrito), así que no duplican filas.
        consulta = (
            select(db.Mascota, func.count().over().label("total"))
            .join(db.Refugio, db.Mascota.refugio_id == db.Refugio.id)
            .outerjoin(distrito_mascota, db.Mascota.distrito_id == distrito_mascota.id)
            .outerjoin(distrito_refugio, db.Refugio.distrito_id == distrito_refugio.id)
            .where(*condiciones)
            .options(*self._opciones_mascota())
            .order_by(*orden)
            .offset((filtro.page - 1) * filtro.limit)
            .limit(filtro.limit)
        )

        with self._sesion() as sesion:
            distritos = self._mapa_distritos(sesion)
            filas = sesion.execute(consulta).all()
            if not filas:
                # Página fuera de rango: solo hace falta el total.
                total = int(
                    sesion.scalar(select(func.count()).select_from(base.subquery()))
                    or 0
                )
                return [], total
            total = int(filas[0][1])
            return [self._mascota(fila[0], distritos) for fila in filas], total

    def obtener_mascota(self, mascota_id: int) -> Mascota | None:
        with self._sesion() as sesion:
            fila = sesion.scalar(
                select(db.Mascota)
                .options(*self._opciones_mascota())
                .where(db.Mascota.id == mascota_id)
            )
            if fila is None:
                return None
            return self._mascota(fila, self._mapa_distritos(sesion))

    def _aplicar_mascota(
        self, fila: db.Mascota, mascota: Mascota, distrito_id: int | None
    ) -> None:
        fila.refugio_id = mascota.refugio_id
        fila.nombre = mascota.nombre
        fila.nombre_corto = mascota.nombre_corto or None
        fila.especie = mascota.especie
        fila.raza = mascota.raza or None
        fila.sexo = mascota.sexo
        fila.edad = _decimal(mascota.edad_anios)
        fila.tamano = mascota.tamano
        fila.descripcion = mascota.descripcion or None
        fila.estado = mascota.estado
        fila.foto_principal = mascota.foto or None
        fila.foto_alt = mascota.alt or None
        fila.peso_kg = _decimal(mascota.peso_kg)
        fila.lugar = mascota.lugar or None
        fila.etiqueta = mascota.etiqueta or None
        fila.etiqueta_icono = mascota.etiqueta_icono or None
        fila.etiqueta_clase = mascota.etiqueta_clase or None
        fila.energia = mascota.energia or None
        fila.urgente = mascota.urgente
        fila.vacunado = mascota.vacunado
        fila.esterilizado = mascota.esterilizado
        fila.distrito_id = distrito_id
        fila.actualizado_en = ahora_utc()

        fila.salud = [
            db.MascotaSalud(orden=indice, texto=item.texto, ok=item.ok)
            for indice, item in enumerate(mascota.salud)
        ]
        fila.fotos = [
            db.MascotaFoto(orden=indice, url=foto.src, alt=foto.alt or None)
            for indice, foto in enumerate(mascota.galeria)
        ]
        fila.rasgos = [
            db.MascotaRasgo(
                orden=indice,
                rasgo=rasgo.texto,
                icono=rasgo.icono or None,
                clase=rasgo.clase or None,
                icono_clase=rasgo.icono_clase or None,
            )
            for indice, rasgo in enumerate(mascota.rasgos)
        ]

    def crear_mascota(self, mascota: Mascota) -> Mascota:
        with self._sesion() as sesion:
            distrito_id = self._id_distrito(sesion, mascota.distrito)
            fila = db.Mascota(creado_en=ahora_utc())
            self._aplicar_mascota(fila, mascota, distrito_id)
            sesion.add(fila)
            sesion.commit()
            nuevo_id = fila.id
        creada = self.obtener_mascota(nuevo_id)
        if creada is None:
            raise NotFoundError("La mascota recién creada no se pudo leer.")
        return creada

    def actualizar_mascota(self, mascota: Mascota) -> Mascota:
        with self._sesion() as sesion:
            fila = sesion.scalar(
                select(db.Mascota)
                .options(*self._opciones_mascota())
                .where(db.Mascota.id == mascota.id)
            )
            if fila is None:
                raise NotFoundError("Mascota no encontrada.", {"mascotaId": mascota.id})
            self._aplicar_mascota(
                fila, mascota, self._id_distrito(sesion, mascota.distrito)
            )
            sesion.commit()
        actualizada = self.obtener_mascota(mascota.id)
        if actualizada is None:
            raise NotFoundError("Mascota no encontrada.", {"mascotaId": mascota.id})
        return actualizada

    def eliminar_mascota(self, mascota_id: int) -> None:
        with self._sesion() as sesion:
            fila = sesion.get(db.Mascota, mascota_id)
            if fila is None:
                raise NotFoundError("Mascota no encontrada.", {"mascotaId": mascota_id})
            sesion.delete(fila)
            try:
                sesion.commit()
            except IntegrityError as error:
                sesion.rollback()
                raise ConflictError(
                    "MASCOTA_CON_SOLICITUDES",
                    "No se puede eliminar una mascota con solicitudes registradas.",
                    {"mascotaId": mascota_id},
                ) from error

    # -- Refugios ---------------------------------------------------------
    def listar_refugios(self) -> list[Refugio]:
        with self._sesion() as sesion:
            distritos = self._mapa_distritos(sesion)
            filas = sesion.scalars(
                select(db.Refugio)
                .options(selectinload(db.Refugio.especies))
                # Orden editorial (D-035); los refugios sin `orden` van al final.
                .order_by(
                    func.coalesce(db.Refugio.orden, 999),
                    db.Refugio.nombre,
                )
            ).all()
            return [self._refugio(fila, distritos) for fila in filas]

    def obtener_refugio(self, refugio_id: str) -> Refugio | None:
        with self._sesion() as sesion:
            fila = sesion.scalar(
                select(db.Refugio)
                .options(selectinload(db.Refugio.especies))
                .where(db.Refugio.id == refugio_id)
            )
            if fila is None:
                return None
            return self._refugio(fila, self._mapa_distritos(sesion))

    # -- Estadísticas -----------------------------------------------------
    def resumen_impacto(self) -> dict[str, object]:
        """Agregados del impacto en 4 consultas, sin materializar entidades.

        Sustituye a `listar_mascotas()` + `listar_refugios()` (Fase 4.2, P3):
        antes se cargaban 16 mascotas con sus tablas hijas y 9 refugios para
        contar en Python.
        """
        disponible = db.Mascota.estado == "disponible"
        with self._sesion() as sesion:
            (
                total_refugios,
                total_adoptadas,
                total_en_acogida,
                total_distritos,
            ) = sesion.execute(
                select(
                    func.count(db.Refugio.id),
                    func.coalesce(func.sum(db.Refugio.adoptadas_historicas), 0),
                    func.coalesce(func.sum(db.Refugio.en_acogida_actual), 0),
                    func.count(func.distinct(db.Refugio.distrito_id)),
                )
            ).one()

            (
                total_mascotas,
                total_perros,
                total_gatos,
            ) = sesion.execute(
                select(
                    func.coalesce(func.sum(case((disponible, 1), else_=0)), 0),
                    func.coalesce(
                        func.sum(case((and_(disponible, db.Mascota.especie == "perro"), 1), else_=0)),
                        0,
                    ),
                    func.coalesce(
                        func.sum(case((and_(disponible, db.Mascota.especie == "gato"), 1), else_=0)),
                        0,
                    ),
                )
            ).one()

            filas = sesion.execute(
                select(db.Refugio.distrito_id, func.coalesce(func.sum(db.Refugio.adoptadas_historicas), 0))
                .group_by(db.Refugio.distrito_id)
            ).all()
            # Mapear distrito_id -> nombre para el dict por distrito.
            distritos = self._mapa_distritos(sesion)
            por_distrito: dict[str, int] = {}
            for distrito_id, adoptadas in filas:
                nombre = distritos.get(distrito_id or 0, str(distrito_id))
                por_distrito[nombre] = por_distrito.get(nombre, 0) + int(adoptadas or 0)

        return {
            "total_mascotas": int(total_mascotas),
            "total_perros": int(total_perros),
            "total_gatos": int(total_gatos),
            "total_refugios": int(total_refugios),
            "total_adoptadas": int(total_adoptadas),
            "total_en_acogida": int(total_en_acogida),
            "total_distritos": int(total_distritos),
            "adoptadas_por_distrito": dict(sorted(por_distrito.items())),
        }

    def listar_mascotas_por_ids(self, ids: list[int]) -> list[Mascota]:
        """Devuelve mascotas por lista de IDs, ordenadas id-asc.

        Usa WHERE id IN (...) para traer solo las solicitadas.
        Orden id-asc para mantener consistencia con listar_mascotas().
        """
        with self._sesion() as sesion:
            filas = sesion.scalars(
                select(db.Mascota)
                .where(db.Mascota.id.in_(ids))
                .order_by(db.Mascota.id.asc())
            ).all()
            distritos = self._mapa_distritos(sesion)
            return [self._mascota(fila, distritos) for fila in filas]

    def listar_mascotas_de_refugio(self, refugio_id: str, *, estado: str = "todos") -> list[Mascota]:
        """Mascotas de un refugio, con filtro de estado opcional.

        Orden id-asc para consistencia.
        """
        with self._sesion() as sesion:
            q = select(db.Mascota).where(db.Mascota.refugio_id == refugio_id)
            if estado != "todos":
                q = q.where(db.Mascota.estado == estado)
            q = q.order_by(db.Mascota.id.asc())
            filas = sesion.scalars(q).all()
            distritos = self._mapa_distritos(sesion)
            return [self._mascota(fila, distritos) for fila in filas]

    def estadisticas_mascotas(self) -> dict[str, object]:
        """Agregaciones completas en SQL Server, sin materializar 16 mascotas.

        Devuelve el mismo dict que estadisticas_mascotas() de memory repo.
        El campo `adoptadas` y `en_acogida` cuentan sobre TODAS las mascotas,
        no solo las disponibles (coincide con el mapper.stats_mascotas).
        """
        with self._sesion() as sesion:
            # Total de mascotas registradas (todos los estados)
            total_registradas = sesion.scalar(
                select(func.coalesce(func.count(db.Mascota.id), 0))
            )

            # Contadores sobre TODAS las mascotas (para adoptadas/en_acogida/urgentes)
            (total_mascotas, total_adoptadas, total_en_acogida, total_urgentes) = sesion.execute(
                select(
                    func.coalesce(func.count(db.Mascota.id), 0),
                    func.coalesce(
                        func.sum(case((db.Mascota.estado == "adoptada", 1), else_=0)),
                        0,
                    ),
                    func.coalesce(
                        func.sum(case((db.Mascota.estado == "en_acogida", 1), else_=0)),
                        0,
                    ),
                    func.coalesce(
                        func.sum(case((db.Mascota.urgente == True, 1), else_=0)),
                        0,
                    ),
                )
            ).one()

            # Count disponibles separately for the "total/disponibles" fields
            disponible = db.Mascota.estado == "disponible"
            disponibles_count = sesion.scalar(
                select(func.coalesce(func.count(db.Mascota.id), 0)).where(disponible)
            )

            # edad promedio sobre disponibles
            edad_promedio = sesion.scalar(
                select(func.coalesce(func.avg(db.Mascota.edad), 0)).where(disponible)
            )

            # por_especie: count over ALL mascotas (como memory repo)
            especie_rows = sesion.execute(
                select(db.Mascota.especie, func.count(db.Mascota.id)).group_by(db.Mascota.especie)
            ).all()
            por_especie: dict[str, int] = {str(row[0]): int(row[1]) for row in especie_rows}

            # por_distrito: contar mascotas POR DISTRITO (como el old mapper.stats_mascotas)
            # cuenta mascotas por valor de mascota.distrito, no por refugio.adoptadas
            por_distrito_rows = sesion.execute(
                select(db.Mascota.distrito_id, func.count(db.Mascota.id))
                .group_by(db.Mascota.distrito_id)
            ).all()
            mapa_distritos = self._mapa_distritos(sesion)
            por_distrito: dict[str, int] = {}
            for distrito_id, count in por_distrito_rows:
                nombre = mapa_distritos.get(distrito_id or 0, str(distrito_id or ""))
                por_distrito[nombre] = por_distrito.get(nombre, 0) + int(count or 0)

            # por_tamano: count over ALL mascotas
            tamano_rows = sesion.execute(
                select(db.Mascota.tamano, func.count(db.Mascota.id)).group_by(db.Mascota.tamano)
            ).all()
            por_tamano: dict[str, int] = {}
            for tamano, count in tamano_rows:
                por_tamano[tamano or "Mediano"] = por_tamano.get(tamano or "Mediano", 0) + int(count or 0)

            total_refugios = int(sesion.scalar(select(func.count(db.Refugio.id))))

        total = int(disponibles_count or 0)

        return {
            "total": total,
            "total_registradas": int(total_registradas),
            "disponibles": total,
            "adoptadas": int(total_adoptadas),
            "en_acogida": int(total_en_acogida),
            "urgentes": int(total_urgentes),
            "total_refugios": total_refugios,
            "edad_promedio": round(float(edad_promedio), 2) if edad_promedio else 0.0,
            "por_especie": por_especie,
            "por_distrito": dict(sorted(por_distrito.items())),
            "por_tamano": dict(sorted(por_tamano.items())),
        }

    # -- Contenido --------------------------------------------------------
    def obtener_contenido(self) -> Contenido:
        with self._sesion() as sesion:
            pasos = sesion.scalars(
                select(db.ContenidoPaso).order_by(db.ContenidoPaso.orden)
            ).all()
            faqs = sesion.scalars(
                select(db.ContenidoFaq).order_by(db.ContenidoFaq.orden)
            ).all()

        def paso(fila: db.ContenidoPaso) -> dict[str, str]:
            return {
                "icono": fila.icono or "",
                "titulo": fila.titulo,
                "texto": fila.descripcion or "",
                "nota": fila.nota or "",
            }

        return Contenido(
            pasos_adopcion=[paso(fila) for fila in pasos if fila.tipo == "adopcion"],
            pasos_refugio=[paso(fila) for fila in pasos if fila.tipo == "refugio"],
            faqs=[
                {"pregunta": fila.pregunta, "respuesta": fila.respuesta}
                for fila in faqs
            ],
            requisitos=[paso(fila) for fila in pasos if fila.tipo == "requisito"],
        )

    def obtener_detalle(self, mascota_id: int) -> DetalleMascota | None:
        with self._sesion() as sesion:
            historia = sesion.scalars(
                select(db.MascotaHistoria)
                .where(db.MascotaHistoria.mascota_id == mascota_id)
                .order_by(db.MascotaHistoria.orden)
            ).all()
            cuidados = sesion.scalars(
                select(db.MascotaCuidado)
                .where(db.MascotaCuidado.mascota_id == mascota_id)
                .order_by(db.MascotaCuidado.orden)
            ).all()
            mascota = sesion.get(db.Mascota, mascota_id)

        cita = None
        if mascota is not None and mascota.cita_texto:
            cita = {
                "texto": mascota.cita_texto,
                "autor": mascota.cita_autor or "",
            }
        if not historia and not cuidados and cita is None:
            return None
        return DetalleMascota(
            historia=[fila.texto for fila in historia],
            cuidados=[
                {"icono": fila.icono, "titulo": fila.titulo, "texto": fila.texto}
                for fila in cuidados
            ],
            rasgos=[],
            cita=cita,
        )

    # -- Usuarios ---------------------------------------------------------
    def _usuario_por(self, campo, valor) -> Usuario | None:
        with self._sesion() as sesion:
            fila = sesion.scalar(select(db.Usuario).where(campo == valor))
            if fila is None:
                return None
            return self._usuario(fila, self._mapa_distritos(sesion))

    def obtener_usuario(self, usuario_id: int) -> Usuario | None:
        with self._sesion() as sesion:
            fila = sesion.get(db.Usuario, usuario_id)
            if fila is None:
                return None
            return self._usuario(fila, self._mapa_distritos(sesion))

    def buscar_usuario_por_email(self, email: str) -> Usuario | None:
        with self._sesion() as sesion:
            fila = sesion.scalar(
                select(db.Usuario).where(
                    func.lower(db.Usuario.email) == email.strip().lower()
                )
            )
            if fila is None:
                return None
            return self._usuario(fila, self._mapa_distritos(sesion))

    def buscar_usuario_por_dni(self, dni: str) -> Usuario | None:
        with self._sesion() as sesion:
            fila = sesion.scalar(select(db.Usuario).where(db.Usuario.dni == dni))
            if fila is None:
                return None
            return self._usuario(fila, self._mapa_distritos(sesion))

    def listar_usuarios(self) -> list[Usuario]:
        with self._sesion() as sesion:
            distritos = self._mapa_distritos(sesion)
            filas = sesion.scalars(select(db.Usuario)).all()
            return [self._usuario(fila, distritos) for fila in filas]

    def crear_usuario(self, usuario: Usuario) -> Usuario:
        with self._sesion() as sesion:
            fila = db.Usuario(
                nombres=usuario.nombre,
                email=usuario.email,
                dni=usuario.dni,
                password_hash=usuario.password_hash,
                google_id=usuario.google_id,
                rol=usuario.rol,
                telefono=usuario.telefono,
                distrito_id=self._id_distrito(sesion, usuario.distrito),
                refugio_id=usuario.refugio_id,
                activo=usuario.activo,
                creado_en=usuario.creado_en,
            )
            sesion.add(fila)
            try:
                sesion.commit()
            except IntegrityError as error:
                sesion.rollback()
                texto = str(error.orig)
                if "UX_usuarios_email" in texto:
                    raise ConflictError(
                        "EMAIL_YA_REGISTRADO",
                        "Ya existe una cuenta con ese correo.",
                    ) from error
                if "UX_usuarios_dni" in texto:
                    raise ConflictError(
                        "DNI_YA_REGISTRADO", "Ya existe una cuenta con ese DNI."
                    ) from error
                raise ConflictError(
                    "USUARIO_DUPLICADO", "Los datos ya están registrados."
                ) from error
            nuevo_id = fila.id
        creado = self.obtener_usuario(nuevo_id)
        if creado is None:
            raise NotFoundError("El usuario recién creado no se pudo leer.")
        return creado

    # -- Solicitudes ------------------------------------------------------
    def _opciones_solicitud(self):
        return (
            selectinload(db.Solicitud.citas),
            selectinload(db.Solicitud.mensajes),
            selectinload(db.Solicitud.seguimiento),
        )

    def listar_solicitudes(self) -> list[Solicitud]:
        with self._sesion() as sesion:
            usuarios = self._mapa_usuarios(sesion)
            filas = sesion.scalars(
                select(db.Solicitud)
                .options(*self._opciones_solicitud())
                .order_by(db.Solicitud.id)
            ).all()
            return [self._solicitud(fila, usuarios) for fila in filas]

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
        """Visibilidad, estado, orden y paginación en SQL (Fase 4.2, P6)."""
        condiciones = []
        if rol != "admin":
            if rol == "refugio" and refugio_id:
                condiciones.append(
                    or_(
                        db.Solicitud.usuario_id == usuario_id,
                        db.Mascota.refugio_id == refugio_id,
                    )
                )
            else:
                condiciones.append(db.Solicitud.usuario_id == usuario_id)
        if estado != "todos":
            condiciones.append(db.Solicitud.estado == estado)
        elif not incluir_canceladas:
            condiciones.append(db.Solicitud.estado != "cancelada")

        base_conteo = (
            select(db.Solicitud.id)
            .outerjoin(db.Mascota, db.Solicitud.mascota_id == db.Mascota.id)
            .where(*condiciones)
        )
        # `COUNT(*) OVER ()` aporta el total sin una consulta extra.
        consulta = (
            select(db.Solicitud, func.count().over().label("total"))
            .outerjoin(db.Mascota, db.Solicitud.mascota_id == db.Mascota.id)
            .where(*condiciones)
            .options(*self._opciones_solicitud())
            .order_by(db.Solicitud.creado_en.desc(), db.Solicitud.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        with self._sesion() as sesion:
            filas = sesion.execute(consulta).all()
            if not filas:
                total = int(
                    sesion.scalar(select(func.count()).select_from(base_conteo.subquery()))
                    or 0
                )
                return [], total
            usuarios = self._mapa_usuarios(sesion)
            total = int(filas[0][1])
            return [self._solicitud(fila[0], usuarios) for fila in filas], total

    def obtener_solicitud(self, solicitud_id: int) -> Solicitud | None:
        with self._sesion() as sesion:
            fila = sesion.scalar(
                select(db.Solicitud)
                .options(*self._opciones_solicitud())
                .where(db.Solicitud.id == solicitud_id)
            )
            if fila is None:
                return None
            return self._solicitud(fila, self._mapa_usuarios(sesion))

    def crear_solicitud(self, solicitud: Solicitud) -> Solicitud:
        with self._sesion() as sesion:
            refugio_id = sesion.scalar(
                select(db.Mascota.refugio_id).where(
                    db.Mascota.id == solicitud.mascota_id
                )
            )
            if refugio_id is None:
                raise NotFoundError(
                    "Mascota no encontrada.", {"mascotaId": solicitud.mascota_id}
                )
            fila = db.Solicitud(
                codigo=f"TMP-{uuid.uuid4().hex[:20]}",
                usuario_id=solicitud.usuario_id,
                mascota_id=solicitud.mascota_id,
                refugio_id=refugio_id,
                estado=solicitud.estado,
                etapa=solicitud.etapa,
                creado_en=solicitud.creada_en,
                actualizado_en=solicitud.actualizada_en,
            )
            sesion.add(fila)
            try:
                sesion.flush()
            except IntegrityError as error:
                sesion.rollback()
                raise ConflictError(
                    "SOLICITUD_DUPLICADA",
                    "Ya tienes una postulación activa para esta mascota.",
                ) from error

            fila.codigo = codigo_solicitud(fila.id, fila.creado_en.year)
            if solicitud.mensaje is not None:
                sesion.add(
                    db.Mensaje(
                        solicitud_id=fila.id,
                        autor_id=_autor_id_mensaje(solicitud.mensaje),
                        texto=solicitud.mensaje.texto,
                        creado_en=solicitud.creada_en,
                    )
                )
            if solicitud.cita is not None:
                sesion.add(
                    db.Cita(
                        solicitud_id=fila.id,
                        fecha_hora=_parsear_fecha(solicitud.cita.fecha),
                        lugar=solicitud.cita.direccion or None,
                        notas=solicitud.cita.fecha or None,
                        coordinadora=solicitud.cita.coordinadora or None,
                        creado_en=solicitud.creada_en,
                    )
                )
            sesion.add(db.SolicitudEvento(solicitud_id=fila.id, etapa=solicitud.etapa))
            sesion.commit()
            nuevo_id = fila.id
        creada = self.obtener_solicitud(nuevo_id)
        if creada is None:
            raise NotFoundError("La solicitud recién creada no se pudo leer.")
        return creada

    def _tamano_archivo(self, archivo: str) -> int:
        if self._uploads is not None:
            nombre = archivo.rsplit("/", 1)[-1]
            ruta = self._uploads / nombre
            if ruta.is_file():
                return max(1, ruta.stat().st_size)
        return 1

    def actualizar_solicitud(self, solicitud: Solicitud) -> Solicitud:
        with self._sesion() as sesion:
            fila = sesion.scalar(
                select(db.Solicitud)
                .options(*self._opciones_solicitud())
                .where(db.Solicitud.id == solicitud.id)
            )
            if fila is None:
                raise NotFoundError(
                    "Solicitud no encontrada.", {"solicitudId": solicitud.id}
                )

            etapa_previa = fila.etapa
            fila.estado = solicitud.estado
            fila.etapa = solicitud.etapa
            fila.motivo_cancelacion = solicitud.motivo_cancelacion
            fila.actualizado_en = solicitud.actualizada_en or ahora_utc()

            if solicitud.etapa != etapa_previa:
                sesion.add(
                    db.SolicitudEvento(solicitud_id=fila.id, etapa=solicitud.etapa)
                )

            if solicitud.mensaje is not None:
                ultimo = sesion.scalar(
                    select(db.Mensaje)
                    .where(db.Mensaje.solicitud_id == fila.id)
                    .order_by(db.Mensaje.creado_en.desc(), db.Mensaje.id.desc())
                    .limit(1)
                )
                if ultimo is None or ultimo.texto != solicitud.mensaje.texto:
                    sesion.add(
                        db.Mensaje(
                            solicitud_id=fila.id,
                            autor_id=_autor_id_mensaje(solicitud.mensaje),
                            texto=solicitud.mensaje.texto,
                            creado_en=ahora_utc(),
                        )
                    )

            if solicitud.cita is not None:
                ultima = sesion.scalar(
                    select(db.Cita)
                    .where(db.Cita.solicitud_id == fila.id)
                    .order_by(db.Cita.creado_en.desc(), db.Cita.id.desc())
                    .limit(1)
                )
                if ultima is None or (
                    ultima.lugar,
                    ultima.notas,
                ) != (solicitud.cita.direccion, solicitud.cita.fecha):
                    sesion.add(
                        db.Cita(
                            solicitud_id=fila.id,
                            fecha_hora=_parsear_fecha(solicitud.cita.fecha),
                            lugar=solicitud.cita.direccion or None,
                            notas=solicitud.cita.fecha or None,
                            coordinadora=solicitud.cita.coordinadora or None,
                            creado_en=ahora_utc(),
                        )
                    )

            existentes = sesion.scalar(
                select(func.count())
                .select_from(db.SeguimientoFoto)
                .where(db.SeguimientoFoto.solicitud_id == fila.id)
            )
            for indice, foto in enumerate(solicitud.seguimiento):
                if indice < (existentes or 0):
                    continue
                sesion.add(
                    db.SeguimientoFoto(
                        solicitud_id=fila.id,
                        # `CK_seguimiento_fotos_mes` solo admite 1, 3 y 6.
                        mes=MESES_SEGUIMIENTO[min(indice, len(MESES_SEGUIMIENTO) - 1)],
                        archivo=foto.src,
                        mime=mimetypes.guess_type(foto.src)[0] or "image/jpeg",
                        tamano_bytes=self._tamano_archivo(foto.src),
                        comentario=foto.alt or None,
                        creado_en=ahora_utc(),
                    )
                )

            sesion.commit()
        actualizada = self.obtener_solicitud(solicitud.id)
        if actualizada is None:
            raise NotFoundError(
                "Solicitud no encontrada.", {"solicitudId": solicitud.id}
            )
        return actualizada

    def finalizar_solicitud(self, solicitud: Solicitud, usuario: Usuario) -> Solicitud:
        """Finaliza la adopción con un orden de bloqueo determinista (A-15).

        Orden: mascota -> solicitudes de esa mascota en id ascendente -> hijos.
        Así dos finalizaciones sobre solicitudes distintas de la misma mascota
        no forman el ciclo que produjo el deadlock 1205 del `COUNT` anterior.
        Si SQL Server aborta una víctima, se reintenta una sola vez la
        transacción completa y solo cuando todavía no hubo `commit`.
        """
        for intento in range(REINTENTOS_DEADLOCK + 1):
            confirmacion = [False]
            try:
                return self._finalizar_solicitud_intento(
                    solicitud, usuario, confirmacion
                )
            except Exception as exc:
                codigo = _codigo_transitorio_sqlserver(exc)
                if codigo is None:
                    raise
                if confirmacion[0]:
                    # Ya hubo commit: repetir podría duplicar eventos/mensajes.
                    raise TransitorioError() from exc
                if intento >= REINTENTOS_DEADLOCK:
                    raise TransitorioError() from exc
                logger.warning(
                    "Error transitorio %s al finalizar solicitud %s; reintentando (%s/%s)",
                    codigo,
                    solicitud.id,
                    intento + 1,
                    REINTENTOS_DEADLOCK,
                )
        raise TransitorioError()  # pragma: no cover

    def _finalizar_solicitud_intento(
        self,
        solicitud: Solicitud,
        usuario: Usuario,
        confirmacion: list[bool],
    ) -> Solicitud:
        """Un intento: una sola transacción y un solo commit."""
        with self._sesion() as sesion:
            # 1) Lectura inicial sin HOLDLOCK: solo el id de mascota. Se lee
            #    una columna (no la entidad) para no fijar una versión obsoleta
            #    en el identity map antes de adquirir los candados.
            mascota_id = sesion.scalar(
                select(db.Solicitud.mascota_id).where(db.Solicitud.id == solicitud.id)
            )
            if mascota_id is None:
                raise NotFoundError(
                    "Solicitud no encontrada.", {"solicitudId": solicitud.id}
                )

            # 2) Primer bloqueo real: la mascota. Serializa las finalizaciones
            #    de una misma mascota y bloquea nuevas solicitudes (FK hija).
            mascota = sesion.scalar(
                select(db.Mascota)
                .with_hint(db.Mascota, "WITH (UPDLOCK, HOLDLOCK)")
                .where(db.Mascota.id == mascota_id)
            )
            if mascota is None:
                raise NotFoundError(
                    "Mascota no encontrada.", {"mascotaId": mascota_id}
                )

            # 3) Segundo bloqueo: todas las solicitudes de la mascota en id
            #    ascendente. Se evita el COUNT con HOLDLOCK que formaba el ciclo.
            ids = list(
                sesion.scalars(
                    select(db.Solicitud.id)
                    .where(db.Solicitud.mascota_id == mascota.id)
                    .order_by(db.Solicitud.id)
                ).all()
            )
            ids = sorted(set(ids) | {solicitud.id})
            filas = {
                actual_id: sesion.scalar(
                    select(db.Solicitud)
                    .with_hint(db.Solicitud, "WITH (UPDLOCK, HOLDLOCK)")
                    .where(db.Solicitud.id == actual_id)
                )
                for actual_id in ids
            }
            fila = filas[solicitud.id]
            if fila is None:
                raise NotFoundError(
                    "Solicitud no encontrada.", {"solicitudId": solicitud.id}
                )
            if fila.mascota_id != mascota.id:
                raise ConflictError(
                    "SOLICITUD_INCONSISTENTE",
                    "La solicitud no pertenece a la mascota indicada.",
                    {"solicitudId": fila.id, "mascotaId": mascota.id},
                )

            if usuario.rol not in {"refugio", "admin"}:
                raise ForbiddenError(
                    "Solo el refugio o un administrador puede finalizar una adopción."
                )
            if usuario.rol == "refugio" and usuario.refugio_id != mascota.refugio_id:
                raise ForbiddenError(
                    "Solo el refugio de la mascota puede finalizar esta adopción."
                )

            if fila.estado == "cancelada":
                raise ConflictError(
                    "SOLICITUD_CANCELADA", "La postulación fue cancelada."
                )

            otras_activas = sum(
                1
                for actual_id, otra in filas.items()
                if actual_id != fila.id and otra.estado == "activa"
            )
            if otras_activas:
                raise ConflictError(
                    "ADOPCION_EN_CURSO",
                    "Existen otras postulaciones activas para esta mascota; "
                    "resuélvelas antes de finalizar la adopción.",
                    {
                        "mascotaId": fila.mascota_id,
                        "solicitudesActivas": otras_activas,
                    },
                )

            if fila.estado == "completada" and fila.etapa >= 5:
                if mascota.estado != "adoptada":
                    raise ConflictError(
                        "SOLICITUD_INCONSISTENTE",
                        "La solicitud está completada pero la mascota no está adoptada.",
                        {"mascotaId": fila.mascota_id},
                    )
                return self._solicitud(fila, self._mapa_usuarios(sesion))

            if fila.etapa >= 5:
                raise ConflictError(
                    "SOLICITUD_INCONSISTENTE",
                    "La solicitud está en etapa final pero no está completada.",
                    {"solicitudId": fila.id},
                )

            cambiada = sesion.execute(
                update(db.Mascota)
                .where(
                    db.Mascota.id == mascota.id,
                    db.Mascota.estado == "disponible",
                )
                .values(estado="adoptada", actualizado_en=ahora_utc())
            )
            if cambiada.rowcount != 1:
                raise ConflictError(
                    "MASCOTA_NO_DISPONIBLE",
                    "Esta mascota ya no está disponible para adopción.",
                    {"mascotaId": mascota.id, "estado": mascota.estado},
                )

            etapa_previa = fila.etapa
            fila.etapa = 5
            fila.estado = "completada"
            fila.actualizado_en = solicitud.actualizada_en or ahora_utc()

            if etapa_previa != 5:
                sesion.add(db.SolicitudEvento(solicitud_id=fila.id, etapa=5))

            texto = solicitud.mensaje.texto if solicitud.mensaje else None
            if texto:
                ultimo = sesion.scalar(
                    select(db.Mensaje)
                    .where(db.Mensaje.solicitud_id == fila.id)
                    .order_by(db.Mensaje.creado_en.desc(), db.Mensaje.id.desc())
                    .limit(1)
                )
                if ultimo is None or ultimo.texto != texto:
                    sesion.add(
                        db.Mensaje(
                            solicitud_id=fila.id,
                            # A-14: autor autenticado real, nunca el adoptante inferido.
                            autor_id=_autor_id_mensaje(solicitud.mensaje),
                            texto=texto,
                            creado_en=ahora_utc(),
                        )
                    )

            sesion.commit()
            confirmacion[0] = True
            finalizada = self._solicitud(fila, self._mapa_usuarios(sesion))
        return finalizada

    # -- Favoritos --------------------------------------------------------
    def listar_favoritos(self, usuario_id: int) -> list[Favorito]:
        with self._sesion() as sesion:
            filas = sesion.scalars(
                select(db.Favorito)
                .where(db.Favorito.usuario_id == usuario_id)
                .order_by(db.Favorito.creado_en)
            ).all()
            return [
                Favorito(
                    usuario_id=fila.usuario_id,
                    mascota_id=fila.mascota_id,
                    creado_en=fila.creado_en,
                )
                for fila in filas
            ]

    def listar_favoritos_mascotas(self, usuario_id: int) -> list[Mascota]:
        """Devuelve las mascotas favoritas de un usuario sin cargar todas las mascotas.

        Usa un JOIN directo entre favorito y mascota para traer solo las
        mascotas que son favoritas del usuario.
        """
        with self._sesion() as sesion:
            filas = sesion.execute(
                select(db.Mascota)
                .join(db.Favorito, db.Favorito.mascota_id == db.Mascota.id)
                .where(db.Favorito.usuario_id == usuario_id)
                .order_by(db.Mascota.id.asc())
            ).scalars().all()
            distritos = self._mapa_distritos(sesion)
            return [self._mascota(fila, distritos) for fila in filas]

    def crear_favorito(self, favorito: Favorito) -> Favorito:
        with self._sesion() as sesion:
            sesion.add(
                db.Favorito(
                    usuario_id=favorito.usuario_id,
                    mascota_id=favorito.mascota_id,
                    creado_en=favorito.creado_en,
                )
            )
            try:
                sesion.commit()
            except IntegrityError as error:
                sesion.rollback()
                raise ConflictError(
                    "FAVORITO_DUPLICADO",
                    "La mascota ya está en tus favoritos.",
                    {"mascotaId": favorito.mascota_id},
                ) from error
        return favorito

    def eliminar_favorito(self, usuario_id: int, mascota_id: int) -> bool:
        with self._sesion() as sesion:
            resultado = sesion.execute(
                delete(db.Favorito).where(
                    db.Favorito.usuario_id == usuario_id,
                    db.Favorito.mascota_id == mascota_id,
                )
            )
            sesion.commit()
            return bool(resultado.rowcount)

    # -- Alertas ----------------------------------------------------------
    def listar_alertas(self) -> list[AlertaRescate]:
        with self._sesion() as sesion:
            distritos = self._mapa_distritos(sesion)
            filas = sesion.scalars(
                select(db.AlertaRescate).order_by(
                    db.AlertaRescate.creado_en.desc(), db.AlertaRescate.id.desc()
                )
            ).all()
            return [self._alerta(fila, distritos) for fila in filas]

    def crear_alerta(self, alerta: AlertaRescate) -> AlertaRescate:
        with self._sesion() as sesion:
            fila = db.AlertaRescate(
                usuario_id=None,
                nombre=alerta.nombre,
                especie=alerta.especie,
                descripcion=alerta.mensaje or "",
                ubicacion=None,
                distrito_id=self._id_distrito(sesion, alerta.distrito),
                contacto=alerta.contacto,
                mensaje=alerta.mensaje,
                estado="atendida" if alerta.atendida else "nueva",
                creado_en=alerta.creado_en,
            )
            sesion.add(fila)
            sesion.commit()
            nuevo_id = fila.id
        with self._sesion() as sesion:
            creada = sesion.get(db.AlertaRescate, nuevo_id)
            if creada is None:
                raise NotFoundError("La alerta recién creada no se pudo leer.")
            return self._alerta(creada, self._mapa_distritos(sesion))
