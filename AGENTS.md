# AGENTS.md — LeonS

Instrucciones permanentes para Claude Code y otros agentes que trabajen en este repositorio. El objetivo no es solo ejecutar tareas: es **decidir bien en conjunto** antes de tocar código.

---

## 0. Cómo usar este documento

- **Claude Code:** se carga automáticamente desde la raíz. Antes de escribir código, confirma que lo entendiste con un resumen de 10 líneas y las preguntas abiertas.
- **Claude en chat:** pega este archivo completo y empieza con: *"Actúa según AGENTS.md. No escribas código todavía; primero analiza y propón."*
- **Jerarquía de instrucciones:** pedido explícito del usuario > AGENTS.md > conveniencia del agente. Si hay conflicto, **detente y pregunta**; no lo resuelvas en silencio.
- **Este documento es normativo.** Si la realidad del repositorio no coincide, repórtalo y propón una actualización; no improvises una arquitectura paralela.
- **Idioma:** español para el dominio y la documentación; inglés solo en nombres de librerías o APIs externas.

---

## 1. Proyecto y objetivo

LeonS es una plataforma de adopción responsable de perros y gatos en Huancayo y el Valle del Mantaro, Perú. Es un trabajo del curso **Programación Web, C-04**.

| Pieza | Ruta | Estado |
|---|---|---|
| Frontend | `Leons/` | Angular 22 con SSR. Completo visualmente. El snapshot del 17/11 indicaba que aún no consumía el backend (constantes y `localStorage`); la Fase 7 quedó registrada como completada en §17.4. |
| Backend nuevo | `Backend/` | **Fases 0–5 completas; Fase 6 G1–G5 cerradas y G6 ejecutada en `LeonsDB` (head `0009`, 16 mascotas / 9 refugios / 3 solicitudes / 3 usuarios sembrados, 0 duplicados).** FastAPI + Uvicorn, repositorio en memoria, 20 tablas modeladas, migraciones Alembic y repositorio SQL Server probado en `LeonsDB_Test` y `LeonsDB`. `LeonsDB` migrada a head `0009` y sembrada (G7 frontend pendiente). Fase 4.1–4.4 ejecutada (seguridad y optimizaciones); 58 pruebas verdes. Ver §4.5. |
| Backend anterior | `LeonS-Mateo/Backend/` | Solo bytecode (`.pyc`), sin fuentes, venv roto. **Se conserva intacto como referencia histórica y no se usa.** |

**Objetivo:** construir el backend nuevo con el contrato `/api/v1` que el frontend espera, sustituir la persistencia en memoria por SQL Server y, más adelante, conectar Angular a la API.

**Fuera de alcance:** rediseñar la interfaz, cambiar las rutas públicas del frontend, implementar el API en `Leons/src/server.ts` o reescribir el backend anterior.

`Leons/src/server.ts` es **solo el servidor de SSR de Angular**. No es el backend de negocio y no se le deben agregar endpoints `/api`.

---

## 2. Protocolo de colaboración y toma de decisiones

Esta sección es la más importante. Un agente que escribe código sin acordar las decisiones genera retrabajo; uno que pregunta demasiado bloquea el avance. El equilibrio es: **decidir juntos lo irreversible, ejecutar sin fricción lo reversible.**

### 2.1 Principios

1. **Hechos, supuestos y propuestas se separan siempre.** Etiqueta cada afirmación como `[HECHO]` (verificado en el repo), `[SUPUESTO]` (no verificable aún) o `[PROPUESTA]` (decisión a tomar).
2. **No inventes.** Si falta un archivo, un dato o una credencial, dilo. El bytecode no es fuente.
3. **Prefiere lo reversible.** Antes de borrar, sobrescribir o migrar, pregunta.
4. **Una fase por turno.** No mezcles auditoría, diseño y ejecución.
5. **Lo simple gana.** Si dos soluciones cumplen, elige la de menos piezas, menos dependencias y menos cambios en el frontend.
6. **El contrato manda.** Las pantallas actuales son el cliente; el JSON no se cambia por comodidad del backend.

### 2.2 Antes de implementar (checklist obligatorio)

1. Relee el objetivo y las restricciones de la fase.
2. Verifica los hechos en el repositorio (rutas, interfaces, versiones, comandos).
3. Lista los supuestos que estás haciendo.
4. Si hay una decisión con impacto, presenta **2 o 3 opciones** con la tabla de 2.3.
5. Espera la elección del usuario. No elijas por él en decisiones irreversibles.
6. Escribe un plan corto: archivos a crear/modificar y criterio de verificación.
7. Implementa **solo** lo aprobado.

### 2.3 Formato de una propuesta de decisión

```markdown
### Decisión: <título>

**Contexto:** <qué obliga a decidir>
**Restricciones:** <tiempo, curso, compatibilidad, riesgo>

| Opción | Ventajas | Costos / riesgos | Reversible | Recomendación |
|---|---|---|---|---|
| A | ... | ... | Sí/No | ⭐ |
| B | ... | ... | Sí/No | |

**Recomiendo A** porque <razón en 1–2 líneas>.
**Si no respondes**, uso A por ser la más reversible.
```

### 2.4 Preguntas

- Máximo **3 preguntas por turno**, agrupadas y con opciones concretas.
- Cada pregunta debe tener un valor por defecto seguro.
- Si el usuario no responde, avanza con el valor por defecto **solo si es reversible**; si no, detente.
- No preguntes lo que ya está decidido en la sección 16 sin señalar que contradice el registro.

### 2.5 Registro de decisiones

- Toda decisión aceptada se documenta en `docs/decisiones.md` (se crea en la Fase 0).
- Formato ADR-lite: `ID`, fecha, contexto, opciones, decisión, consecuencias.
- Los IDs ya tomados están en la sección 16. No los reabras sin una razón nueva.

### 2.6 Al revisar código

- Cada hallazgo cita `archivo:línea` y evidencia reproducible.
- Separa **defecto** (rompe algo) de **mejora** (podría ser mejor).
- Severidad: `crítico` (seguridad/pérdida de datos), `alto` (funcionalidad), `medio` (mantenibilidad), `bajo` (estilo).
- No modifiques archivos durante una revisión. El entregable es un informe.

### 2.7 Al implementar

1. Plan de 5 líneas.
2. Diff mínimo y coherente con el estilo existente.
3. Verificación ejecutada (comandos y resultado).
4. Resumen: qué cambió, qué se probó, qué queda pendiente.

### 2.8 Al cerrar cada fase

Responde con cuatro bloques y **detente**:

```text
Hecho: ...
Verificado: <comando y resultado>
Decisiones tomadas: <IDs>
Siguiente fase: <qué falta y qué necesito del usuario>
```

### 2.9 Criterios para recomendar

Ordena las opciones por estos criterios, en este orden:

1. **Cumple el entregable del curso** y lo que el docente evalúa.
2. **No rompe el frontend actual** ni el contrato JSON.
3. **Riesgo técnico** (SQL Server, credenciales, SSR, migraciones).
4. **Tiempo restante** y complejidad de la puesta en marcha.
5. **Mantenibilidad** para el equipo.

### 2.10 Señales de alerta: detente y pregunta

