from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.domain import SeedData

RUTA_SEED = Path(__file__).with_name("seed.json")


@lru_cache
def load_seed() -> SeedData:
    """Carga el seed generado desde Frontend/src/app/data/*.data.ts."""
    datos = json.loads(RUTA_SEED.read_text(encoding="utf-8"))
    return SeedData.model_validate(datos)
