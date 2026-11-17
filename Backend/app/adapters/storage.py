from __future__ import annotations

import uuid
from pathlib import Path
from typing import Protocol

from fastapi import UploadFile

from app.config import settings


class ArchivoGuardado:
    def __init__(self, nombre: str, url: str, mime_type: str, tamanio: int):
        self.nombre = nombre
        self.url = url
        self.mime_type = mime_type
        self.tamanio = tamanio

    def model_dump(self) -> dict[str, object]:
        return {
            "nombre": self.nombre,
            "url": self.url,
            "mimeType": self.mime_type,
            "tamanio": self.tamanio,
        }


class StorageAdapter(Protocol):
    async def guardar(self, archivo: UploadFile, prefijo: str = "seguimiento") -> ArchivoGuardado: ...


class LocalStorageAdapter(StorageAdapter):
    async def guardar(self, archivo: UploadFile, prefijo: str = "seguimiento") -> ArchivoGuardado:
        directorio = settings.upload_dir_path
        directorio.mkdir(parents=True, exist_ok=True)

        nombre_original = Path(archivo.filename or "archivo").name
        extension = Path(nombre_original).suffix.lower() or ".bin"
        nombre = f"{prefijo}-{uuid.uuid4()}{extension}"
        contenido = await archivo.read()
        (directorio / nombre).write_bytes(contenido)

        return ArchivoGuardado(
            nombre=nombre_original,
            url=f"{settings.public_base_url.rstrip('/')}/uploads/{nombre}",
            mime_type=archivo.content_type or "application/octet-stream",
            tamanio=len(contenido),
        )
