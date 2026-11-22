# LeonS — Backend

API de adopción responsable de perros y gatos en Huancayo y el Valle del Mantaro.
Trabajo del curso **Programación Web, C-04**.

## Stack y estado

| Aspecto | Detalle |
|---|---|
| Framework | FastAPI + Uvicorn |
| Validación | Pydantic v2, JSON en camelCase |
| Seguridad | JWT HS256, bcrypt, CORS por lista blanca, rate limit local |
| Persistencia | SQL Server, SQLAlchemy 2.0, pyodbc, Alembic |
| Repositorios | `memory` para desarrollo rápido y `sqlserver` para persistencia |
| Contrato | `/api/v1`, compatible con `Leons/src/app/data/*.ts` |
| Migraciones | Alembic `0001`–`0009`, head actual `0009` |
| Pruebas | 105/105 en la última ejecución reportada |

La persistencia en memoria **ya no es la única opción**: sigue disponible para desarrollo y pruebas, pero la persistencia vigente para el proyecto es SQL Server.

---

## Estructura

```text
Backend/
├── app/
│   ├── main.py             # entrada Uvicorn: app.main:app
│   ├── app.py              # create_app: CORS, errores, /health, /uploads
│   ├── config.py           # Settings (pydantic-settings)
│   ├── container.py        # selección de repositorio y adapters
│   ├── domain.py           # dataclasses y Protocolo Repositorio
│   ├── schemas.py          # DTO Pydantic con alias camelCase
│   ├── mapper.py           # campos de presentación calculados
│   ├── security.py         # bcrypt + JWT
│   ├── modules/            # routers de /api/v1
│   ├── services/           # reglas de negocio
│   ├── repositories/       # memory.py y sqlserver.py
│   ├── adapters/           # storage, PDF, notificaciones, rate limit
│   ├── db/                 # modelos SQLAlchemy y sesión
│   ├── data/               # seed.json y loader.py
│   └── seguridad_arranque.py
├── db/                     # seed.py, export_schema.py y schema.sql
├── migrations/versions/    # revisiones Alembic 0001–0009
├── tests/                  # test_api.py, test_config.py, test_sqlserver.py
├── .env.example
├── pyproject.toml / uv.lock / .python-version
└── alembic.ini
```

Flujo de capas: `router → service → repository → SQLAlchemy → pyodbc → SQL Server`.
Los routers no contienen reglas de negocio y los repositorios no conocen HTTP.

---

## Requisitos

- Windows 10 u 11.
- `uv` 0.13.x o superior.
- Python 3.13, fijado en `.python-version`; `uv` puede instalarlo.
- SQL Server 2019+ o Express, con ODBC Driver 18, si se usa `REPOS_BACKEND=sqlserver`.
- Base local con collation `Modern_Spanish_CI_AI`.

---

## Configuración local

```powershell
cd Backend
uv sync
Copy-Item .env.example .env
```

Editar `Backend/.env` sin subirlo a Git. Variables principales:

| Variable | Uso |
|---|---|
| `APP_ENV` | entorno de ejecución; `development` para la demostración local |
| `API_PREFIX` | prefijo `/api/v1` |
| `JWT_SECRET` | secreto local; reemplazar el marcador de ejemplo |
| `ACCESS_TOKEN_MINUTES` | duración del token |
| `CORS_ORIGINS` | orígenes permitidos; en local incluye `4200` y `4000` |
| `REPOS_BACKEND` | `memory` o `sqlserver` |
| `DB_URL` | base principal local |
| `DB_TEST_URL` | base de pruebas, usada por defecto por el seed |
| `UPLOADS_DIR` | directorio de archivos subidos, ignorado por Git |
| `RATE_LIMIT_*` | límites de alertas, login y registro |

El ejemplo usa Windows Auth en local. No incluir credenciales reales en `.env.example`.

---

## Arranque

```powershell
cd Backend
uv run uvicorn app.main:app --reload --port 8000
```

| Recurso | URL |
|---|---|
| API | `http://localhost:8000/api/v1` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| Salud | `http://localhost:8000/health` |
| Uploads | `http://localhost:8000/uploads/<archivo>` |

---

## Endpoints principales

Todo cuelga de `/api/v1`, salvo `/health`, `/docs`, `/redoc` y `/uploads`.

