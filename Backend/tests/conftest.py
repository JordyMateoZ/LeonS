from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters import ArchivoGuardado
from app.app import create_app
from app.container import create_dependencies


class StorageMemoriaTest:
    async def guardar(self, archivo, prefijo: str = "seguimiento") -> ArchivoGuardado:
        contenido = await archivo.read()
        return ArchivoGuardado(
            nombre=archivo.filename or "archivo.png",
            url=f"http://localhost/uploads/{archivo.filename or 'archivo.png'}",
            mime_type=archivo.content_type or "image/png",
            tamanio=len(contenido),
        )


class NotificacionesSilenciosas:
    async def correo(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        return None

    async def whatsapp(self, numero: str, mensaje: str) -> None:
        return None


@pytest.fixture
def client() -> TestClient:
    deps = create_dependencies(
        {
            "storage": StorageMemoriaTest(),
            "notificaciones": NotificacionesSilenciosas(),
        }
    )
    return TestClient(create_app(deps))


def token_demo(client: TestClient, email: str = "demo@leons.pe", password: str = "demo1234") -> str:
    respuesta = client.post(
        "/api/v1/auth/login",
        json={"identificador": email, "password": password},
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["data"]["token"]
