from __future__ import annotations

import re
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    port: int = Field(default=3001, gt=0)
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    public_base_url: str = "http://localhost:3001"
    cors_origin: str = "*"

    jwt_secret: str = "leons-dev-secret-cambiar-en-produccion"
    jwt_expires_in: str = "7d"
    google_client_id: str = ""

    upload_dir: str = "storage/uploads"

    rate_limit_window_ms: int = Field(default=900_000, gt=0)
    rate_limit_auth_max: int = Field(default=20, gt=0)
    rate_limit_alerts_max: int = Field(default=10, gt=0)

    @field_validator("api_prefix")
    @classmethod
    def _normalizar_prefix(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            return "/api/v1"
        return valor if valor.startswith("/") else f"/{valor}"

    @property
    def cors_origins(self) -> list[str]:
        if self.cors_origin.strip() == "*":
            return ["*"]
        return [origen.strip() for origen in self.cors_origin.split(",") if origen.strip()]

    @property
    def upload_dir_path(self) -> Path:
        """Ruta absoluta de uploads, siempre dentro de Backend/."""
        ruta = Path(self.upload_dir)
        return ruta if ruta.is_absolute() else BACKEND_DIR / ruta

    @property
    def jwt_expiration(self) -> timedelta:
        coincidencia = re.fullmatch(r"(\d+)\s*([smhd])", self.jwt_expires_in.strip().lower())
        if not coincidencia:
            return timedelta(days=7)
        cantidad, unidad = coincidencia.groups()
        multiplicadores = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return timedelta(seconds=int(cantidad) * multiplicadores[unidad])


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
