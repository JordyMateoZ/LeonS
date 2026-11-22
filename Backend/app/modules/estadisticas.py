from fastapi import APIRouter, Depends

from ..container import Container
from ..dependencies import get_container
from ..mapper import impacto_out_desde_resumen
from ..schemas import ImpactoOut

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


@router.get("/impacto", response_model=ImpactoOut)
def impacto(container: Container = Depends(get_container)) -> ImpactoOut:
    # P3: agregaciones en el repositorio (SQL en SQL Server; Python en memoria).
    return impacto_out_desde_resumen(container.repo.resumen_impacto())
