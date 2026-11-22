from fastapi import APIRouter, Depends, Request, status

from ..container import Container
from ..dependencies import get_container, get_current_user
from ..domain import Usuario
from ..errors import NotImplementedAppError
from ..mapper import usuario_out
from ..schemas import (
    AuthResponse,
    GoogleRequest,
    LoginRequest,
    MensajeOut,
    RecuperarRequest,
    RegistroRequest,
    UsuarioOut,
)
from ..services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registro", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def registro(
    datos: RegistroRequest,
    request: Request,
    container: Container = Depends(get_container),
) -> AuthResponse:
    ip = request.client.host if request.client else "desconocido"
    container.limiter_register.consumir(f"registro:{ip}")
    usuario, token = auth_service.registrar(container.repo, datos, container.settings)
    return AuthResponse(usuario=usuario_out(usuario), token=token)


@router.post("/login", response_model=AuthResponse)
def login(
    datos: LoginRequest,
    request: Request,
    container: Container = Depends(get_container),
) -> AuthResponse:
    ip = request.client.host if request.client else "desconocido"
    container.limiter_auth.consumir(f"login:{ip}")
    usuario, token = auth_service.autenticar(container.repo, datos, container.settings)
    return AuthResponse(usuario=usuario_out(usuario), token=token)


@router.post("/google", response_model=AuthResponse)
def login_google(_: GoogleRequest) -> AuthResponse:
    raise NotImplementedAppError("El acceso con Google todavía no está configurado.")


@router.post("/recuperar", response_model=MensajeOut, status_code=status.HTTP_202_ACCEPTED)
def recuperar(_: RecuperarRequest) -> MensajeOut:
    return MensajeOut(
        mensaje="Si el correo está registrado, enviaremos las instrucciones de recuperación."
    )


@router.get("/me", response_model=UsuarioOut)
def perfil(usuario: Usuario = Depends(get_current_user)) -> UsuarioOut:
    return usuario_out(usuario)
