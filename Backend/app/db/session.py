"""Sesión de SQLAlchemy contra SQL Server (Fase 6).

La URL llega desde `Settings` (`.env`); nunca se escribe aquí.
`pool_pre_ping` evita conexiones muertas tras un reinicio del servicio y
`pool_recycle` corta las que SQL Server cerraría por inactividad.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def crear_engine(url: str) -> Engine:
    if not url:
        raise RuntimeError(
            "Falta DB_URL en Backend/.env. Revisa Backend/.env.example."
        )
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )


def crear_fabrica(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
