"""Lanzador del FastAPI E2E (puerto 8010), aislado de `.env`.

Las variables se fijan **en este proceso** antes de importar `app.main`:
pydantic-settings les da prioridad sobre el archivo `.env`, que no se toca.
El guard fail-closed se ejecuta antes de abrir el puerto.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import BASE_DIR, get_settings


def main() -> None:
    base = get_settings()  # lee .env una vez; sus valores no se imprimen

    os.environ["APP_ENV"] = "development"
    os.environ["REPOS_BACKEND"] = "sqlserver"
    os.environ["DB_URL"] = base.db_test_url
    os.environ["DB_TEST_URL"] = base.db_test_url
    os.environ["JWT_SECRET"] = secrets.token_urlsafe(32)  # propio de esta corrida
    os.environ["ACCESS_TOKEN_MINUTES"] = "60"
    os.environ["CORS_ORIGINS"] = json.dumps(
        ["http://localhost:4300", "http://127.0.0.1:4300"]
    )
    os.environ["UPLOADS_DIR"] = str(BASE_DIR / "uploads-e2e")
    os.environ["E2E_EXPECT_DB"] = "LeonsDB_Test"

    get_settings.cache_clear()

    from app.e2e import verificar_base_e2e

    nombre = verificar_base_e2e()
    print(f"[E2E] base efectiva verificada: {nombre}")

    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8010, log_level="info")


if __name__ == "__main__":
    main()
