# LeonS

Plataforma de adopción responsable de perros y gatos en Huancayo y el Valle del Mantaro, Perú.
Trabajo del curso **Programación Web, C-04**.

LeonS permite explorar mascotas y refugios, publicar alertas de rescate, crear solicitudes de adopción, gestionar favoritos y seguir el estado de una postulación. El proyecto se ejecuta localmente: no requiere despliegue en Internet.

> **Estado de la documentación (GITHUB-02):** los comandos y rutas descritos aquí se verificaron contra el repositorio local. **No se ha probado una instalación desde un clon limpio** y **no se ha realizado ningún despliegue**. Los pasos que dependen de SQL Server o de la máquina del docente quedan marcados como pendientes de validación en un entorno nuevo.

---

## 1. Objetivo del proyecto

- Construir un backend con contrato `/api/v1` compatible con el frontend Angular.
- Persistir los datos en SQL Server mediante SQLAlchemy 2.0, Alembic y ODBC Driver 18.
- Mantener las pantallas actuales de Angular y su API pública de servicios.
- Proporcionar datos demo reproducibles para una demostración universitaria local.
- Dejar registradas las decisiones técnicas y las limitaciones de seguridad.

---

## 2. Tecnologías

| Capa | Tecnología |
|---|---|
| Frontend | Angular 22.2, TypeScript 6.0, Tailwind CSS 4.3, Vitest 5, SSR |
| Backend | FastAPI, Uvicorn, Pydantic v2 |
| Persistencia | SQL Server 2019+ / Express, SQLAlchemy 2.0, pyodbc, Alembic |
| Seguridad | bcrypt, JWT HS256, CORS por lista blanca, rate limit local |
| Entorno | Windows, Node.js 24.22, npm 11.19, `uv` 0.13, Python 3.13 |
| Pruebas | pytest, Vitest, Playwright para evidencias E2E |

Versiones observadas en la máquina de desarrollo: Node `v24.22.0`, npm `11.19.1`, `uv 0.13.7`. Python 3.13 está fijado en `Backend/.python-version`.

---

## 3. Estructura del repositorio

```text
LeonS/
├── AGENTS.md              # normas y registro operativo del proyecto
├── README.md              # este documento
├── .gitignore             # ignorados globales
├── Backend/               # API FastAPI vigente
│   ├── app/               # routers, servicios, repositorios, modelos y adapters
│   ├── db/                # seed.py, export_schema.py y schema.sql
│   ├── migrations/        # revisiones Alembic 0001–0009
│   ├── tests/             # pruebas de API, configuración e integración SQL
│   ├── .env.example       # plantilla sin secretos reales
│   └── README.md
├── Leons/                 # frontend Angular vigente
│   ├── src/               # componentes, páginas, datos y environments
│   ├── e2e/               # especificaciones y evidencias E2E revisadas
│   ├── scripts/           # exportador del seed desde Angular
│   └── README.md
└── docs/                  # decisiones, modelo de datos, auditoría y evidencias
```

`LeonS-Mateo/` se conserva físicamente como referencia histórica, pero está excluido del seguimiento Git mediante el `.gitignore` raíz. El backend funcional es `Backend/`. No se debe modificar, descompilar ni reactivar `LeonS-Mateo/Backend/`.

---

## 4. Requisitos para Windows

