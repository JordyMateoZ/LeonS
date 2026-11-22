"""Base declarativa de SQLAlchemy 2.0 para LeonS.

Convenciones de nombres alineadas con el esquema ya creado en `LeonsDB`:

* ``PK_<tabla>``
* ``FK_<tabla>_<tabla_referenciada>``
* ``UX_<tabla>_<columna>``
* ``CK_<tabla>_<sufijo>``
* ``IX_<tabla>_<sufijo>`` (siempre explícito)

SQL Server no tiene ``BOOLEAN`` ni ``ENUM``: se usa ``BIT`` y
``NVARCHAR(n)`` + ``CHECK``. El texto de usuario siempre es ``Unicode``
(``NVARCHAR``) para conservar tildes con la collation
``Modern_Spanish_CI_AI``.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

CONVENCION_NOMBRES = {
    "ix": "IX_%(table_name)s_%(column_0_name)s",
    "uq": "UX_%(table_name)s_%(column_0_name)s",
    "ck": "CK_%(table_name)s_%(constraint_name)s",
    "fk": "FK_%(table_name)s_%(referred_table_name)s",
    "pk": "PK_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)
