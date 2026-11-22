from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Error de negocio con código estable para el cliente."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundError(AppError):
    def __init__(self, message: str = "Recurso no encontrado", details: Any | None = None) -> None:
        super().__init__("NOT_FOUND", message, 404, details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "No autenticado") -> None:
        super().__init__("UNAUTHORIZED", message, 401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "No tienes permisos para esta acción") -> None:
        super().__init__("FORBIDDEN", message, 403)


class ConflictError(AppError):
    def __init__(self, code: str, message: str, details: Any | None = None) -> None:
        super().__init__(code, message, 409, details)


class ValidationError(AppError):
    def __init__(self, code: str, message: str, details: Any | None = None) -> None:
        super().__init__(code, message, 422, details)


class NotImplementedAppError(AppError):
    def __init__(self, message: str = "Función todavía no implementada") -> None:
        super().__init__("NOT_IMPLEMENTED", message, 501)


class TransitorioError(AppError):
    """Fallo temporal de infraestructura, sin detalles internos para el cliente."""

    def __init__(
        self,
        message: str = "No se pudo completar la operación por una condición temporal. Inténtalo nuevamente.",
    ) -> None:
        super().__init__("SERVICIO_NO_DISPONIBLE", message, 503)
