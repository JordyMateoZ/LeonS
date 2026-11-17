from __future__ import annotations

import uvicorn

from app.config import settings


def main() -> None:
    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=settings.port,
        log_level="info",
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()