- Vas a borrar o mover `LeonS-Mateo/`, `Leons/` o datos existentes.
- Vas a cambiar una ruta, un campo JSON o el nombre de un service.
- Vas a ejecutar una migración o un `DROP`/`TRUNCATE`.
- Vas a agregar una dependencia pesada.
- Vas a reescribir un template o el diseño visual.
- No tienes conexión a SQL Server o no conoces las credenciales.
- El pedido contradice una decisión registrada.

---

## 3. Regla de fases y puertas de aprobación

| Fase | Entregable | ¿Escribe código? |
|---|---|---|
| 0 | Esqueleto del backend nuevo, configuración, seed y repositorio en memoria | Sí, solo en `Backend/` |
| 1 | Auth, roles y JWT | Sí |
| 2 | Catálogo, refugios, contenido y estadísticas | Sí |
| 3 | Solicitudes, favoritos, alertas y uploads | Sí |
| 4 | Auditoría del backend nuevo (4.1–4.4: seguridad y optimizaciones) | Auditoría original: **no**. Subfases 4.1–4.4: sí, solo `Backend/` y con autorización explícita |
| 5 | Diseño de BD: modelos SQLAlchemy, Alembic, `schema.sql` | Solo `Backend/db`, `Backend/migrations`, `docs/` |
| 6 | Repositorio SQL Server, seed y pruebas de integración | Sí |
| 7 | Integración del frontend Angular | Sí |
| 8 | QA, documentación y cierre | Sí |

Al final de cada fase: aplica 2.8 y espera aprobación explícita. Sin "aprobado" no se avanza.

> Nota (20/11/2026): la Fase 4 original era solo lectura, pero las subfases 4.1–4.4 se ejecutaron con autorizaciones explícitas que permitieron cambios acotados dentro de `Backend/` (ver §4.5). El informe `docs/REVISION-BACKEND.md` sigue sin entregarse.

---

## 4. Estado actual verificado

Verificado el 17/11/2026. Si algo no coincide al abrir el proyecto, repórtalo antes de asumir que este documento está desactualizado. Los cambios posteriores (Fase 4.1–4.4 y Fase 7) se registran en §4.5 y §17.4; los apartados 4.1–4.4 conservan el snapshot original.

### 4.1 Frontend (`Leons/`)

- Angular **22.2**, TypeScript **6.0**, Tailwind **4.3**, Vitest **5**.
- SSR activo: `outputMode: "server"` en `angular.json`, entrada `src/server.ts`.
- 10 rutas en `src/app/app.routes.ts`: `''`, `mascotas`, `mascotas/:id`, `refugios`, `refugios/:id`, `login`, `mis-solicitudes`, `impacto`, `sobre-nosotros`, `como-funciona`.
- `src/app/app.routes.server.ts` prerenderiza **todas** las rutas, incluidos `mascotas/:id` y `refugios/:id`, leyendo constantes en build.
- Datos en `src/app/data/`:
  - `mascotas.data.ts`: **16 mascotas**.
  - `refugios.data.ts`: **9 refugios**.
  - `solicitudes.data.ts`: **3 solicitudes demo**.
  - `detalle.data.ts` y `contenido.data.ts`: requisitos, FAQ, pasos e historias.
- `MascotasService` expone arrays síncronos (`mascotas`, `todas`, `refugios`) y métodos (`porId`, `similares`, `resumenDeRefugio`).
- `SolicitudesService` mezcla las 3 demo con las creadas por el usuario y persiste en `localStorage` (`leons.solicitudes.v1`).
- `login.ts` simula el acceso; `googleClientId = ''`.
- No existe `HttpClient`, ni `src/environments/`, ni interceptores, ni guards.

### 4.2 Backend anterior (`LeonS-Mateo/Backend/`)

- Solo quedan 34 archivos `__pycache__/*.pyc`; no hay `.py`, `pyproject.toml`, seed ni `.env`.
- El `.venv` apunta a `D:\Project-MN\LeonS-Navarro` y depende de un `C:\Python314` inexistente.
- **No es usable ni auditable.** Se conserva por trazabilidad y para no perder la referencia del contrato.
- Prohibido descompilarlo, citarlo como fuente o intentar revivirlo.

### 4.3 Backend nuevo (`Backend/`)

- **Existe y funciona en memoria.** Implementa las Fases 0–5 del contrato `/api/v1`.
- Stack: FastAPI + Uvicorn + Pydantic v2; SQLAlchemy 2.0 + Alembic + pyodbc ya están instalados y los modelos cubren las 20 tablas. El repositorio SQL Server vive en `repositories/sqlserver.py` y se ejercita en `tests/test_sqlserver.py` contra `LeonsDB_Test`.
- Estructura: `modules/` (routers), `services/` (reglas), `repositories/memory.py`, `adapters/` (storage, PDF, rate limit, notificaciones), `data/seed.json`, `db/` (modelos y export) y `migrations/` (Alembic).
- Capas: `router → service → repository`; los routers no tienen reglas de negocio. Los servicios se tipan contra el protocolo `Repositorio`, no contra `MemoryRepository` (D-020).
- Seed generado el 17/11/2026 desde Angular con `Leons/scripts/export-seed.ts`: **16 mascotas, 9 refugios, 3 solicitudes demo**.
- Python fijado en **3.13** con `Backend/.python-version` (ver D-013).
- Verificado:
  - `uv run pytest -p no:warnings` → **28/28** (15 en memoria + 13 de integración).
  - `uv run uvicorn app.main:app --port 8010` → `/health` 200, `/docs` 200,
    `/api/v1/mascotas` total 16, `/api/v1/estadisticas/impacto` 702 adoptadas.
  - `uv run alembic -x target=test upgrade head` → `0009`; `check` sin diferencias;
    round-trip `downgrade -1` / `upgrade head` correcto.
  - `uv run python db/seed.py` dos veces → la segunda inserta 0 filas.
  - 18 rutas GET comparadas entre `memory` y `sqlserver`: JSON idéntico.
  - G5 (18/11/2026): `LeonsDB` migrada a head `0009` con backup verificado; `alembic check` limpio; 22 tablas, 0 filas; `sysdiagrams` intacto (D-040).
- Estado al 20/11/2026: Fase 4.1–4.4 ejecutada (ver §4.5); Fase 7 (integración frontend) completada; Fase 8 (QA y cierre) en curso. Este apartado conserva el snapshot del 17/11.

### 4.4 Entorno disponible

- Node **24.22**, npm **11.19**, `uv` **0.13.x**, Python **3.13.18** (fijado con `.python-version`).
- No hay `git` en el `PATH` de esta máquina; si se necesita, usar la ruta de Git for Windows o pedir al usuario.
- SQL Server: **pendiente de confirmar** instancia, versión y autenticación (ver sección 16).

### 4.5 Fase 4 — auditoría, seguridad y optimizaciones (20/11/2026)

La auditoría original (prompt §18.3) era solo lectura y **no generó**
`docs/REVISION-BACKEND.md`. Las subfases posteriores sí fueron autorizadas
por escrito y se limitaron a `Backend/`:

| Subfase | Alcance | Archivos tocados |
|---|---|---|
| 4.1 | S1 (secreto JWT en producción), S6 (rate limit de `/auth/login` y `/auth/registro`), S10 (cuentas desactivadas) | `app/config.py`, `app/adapters/rate_limit.py`, `app/container.py`, `app/modules/auth.py`, `app/dependencies.py`, `tests/test_api.py` |
| 4.2 | P1 (filtros/orden/paginación del catálogo en SQL), P2 (carga por lotes de relaciones), P3 (agregaciones de impacto), P6 (búsqueda de solicitudes en SQL) | `app/domain.py` (`FiltroMascotas`, `buscar_mascotas`, `buscar_solicitudes`), `app/services/{catalogo,solicitudes}.py`, `app/modules/{estadisticas,solicitudes}.py`, `app/mapper.py`, `app/repositories/{memory,sqlserver}.py`, `tests/{test_api,test_sqlserver}.py` |
| 4.3 | Métodos de repositorio para evitar cargas completas: `listar_mascotas_por_ids`, `listar_mascotas_de_refugio`, `estadisticas_mascotas`, `listar_favoritos_mascotas` | `app/domain.py` (Protocolo), ambos repositorios, `app/services/catalogo.py`, `app/modules/{mascotas,refugios,favoritos}.py` |
| 4.4 | S2 (CORS configurable), S3 (TLS de SQL Server), puerta de configuración de producción y evaluación de rate limit distribuido | `app/config.py`, `.env.example`, `tests/test_config.py` (nuevo) |

Detalles de la Fase 4.4:

- **S2:** `CORS_ORIGINS` (lista JSON) mantiene en desarrollo
  `http://localhost:4200` y `http://localhost:4000`. En producción es
  obligatoria, rechaza `*` (con credenciales activas) y cualquier origen
  localhost/127.0.0.1/0.0.0.0/::1. `app.py` sigue usando
  `settings.cors_origins` con `allow_credentials=True`. No se inventaron
  dominios: los reales son Q-08; los `*.example.com` de `.env.example` y de
  pruebas son marcadores.
- **S3:** ODBC Driver 18. En desarrollo se conserva
  `TrustServerCertificate=yes`. En producción se exige `DB_URL` con
  `Encrypt=yes` y se rechaza `TrustServerCertificate` activo. **No se validó
  un certificado real**: solo se valida la cadena de conexión. Requiere un
  certificado válido del servidor (Q-09) antes del despliegue.
- **Rate limit distribuido:** el adaptador `adapters/rate_limit.py` sigue siendo
  en memoria y local a cada proceso (ventana deslizante por IP). Con varios
  workers o instancias el límite efectivo se multiplica. Es suficiente para
  desarrollo y para una sola instancia. Para producción con réplicas se
  propone un backend compartido (por ejemplo Redis): clave por IP + endpoint,
  `INCR` atómico con `EXPIRE`, variables nuevas (`RATE_LIMIT_BACKEND`,
  `REDIS_URL`), servicio Redis con autenticación/TLS y política de fallo
  explícita. **No implementado**: requiere autorización independiente,
  dependencia nueva e infraestructura (D-043, Q-10). Los límites actuales se
  conservan: alertas 5/60 s, login 10/60 s, registro 5/60 s; el código de
  error sigue siendo `RATE_LIMIT` (HTTP 429).
- **Puerta de producción:** `Settings` valida que `APP_ENV=production` no
  herede secretos ni orígenes de desarrollo: JWT propio ≥ 32 caracteres (S1),
  CORS explícito (S2), DB_URL con TLS (S3). Los mensajes de error no incluyen
  la URL de conexión ni secretos.

Verificación de la Fase 4.4:

- `uv run pytest -p no:warnings` → **58 passed** (23 `test_api` + 17
  `test_sqlserver` + 18 `test_config`).
- `uv run pytest tests/test_sqlserver.py -p no:warnings` → **17 passed**.
- `uv run alembic -x target=main check` → imprime
  `No new upgrade operations detected.`; el wrapper `uv` termina con código 1
  aunque Alembic no proponga cambios (comportamiento ya observado, no un
  diff de esquema).
- Comprobación ad-hoc de desarrollo/producción: `/health` 200 en ambos,
  `/api/v1/mascotas` → 16, CORS de producción solo el origen configurado,
  rechazo de CORS local/heredado y de `TrustServerCertificate=yes`.
- `LeonsDB`: solo lectura; head `0009`; 16 mascotas / 9 refugios / 3
  solicitudes / 3 usuarios. Sin migraciones, seeds ni escrituras nuevas.

Decisiones D-040 a D-043 y preguntas Q-08 a Q-10 en §16. **Regularizado en
5.6.3.3B:** los ADR-lite de D-040 a D-043 se replicaron en `docs/decisiones.md`;
D-036 conserva su significado histórico. Los informes E2E previos pueden citar
D-039 con el identificador anterior.

### 4.6 Fase 4 complementaria — AUD-01 y AUD-02 (S4-A/S4-B/S4-C, 20/11/2026)

**Alcance autorizado:** S4-A fue análisis estático sin cambios; S4-B aplicó solo
la opción A de AUD-01 y AUD-02 en `Backend/app/**` y `Backend/tests/**`; S4-C fue
validación independiente en un proceso nuevo de FastAPI (`:8020`,
`APP_ENV=development`, `REPOS_BACKEND=memory`, sin conexión a SQL Server), aprobada
por el usuario para **desarrollo y demostración universitaria local**. No es
despliegue ni cierre definitivo.

- **AUD-01 — corregido y validado para desarrollo local.** `app/services/auth.py`
  rechaza cualquier `rol != "adoptante"` con `ForbiddenError` (HTTP 403,
  `FORBIDDEN`) antes de consultar duplicados o crear usuarios, y persiste siempre
  `rol="adoptante"` y `refugio_id=None`. `admin` sigue dando 422 desde `schemas.py`,
  que no se modificó. Evidencia S4-C: adoptante **201**, refugio **403**, admin
  **422**, token del adoptante sin permisos de refugio/admin (**403**), correos
  rechazados sin cuenta (**401**) y las 3 cuentas demo con login **200**.
- **AUD-02 — mitigado mediante comprobación de arranque, con limitaciones.**
  `app/seguridad_arranque.py` consulta, solo con `APP_ENV=production` y
  `REPOS_BACKEND=sqlserver`,
  `SELECT COUNT(*) FROM dbo.usuarios WHERE LOWER(email) IN :correos`
  (parametrizada, `expanding=True`) usando los correos de `DEMO_USERS` (D-016).
  Falla cerrado ante cuentas demo o errores de verificación, con mensajes
  genéricos que no revelan correos, hashes, contraseñas, JWT ni cadenas de conexión.
  `app.py:51-55,66` lo ejecuta en el `lifespan`, antes de aceptar solicitudes.
  **No probado en un despliegue real de producción** y **no reemplaza la rotación
  o eliminación controlada de credenciales demo**. Detecta correos, no DNIs ni hashes.
- **Regresiones:** S4-B → 105/105 backend (`test_api` 30, `test_config` 27,
  `test_sqlserver` 48) y 132/132 frontend; S4-C → 13/13 comprobaciones HTTP y
  8/8 pruebas específicas aisladas. `LeonsDB` y `LeonsDB_Test` conservaron su
  baseline (`0009`; huella de `dbo.usuarios` idéntica antes y después).
- **Sin cambios:** rutas, campos JSON, `schemas.py`, seeds, migraciones, `.env`,
  frontend ni documentación (hasta este cierre). AUD-03…AUD-28 y Q-08/Q-09/Q-10
  permanecen en su estado anterior. El proyecto **no está listo para producción**.

---

## 5. Arquitectura objetivo del backend

