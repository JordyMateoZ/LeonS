"""Aplicación FastAPI: configuración, errores, CORS, estáticos y routers."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import Settings, get_settings
from .container import build_container
from .errors import AppError
from .modules import (
    alertas,
    auth,
    contenido,
    estadisticas,
    favoritos,
    mascotas,
    refugios,
    solicitudes,
)
from .seguridad_arranque import verificar_arranque_produccion

logger = logging.getLogger("leons")

CODIGOS_HTTP = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT",
    500: "INTERNAL_ERROR",
    501: "NOT_IMPLEMENTED",
}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    container = build_container(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        # AUD-02: se ejecuta durante el arranque, antes de aceptar solicitudes.
        verificar_arranque_produccion(settings)
        yield

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "API de adopción responsable de perros y gatos en Huancayo y el Valle "
            "del Mantaro. Contrato `/api/v1` en camelCase para el frontend Angular."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.state.container = container

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        detalles = [
            {
                "campo": ".".join(str(parte) for parte in error["loc"][1:]) or "body",
                "mensaje": error["msg"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Datos inválidos.",
                "details": detalles,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": CODIGOS_HTTP.get(exc.status_code, "ERROR_HTTP"),
                "message": str(exc.detail),
                "details": None,
            },
        )

    @app.exception_handler(Exception)
    async def error_inesperado(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado en %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "Ocurrió un error inesperado.",
                "details": None,
            },
        )

    @app.get("/health", tags=["sistema"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": "1.0.0",
            "env": settings.app_env,
            "backend": settings.repos_backend,
        }

    for modulo in (
        auth,
        mascotas,
        refugios,
        solicitudes,
        favoritos,
        alertas,
        contenido,
        estadisticas,
    ):
        app.include_router(modulo.router, prefix=settings.api_prefix)

    app.mount(
        "/uploads",
        StaticFiles(directory=str(settings.uploads_dir)),
        name="uploads",
    )

    return app
