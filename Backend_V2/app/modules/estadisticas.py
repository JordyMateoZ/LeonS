from fastapi import APIRouter, Depends

from ..container import Container
from ..dependencies import get_container
from ..mapper import impacto_out
from ..schemas import ImpactoOut

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


@router.get("/impacto", response_model=ImpactoOut)
def impacto(container: Container = Depends(get_container)) -> ImpactoOut:
    return impacto_out(container.repo.listar_mascotas(), container.repo.listar_refugios())
