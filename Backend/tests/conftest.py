from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.app import create_app
from app.config import BASE_DIR, Settings

SEED = BASE_DIR / "app" / "data" / "seed.json"


@pytest.fixture()
def app(tmp_path: Path):
    settings = Settings(
        app_env="test",
        jwt_secret="test-secret-con-mas-de-32-bytes-para-hs256",
        uploads_dir=tmp_path / "uploads",
        seed_path=SEED,
        repos_backend="memory",
        rate_limit_alerts_max=5,
        rate_limit_window_seconds=60,
    )
    return create_app(settings)


@pytest.fixture()
def client(app):
    with TestClient(app) as cliente:
        yield cliente


def autenticar(
    client: TestClient,
    identificador: str = "demo@leons.pe",
    password: str = "demo12345",
) -> dict[str, str]:
    respuesta = client.post(
        "/api/v1/auth/login",
        json={"identificador": identificador, "password": password},
    )
    assert respuesta.status_code == 200, respuesta.text
    token = respuesta.json()["token"]
    return {"Authorization": f"Bearer {token}"}
