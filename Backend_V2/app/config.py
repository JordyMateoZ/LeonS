from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Configuración por entorno. Ver Backend/.env.example."""

    app_name: str = "LeonS API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"

    jwt_secret: str = "dev-secret-change-me-en-produccion-32-bytes"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24

    cors_origins: list[str] = [
        "http://localhost:4200",
        "http://localhost:4000",
    ]

    repos_backend: Literal["memory", "sqlserver"] = "memory"
    db_url: str = ""
    db_test_url: str = ""

    uploads_dir: Path = BASE_DIR / "uploads"
    seed_path: Path = BASE_DIR / "app" / "data" / "seed.json"

    rate_limit_alerts_max: int = 5
    rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
