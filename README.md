# 🐾 LeonS — Plataforma de Adopción Responsable

**Proyecto académico — Programación Web | Universidad Continental**

LeonS es una aplicación web orientada a promover la adopción responsable de perros y gatos en Huancayo y el Valle del Mantaro, facilitando la conexión entre personas interesadas en adoptar y refugios de animales.

El proyecto busca contribuir al bienestar animal mediante una plataforma accesible que permita consultar mascotas disponibles, conocer refugios y gestionar solicitudes de adopción.

## 1. Tecnologías utilizadas

| Componente | Tecnología |
|---|---|
| Frontend | Angular 22, TypeScript, HTML y CSS |
| Backend | Python, FastAPI |
| Base de datos | Microsoft SQL Server |
| Persistencia | SQLAlchemy 2.0, pyodbc |
| Migraciones | Alembic |
| Autenticación | JWT y bcrypt |
| Control de versiones | Git y GitHub |

La aplicación utiliza una arquitectura que separa la interfaz de usuario, la lógica de negocio y la persistencia de datos.

## 2. Funcionalidades principales

- **Catálogo de mascotas:** consulta de perros y gatos disponibles para adopción, con filtros y detalles.
- **Refugios:** visualización de información de los refugios registrados.
- **Autenticación:** registro e inicio de sesión con control de roles.
- **Solicitudes de adopción:** creación, consulta y cancelación de solicitudes.
- **Favoritos:** gestión de mascotas de interés.
- **Estadísticas:** visualización de indicadores de impacto de la plataforma.

## 3. Estructura del proyecto

```text
LeonS/
├── Leons/              # Frontend Angular
├── Backend/            # API REST FastAPI
│   ├── app/            # Lógica de negocio y endpoints
│   ├── db/             # Scripts y datos de ejemplo
│   ├── migrations/     # Migraciones de SQL Server
│   └── tests/          # Pruebas del backend
├── docs/               # Documentación técnica
└── README.md
```

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

## 5. Instalación y configuración

### Frontend — Angular

Desde la carpeta `Leons/`:

```powershell
npm install
npm start
```

Abrir en el navegador:

`http://localhost:4200`

### Backend — FastAPI

Desde la carpeta `Backend/`:

```powershell
uv sync
Copy-Item .env.example .env
```

Configurar el archivo `.env` con los datos de conexión de SQL Server y un secreto JWT propio.

Iniciar el servidor:

```powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API: `http://127.0.0.1:8000/api/v1`

Documentación interactiva: `http://127.0.0.1:8000/docs`

### Base de datos — SQL Server

Crear una base de datos local en SQL Server con la configuración de conexión correspondiente en `Backend/.env`.

Para una base de pruebas nueva, utilizar `DB_TEST_URL` y ejecutar desde `Backend/`:

```powershell
uv run alembic -x target=test upgrade head
uv run python db/seed.py
```

Las migraciones Alembic crean la estructura de las tablas y el script de inicialización incorpora datos de ejemplo. El seed está diseñado para bases cuyo nombre termina en `_Test`.

**Nota:** no ejecutar estos comandos sobre una base existente sin comprobar previamente su estado. El procedimiento completo desde un clon limpio aún no ha sido validado.

## 6. Integración del sistema

LeonS utiliza el siguiente flujo de comunicación:

**Angular → API REST FastAPI → SQLAlchemy / pyodbc → SQL Server**

Angular realiza solicitudes HTTP al backend, FastAPI procesa las operaciones y SQL Server almacena la información.

De esta manera, el sistema integra frontend, backend y base de datos.

## 7. Pruebas

Para ejecutar las pruebas del frontend:

```powershell
cd Leons
npm test
```

Para ejecutar las pruebas del backend:

```powershell
cd Backend
uv run pytest
```

Las pruebas de integración SQL requieren una base de pruebas configurada correctamente; no deben ejecutarse contra la base principal.

## 8. Documentación adicional

Para consultar información técnica más detallada:

- `Leons/README.md` — Frontend Angular.
- `Backend/README.md` — Backend FastAPI y SQL Server.
- `docs/modelo-datos.md` — Modelo de datos.
- `docs/decisiones.md` — Decisiones técnicas.

---

**LeonS — Tecnología al servicio del bienestar animal.**

Proyecto desarrollado con fines académicos para el curso de Programación Web de la Universidad Continental.

*La aplicación está preparada para desarrollo y demostración local; no constituye un servicio desplegado en producción.*