```
Backend/
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
├── alembic.ini
├── app/
│   ├── main.py              # uvicorn app.main:app
│   ├── app.py               # create_app: CORS, handlers, /health, /uploads
│   ├── config.py            # Settings con pydantic-settings
│   ├── container.py         # Dependencies: repos, storage, notificaciones
│   ├── domain.py            # dataclasses + Protocolos de repositorio
│   ├── schemas.py           # Pydantic v2, alias camelCase
│   ├── mapper.py            # dominio → DTO con campos de presentación
│   ├── security.py          # bcrypt + JWT
│   ├── errors.py
│   ├── modules/             # auth, mascotas, refugios, solicitudes,
│   │                        # favoritos, alertas, contenido, estadisticas
│   ├── services/            # reglas de negocio y transacciones
│   ├── repositories/
│   │   ├── memory.py        # Fases 0–3
│   │   └── sqlserver.py     # Fase 6
│   ├── adapters/            # storage, pdf, notificaciones, rate_limit
│   ├── db/                  # SQLAlchemy: base, session, modelos
│   └── data/                # seed.json + loader.py
├── migrations/              # versiones de Alembic
├── db/
│   ├── seed.py
│   └── schema.sql           # export legible para SSMS/entrega
└── tests/
    ├── conftest.py
    ├── test_api.py          # 23 pruebas (15 originales + seguridad/optimizaciones)
    ├── test_config.py       # 18 pruebas de configuración segura (Fase 4.4)
    └── test_sqlserver.py    # integración contra LeonsDB_Test (17 pruebas)
```

Capas: `router → service → repository → SQLAlchemy Session → pyodbc → SQL Server`.
Los routers no contienen reglas de negocio; los repositorios no conocen HTTP.

---

## 6. Modelo de dominio y contrato JSON

Entidades: **Usuario**, **Mascota**, **Refugio**, **Solicitud**, **Favorito**, **AlertaRescate**, **PasoContenido**, **PreguntaFrecuente**, **Contenido**, **Page**.

- Nombres de dominio en español; JSON en **camelCase**.
- Pydantic con `alias_generator=to_camel` y `populate_by_name=True`.
- Los DTO deben coincidir con las interfaces de `Leons/src/app/data/*.ts` (`Mascota`, `Refugio`, `Solicitud`), incluidos `fichaId`, `refugioId`, `motivoCancelacion`, `totalPages`.
- **Campos de presentación** (`badgeClase`, `chipTexto`, `chipClase`, `fechaTexto`, `puntoClase`, `pasoTexto`, `headerClase`, `iconoMini`, `barraClase`, textos de `etapas`): se calculan en `mapper.py` y **no se guardan en la BD**.
- Los arrays (`salud`, `galeria`, `rasgos`, `etapas`, `fotosSeguimiento`) se normalizan en tablas hijas y se reconstruyen en el mapper.

---

## 7. API `/api/v1`

| Grupo | Endpoints |
|---|---|
| Sistema | `GET /health`, `GET /docs` |
| Auth | `POST /auth/registro`, `/auth/login`, `/auth/google`, `/auth/recuperar`; `GET /auth/me` |
| Catálogo | `GET /mascotas`, `/mascotas/destacadas`, `/mascotas/stats`, `/mascotas/{id}`, `/mascotas/{id}/detalle`, `/mascotas/{id}/similares`; `POST/PATCH/DELETE /mascotas` (admin) |
| Refugios | `GET /refugios`, `/refugios/{id}`, `/refugios/{id}/mascotas` |
| Solicitudes | `GET/POST /solicitudes`, `GET /solicitudes/{id}`, `PATCH /solicitudes/{id}/cancelar`, `PATCH /solicitudes/{id}/etapa`, `POST /solicitudes/{id}/citas`, `POST /solicitudes/{id}/mensajes`, `POST /solicitudes/{id}/seguimiento` |
| Favoritos | `GET/POST/DELETE /favoritos` |
| Alertas | `POST/GET /alertas-rescate` |
| Contenido | `GET /contenido`, `/contenido/pasos`, `/contenido/faqs` |
| Estadísticas | `GET /estadisticas/impacto` |

Reglas:

- Paginación `page`, `limit`, `total`, `totalPages`.
- Errores con `code`, `message`, `details`.
- `POST /solicitudes` rechaza duplicados activos y mascotas no disponibles.
- `POST /auth/login` acepta correo **o** DNI.
- Endpoints públicos no exponen `passwordHash`, `googleId` ni DNI de terceros.
- No cambiar rutas ni campos sin proponer `/api/v2` y obtener aprobación.

---

## 8. Base de datos

### 8.1 Motor y acceso

- **SQL Server 2019+** (Express válido).
- Collation de la base: **`Modern_Spanish_CI_AI`**.
- **SQLAlchemy 2.0** (ORM declarativo) + **Alembic** + **pyodbc** + **ODBC Driver 18**.
- Sin SQL concatenado: consultas con parámetros o expresiones del ORM.
- Esquema revisable en SSMS y exportado a `db/schema.sql`.

### 8.2 Configuración

```dotenv
# Windows Auth (Q-02: valor por defecto en local)
DB_URL=mssql+pyodbc://@localhost\SQLEXPRESS/LeonsDB?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&Encrypt=yes&TrustServerCertificate=yes
DB_TEST_URL=mssql+pyodbc://@localhost\SQLEXPRESS/LeonsDB_Test?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&Encrypt=yes&TrustServerCertificate=yes
REPOS_BACKEND=sqlserver
JWT_SECRET=cambia-esto
```

- La instancia nombrada lleva la **barra invertida literal** (`localhost\SQLEXPRESS`).
  SQLAlchemy 2.1 **no** decodifica `%5C` en el host: verificado el 18/11/2026,
  `%5C` falla con «No se pudo abrir una conexión».
- Login SQL (solo si Q-02 cambia):
  `mssql+pyodbc://leons_app:ClaveSegura@localhost\SQLEXPRESS/LeonsDB?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes`.
- `create_engine(..., pool_pre_ping=True, pool_recycle=1800)`.
- `.env` fuera de git; `.env.example` documenta ambos modos sin secretos reales.
- `CORS_ORIGINS` (Fase 4.4, S2): en desarrollo mantiene los dos orígenes
  locales; en producción es obligatorio y no admite `*` ni orígenes locales.
- TLS (Fase 4.4, S3): ODBC Driver 18 cifra por defecto, pero
  `TrustServerCertificate=yes` **desactiva la validación del certificado**.
  Solo se tolera en desarrollo; en producción se exige `Encrypt=yes` y se
  rechaza `TrustServerCertificate`. La validación implementada es de la
  cadena de conexión, no de un certificado real (Q-09).

### 8.3 Tablas (20)

`migraciones`, `distritos`, `usuarios`, `refugios`, `refugio_especies`, `mascotas`, `mascota_salud`, `mascota_fotos`, `mascota_rasgos`, `mascota_historia`, `mascota_cuidados`, `solicitudes`, `solicitud_eventos`, `citas`, `mensajes`, `seguimiento_fotos`, `favoritos`, `alertas_rescate`, `contenido_pasos`, `contenido_faqs`.

- Los modelos viven en `Backend/app/db/models/` y el detalle está en `docs/modelo-datos.md`.
- Alembic añade su tabla técnica `alembic_version`: no es una tabla de dominio
  y no se cuenta en las 20 (D-022); la base tiene 21 tablas en total.