1. Windows 10 u 11.
2. Node.js 24.x y npm 11.x, o una versión compatible con Angular 22.
3. [`uv`](https://docs.astral.sh/uv/) 0.13.x o superior.
4. Python 3.13; `uv` puede instalarlo automáticamente porque existe `Backend/.python-version`.
5. SQL Server 2019 o superior. El proyecto usa una instancia local `localhost\SQLEXPRESS`; Express es suficiente.
6. ODBC Driver 18 for SQL Server.
7. Opcional: SQL Server Management Studio para crear y revisar bases localmente.
8. Git, si se desea clonar o actualizar el repositorio.

No es necesario instalar dependencias globales de Python: `uv sync` prepara el entorno dentro de `Backend/`.

---

## 5. Instalación de Angular

```powershell
cd Leons
npm install
```

El proyecto usa `package-lock.json`; ese archivo debe conservarse en Git.

Para comprobar la instalación sin iniciar servicios:

```powershell
npm run build
npm test
```

---

## 6. Instalación del backend con uv

```powershell
cd Backend
uv sync
Copy-Item .env.example .env
```

Después de copiar la plantilla, editar `Backend/.env` con la configuración local de la máquina. **No subir `Backend/.env` a GitHub**: ya está ignorado.

Variables principales, todas documentadas en `Backend/.env.example`:

- `APP_ENV`, `API_PREFIX`
- `JWT_SECRET`, `ACCESS_TOKEN_MINUTES`
- `CORS_ORIGINS`
- `REPOS_BACKEND`
- `DB_URL`, `DB_TEST_URL`
- `UPLOADS_DIR`
- parámetros de rate limit

`REPOS_BACKEND=memory` permite arrancar sin SQL Server con datos demo en memoria. `REPOS_BACKEND=sqlserver` usa la base configurada en `DB_URL`.

---

## 7. Configuración local de SQL Server

No existe un script versionado para crear la base de datos; este paso debe hacerse manualmente en SQL Server o SSMS y está **pendiente de validar desde un clon limpio**.

Bases previstas:

| Base | Uso |
|---|---|
| `LeonsDB_Test` | pruebas de integración y seed controlado |
| `LeonsDB` | base principal local actual del proyecto |

Para un compañero, crear una base nueva vacía, por ejemplo `LeonsDB_Test`, con collation `Modern_Spanish_CI_AI`, y copiar los valores de conexión de `Backend/.env.example` a `Backend/.env`. La instancia local usada en el proyecto lleva la barra invertida literal `localhost\SQLEXPRESS`.

No reutilizar contraseñas personales. No subir respaldos `.bak`, `.mdf` ni `.ldf`.

---

## 8. Migraciones Alembic

Las migraciones `0001` a `0009` están en `Backend/migrations/versions/`. La revisión actual registrada en las bases del proyecto es `0009`.

```powershell
cd Backend

# Base de pruebas
uv run alembic -x target=test upgrade head
uv run alembic -x target=test check

# Base principal local
uv run alembic -x target=main upgrade head
```

El argumento `-x target=...` debe ir **antes** del subcomando. `target=test` usa `DB_TEST_URL` y `target=main` usa `DB_URL`.

Solo ejecutar `upgrade` sobre una base propia o debidamente autorizada. `LeonsDB` ya fue migrada en la puerta G5; no repetir el procedimiento sin una razón.

---

## 9. Carga controlada de datos de ejemplo

El archivo `Backend/app/data/seed.json` se genera desde las constantes de Angular. No se edita a mano. Si cambian las constantes, regenerarlo:

```powershell
cd Leons
node_modules/.bin/esbuild scripts/export-seed.ts --bundle --platform=node --format=esm --outfile=scripts/.tmp/export-seed.mjs
node scripts/.tmp/export-seed.mjs ../Backend/app/data/seed.json
```

Para sembrar la base de pruebas:

```powershell
cd Backend
uv run python db/seed.py
```

Por defecto, `db/seed.py` usa `DB_TEST_URL` y se niega a sembrar bases cuyo nombre no termine en `_Test`. El modificador `--force` existe para bases distintas y solo debe usarse de forma explícita, con respaldo y autorización. **No ejecutar `--force` contra `LeonsDB` como parte de una instalación normal.**

El seed es idempotente: no duplica filas ya existentes.

---

## 10. Inicio de FastAPI

```powershell
cd Backend
uv run uvicorn app.main:app --reload --port 8000
```

Recursos:

| Recurso | URL |
|---|---|
| API | `http://localhost:8000/api/v1` |
| Swagger | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| Salud | `http://localhost:8000/health` |

---

## 11. Inicio de Angular

En otra terminal:

```powershell
cd Leons
npm start
```

Abrir `http://localhost:4200`.

Para ejecutar la salida SSR compilada:

```powershell
npm run build
npm run serve:ssr:Leons
```

El frontend de desarrollo apunta a `http://localhost:8000/api/v1` mediante `Leons/src/environments/environment.ts`. El archivo de producción contiene marcadores y debe configurarse solo si se planifica un despliegue, lo cual no forma parte de esta entrega.

---

## 12. Pruebas

```powershell
# Backend
cd Backend
uv run pytest -p no:warnings

# Frontend
cd ..\Leons
npm test
npm run build
```

Última ejecución reportada en el proyecto:

| Suite | Resultado |
|---|---:|
| Backend | 105/105 (`test_api` 30, `test_config` 27, `test_sqlserver` 48) |
| Frontend | 132/132 |
| Build Angular | correcto |

Las pruebas `test_sqlserver.py` requieren `LeonsDB_Test`. No ejecutarlas contra `LeonsDB`. `npm run e2e` usa una configuración aislada y no se ejecutó durante la preparación GITHUB-02.

---

## 13. Demostración al docente

1. Verificar que SQL Server esté iniciado y que la base elegida esté migrada y sembrada.
2. Iniciar FastAPI en el puerto `8000`.
3. Iniciar Angular en el puerto `4200`.
4. Abrir `http://localhost:4200` y revisar catálogo, ficha de mascota y refugios.
5. Probar registro/login con una cuenta demo local; las credenciales de demostración están documentadas en el código del loader y no deben reutilizarse fuera del entorno local.
6. Crear y cancelar una solicitud de adopción.
7. Revisar favoritos, alertas de rescate y estadísticas de impacto.
8. Mostrar `/docs` del backend como contrato de la API.
9. Si se requiere evidencia, usar las pruebas y documentos de `docs/`, no artefactos generados de Playwright.

---

## 14. Limitaciones y advertencias de seguridad

- Proyecto preparado para **desarrollo y demostración local**, no para producción.
- Las credenciales demo son intencionales y públicas por diseño; no reutilizar contraseñas, correos ni hashes en entornos reales.
- El guard AUD-02 solo se activa con `APP_ENV=production` y `REPOS_BACKEND=sqlserver`; no ha sido probado en un despliegue real.
- El rate limit es local al proceso; no existe backend distribuido.
- Q-08, Q-09 y Q-10 siguen abiertas: dominios reales de CORS, certificado TLS y rate limit distribuido.
- `environment.prod.ts` contiene marcadores; no se ha configurado un dominio de producción.
- No se ha validado el procedimiento desde un clon limpio.
- No se realizó push ni publicación como parte de GITHUB-02.

---

## 15. Referencias técnicas

- `AGENTS.md`: normas del proyecto, fases y decisiones operativas.
- `docs/decisiones.md`: registro ADR-lite.
- `docs/modelo-datos.md`: modelo entidad-relación y diccionario.
- `docs/REVISION-BACKEND.md`: auditoría y estado de AUD-01/AUD-02.
- `docs/G5-comparacion.md`: verificación de migraciones.
- `docs/G6-seed.md`: ejecución e idempotencia del seed.
- `Backend/README.md`: detalle operativo de la API.
- `Leons/README.md`: detalle operativo del frontend.
