"""Adaptador de almacenamiento local para fotos de seguimiento."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from ..errors import ValidationError

EXTENSIONES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_BYTES = 5 * 1024 * 1024


class LocalStorage:
    """Guarda archivos en `uploads/` y devuelve la URL pública."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def guardar_imagen(self, nombre_original: str | None, content_type: str | None, contenido: bytes) -> str:
        if not contenido:
            raise ValidationError("ARCHIVO_VACIO", "El archivo está vacío.")
        if len(contenido) > MAX_BYTES:
            raise ValidationError("ARCHIVO_DEMASIADO_GRANDE", "La imagen supera los 5 MB.")

        tipo = (content_type or "").lower().split(";")[0].strip()
        extension = EXTENSIONES.get(tipo)
        if extension is None:
            raise ValidationError(
                "MIME_NO_SOPORTADO",
                "Solo se aceptan imágenes JPEG, PNG o WEBP.",
                {"contentType": content_type},
            )

        seguro = re.sub(r"[^a-zA-Z0-9._-]", "_", nombre_original or "foto")[:40]
        nombre = f"{uuid.uuid4().hex}-{seguro}{extension}"
        destino = (self.base_dir / nombre).resolve()
        if self.base_dir.resolve() not in destino.parents:
            raise ValidationError("RUTA_INVALIDA", "Nombre de archivo inválido.")

        destino.write_bytes(contenido)
        return f"/uploads/{nombre}"
