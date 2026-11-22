"""Endurecimiento de configuración y seguridad (Fase 4.4).

Cubre S1 (secreto JWT), S2 (CORS), S3 (TLS de SQL Server), S6 (rate limiting)
y S10 (bloqueo de cuentas desactivadas) a nivel de configuración y adaptadores.
No requiere base de datos: usa el repositorio en memoria del seed.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, text

from app.adapters.rate_limit import RateLimiter
from app.app import create_app
from app.config import SECRETO_JWT_POR_DEFECTO, Settings
from app.container import build_container
from app.errors import AppError, UnauthorizedError
from app.schemas import LoginRequest
from app import seguridad_arranque as arranque
from app.services import auth as auth_service

SECRETO_PRODUCCION = "produccion-propia-y-aleatoria-de-32-bytes"

URL_DESARROLLO = (
    "mssql+pyodbc://@localhost\\SQLEXPRESS/LeonsDB"
    "?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes"
    "&Encrypt=yes&TrustServerCertificate=yes"
)
URL_PRODUCCION = (
    "mssql+pyodbc://@servidor\\SQLEXPRESS/LeonsDB"
    "?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&Encrypt=yes"
)
ORIGEN_PRODUCCION = "https://leons.example.com"


def _settings(**sobrescritos) -> Settings:
    valores: dict = {
        "app_env": "test",
        "jwt_secret": "test-secret-con-mas-de-32-bytes-para-hs256",
        "repos_backend": "memory",
    }
    valores.update(sobrescritos)
    return Settings(**valores)


def _settings_produccion(**sobrescritos) -> Settings:
    valores: dict = {
        "app_env": "production",
        "jwt_secret": SECRETO_PRODUCCION,
        "cors_origins": [ORIGEN_PRODUCCION],
        # A-18: producción exige persistencia real; las pruebas de CORS/TLS
        # sobrescriben estos valores según lo que cada una verifica.
        "repos_backend": "sqlserver",
        "db_url": URL_PRODUCCION,
    }
    valores.update(sobrescritos)
    return _settings(**valores)


# -- S2: CORS ---------------------------------------------------------------


def test_produccion_rechaza_cors_no_configurado() -> None:
    """Sin CORS_ORIGINS explícito, producción no hereda localhost."""
    with pytest.raises(ValidationError) as exc:
        _settings(
            app_env="production",
            jwt_secret=SECRETO_PRODUCCION,
            repos_backend="sqlserver",
            db_url=URL_PRODUCCION,
        )
    assert "CORS_ORIGINS" in str(exc.value)


def test_produccion_rechaza_cors_locales() -> None:
    with pytest.raises(ValidationError) as exc:
        _settings_produccion(
            cors_origins=[ORIGEN_PRODUCCION, "http://localhost:4200"]
        )
    assert "local" in str(exc.value).lower()


def test_produccion_rechaza_cors_comodin() -> None:
    with pytest.raises(ValidationError) as exc:
        _settings_produccion(cors_origins=["*"])
    assert "*" in str(exc.value)


def test_produccion_acepta_cors_explicito() -> None:
    ajustes = _settings_produccion(cors_origins=[ORIGEN_PRODUCCION])
    assert ajustes.cors_origins == [ORIGEN_PRODUCCION]


def test_desarrollo_mantiene_compatibilidad_cors() -> None:
    ajustes = _settings(app_env="development")
    assert ajustes.cors_origins == [
        "http://localhost:4200",
        "http://localhost:4000",
    ]
    assert _settings(app_env="development", cors_origins=["*"]).cors_origins == ["*"]


# -- S3: TLS de SQL Server --------------------------------------------------


def test_produccion_rechaza_trust_server_certificate() -> None:
    with pytest.raises(ValidationError) as exc:
        _settings_produccion(repos_backend="sqlserver", db_url=URL_DESARROLLO)
    assert "TrustServerCertificate" in str(exc.value)


def test_produccion_exige_encrypt_si() -> None:
    url_sin_encrypt = (
        "mssql+pyodbc://@servidor\\SQLEXPRESS/LeonsDB"
        "?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes"
    )
    with pytest.raises(ValidationError) as exc:
        _settings_produccion(repos_backend="sqlserver", db_url=url_sin_encrypt)
    assert "Encrypt" in str(exc.value)

    url_encrypt_no = f"{URL_PRODUCCION}&Encrypt=no"
    with pytest.raises(ValidationError):
        _settings_produccion(repos_backend="sqlserver", db_url=url_encrypt_no)


def test_produccion_exige_db_url() -> None:
    with pytest.raises(ValidationError) as exc:
        _settings_produccion(repos_backend="sqlserver", db_url="")
    assert "DB_URL" in str(exc.value)


def test_produccion_acepta_tls_valido() -> None:
    ajustes = _settings_produccion(repos_backend="sqlserver", db_url=URL_PRODUCCION)
    assert ajustes.db_url == URL_PRODUCCION


def test_a18_produccion_rechaza_repositorio_en_memoria() -> None:
    """A-18: en memoria se cargan las credenciales demo (D-016) y no persiste."""
    with pytest.raises(ValidationError) as exc:
        _settings_produccion(repos_backend="memory")
    assert "REPOS_BACKEND" in str(exc.value)


def test_a18_produccion_exige_db_url_valida() -> None:
    with pytest.raises(ValidationError) as exc:
        _settings_produccion(repos_backend="sqlserver", db_url="")
    assert "DB_URL" in str(exc.value)


def test_a18_desarrollo_admite_repositorio_en_memoria() -> None:
    ajustes = _settings(app_env="development")
    assert ajustes.repos_backend == "memory"


def test_desarrollo_admite_trust_server_certificate() -> None:
    ajustes = _settings(
        app_env="development", repos_backend="sqlserver", db_url=URL_DESARROLLO
    )
    assert "TrustServerCertificate=yes" in ajustes.db_url


def test_los_errores_de_tls_no_exponen_la_url() -> None:
    with pytest.raises(ValidationError) as exc:
        _settings_produccion(repos_backend="sqlserver", db_url=URL_DESARROLLO)
    mensaje = str(exc.value)
    assert "localhost" not in mensaje
    assert "LeonsDB" not in mensaje


# -- S1: secreto JWT --------------------------------------------------------


def test_s1_rechaza_secreto_por_defecto_en_produccion() -> None:
    with pytest.raises(ValidationError):
        _settings_produccion(jwt_secret=SECRETO_JWT_POR_DEFECTO)


def test_s1_rechaza_secreto_corto_en_produccion() -> None:
    with pytest.raises(ValidationError):
        _settings_produccion(jwt_secret="corto")


def test_s1_desarrollo_admite_el_valor_por_defecto() -> None:
    ajustes = _settings(app_env="development", jwt_secret=SECRETO_JWT_POR_DEFECTO)
    assert ajustes.jwt_secret == SECRETO_JWT_POR_DEFECTO


# -- S6: rate limiting ------------------------------------------------------


def test_s6_limites_por_defecto_desarrollo() -> None:
    ajustes = _settings()
    assert (ajustes.rate_limit_auth_max, ajustes.rate_limit_auth_window_seconds) == (10, 60)
    assert (
        ajustes.rate_limit_register_max,
        ajustes.rate_limit_register_window_seconds,
    ) == (5, 60)
    assert (ajustes.rate_limit_alerts_max, ajustes.rate_limit_window_seconds) == (5, 60)


def test_s6_contenedor_usa_limites_configurados() -> None:
    ajustes = _settings(rate_limit_auth_max=3, rate_limit_auth_window_seconds=30)
    contenedor = build_container(ajustes)
    assert contenedor.limiter_auth.maximo == 3
    assert contenedor.limiter_auth.ventana == 30
    assert contenedor.limiter_register.maximo == ajustes.rate_limit_register_max
    assert contenedor.limiter.maximo == ajustes.rate_limit_alerts_max


def test_s6_limite_devuelve_rate_limit() -> None:
    limitador = RateLimiter(maximo=1, ventana_segundos=60)
    limitador.consumir("ip-de-prueba")
    with pytest.raises(AppError) as exc:
        limitador.consumir("ip-de-prueba")
    assert exc.value.code == "RATE_LIMIT"
    assert exc.value.status_code == 429
    assert exc.value.details["reintentarEnSegundos"] >= 1


# -- S10: cuentas desactivadas ---------------------------------------------


def test_s10_autenticar_rechaza_cuenta_desactivada() -> None:
    ajustes = _settings()
    contenedor = build_container(ajustes)
    repo = contenedor.repo
    usuario = repo.buscar_usuario_por_email("demo@leons.pe")
    assert usuario is not None
    usuario.activo = False

    with pytest.raises(UnauthorizedError):
        auth_service.autenticar(
            repo,
            LoginRequest(identificador="demo@leons.pe", password="demo12345"),
            ajustes,
        )

    usuario.activo = True


# -- AUD-02: guard de arranque contra cuentas demo --------------------------


def test_produccion_rechaza_bd_con_cuentas_demo() -> None:
    with pytest.raises(RuntimeError) as exc:
        arranque.verificar_arranque_produccion(
            _settings_produccion(), contador=lambda: 3
        )
    mensaje = str(exc.value)
    assert "demostración" in mensaje
    assert "leons.pe" not in mensaje
    assert "hash" not in mensaje.lower()
    assert SECRETO_PRODUCCION not in mensaje
    assert "mssql" not in mensaje


def test_produccion_acepta_bd_sin_marcadores_demo() -> None:
    arranque.verificar_arranque_produccion(
        _settings_produccion(), contador=lambda: 0
    )


def test_contar_cuentas_demo_usa_sql_parametrizado() -> None:
    """Ejercita la consulta real sin tocar SQL Server: SQLite con esquema `dbo`."""
    motor = create_engine("sqlite://")
    try:
        with motor.begin() as conexion:
            conexion.execute(text("ATTACH DATABASE ':memory:' AS dbo"))
            conexion.execute(text("CREATE TABLE dbo.usuarios (email TEXT)"))
            conexion.execute(
                text("INSERT INTO dbo.usuarios (email) VALUES (:email)"),
                {"email": "demo@leons.pe"},
            )
        assert arranque.contar_cuentas_demo(motor) == 1
    finally:
        motor.dispose()


def test_produccion_rechaza_fallo_de_verificacion() -> None:
    def contador_que_falla() -> int:
        raise OSError("detalle interno de conexión")

    with pytest.raises(RuntimeError) as exc:
        arranque.verificar_arranque_produccion(
            _settings_produccion(), contador=contador_que_falla
        )
    mensaje = str(exc.value)
    assert mensaje == arranque.MENSAJE_VERIFICACION_FALLIDA
    assert "detalle interno" not in mensaje
    assert "mssql" not in mensaje


def test_guard_inactivo_en_desarrollo_y_conserva_cuentas_demo() -> None:
    ajustes = _settings()
    contador = Mock(return_value=3)

    arranque.verificar_arranque_produccion(ajustes, contador=contador)

    contador.assert_not_called()
    repo = build_container(ajustes).repo
    assert repo.buscar_usuario_por_email("demo@leons.pe") is not None


def test_guard_se_ejecuta_durante_el_arranque_de_fastapi(monkeypatch) -> None:
    guardia = Mock()
    monkeypatch.setattr("app.app.verificar_arranque_produccion", guardia)
    ajustes = _settings()

    with TestClient(create_app(ajustes)):
        pass

    guardia.assert_called_once_with(ajustes)
