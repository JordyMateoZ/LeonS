from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.config import settings
from app.container import Dependencies, create_dependencies
from app.errors import AppError, to_error_body
from app.modules import (
    alertas_router,
    auth_router,
    contenido_router,
    estadisticas_router,
    favoritos_router,
    mascotas_router,
    refugios_router,
    solicitudes_router,
)

logger = logging.getLogger("leons")


def create_app(deps: Dependencies | None = None) -> FastAPI:
    app = FastAPI(
        title="LeonS API",
        version=__version__,
        description="API de adopción responsable del Valle del Mantaro",
    )
    app.state.deps = deps or create_dependencies()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=to_error_body(exc))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        detalles = [
            {"loc": list(error.get("loc", [])), "msg": error.get("msg", ""), "type": error.get("type", "")}
            for error in exc.errors()
        ]
        cuerpo = to_error_body(AppError(400, "BAD_REQUEST", "Datos inválidos", detalles))
        return JSONResponse(status_code=400, content=cuerpo)

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        codigo = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        mensaje = "Recurso no encontrado" if exc.status_code == 404 else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=to_error_body(AppError(exc.status_code, codigo, mensaje)),
        )

    @app.exception_handler(Exception)
    async def unexpected_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error inesperado", exc_info=exc)
        cuerpo = to_error_body(
            AppError(500, "INTERNAL_ERROR", "Ocurrió un error inesperado")
        )
        return JSONResponse(status_code=500, content=cuerpo)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"data": {"ok": True, "servicio": "leons-backend", "version": __version__}}

    directorio_uploads = settings.upload_dir_path
    directorio_uploads.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/uploads",
        StaticFiles(directory=str(directorio_uploads)),
        name="uploads",
    )

    @app.get(settings.api_prefix, tags=["info"])
    async def info() -> dict:
        return {
            "data": {
                "nombre": "LeonS API",
                "version": "v1",
                "modulos": [
                    "auth",
                    "mascotas",
                    "refugios",
                    "solicitudes",
                    "favoritos",
                    "alertas-rescate",
                    "contenido",
                    "estadisticas",
                ],
            }
        }

    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(mascotas_router, prefix=settings.api_prefix)
    app.include_router(refugios_router, prefix=settings.api_prefix)
    app.include_router(solicitudes_router, prefix=settings.api_prefix)
    app.include_router(favoritos_router, prefix=settings.api_prefix)
    app.include_router(alertas_router, prefix=settings.api_prefix)
    app.include_router(contenido_router, prefix=settings.api_prefix)
    app.include_router(estadisticas_router, prefix=settings.api_prefix)

    return app


app = create_app()