- Revisiones: `0001` (esquema base), `0002` (columnas del contrato JSON, solo
  aditiva), `0003` (`NTEXT` → `NVARCHAR(MAX)`), `0004` (`alertas_rescate.nombre`/`mensaje`),
  `0005` (`mascota_historia`, `mascota_cuidados`, distrito y presentación de mascota),
  `0006` (longitud de `mascota_rasgos.clase`), `0007` (`mascotas.vacunado`/`esterilizado`),
  `0008` (`IX_mascotas_catalogo` con `INCLUDE`) y `0009` (`refugios.orden`).
  Ver D-019 y D-026 a D-035.

### 8.4 Reglas de modelado

- `refugios.id` es `NVARCHAR(60)` (slug), no numérico.
- `mascotas.id` es `INT IDENTITY(1,1)`; el seed preserva 1–16 con `IDENTITY_INSERT` y `DBCC CHECKIDENT`.
- `usuarios.email` y `usuarios.dni` únicos; `dni` nullable para Google.
- `solicitudes.codigo` único (`#SOL-HYO-<año>-<NNN>`).
- Una sola postulación activa por usuario y mascota, sin bloquear una nueva tras cancelar:

```python
Index(
    "UX_solicitudes_activa",
    "usuario_id",
    "mascota_id",
    unique=True,
    mssql_where=text("estado = 'activa'"),
)
```

- `refugios.adoptadas_historicas` y `en_acogida_actual` son contadores históricos; los valores demo (86, 72, 110…) no coinciden con las 16 mascotas y eso se justifica en `docs/modelo-datos.md`.
- `seguimiento_fotos` guarda metadatos; el archivo vive en `/uploads`.

### 8.5 Trampas de SQL Server

1. **Cascadas múltiples:** `solicitudes` referencia `usuarios`, `mascotas` y `refugios`; `mascotas` también referencia `refugios`. Usar `ondelete="NO ACTION"` fuera de las hijas directas de `solicitudes`.
2. **Sin `ENUM`:** `NVARCHAR(20)` + `CHECK` (`CK_mascotas_estado`, etc.).
3. **Sin `BOOLEAN`:** `Boolean` de SQLAlchemy se mapea a `BIT`.
4. **Tildes:** usar `Unicode` para `NVARCHAR(n)` y `mssql.NVARCHAR(None)` para
   `NVARCHAR(MAX)`. `UnicodeText` se traduce a `NTEXT` (obsoleto) en SQL Server:
   no usarlo. Nunca `String` para texto de usuario.
5. **Paginación:** `ORDER BY ... OFFSET ... ROWS FETCH NEXT ... ROWS ONLY`.
6. **Búsqueda:** `LIKE` con parámetros; escapar `%`, `_` y `[`.
7. **Identidad:** `OUTPUT INSERTED.id` o `SCOPE_IDENTITY()`; nunca `@@IDENTITY`.
8. **Fechas:** `DATETIME2` en UTC; serializar ISO 8601.

### 8.6 Alembic

```powershell
cd Backend

# Validar en la base de pruebas
uv run alembic -x target=test upgrade head
uv run alembic -x target=test check

# Aplicar a LeonsDB (Fase 6)
uv run alembic -x target=main upgrade head

uv run alembic -x target=main revision --autogenerate -m "cambio"
uv run alembic -x target=test downgrade -1
```

- `-x target=...` va **antes** del subcomando; si se coloca después, Alembic
  responde `unrecognized arguments`.
- `env.py` toma la URL de `Settings`, no de un valor hardcodeado.
- `target_metadata = Base.metadata`, `compare_type=True`,
  `compare_server_default=False`.
- `include_object` filtra `sysdiagrams`, la tabla que crea SSMS en `LeonsDB`.
  Sin ese filtro, `autogenerate` propone borrarla (D-034).
- `alembic.ini` no debe contener `timezone = UTC`: Windows no trae `tzdata` y
  Alembic falla con «Can't locate timezone: UTC».
- Cada cambio de esquema es una revisión nueva; no editar una migración ya
  aplicada.
- `Backend/db/schema.sql` se regenera con `uv run python db/export_schema.py`;
  no se edita a mano.

---

## 9. Reglas de negocio

- Roles: `adoptante`, `refugio`, `admin`.
- Un adoptante puede postular a una mascota disponible; no puede tener dos postulaciones activas a la misma mascota.
- Una mascota adoptada o en acogida no se puede postular.
- Cancelar exige motivo y no borra el historial.
- Flujo de 5 pasos: Enviada → Revisión → Visita/Entrevista → Aprobación → Adopción.
- El refugio cambia la etapa, agenda cita y deja mensajes.
- Seguimiento post-adopción a 1, 3 y 6 meses.
- Estadísticas por especie/distrito se calculan con agregaciones SQL, no cargando todas las filas.

---

## 10. Seed y datos demo

- `Leons/scripts/export-seed.ts` (ejecutado con `tsx`) importa las constantes de Angular y genera `Backend/app/data/seed.json`: 16 mascotas, 9 refugios, 3 solicitudes y contenido.
- `Backend/db/seed.py` inserta de forma **idempotente** y preserva ids.
- El seed es la única fuente de datos inicial. Prohibido inventar mascotas, refugios o solicitudes "parecidas".
- Si una constante cambia en Angular, se regenera el seed; no se edita a mano.

---

## 11. Frontend: integración sin romper las pantallas

- Mantener la **API pública** de `MascotasService` y `SolicitudesService`; cambia la fuente, no la forma.
- Cargar datos al iniciar con `provideAppInitializer` + `firstValueFrom`, guardando en arrays/signals; usar `TransferState` para no duplicar la carga en SSR.
- Crear `src/environments/environment.ts` con `apiUrl`.
- Añadir `core/api/api.config.ts`, `core/auth/auth.service.ts`, interceptores y `authGuard`.
- Token en `localStorage` solo en navegador; la autenticación no se renderiza en SSR.
- `login.ts` pasa de simulación a `AuthService`, manteniendo el diseño.
- `SolicitudesService` elimina demo y `localStorage` al final de la Fase 7.
- Favoritos pasan del signal local a `FavoritosService`, sin tocar el HTML.
- En `app.routes.server.ts`, `mascotas`, `mascotas/:id`, `refugios` y `refugios/:id` pasan a `RenderMode.Server`; el marketing sigue prerenderizado.
- En SSR, las peticiones usan URL absoluta. CORS debe permitir `http://localhost:4200` y `http://localhost:4000`.

---

## 12. Pruebas

### Backend

```powershell
cd Backend
uv run pytest -p no:warnings
```

- 15 pruebas equivalentes a las del backend anterior: `test_health`, `test_mascotas_paginacion_y_estado`, `test_mascotas_filtros`, `test_stats_detalle_y_similares`, `test_refugios`, `test_contenido_e_impacto`, `test_registro_y_perfil`, `test_registro_rechaza_datos_invalidos`, `test_login_por_correo_y_dni`, `test_listar_solicitudes_demo`, `test_crear_solicitud_duplicados_y_no_disponible`, `test_cancelar_y_documentos_pdf`, `test_favoritos`, `test_fotos_seguimiento`, `test_alertas_rescate`.
- `tests/test_sqlserver.py` usa `LeonsDB_Test`, prepara esquema y seed, y **no toca `LeonsDB`**.
- Total verificado el 20/11/2026: **58 pruebas** (23 en `test_api.py`, 18 en `test_config.py`, 17 en `test_sqlserver.py`). `tests/test_config.py` cubre S1, S2, S3, S6 y S10 sin base de datos.

