from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import EmailStr, Field, field_validator, model_validator

from app.config import settings
from app.domain import DomainModel, Usuario
from app.errors import AppError, ConflictError, NotFoundError, NotImplementedError
from app.middleware.auth import AuthUser, Deps, firmar_token
from app.middleware.rate_limit import limitar_auth
from app.repositories import hash_password, verificar_password, nuevo_id

router = APIRouter(prefix="/auth", tags=["auth"])


def usuario_publico(usuario: Usuario) -> dict:
    datos = usuario.model_dump(by_alias=True, mode="json")
    datos.pop("passwordHash", None)
    datos.pop("googleId", None)
    return datos


class RegistroRequest(DomainModel):
    nombre: str = Field(min_length=2, max_length=80)
    apellido: str | None = Field(default=None, min_length=2, max_length=80)
    email: EmailStr
    dni: str = Field(pattern=r"^\d{8}$")
    password: str = Field(min_length=8, max_length=72)
    terminos: bool
    rol: Literal["adopter", "shelter"] = "adopter"
    telefono: str | None = Field(default=None, min_length=9, max_length=30)
    distrito: str | None = Field(default=None, min_length=2, max_length=80)

    @field_validator("terminos")
    @classmethod
    def terminos_deben_aceptarse(cls, valor: bool) -> bool:
        if not valor:
            raise ValueError("Debes aceptar los términos")
        return valor


class LoginRequest(DomainModel):
    identificador: str | None = None
    email: EmailStr | None = None
    dni: str | None = None
    password: str = Field(min_length=1)

    @model_validator(mode="after")
    def requiere_identificador(self) -> "LoginRequest":
        if not (self.identificador or self.email or self.dni):
            raise ValueError("Indica tu correo o DNI")
        return self


class RecuperarRequest(DomainModel):
    email: EmailStr


class GoogleRequest(DomainModel):
    id_token: str = Field(min_length=10)
    rol: Literal["adopter", "shelter"] = "adopter"


@router.post("/registro", status_code=201)
async def registro(body: RegistroRequest, deps: Deps, _: None = Depends(limitar_auth)) -> dict:
    email = str(body.email).casefold()

    if await deps.repos.usuarios.find_by_email(email):
        raise ConflictError("Ya existe una cuenta con ese correo electrónico")
    if await deps.repos.usuarios.find_by_dni(body.dni):
        raise ConflictError("Ya existe una cuenta con ese DNI")

    fecha = datetime.now(timezone.utc).isoformat()
    usuario = Usuario(
        id=nuevo_id(),
        nombre=body.nombre,
        apellido=body.apellido,
        email=email,
        dni=body.dni,
        password_hash=hash_password(body.password),
        rol=body.rol,
        telefono=body.telefono,
        distrito=body.distrito,
        terminos_aceptados=True,
        activo=True,
        creado_en=fecha,
        actualizado_en=fecha,
    )
    await deps.repos.usuarios.create(usuario)
    await deps.notificaciones.correo(
        usuario.email,
        "Bienvenido/a a LeonS",
        "Tu cuenta está lista para postular adopciones responsables.",
    )

    return {"data": {"usuario": usuario_publico(usuario), "token": firmar_token(usuario)}}


@router.post("/login")
async def login(body: LoginRequest, deps: Deps, _: None = Depends(limitar_auth)) -> dict:
    identificador = (body.identificador or body.email or body.dni or "").strip()
    usuario = await deps.repos.usuarios.find_by_email(identificador.casefold())
    if not usuario:
        usuario = await deps.repos.usuarios.find_by_dni(identificador)

    if not usuario or not verificar_password(body.password, usuario.password_hash):
        raise AppError(
            401,
            "CREDENCIALES_INVALIDAS",
            "Correo/DNI o contraseña incorrectos",
        )

    return {"data": {"usuario": usuario_publico(usuario), "token": firmar_token(usuario)}}


@router.post("/google")
async def google(_body: GoogleRequest, _: None = Depends(limitar_auth)) -> dict:
    if not settings.google_client_id:
        raise NotImplementedError(
            "El inicio de sesión con Google está desactivado hasta configurar GOOGLE_CLIENT_ID"
        )
    raise NotImplementedError("La verificación de Google todavía no está conectada")


@router.post("/recuperar", status_code=202)
async def recuperar(body: RecuperarRequest, deps: Deps, _: None = Depends(limitar_auth)) -> dict:
    usuario = await deps.repos.usuarios.find_by_email(str(body.email).casefold())
    if usuario:
        await deps.notificaciones.correo(
            usuario.email,
            "Recupera tu acceso a LeonS",
            "Usa el enlace seguro que te enviamos para restablecer tu contraseña.",
        )
    return {"data": {"aceptado": True}}


@router.get("/me")
async def me(usuario: AuthUser) -> dict:
    return {"data": usuario_publico(usuario)}
