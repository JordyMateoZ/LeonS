# LeonS Backend

API del proyecto **LeonS Huancayo**, preparada para alimentar el frontend Angular existente y, más adelante, conectarse a una base de datos SQL sin reescribir casos de uso ni rutas.

## Stack

- Python 3.11+ (verificado con 3.14)
- FastAPI + uvicorn
- Pydantic v2 + pydantic-settings (validación y configuración)
- PyJWT + bcrypt (autenticación)
- pytest + TestClient/httpx (pruebas)
- Persistencia en memoria intercambiable mediante contratos `Protocol` async (SQL-ready)

## Ejecución (recomendado con uv)

Puedes ejecutar desde la **raíz del workspace** (`D:\Project-MN\LeonS-Navarro`) o desde `Backend/`:

```powershell
uv run uvicorn Backend.main:app
```

> El proyecto se instala en modo editable (`leons-backend`), por lo que el paquete `Backend` es importable desde ambas carpetas.

`uv` crea `.venv` en la raíz y sincroniza las dependencias desde `pyproject.toml` automáticamente.
El comando anterior usa el puerto por defecto de uvicorn: `http://127.0.0.1:8000`.
Para usar el puerto 3001:

```powershell
uv run uvicorn Backend.main:app --port 3001
```

Pruebas:

```powershell
uv run pytest
```

Opcional: regenerar el seed desde `Frontend/src/app/data` (requiere Node + TypeScript del frontend):

```powershell
node Backend/scripts/export_seed.mjs
```

### Alternativa con venv clásico

Desde `Backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m app.main
# o: .\.venv\Scripts\uvicorn.exe app.app:app --reload --port 3001
.\.venv\Scripts\python.exe -m pytest -q
```

- Con `uv run uvicorn Backend.main:app`: `http://127.0.0.1:8000`
- Con `python -m app.main` o `--port 3001`: `http://localhost:3001`
- Health: `/health` · Swagger: `/docs` · Base API: `/api/v1`

## Datos de demostración

El seed se genera desde `Frontend/src/app/data/*.data.ts` y se guarda en `app/data/seed.json`:

- 16 mascotas (12 disponibles)
- 9 refugios
- 3 solicitudes demo (2 activas, 1 finalizada)
- FAQs y pasos de adopción/refugio

Usuarios iniciales:

| Rol | Correo | Contraseña |
| --- | --- | --- |
| `adopter` | `demo@leons.pe` | `demo1234` |
| `admin` | `admin@leons.pe` | `admin1234` |

## Arquitectura

```text
(raíz del workspace)
├── pyproject.toml        # dependencias y config de uv/pytest
└── Backend/
    ├── __init__.py       # hace de paquete importable
    ├── main.py           # expone `app` para `uvicorn Backend.main:app`
    ├── app/
    │   ├── adapters/     # storage local, notificaciones log, PDF, rate limit
    │   ├── data/seed.json# datos exportados del frontend (sin clases CSS)
    │   ├── domain.py     # tipos + Protocol async de repositorios
    │   ├── mapper.py     # campos de presentación derivados (compatibilidad frontend)
    │   ├── middleware/   # auth JWT, roles, errores, rate limit
    │   ├── modules/      # routers por dominio
    │   ├── repositories/ # implementación en memoria (cambiable por SQL)
    │   ├── app.py        # fábrica de la aplicación FastAPI
    │   └── config.py     # settings desde .env
    ├── tests/            # 15 pruebas con TestClient
    └── scripts/export_seed.mjs
```

La respuesta estándar es:

```json
{ "data": {}, "meta": {} }
```

Y los errores:

```json
{ "error": { "code": "CONFLICT", "message": "...", "details": {} } }
```

## Compatibilidad con el frontend

El backend **no guarda clases CSS**. Los campos `badgeClase`, `etiquetaClase`, `chipClase`, etc., se derivan en `app/mapper.py` para que las plantillas Angular actuales puedan consumir la API sin cambios mayores.

Reglas de negocio implementadas:

- Catálogo público = solo mascotas `disponible` (usar `todos=true` para ver el registro completo).
- No se permite duplicar solicitud activa por mascota/solicitante: devuelve `409`.
- Nueva solicitud: `active`, `paso=2/5`, expediente `#SOL-HYO-{año}-{id}` y respuesta estimada de 24–48 h.
- Login por correo o DNI.
- Registro exige términos y contraseña ≥ 8 caracteres.
- Google y envío real de correo/WhatsApp quedan como adaptadores desactivados por configuración.

## Conexión SQL futura

Todo el acceso a datos pasa por el protocolo `Repositorios` (`app/domain.py`). Hoy lo implementa `crear_repositorios()` en `app/repositories/in_memory.py`. Para migrar:

1. Crear `app/repositories/sql.py` implementando los mismos protocolos con SQLAlchemy/SQLModel.
2. Cambiar `create_dependencies()` en `app/container.py` para inyectar el nuevo repositorio.
3. Ejecutar el mismo `pytest`: las rutas y reglas no deberían cambiar.

Ver [SQL-MIGRATION.md](./SQL-MIGRATION.md) para el modelo de tablas sugerido.

## Endpoints

Ver [API.md](./API.md).

## Solución de problemas

### `ModuleNotFoundError: No module named 'Backend'`

Python interpreta `Backend.main` como el módulo `main` dentro de un paquete llamado `Backend`. El paquete se busca en el directorio actual y en el `sys.path`. Si ejecutabas el comando desde `Backend/`, no existe `Backend/Backend/`, por eso la importación fallaba.

La configuración actual de `pyproject.toml` instala el proyecto en modo editable, de modo que `Backend` es importable desde la raíz y desde `Backend/`. Si el error reaparece (por ejemplo, tras borrar `.venv`), sincroniza de nuevo:

```powershell
uv sync
```

### El puerto 8000 está ocupado

```powershell
uv run uvicorn Backend.main:app --port 3001
```