### Frontend

```powershell
cd Leons
npm test
npm run build
```

### Checklist manual

- [ ] Catálogo con filtros, orden, paginación y favoritos.
- [ ] Ficha de mascota completa.
- [ ] Refugios: listado, detalle y resumen.
- [ ] Registro y login (correo y DNI).
- [ ] Crear y cancelar solicitud.
- [ ] Panel de refugio: etapa, cita y mensaje.
- [ ] Alerta de rescate.
- [ ] Recarga directa de `/mascotas/1` y `/refugios/huellitas-wanka`.

---

## 13. Convenciones

### Python

- PEP 8, type hints, `from __future__ import annotations`, nombres de dominio en español.
- Pydantic para entrada/salida; no devolver dataclasses crudas.
- `logging`, nunca `print`.
- Dependencias nuevas solo con justificación y aprobación.

### SQLAlchemy

- Modelos declarativos en `app/db/models/`, un archivo por agregado.
- `Mapped[...]` + `mapped_column(...)`.
- `Unicode`/`UnicodeText` para texto; `Boolean` para `BIT`; `Numeric(3,1)` para edad.
- Nombres de constraints: `PK_`, `FK_`, `CK_`, `UX_`, `IX_`.
- Relaciones con `lazy="selectin"` cuando se serialicen; evitar N+1.

### SQL

- Tablas y columnas en `snake_case` y plural.
- Toda migración se prueba en `LeonsDB_Test` antes de `LeonsDB`.

### TypeScript / Angular

- Standalone, signals, `inject()`, Tailwind.
- camelCase en TS y JSON.
- Prettier; no reformatear archivos ajenos al cambio.

### Documentación

- `docs/decisiones.md`: registro de decisiones.
- `docs/REVISION-BACKEND.md`: auditoría.
- `docs/modelo-datos.md`: diagrama Mermaid y diccionario.
- Actualizar `AGENTS.md` si cambia la arquitectura.

---

## 14. Seguridad

- `.env` fuera de git; `.env.example` sin secretos.
- `JWT_SECRET` fuerte y distinto por entorno.
- bcrypt para contraseñas; nunca texto plano.
- Consultas parametrizadas; sin concatenación.
- CORS con lista blanca; no `*` con credenciales. En producción,
  `CORS_ORIGINS` es obligatorio y no puede incluir localhost (D-041, Q-08).
- Rate limit en alertas (5/60 s), login (10/60 s) y registro (5/60 s), con
  código `RATE_LIMIT`. Es local al proceso; para varias instancias requiere
  D-043/Q-10 (aún no autorizado).
- Producción no arranca con `JWT_SECRET` débil, CORS heredado ni
  `TrustServerCertificate=yes` (S1/S2/S3, D-042, Q-09).
- Uploads: validar MIME y tamaño; evitar path traversal.
- No loggear tokens, contraseñas ni DNI completos.
- Público por diseño: teléfono/WhatsApp de refugios. Privado: email y DNI de usuarios.

---

## 15. Guardrails

**Prohibido:**

- Usar, descompilar o revivir `LeonS-Mateo/Backend/`.
- Modificar `LeonS-Mateo/` sin pedido explícito.
- Implementar el API en `Leons/src/server.ts`.
- Cambiar rutas, contratos JSON o nombres de services sin aprobación.
- Reescribir templates o el diseño visual.
- Versionar `.venv/`, `__pycache__/`, `dist/`, `node_modules/`, `.env`.
- Ejecutar migraciones contra `master`.
- Mezclar fases o continuar sin aprobación.

**Si falta información, detente y pregunta.** Un turno corto con una buena pregunta vale más que un cambio grande basado en suposiciones.

---

## 16. Registro de decisiones y preguntas abiertas

### 16.1 Decisiones tomadas (no reabrir sin razón nueva)

| ID | Decisión | Consecuencia |
|---|---|---|
| D-001 | Backend nuevo, no recuperar el anterior | Se crea `Backend/` desde cero |
| D-002 | Ubicación `Backend/` en la raíz | Fuera de `Leons/` y de `LeonS-Mateo/` |
| D-003 | FastAPI + Uvicorn | Es el stack del docente |
| D-004 | SQLAlchemy 2.0 + Alembic + pyodbc | ORM y migraciones versionadas |
| D-005 | SQL Server (`LeonsDB` y `LeonsDB_Test`) | Requiere ODBC Driver 18 |
| D-006 | Contrato `/api/v1` completo | Auth, catálogo, solicitudes, favoritos, alertas, contenido, stats |
| D-007 | JSON camelCase compatible con Angular | No se tocan los templates |
| D-008 | Campos de presentación calculados, no persistidos | Mapper en el backend |
| D-009 | Seed exportado desde las constantes de Angular | 16 mascotas, 9 refugios, 3 solicitudes |
| D-010 | `LeonS-Mateo/` intacto | Solo referencia histórica |
| D-011 | Fases con puertas de aprobación | Una fase por turno |
| D-012 | Revisión antes de SQL Server | Fase 4 es solo lectura |
| D-013 | Fijar Python 3.13 con `Backend/.python-version` | Wheels disponibles; nadie compila `pyyaml` |
| D-014 | La paginación devuelve la clave `items` | `{ items, page, limit, total, totalPages }` |
| D-015 | PDF mínimo propio en `adapters/pdf.py` | Sin dependencias; solo texto plano |
| D-016 | Credenciales demo en `data/loader.py`, no en el seed | Hash bcrypt con `lru_cache` |
| D-017 | Una solicitud nueva nace en la etapa 2 | Coincide con el frontend actual |
| D-018 | Overrides editoriales para Chaska (id 1) en `detalles` | Mapper usa plantillas si no hay override |
| D-019 | Migraciones aditivas `0002` y `0003` sobre el esquema existente | `LeonsDB` se actualiza sin `DROP` ni pérdida de datos |
| D-020 | Los servicios dependen del protocolo `Repositorio` | La Fase 6 cambia solo el contenedor |
| D-021 | `contenido_pasos.tipo` con `orden` único global | Requisitos sin crear una tabla 19 |
| D-022 | Alembic usa `alembic_version`; `migraciones` es funcional | 21 tablas en la base: 20 de dominio + la técnica |
| D-023 | `fichaId` derivado del `id`, no persistido | Semilla `LS-HYO-{481+id}`; altas `{5000+id}` |
| D-024 | `alertas_rescate.estado` ↔ `atendida` calculado | Mapper traduce `estado <> 'nueva'` |
| D-025 | `crear_*()` inserta y devuelve la entidad con el id de SQL Server | Los servicios dejan de calcular ids y códigos |
| D-026 | `alertas_rescate.nombre` y `mensaje` con migración aditiva `0004` | No se copia `contacto` ni se inventan mensajes |
| D-027 | Comparar `LeonsDB` con `0001` antes de cualquier `stamp` | `stamp`/`upgrade` sobre `LeonsDB` siguen pendientes |
| D-028 | Matriz de mapeo dominio ↔ tablas como base de la Fase 6 | Reglas auditables y verificadas contra el seed |
| D-029 | Distrito, `etiqueta_clase` e iconos de rasgo con columnas propias | Migración aditiva `0005` |
| D-030 | `mascota_historia`, `mascota_cuidados` y cita editorial en `mascotas` | La base pasa a 20 tablas de dominio |
| D-031 | `cierre` y `destacado` de una postulación se derivan | Diferencia cosmética documentada |
| D-032 | `mascotas.vacunado`/`esterilizado` persistidos con respaldo derivado | Migración aditiva `0007`; paridad 16/16 |
| D-033 | Los textos editoriales de las solicitudes demo se derivan | Diferencia cosmética documentada |
| D-034 | `sysdiagrams` filtrado en `env.py`; índice del catálogo con `INCLUDE` | `alembic check` limpio; revisión `0008` |
| D-035 | `refugios.orden` conserva el orden editorial del listado | Paridad 18/18 rutas GET entre memoria y SQL Server |
| D-040 | G5/G6: migrar y sembrar `LeonsDB` con backup verificado | Head `0009`, 16/9/3/3 filas, seed idempotente; sin escrituras posteriores |
| D-041 | CORS explícito en producción (`CORS_ORIGINS`) | No se heredan localhost; se rechaza `*`; dominios reales pendientes (Q-08) |
| D-042 | TLS obligatorio en producción (`Encrypt=yes`, sin `TrustServerCertificate`) | Solo se valida la cadena de conexión; certificado real pendiente (Q-09) |
| D-043 | Rate limit distribuido: evaluado, **no implementado** | Se mantiene el limitador en memoria; Redis requiere autorización, dependencia e infraestructura (Q-10) |

