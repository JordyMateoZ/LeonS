from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

# Secreto por defecto del entorno de desarrollo. Nunca debe usarse en producción.
SECRETO_JWT_POR_DEFECTO = "dev-secret-change-me-en-produccion-32-bytes"

# Huéspedes que solo existen en la máquina de desarrollo.
ORIGENES_LOCALES = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "::1"})
# Valores que ODBC Driver 18 entiende como "activado".
VALORES_VERDADEROS = frozenset({"yes", "true", "1"})
# Parámetros de la cadena de conexión ODBC (`?clave=valor&clave=valor`).
_PARAMETRO_ODBC = re.compile(r"[?&;]([A-Za-z_][A-Za-z0-9_]*)=([^&;]*)")


def _es_origen_local(origen: str) -> bool:
    """Indica si el origen apunta a la máquina local (Fase 4.4, S2)."""
    try:
        host = urlsplit(origen).hostname or ""
    except ValueError:
        return False
    return host.lower().strip("[]") in ORIGENES_LOCALES


def _parametros_conexion(url: str) -> dict[str, str]:
    """Extrae los parámetros de la cadena de conexión sin exponer la URL."""
    return {
        clave.lower(): valor
        for clave, valor in _PARAMETRO_ODBC.findall(url)
    }


def _validar_tls_produccion(url: str) -> str:
    """Exige cifrado y validación de certificado en producción (Fase 4.4, S3).

    El mensaje nunca incluye la URL: puede contener credenciales.
    """
    if not (url or "").strip():
        raise ValueError("DB_URL es obligatoria en producción.")
    parametros = _parametros_conexion(url)
    if parametros.get("trustservercertificate", "").lower() in VALORES_VERDADEROS:
        raise ValueError(
            "La conexión a SQL Server no puede usar TrustServerCertificate=yes "
            "en producción; el certificado del servidor debe validarse."
        )
    if parametros.get("encrypt", "").lower() not in VALORES_VERDADEROS:
        raise ValueError(
            "La conexión a SQL Server debe declarar Encrypt=yes en producción."
        )
    return url


class Settings(BaseSettings):
    """Configuración por entorno. Ver Backend/.env.example."""

    app_name: str = "LeonS API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"

    jwt_secret: str = SECRETO_JWT_POR_DEFECTO
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
    rate_limit_auth_max: int = 10
    rate_limit_auth_window_seconds: int = 60
    rate_limit_register_max: int = 5
    rate_limit_register_window_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("jwt_secret")
    @classmethod
    def _validar_secreto_jwt(cls, valor: str, info) -> str:
        valor = (valor or "").strip()
        if not valor:
            raise ValueError("JWT_SECRET no puede estar vacío.")
        # En producción se exige un secreto fuerte y distinto del valor de desarrollo.
        entorno = (info.data.get("app_env") or "development").lower()
        if entorno == "production":
            if valor == SECRETO_JWT_POR_DEFECTO:
                raise ValueError(
                    "JWT_SECRET no puede ser el valor por defecto en producción."
                )
            if len(valor) < 32:
                raise ValueError("JWT_SECRET debe tener al menos 32 caracteres en producción.")
            valores_debiles = {"secret", "changeme", "password", "123456", "test"}
            if valor.lower() in valores_debiles:
                raise ValueError("JWT_SECRET es demasiado débil para producción.")
        return valor

    @field_validator("app_env")
    @classmethod
    def _normalizar_entorno(cls, valor: str) -> str:
        return (valor or "development").strip().lower()

    @field_validator("cors_origins")
    @classmethod
    def _validar_cors(cls, valor: list[str], info) -> list[str]:
        """CORS explícito y sin orígenes locales en producción (Fase 4.4, S2).

        El valor por defecto son los dos orígenes locales del frontend; si en
        producción no se configura `CORS_ORIGINS`, la validación lo detecta en
        lugar de heredar `localhost` en silencio.
        """
        origenes = [
            origen.strip() for origen in (valor or []) if origen and origen.strip()
        ]
        entorno = (info.data.get("app_env") or "development").lower()
        if entorno != "production":
            return origenes
        if not origenes:
            raise ValueError(
                "CORS_ORIGINS es obligatorio en producción; configura los "
                "dominios reales del frontend."
            )
        if any(origen == "*" for origen in origenes):
            raise ValueError(
                "CORS_ORIGINS no puede ser '*' en producción, menos aún con "
                "allow_credentials habilitado."
            )
        locales = [origen for origen in origenes if _es_origen_local(origen)]
        if locales:
            raise ValueError(
                "CORS_ORIGINS en producción no puede incluir orígenes locales "
                "(localhost/127.0.0.1); usa los dominios reales."
            )
        return origenes

    @field_validator("db_url")
    @classmethod
    def _validar_db_url(cls, valor: str, info) -> str:
        """TLS y URL de conexión exigidos en producción (Fase 4.4, S3)."""
        entorno = (info.data.get("app_env") or "development").lower()
        backend = (info.data.get("repos_backend") or "memory").lower()
        if entorno != "production":
            return valor
        if backend == "sqlserver" and not (valor or "").strip():
            raise ValueError("DB_URL es obligatoria en producción.")
        if (valor or "").strip():
            _validar_tls_produccion(valor)
        return valor

    @model_validator(mode="after")
    def _validar_produccion(self) -> Settings:
        """Puerta de configuración para despliegues de producción (Fase 4.4).

        Garantiza que producción no arranque heredando valores de desarrollo:
        secreto JWT por defecto (S1), CORS local (S2), TLS sin validar (S3)
        ni el repositorio en memoria con credenciales demo (A-18).
        """
        if self.app_env != "production":
            return self
        if self.jwt_secret == SECRETO_JWT_POR_DEFECTO or len(self.jwt_secret) < 32:
            raise ValueError(
                "JWT_SECRET en producción debe ser un valor propio de al menos 32 caracteres."
            )
        # A-18: el repositorio en memoria existe para desarrollo y pruebas.
        # `cargar_seed()` inyecta las cuentas demo (D-016), así que dejarlo
        # disponible en producción permitiría credenciales conocidas y una
        # persistencia volátil. Los mensajes de error no incluyen secretos.
        if self.repos_backend != "sqlserver":
            raise ValueError(
                "REPOS_BACKEND debe ser 'sqlserver' en producción: el repositorio "
                "en memoria no es persistente y carga credenciales de demostración."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