| Grupo | Endpoints |
|---|---|
| Auth | `POST /auth/registro`, `/auth/login`, `/auth/google`, `/auth/recuperar`; `GET /auth/me` |
| Catálogo | `GET /mascotas`, `/destacadas`, `/stats`, `/{id}`, `/{id}/detalle`, `/{id}/similares`; altas administrativas |
| Refugios | `GET /refugios`, `/{id}`, `/{id}/mascotas` |
| Solicitudes | `GET/POST /solicitudes`, detalle, cancelación, cambio de etapa, citas, mensajes, seguimiento y documentos PDF |
| Favoritos | `GET/POST /favoritos` y `DELETE /favoritos/{mascotaId}` |
| Alertas | `POST/GET /alertas-rescate` |
| Contenido | `GET /contenido`, `/pasos`, `/faqs` |
| Estadísticas | `GET /estadisticas/impacto` |

`GET /mascotas` admite paginación, búsqueda, filtros por especie/distrito/tamaño/estado, orden y marcadores booleanos. La respuesta paginada usa `{ items, page, limit, total, totalPages }`.

Los errores tienen la forma `{ code, message, details }`.

---

## Migraciones Alembic

```powershell
cd Backend

# Base de pruebas
uv run alembic -x target=test upgrade head
uv run alembic -x target=test check

# Base principal local
uv run alembic -x target=main upgrade head
```

- `-x target=...` va antes del subcomando.
- `target=test` usa `DB_TEST_URL`; `target=main` usa `DB_URL`.
- La head actual es `0009`.
- `env.py` ignora `sysdiagrams` para que `autogenerate` no proponga borrarlo.
- No editar migraciones ya aplicadas.

`Backend/db/schema.sql` se regenera con:

```powershell
uv run python db/export_schema.py
```

No se edita a mano.

---

## Seed

`app/data/seed.json` se exporta desde las constantes de Angular:

```powershell
cd Leons
node_modules/.bin/esbuild scripts/export-seed.ts --bundle --platform=node --format=esm --outfile=scripts/.tmp/export-seed.mjs
node scripts/.tmp/export-seed.mjs ../Backend/app/data/seed.json
```

Contenido actual: 16 mascotas, 9 refugios, 3 solicitudes demo, pasos, FAQ y detalles editoriales.

Para sembrar:

```powershell
cd Backend
uv run python db/seed.py
```

- Usa `DB_TEST_URL` por defecto.
- Solo permite bases que terminen en `_Test`, salvo `--force`.
- Es idempotente y preserva los ids 1–16 de mascotas.
- No ejecutar `--force` contra `LeonsDB` salvo autorización explícita y respaldo.

Las cuentas demo se definen en `app/data/loader.py`, se hashean con bcrypt en memoria y no forman parte del seed. Son exclusivas de desarrollo y demostración local.

---

## Pruebas

```powershell
cd Backend
uv run pytest -p no:warnings
```

Última ejecución reportada:

| Archivo | Pruebas |
|---|---:|
| `tests/test_api.py` | 30 |
| `tests/test_config.py` | 27 |
| `tests/test_sqlserver.py` | 48 |
| **Total** | **105** |

`test_sqlserver.py` requiere `LeonsDB_Test` y no debe apuntar a `LeonsDB`.

---

## Seguridad y correcciones recientes

- Contraseñas con bcrypt; JWT HS256 con expiración.
- CORS con lista blanca; en producción no se heredan orígenes locales.
- Rate limit en alertas, login y registro, local al proceso.
- Uploads validados por MIME y tamaño; nombre saneado.
- `.env` excluido de Git; `.env.example` sin secretos reales.
- **AUD-01 corregido:** el registro público fuerza `rol="adoptante"` y `refugio_id=None`; `rol="refugio"` se rechaza con `403` y `admin` con `422` desde esquemas.
- **AUD-02 mitigado:** `app/seguridad_arranque.py` realiza una comprobación parametrizada y fail-closed solo con `APP_ENV=production` y `REPOS_BACKEND=sqlserver`. No sustituye la rotación/eliminación de credenciales demo y no ha sido probado en un despliegue real.

Producción exige `JWT_SECRET` propio, `CORS_ORIGINS` real, `REPOS_BACKEND=sqlserver`, `DB_URL` cifrada sin `TrustServerCertificate`, y bases sin credenciales demo. Estas condiciones son una puerta de configuración, no una certificación de despliegue.

---

## Limitaciones

- No está preparado para Internet ni para producción.
- Q-08 (dominios CORS), Q-09 (certificado TLS) y Q-10 (rate limit distribuido) permanecen abiertas.
- No se ha validado una instalación completa desde un clon limpio.
- No se ejecutaron migraciones, seeds ni pruebas durante la preparación GITHUB-02.

Para contexto completo, ver `AGENTS.md` y `docs/REVISION-BACKEND.md`.