El detalle de cada decisión (contexto, opciones y consecuencias) está en `docs/decisiones.md`. D-036 conserva su significado histórico: prefijo doble de CHECK de Alembic SQL Server. La correspondencia aplicada en 5.6.3.3B es: D-036 migración/seed → D-040; D-037 CORS → D-041; D-038 TLS → D-042; D-039 rate limit → D-043. Los informes E2E previos conservan sus referencias originales por ser evidencia histórica.

### 16.2 Preguntas abiertas (responder antes de la fase que corresponda)

| # | Pregunta | Fase | Valor por defecto | Estado |
|---|---|---|---|---|
| Q-01 | ¿SQL Server Express, Developer o Standard? ¿Instancia y puerto? | 5 | `localhost\SQLEXPRESS` | Abierta |
| Q-02 | ¿Autenticación Windows o login SQL `leons_app`? | 5 | Windows Auth en local | Abierta |
| Q-03 | ¿El docente exige SQL puro en vez de SQLAlchemy? | 5 | SQLAlchemy + `schema.sql` exportado | Abierta |
| Q-04 | ¿Google OAuth real o stub documentado? | 1 | Stub que responde 501 | Respondida con el valor por defecto |
| Q-05 | ¿PDF/carnet obligatorio en la entrega? | 3 | Generador mínimo sin dependencias | Respondida con D-015 |
| Q-06 | ¿Despliegue local o en nube? | 8 | Local (Uvicorn + `npm start`) | Abierta |
| Q-07 | ¿El backend debe entregarse dentro de `LeonS-Mateo`? | 0 | No: `Backend/` en la raíz | Respondida con D-002 |
| Q-08 | ¿Cuáles son los dominios reales del frontend en producción para `CORS_ORIGINS`? | 8 | Sin dominios inventados; blocking para el despliegue | Abierta |
| Q-09 | ¿El servidor SQL tiene un certificado válido firmado por una CA de confianza? | 8 | Sí; de lo contrario no se puede desplegar con TLS seguro | Abierta |
| Q-10 | ¿Se autoriza un backend compartido de rate limiting (Redis u otro) para múltiples instancias? | 8 | No: se mantiene el limitador en memoria | Abierta |

Si una respuesta cambia una decisión D-xxx, actualiza este registro y avisa.

---

## 17. Definition of Done

### 17.1 Fases 0–3 (verificadas el 17/11/2026)

- [x] `Backend/` creado con estructura, README y `.env.example`.
- [x] `uv run pytest` → 15/15.
- [x] `/health` y `/docs` funcionando.
- [x] `GET /api/v1/mascotas` → 16; `/refugios` → 9; `/solicitudes` → 3 demo.
- [x] Login por correo y DNI; `/auth/me` valida el token.
- [x] Reglas de duplicado y mascota no disponible verificadas.
- [x] `LeonS-Mateo/` sin cambios.
- [x] `AGENTS.md` y `docs/decisiones.md` actualizados.

### 17.2 Fase 5 (verificada el 18/11/2026)

- [x] `Backend/app/db/models/` mapea las 20 tablas; `Base.metadata` confirma 20.
- [x] `docs/modelo-datos.md` con diagrama Mermaid, diccionario y justificación
      de `adoptadas_historicas` / `en_acogida_actual` y de `etapa = 2`.
- [x] `0001` base + `0002` aditiva + `0003` (`NTEXT` → `NVARCHAR(MAX)`).
- [x] `uv run alembic -x target=test upgrade head` → `0009`; `check` sin diferencias.
- [x] `Backend/db/schema.sql` exportado: 20 `CREATE TABLE`, 20 índices, 0 `NTEXT`.
- [x] Protocolo `Repositorio` en `domain.py`; servicios y contenedor desacoplados.
- [x] `uv run pytest` → 15/15 en memoria.
- [x] `LeonsDB` intacta: solo lectura, sin migraciones ni escrituras.

### 17.3 Fase 6, puertas G1–G4 (verificadas el 18/11/2026)

- [x] G1: protocolo con `crear_*`/`actualizar_*` que devuelven el id de SQL Server
      y migración aditiva `0004` (`alertas_rescate.nombre`/`mensaje`).
- [x] G2: `0005` (distrito, presentación, `mascota_historia`, `mascota_cuidados`).
- [x] G3: `repositories/sqlserver.py` completo, `db/seed.py` idempotente,
      `0006`/`0007` y `tests/test_sqlserver.py` contra `LeonsDB_Test`.
- [x] G4: `alembic check` limpio con `include_object` y `0008`/`0009`;
      paridad del índice del catálogo y del orden de `/refugios` en ambas bases.
- [x] `uv run pytest -p no:warnings` → 28/28.

### 17.4 Pendiente y cierre (fases 4, 6–8)

