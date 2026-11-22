"""Reglas de autenticación y registro."""

from __future__ import annotations

from ..config import Settings
from ..domain import Repositorio, Usuario
from ..errors import ConflictError, ForbiddenError, UnauthorizedError, ValidationError
from ..schemas import LoginRequest, RegistroRequest
from ..security import crear_token, hash_password, verificar_password


def registrar(
    repo: Repositorio, datos: RegistroRequest, settings: Settings
) -> tuple[Usuario, str]:
    # AUD-01: el registro público nunca acepta roles privilegiados, aunque el
    # cliente envíe un `refugio_id` válido. Se rechaza antes de consultar duplicados
    # o de crear cualquier usuario. `admin` ya lo rechaza Pydantic con 422.
    if datos.rol != "adoptante":
        raise ForbiddenError("El registro público solo crea cuentas adoptante.")

    if repo.buscar_usuario_por_email(datos.email):
        raise ConflictError("EMAIL_YA_REGISTRADO", "Ya existe una cuenta con ese correo.")
    if repo.buscar_usuario_por_dni(datos.dni):
        raise ConflictError("DNI_YA_REGISTRADO", "Ya existe una cuenta con ese DNI.")

    usuario = Usuario(
        id=0,
        nombre=datos.nombre,
        email=str(datos.email).lower(),
        dni=datos.dni,
        telefono=datos.telefono,
        distrito=datos.distrito,
        rol="adoptante",
        refugio_id=None,
        password_hash=hash_password(datos.password),
    )
    creado = repo.crear_usuario(usuario)
    return creado, crear_token(creado, settings)


def autenticar(
    repo: Repositorio, datos: LoginRequest, settings: Settings
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

    if not usuario.activo:
        raise UnauthorizedError("La cuenta está desactivada.")

    return usuario, crear_token(usuario, settings)
