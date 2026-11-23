from typing import Literal

from fastapi import APIRouter, Depends, Query

from ..container import Container
from ..dependencies import get_container
from ..mapper import contenido_out
from ..schemas import ContenidoOut, FaqOut, PasoOut
from ..services import contenido as contenido_service

router = APIRouter(prefix="/contenido", tags=["contenido"])


@router.get("", response_model=ContenidoOut)
def contenido(container: Container = Depends(get_container)) -> ContenidoOut:
    return contenido_out(contenido_service.obtener_contenido(container.repo))


@router.get("/pasos", response_model=list[PasoOut])
def pasos(
    container: Container = Depends(get_container),
    tipo: Literal["adopcion", "refugio"] = Query("adopcion"),
) -> list[PasoOut]:
    return [PasoOut(**paso) for paso in contenido_service.pasos(container.repo, tipo)]


@router.get("/faqs", response_model=list[FaqOut])
def faqs(container: Container = Depends(get_container)) -> list[FaqOut]:
    return [FaqOut(**faq) for faq in contenido_service.faqs(container.repo)]