- [x] Fase 4.1: S1 (JWT), S6 (rate limit login/registro) y S10 (cuentas desactivadas). Ver §4.5.
- [x] Fase 4.2: P1, P2, P3 y P6 con paridad verificada en memoria y SQL Server.
- [x] Fase 4.3: métodos de lote en el Protocolo y en ambos repositorios.
- [x] Fase 4.4: S2 (CORS), S3 (TLS), puerta de producción y evaluación de rate limit distribuido (D-043 pendiente de implementación).
- [x] Fase 4 complementaria S4-A/S4-B: análisis estático y corrección de AUD-01/AUD-02 (opciones A autorizadas). Ver §4.6.
- [x] Fase 4 complementaria S4-C: validación independiente aprobada para desarrollo/demostración local: 13/13 HTTP y 8/8 pruebas aisladas. Ver §4.6.
- [x] AUD-01 corregido y validado en local; AUD-02 mitigado con guard de arranque (no probado en producción real). Ver §4.6.
- [x] `uv run pytest -p no:warnings` → 58/58; `tests/test_sqlserver.py` → 17/17 (snapshot histórico de Fase 4.4).
- [x] `LeonsDB` intacta tras Fase 4.4: head `0009`, 16/9/3/3 filas, solo lectura.
- [ ] Aprobación plena de `docs/REVISION-BACKEND.md` como informe de auditoría: el archivo existe desde el 20/11/2026 y se actualizó en el cierre documental S4-C con el estado de AUD-01/AUD-02; su aprobación como puerta de despliegue sigue pendiente.
- [x] D-036 conserva su significado histórico; ADR-lite de D-040 a D-043 en `docs/decisiones.md` (autorizado en 5.6.3.3B).
- [x] Cierre técnico de 5.6.3 para desarrollo y demostración local (20/11/2026). No implica despliegue ni cierre definitivo de LeonS. Ver §17.5.
- [ ] Responder Q-08, Q-09 y Q-10 antes del despliegue.
- [x] G5 de la Fase 6: migrar `LeonsDB` (`-x target=main`) — completado 18/11/2026, head `0009`, 0 filas, backup verificado. (D-040)
- [x] G6 de la Fase 6: seed en `LeonsDB` — completado 18/11/2026. 16 mascotas, 9 refugios, 3 solicitudes, 3 usuarios, 6 distritos, 11 pasos, 6 FAQ. Idempotente (segunda ejecución inserta 0). Backup `LeonsDB_preG6_20261118_210007.bak` verificado. (D-040)
- [x] Frontend consume `/api/v1` sin cambiar templates ni la API pública de los services. (G7.2–G7.6)
- [x] `localStorage` de solicitudes eliminado. (G7.5)
- [x] Rutas dinámicas en `RenderMode.Server`; build de producción correcto. (G7.1, G7.8)
- [x] `npm test` y `npm run build` verdes. (G7.7, G7.8)

### 17.5 Cierre técnico de la fase 5.6.3 — entorno de desarrollo y demostración local (20/11/2026)

**Alcance:** implementación y validación local. **No** es un despliegue en producción ni el cierre definitivo del proyecto LeonS. Según la verificación independiente aceptada por el usuario:

- [x] 5.6.3.2B / 5.6.3.2D: 13/13 pruebas E2E y 18/18 evidencias funcionales PASS, conservadas como evidencia histórica; no se repitió Playwright en 5.6.3.3.
- [x] 5.6.3.3A: auditoría final de regresiones y verificación de estado de bases, servidores y manifiestos.
- [x] 5.6.3.3B: limpieza de pruebas SQL por IDs exactos con `finally` y `DB_NAME() = 'LeonsDB_Test'`; huella antes/después idéntica.
- [x] Conciliación documental: D-036 conserva su significado histórico; D-040 a D-043 regularizados en `AGENTS.md` y `docs/decisiones.md`.
- [x] Regresiones locales: 96/96 pruebas backend, 132/132 frontend y ambos builds Angular correctos.
- [x] Estado de datos: `LeonsDB` intacta; `LeonsDB_Test` idéntica al baseline del manifiesto `e2e20261120221842z1fr`.
- [ ] Q-08, Q-09 y Q-10 permanecen abiertas: bloquean despliegue, no la demostración local.
- [ ] `docs/REVISION-BACKEND.md` no formaba parte del cierre técnico 5.6.3: se creó después y se actualizó en el cierre documental S4-C (§4.6), sin cambiar el alcance de este registro.

Este registro documenta el cierre autorizado únicamente para desarrollo y demostración local. Cualquier despliegue, producción o cierre definitivo requiere una aprobación explícita posterior.

---

## 18. Prompts de referencia

### 18.1 Arranque: entender y decidir juntos

```text
Lee AGENTS.md completo. No escribas código todavía.

Devuelve:
1. Resumen de 10 líneas de lo que entiendes del proyecto y del objetivo.
2. Hechos verificados en el repo vs. supuestos.
3. Contradicciones, vacíos o riesgos que detectes.
4. Las 3 decisiones más importantes que debemos tomar antes de empezar,
   con 2 opciones cada una, ventajas/riesgos y tu recomendación.
5. Plan de la Fase 0 en 5 pasos, con archivos y criterio de verificación.

Respeta la sección 2 (protocolo de decisión). Espera mi respuesta antes de avanzar.
```

### 18.2 Fase 0 — Esqueleto del backend

```text
Aprobado. Ejecuta únicamente la Fase 0 de AGENTS.md.

Crea Backend/ con FastAPI + Uvicorn, configuración, /health, /docs,
manejo de errores, repositorio en memoria y seed.json exportado desde Angular.
Incluye tests/conftest.py y las pruebas de health y mascotas.

No implementes auth ni SQL Server todavía.
Al terminar: ejecuta uv run pytest, reporta el resultado y detente.
```

### 18.3 Fase 4 — Auditoría (solo lectura)

```text
Actúa como revisor senior de backend. Lee AGENTS.md y el código de Backend/.

Fase 4 es SOLO LECTURA: no crees, edites ni borres archivos, no instales
dependencias y no toques la base de datos.

Entrega docs/REVISION-BACKEND.md con:
1. Resumen ejecutivo.
2. Tabla: ID | Severidad | Archivo:línea | Problema | Impacto | Fix | Fase.
3. Inventario de endpoints y verificación del contrato /api/v1.
4. Checklist: JWT/roles, validación, errores, transacciones, inyección SQL,
   secretos, CORS, rate limit, uploads, N+1, acoplamiento a memoria.
5. Riesgos de migrar a SQL Server y plan propuesto.

Cita archivo:línea. Separa defecto de mejora. No modifiques código.
Al terminar, detente y espera aprobación.
```

> Nota (20/11/2026): este prompt describe la auditoría original, de solo lectura. Las subfases 4.1–4.4 posteriores se ejecutaron con autorizaciones explícitas y se resumen en §4.5.

### 18.4 Fase 5 — Diseño de base de datos

```text
Aprobado. Ejecuta únicamente la Fase 5 de AGENTS.md.

Entrega:
- app/db/models/ con las 18 tablas, CHECK, FKs, índices y collation.
- migrations/0001_init con Alembic.
- db/schema.sql exportado y legible.
- docs/modelo-datos.md con Mermaid, diccionario y justificación de
  adoptadas_historicas / en_acogida_actual.

Antes de aplicar nada, muestra el SQL generado y espera aprobación.
```

### 18.5 Fase 6 — SQL Server

```text
Aprobado. Ejecuta únicamente la Fase 6 de AGENTS.md.

Implementa:
- app/db/session.py con pyodbc y configuración por entorno.
- app/repositories/sqlserver.py respetando los Protocolos.
- db/seed.py idempotente con IDENTITY_INSERT.
- tests/test_sqlserver.py contra LeonsDB_Test.
- Integración en app/container.py mediante REPOS_BACKEND.

No toques el frontend. Al terminar, ejecuta uv run pytest y reporta.
```

---

## 19. Comandos rápidos

```powershell
# Backend (después de la Fase 0)
cd Backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run pytest

# Migraciones (Fase 5 en adelante)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "cambio"

# Frontend
cd Leons
npm start
npm test
npm run build
```

- API: `http://localhost:8000/api/v1`
- Docs: `http://localhost:8000/docs`
- Frontend dev: `http://localhost:4200`
- Frontend SSR: `http://localhost:4000`
