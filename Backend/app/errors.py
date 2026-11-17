from __future__ import annotations

from typing import Any


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details: Any | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


class BadRequestError(AppError):
    def __init__(self, message: str = "Solicitud inválida", details: Any | None = None):
        super().__init__(400, "BAD_REQUEST", message, details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Debes iniciar sesión para continuar"):
        super().__init__(401, "UNAUTHORIZED", message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "No tienes permisos para realizar esta acción"):
        super().__init__(403, "FORBIDDEN", message)


class NotFoundError(AppError):
    def __init__(self, recurso: str = "Recurso", message: str | None = None):
        super().__init__(404, "NOT_FOUND", message or f"{recurso} no encontrado")


class ConflictError(AppError):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(409, "CONFLICT", message, details)


class NotImplementedError(AppError):
    def __init__(self, message: str = "Funcionalidad no disponible en este entorno"):
        super().__init__(501, "NOT_IMPLEMENTED", message)


def to_error_body(error: AppError) -> dict[str, Any]:
    cuerpo: dict[str, Any] = {"code": error.code, "message": error.message}
    if error.details is not None:
        cuerpo["details"] = error.details
    return {"error": cuerpo}
