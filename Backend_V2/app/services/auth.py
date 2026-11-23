"""Reglas de autenticación y registro."""

from __future__ import annotations

from ..config import Settings
from ..domain import Usuario
from ..errors import ConflictError, UnauthorizedError, ValidationError
from ..repositories.memory import MemoryRepository
from ..schemas import LoginRequest, RegistroRequest
from ..security import crear_token, hash_password, verificar_password


def registrar(
    repo: MemoryRepository, datos: RegistroRequest, settings: Settings
) -> tuple[Usuario, str]:
    if repo.buscar_usuario_por_email(datos.email):
        raise ConflictError("EMAIL_YA_REGISTRADO", "Ya existe una cuenta con ese correo.")
    if repo.buscar_usuario_por_dni(datos.dni):
        raise ConflictError("DNI_YA_REGISTRADO", "Ya existe una cuenta con ese DNI.")

    if datos.rol == "refugio":
        if not datos.refugio_id or repo.obtener_refugio(datos.refugio_id) is None:
            raise ValidationError(
                "REFUGIO_INVALIDO",
                "Para registrarte como refugio debes indicar un refugio existente.",
                {"refugioId": datos.refugio_id},
            )

    usuario = Usuario(
        id=repo.siguiente_usuario_id(),
        nombre=datos.nombre,
        email=str(datos.email).lower(),
        dni=datos.dni,
        telefono=datos.telefono,
        distrito=datos.distrito,
        rol=datos.rol,
        refugio_id=datos.refugio_id if datos.rol == "refugio" else None,
        password_hash=hash_password(datos.password),
    )
    repo.crear_usuario(usuario)
    return usuario, crear_token(usuario, settings)


def autenticar(
    repo: MemoryRepository, datos: LoginRequest, settings: Settings
) -> tuple[Usuario, str]:
    identificador = (datos.identificador or datos.email or datos.dni or "").strip()
    if not identificador:
        raise ValidationError(
            "CREDENCIALES_REQUERIDAS",
            "Envía tu correo, tu DNI o el campo identificador.",
        )

    usuario = (
        repo.buscar_usuario_por_email(identificador)
        if "@" in identificador
        else repo.buscar_usuario_por_dni(identificador)
    )
    if usuario is None or not verificar_password(datos.password, usuario.password_hash):
        raise UnauthorizedError("Correo/DNI o contraseña incorrectos.")

    return usuario, crear_token(usuario, settings)
