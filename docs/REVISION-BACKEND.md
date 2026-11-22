# Revisión técnica del backend LeonS — Fase 4 (auditoría de solo lectura)

| Campo | Valor |
|---|---|
|>Fecha del informe | 20/11/2026 |
|Objeto auditado | `Backend/` (API `/api/v1`), su contrato, persistencia SQL Server y evidencias de cierre 5.6.3 |
|Modalidad | **Solo lectura en la auditoría original**. No se crearon, editaron ni borraron archivos de código, configuración, esquema, datos ni documentos distintos de este informe. El cierre documental S4-C se limitó a `AGENTS.md` y este informe |
|Normativa aplicada | `AGENTS.md` §2.6, §2.8 y §18.3 (el contenido citado como «línea 790» corresponde hoy a `AGENTS.md:790`: «Entrega docs/REVISION-BACKEND.md con…») |
|Estado | **Informe original entregado para revisión; aprobación de producción no otorgada**. El usuario aprobó los resultados de validación S4-C para desarrollo/demostración local y autorizó este registro; `AGENTS.md:723` y `AGENTS.md:745` se ajustaron a ese alcance. Estado posterior de AUD-01/AUD-02 en §9.1 |
|Alcance temporal | Estado del repositorio al 20/11/2026, con el cierre técnico local de 5.6.3 registrado en `AGENTS.md:734-747` |

Convención de etiquetas usada en todo el documento: **[HECHO]** verificado en el repositorio o en ejecución de solo lectura; **[SUPUESTO]** no verificable con la evidencia disponible; **[PROPUESTA]** recomendación que requiere decisión. Las severidades siguen `AGENTS.md` §2.6: `crítico`, `alto`, `medio`, `bajo`; se separa `defecto` de `mejora`.

---

## 1. Resumen ejecutivo

1. **[HECHO]** El backend nuevo de LeonS está implementado con FastAPI + Uvicorn + Pydantic v2, expone `/api/v1`, usa SQLAlchemy 2.0/Alembic/pyodbc y tiene dos repositorios intercambiables (`MemoryRepository` y `SqlServerRepository`) detrás del protocolo `Repositorio` (`Backend/app/domain.py:248-354`, `Backend/app/container.py:25-35`).
2. **[HECHO]** La arquitectura es coherente: `router → service → repository → SQLAlchemy → SQL Server`. Los routers solo gestionan HTTP; el mapeo de campos de presentación está aislado en `Backend/app/mapper.py` y los DTO en `Backend/app/schemas.py`.
3. **[HECHO]** Verificación en vivo de esta auditoría: `GET /health` devolvió `200` con `{"status":"ok","app":"LeonS API","version":"1.0.0","env":"development","backend":"sqlserver"}`. Los `SELECT` de solo lectura confirmaron `LeonsDB` en head `0009` con 16 mascotas / 9 refugios / 3 solicitudes / 3 usuarios / 0 alertas, y `LeonsDB_Test` en head `0009` con la huella de pruebas documentada (74 solicitudes, 71 alertas, 72 mensajes, 74 eventos).
4. **[HECHO]** No se encontró un defecto `crítico` (P0) de seguridad o pérdida de datos. Sí hay dos riesgos `altos` accionables antes de cualquier despliegue: autoasignación del rol `refugio` en registro público (AUD-01) y cuentas demo —incluida admin— presentes en la base sembrada (AUD-02).
5. **[HECHO]** Las preguntas Q-08 (dominios CORS reales), Q-09 (certificado TLS válido) y Q-10 (rate limit distribuido) permanecen abiertas (`AGENTS.md:671-673`, `AGENTS.md:744`). La validación de TLS implementada es de cadena de conexión, no de un certificado real (`Backend/app/config.py:42-59`); durante esta auditoría, `sqlcmd` requirió `-C` para leer la BD local, lo que corrobora Q-09.
6. **[HECHO]** El cierre técnico de 5.6.3 cubre **desarrollo y demostración local únicamente** (`AGENTS.md:734-747`). No implica despliegue, producción ni cierre definitivo. Este informe no cambia ese alcance.
7. **[HECHO]** Las cifras históricas aceptadas son 96/96 pruebas backend, 132/132 frontend, 13/13 E2E y 18/18 evidencias funcionales PASS (`INFORME-5.6.3.2D.md:5,25,29,38,69-72`; `AGENTS.md:742`). **No se repitieron** en esta auditoría.
8. **[HECHO]** Existe un desfase documental: `AGENTS.md:24` y `AGENTS.md:721` siguen citando 58 pruebas y G7 pendiente, mientras `AGENTS.md:729-732,742` registran G7 completado y 96 pruebas (AUD-21). También se identificó un N+1 residual en tres métodos de lote del repositorio SQL Server (AUD-24), sin impacto en el contrato pero con coste de consultas.
9. **[PROPUESTA]** Conservar el backend tal como está para la demostración local; tratar AUD-01, AUD-02 y Q-08/Q-09/Q-10 como puertas explícitas de cualquier fase de despliegue, con aprobación independiente.
10. **[PROPUESTA]** No crear una nueva migración, seed ni cambio de contrato sin pasar primero por `LeonsDB_Test` y obtener autorización, conforme `AGENTS.md` §2.10 y §8.6.

> **Nota de estado posterior (20/11/2026):** los puntos 4 y 9 conservan la evaluación original de la auditoría. AUD-01 y AUD-02 se corrigieron/mitigaron en S4-B y se validaron en S4-C **para desarrollo local**; véanse §8.1b y §9.1. El resto de hallazgos AUD-03…AUD-28 y las preguntas Q-08/Q-09/Q-10 permanecen en su estado original. No se declara disponibilidad para producción.

---

## 2. Metodología

### 2.1 Lecturas realizadas

- `AGENTS.md` completo (859 líneas), con atención especial a §2.6, §8, §16, §17.4/§17.5 y §18.3 (`AGENTS.md:782-800`).
- `docs/decisiones.md`, `docs/modelo-datos.md`, `docs/G5-comparacion.md`, `docs/G6-seed.md`.
- `Backend/README.md`, `Backend/.env.example`, `Backend/pyproject.toml` (configuración declarada), `Backend/app/**`, `Backend/migrations/**`, `Backend/db/**` y `Backend/tests/**` (inspección estática con `read`/`grep`).
- Evidencias: `Leons/e2e/evidence/INFORME-5.6.3.2D.md`, `INFORME-5.6.3.2B.md`, `e2e20261120221842z1fr.jsonl` y `Leons/e2e/manifests/e2e20261120221842z1fr.json`.

### 2.2 Únicas ejecuciones realizadas

| Comando | Resultado | Naturaleza |
|---|---|---|
| `curl.exe -s -S --max-time 10 -w "\nSTATUS=%{http_code}\n" "http://localhost:8000/health"` | `STATUS=200`, cuerpo `{"status":"ok","app":"LeonS API","version":"1.0.0","env":"development","backend":"sqlserver"}` | Solo lectura HTTP |
| `sqlcmd -S 'localhost\SQLEXPRESS' -d LeonsDB -C -Q "SELECT DB_NAME(), COUNT(*) …"` | `LeonsDB 16 9 3 3 0 0009` | Solo `SELECT` |
| `sqlcmd -S 'localhost\SQLEXPRESS' -d LeonsDB_Test -C -Q "SELECT DB_NAME(), COUNT(*) …"` | `LeonsDB_Test 16 9 74 3 71 72 74 0009` | Solo `SELECT` |

**[HECHO]** La opción `-C` de `sqlcmd` equivale a confiar en el certificado del servidor en el cliente. Se usó únicamente para poder leer la instancia local de desarrollo; no modifica la BD ni la configuración. Constituye evidencia adicional de que Q-09 sigue abierta: sin esa opción, ODBC Driver 18 rechazó la conexión por «cadena de certificación emitida por una entidad en la que no se confía».

### 2.3 Lo que NO se hizo

- No se ejecutaron `pytest`, `npm test`, `npm run build`, Playwright, Alembic ni seeds.
- No se crearon usuarios, solicitudes, alertas ni mensajes de prueba.
- No se reiniciaron servidores ni se instalaron dependencias.
- No se abrieron secretos: no se leyó `Backend/.env`; solo `Backend/.env.example` (`Backend/.gitignore:5` confirma que `.env` está fuera de control de versiones).

### 2.4 Regla de evidencia

**[HECHO]** Todo resultado de pruebas citado como «histórico» proviene de informes ya aceptados y se identifica como tal. Ningún número de esa sección debe interpretarse como ejecutado en esta auditoría. Los hallazgos nuevos se sustentan en código fuente leído o en las tres ejecuciones de solo lectura listadas arriba.

---

## 3. Alcance

### 3.1 Incluido

- Arquitectura y capas del backend nuevo (`Backend/app/`).
- Contrato `/api/v1`: rutas, esquemas Pydantic, alias camelCase, paginación, errores, roles y autenticación.
- Seguridad: JWT, bcrypt, CORS, TLS de conexión, rate limit, uploads, exposición de PII y puerta de producción.
- Persistencia: 20 modelos de dominio, Alembic `0001`–`0009`, sesiones, transacciones, SQL parametrizado, optimizaciones P1/P2/P3/P6 y estado actual de `LeonsDB`/`LeonsDB_Test`.
- Pruebas automatizadas y evidencias E2E, como documentación y código estático.
- Conciliación documental D-036 → D-040…D-043 y cierre técnico 5.6.3.

### 3.2 Excluido

- Rediseño de interfaz, templates o rutas públicas de Angular.
- Escritura en bases de datos, migraciones, seeds o limpieza de datos.
- Revivir, descompilar o modificar `LeonS-Mateo/Backend/` (prohibido por `AGENTS.md` §15).
- Implementar endpoints en `Leons/src/server.ts` (prohibido por `AGENTS.md` §1).
- Resolver Q-08, Q-09 o Q-10 sin información del usuario.
- Declarar despliegue, producción o cierre definitivo.

---

## 4. Arquitectura

### 4.1 Mapa de capas verificado

| Capa | Archivo:línea | Responsabilidad |
|---|---|---|
| Entrada | `Backend/app/main.py:9-18` | Importa `create_app`, ejecuta `verificar_base_e2e()` y expone `app` a Uvicorn. |
| Fail-closed E2E | `Backend/app/e2e.py:29-48` | Si `E2E_EXPECT_DB` está activo, exige `SELECT DB_NAME() = 'LeonsDB_Test'`; el error no expone la URL. |
| Composición HTTP | `Backend/app/app.py:45-145` | FastAPI, `app.state.container`, CORS, 4 handlers, `/health`, 8 routers y montaje de `/uploads`. |
| Configuración | `Backend/app/config.py:62-198` | `Settings` con validadores de JWT, CORS, TLS y puerta de producción. |
| Inyección de dependencias | `Backend/app/container.py:14-45`, `Backend/app/dependencies.py:16-71` | Repositorio, storage, tres limitadores y notificador; `get_current_user` y `require_roles`. |
| Routers | `modules/auth.py:19`, `mascotas.py:26`, `refugios.py:11`, `solicitudes.py:21`, `favoritos.py:10`, `alertas.py:10`, `contenido.py:11`, `estadisticas.py:8` | Parámetros HTTP, `Depends`, `response_model` y status; delegan reglas a servicios. |
| Servicios | `services/auth.py:12-64`, `catalogo.py:12-148`, `solicitudes.py:45-292`, `social.py:10-51`, `contenido.py:8-18` | Reglas de negocio, autorización y coordenación transaccional vía repositorio. |
| Dominio | `Backend/app/domain.py:42-245`, `248-354` | Dataclasses en español y `Protocol Repositorio`, sin HTTP ni SQLAlchemy. |
| Mapper / esquemas | `Backend/app/mapper.py:1-5,169-218,484-618`; `schemas.py:11-22,30-464` | Campos de presentación calculados; DTO camelCase con `populate_by_name`. |
| Repositorios | `repositories/memory.py:41`; `repositories/sqlserver.py:237-...` | Misma interfaz; SQL Server empuja filtros/orden/paginación a SQL. |
| SQLAlchemy | `db/base.py:22-32`, `db/session.py:15-29`, `db/models/*.py` | 20 `__tablename__`, naming convention, `pool_pre_ping`, `pool_recycle=1800`. |
| Adaptadores | `adapters/storage.py:21-50`, `pdf.py:15-53`, `rate_limit.py:12-33`, `notifications.py:10-12` | Archivos, PDF mínimo, limitador local y notificación por log. |
| Persistencia/DDL | `migrations/env.py:30-91`, `versions/0001…0009`, `db/seed.py`, `db/export_schema.py:60-78` | Alembic con `-x target=main|test`, filtro de `sysdiagrams`, seed idempotente y `schema.sql` generado. |

**[HECHO]** Separación de capas confirmada en un caso completo: `modules/mascotas.py:51,134` → `services/catalogo.py:35,113` → `domain.py:248-354` → `repositories/sqlserver.py:466, ...`.

**[HECHO]** Excepción menor: el consumo del limitador está en los routers (`modules/auth.py:28-29,40-41`, `modules/alertas.py:19-20`), no en un middleware. No rompe el contrato, pero mezcla una preocupación transversal con HTTP.

### 4.2 Configuración y ciclo de vida

- `Settings` se cachea con `lru_cache` (`config.py:196-198`) y `create_app(settings?)` permite inyección en pruebas (`app.py:45-47`).
- `build_container` elige `SqlServerRepository` o `MemoryRepository` según `REPOS_BACKEND` (`container.py:25-35`); en producción se exige `sqlserver` (`config.py:184-192`).
- CORS usa lista blanca con `allow_credentials=True` (`app.py:61-67`); en producción se exige configuración, se rechazan `*`, localhost y TLS no validado (`config.py:123-193`).
- Sesión SQL por operación: `_sesion()` hace `rollback()` en excepción y `close()` en `finally` (`repositories/sqlserver.py:246-255`).

### 4.3 Relación con el frontend

**[HECHO]** El frontend consume `/api/v1` sin cambiar la API pública de sus services: `environment.ts:1-5`, `api.config.ts:8-23`, `app.config.ts:16-18`, `initial-data.service.ts:86-95,122-128,151-183`, `auth.service.ts:90-157,223-228`. Las rutas dinámicas usan `RenderMode.Server` (`app.routes.server.ts:3-11`). El token se guarda en `localStorage` solo en navegador.

**[HECHO]** No se encontraron consumidores frontend para `/alertas-rescate`, `/documentos`, `/etapa`, `/citas`, `/mensajes`, `/seguimiento`, `/auth/google`, `/auth/recuperar`, `/mascotas/stats` ni la llamada HTTP a `/mascotas/destacadas`. Son capacidades del backend disponibles para la entrega, no flujos activos de la UI actual.

---

## 5. Revisión funcional del contrato `/api/v1`

### 5.1 Inventario de endpoints

Prefijo global `/api/v1` (`config.py:67`, aplicado en `app.py:127-137`). **36 rutas bajo el prefijo**, más `/health`, `/docs`, `/redoc` y `/uploads/{archivo}` en la raíz.

#### Sistema

| Método | Ruta | Auth | Origen |
|---|---|---|---|
| GET | `/health` | Público | `app.py:117-125` |
| GET | `/docs`, `/redoc` | Público | `app.py:56-57` |
| GET | `/uploads/{archivo}` | Público | `app.py:139-143` |

#### Auth

| Método | Ruta | Auth/rol | Origen y observación |
|---|---|---|---|
| POST | `/auth/registro` | Público | `auth.py:22-31`; 201; límite 5/60; 409 `EMAIL_YA_REGISTRADO`/`DNI_YA_REGISTRADO`; 422 `REFUGIO_INVALIDO` |
| POST | `/auth/login` | Público | `auth.py:34-43`; correo o DNI; límite 10/60; 401/429 |
| POST | `/auth/google` | Público | `auth.py:46-48`; stub 501 (Q-04 respondida con valor por defecto) |
| POST | `/auth/recuperar` | Público | `auth.py:51-55`; 202 genérico, sin envío real |
| GET | `/auth/me` | Bearer | `auth.py:58-60`; valida usuario activo en cada petición (`dependencies.py:31-46`) |

#### Catálogo

| Método | Ruta | Auth/rol | Origen y observación |
|---|---|---|---|
| GET | `/mascotas` | Público | `mascotas.py:33-71`; `page`, `limit 1..50`, filtros y orden; `PageMascotas` |
| GET | `/mascotas/destacadas` | Público | `mascotas.py:74-84`; `ids` por coma, default `1,2,3,4` |
| GET | `/mascotas/stats` | Público | `mascotas.py:87-89` |
| GET | `/mascotas/{id}` | Público | `mascotas.py:92-95`; 404 |
| GET | `/mascotas/{id}/detalle` | Público | `mascotas.py:98-111` |
| GET | `/mascotas/{id}/similares` | Público | `mascotas.py:114-125`; `limite 1..10` |
| POST | `/mascotas` | `admin\|refugio` | `mascotas.py:128-135`; 403 si refugio ajeno |
| PATCH | `/mascotas/{id}` | `admin\|refugio` | `mascotas.py:138-146`; `exclude_unset` |
| DELETE | `/mascotas/{id}` | `admin` | `mascotas.py:149-155`; 409 `MASCOTA_CON_SOLICITUDES` |

#### Refugios, solicitudes y social

| Método | Ruta | Auth/rol | Origen y observación |
|---|---|---|---|
| GET | `/refugios` | Público | `refugios.py:18-32` |
| GET | `/refugios/{id}` | Público | `refugios.py:35-42` |
| GET | `/refugios/{id}/mascotas` | Público | `refugios.py:45-56`; usa `listar_mascotas_de_refugio` |
| GET | `/solicitudes` | Bearer | `solicitudes.py:51-71`; visibilidad en SQL (`services/solicitudes.py:69-92`) |
| POST | `/solicitudes` | `adoptante` | `solicitudes.py:74-81`; 409 duplicado/no disponible; etapa inicial 2 (D-017) |
| GET | `/solicitudes/{id}` | Bearer + acceso | `solicitudes.py:84-90` |
| PATCH | `/solicitudes/{id}/cancelar` | Bearer | `solicitudes.py:93-102`; motivo opcional (AUD-09) |
| PATCH | `/solicitudes/{id}/etapa` | Bearer + refugio/admin | `solicitudes.py:105-115`; etapa 5 atómica (`services/solicitudes.py:175-194`) |
| POST | `/solicitudes/{id}/citas` | Bearer + refugio/admin | `solicitudes.py:118-126`; fecha validada en repo |
| POST | `/solicitudes/{id}/mensajes` | Bearer + acceso | `solicitudes.py:129-139`; autor real del token |
| POST | `/solicitudes/{id}/seguimiento` | Bearer + acceso | `solicitudes.py:142-165`; multipart, MIME/tamaño/ruta |
| GET | `/solicitudes/{id}/documentos` | Bearer + acceso | `solicitudes.py:168-181`; PDF `application/pdf` |
| GET/POST/DELETE | `/favoritos` | Bearer | `favoritos.py:22-55`; 409 `FAVORITO_DUPLICADO` |
| POST/GET | `/alertas-rescate` | Público / `admin\|refugio` | `alertas.py:13-38`; límite 5/60; paginación incompleta (AUD-06) |
| GET | `/contenido`, `/contenido/pasos`, `/contenido/faqs` | Público | `contenido.py:14-29` |
| GET | `/estadisticas/impacto` | Público | `estadisticas.py:11-14`; agregación en repositorio |

### 5.2 Verificación del contrato

| Regla de `AGENTS.md` §7 | Estado | Evidencia |
|---|---|---|
| Prefijo `/api/v1` y JSON camelCase | ✅ | `config.py:67`, `app.py:127-137`, `schemas.py:11-22` (`alias_generator=to_camel`, `populate_by_name`) |
| Paginación `{items,page,limit,total,totalPages}` | ⚠️ | Correcto en `PageMascotas` (`schemas.py:82-88`) y `PageSolicitudes` (`schemas.py:385-391`); incompleto en `PageAlertas` (`schemas.py:451-454`, AUD-06) |
| Errores `{code,message,details}` | ✅ | `errors.py:6-60`, handlers en `app.py:69-115`, `schemas.py:461-464` |
| `POST /solicitudes` rechaza duplicados y mascotas no disponibles | ✅ | `services/solicitudes.py:103-129` |
| `POST /auth/login` acepta correo o DNI | ✅ | `services/auth.py:46-57` |
| Endpoints públicos sin `passwordHash`, `googleId` ni DNI de terceros | ✅ | `schemas.py:291-306`, `351-383`; DNI propio solo en `/auth/me` |
| Sin cambios de ruta ni campo sin propuesta `/api/v2` | ✅ | No se detectaron cambios en esta auditoría; solo se recomiendan mejoras |

**[HECHO]** Los campos de presentación (`badgeClase`, `chipTexto`, `fechaTexto`, `etapas`, etc.) se calculan en `mapper.py` y no se persisten, conforme D-008. Los arrays normalizados se reconstruyen en el mapper.

---

## 6. Seguridad

### 6.1 Checklist exigido por `AGENTS.md:794-795`

| Ámbito | Estado | Evidencia y matiz |
|---|---|---|
| JWT / roles | ✅ con observación | HS256 con `exp`/`iat`/`sub`/`rol` (`security.py:26-44`); autorización contra usuario de BD en cada petición (`dependencies.py:31-69`). Sin `aud`/`iss`/`jti`/revocación (AUD-14). |
| Validación | ✅ | Pydantic con `EmailStr`, DNI `^\d{8}$`, password 8–72, enums y rangos (`schemas.py:265-280,393-405,423-437`); `str_strip_whitespace`. |
| Errores | ✅ | `{code,message,details}`; 500 no expone detalles internos (`app.py:105-115`); validación devuelve campo y mensaje, no valores (`app.py:76-92`). |
| Transacciones | ✅ | `_sesion()` con rollback/close (`repositories/sqlserver.py:246-255`); `finalizar_solicitud` atómica con reintento ante deadlock 1205/1222 (`sqlserver.py:1281-1312`); probado en E2E B2/B3. |
| Inyección SQL | ✅ | Consultas ORM y parámetros; `LIKE` con escape (`repositories/sqlserver.py`); sin concatenación detectada. |
| Secretos | ✅ con riesgo | JWT con valor por defecto solo en desarrollo; `.env` fuera de git; puerta de producción rechaza secreto débil (`config.py:98-116,170-193`). Cuentas demo en SQL sembrada: AUD-02. |
| CORS | ✅ en código / ⚠️ por decisión | Lista blanca, `*` y localhost rechazados en producción (`config.py:123-154`, `app.py:61-67`). Q-08 abierta: AUD-03. |
| Rate limit | ✅ local / ⚠️ distribuido | Ventana deslizante con `time.monotonic()` y lock (`adapters/rate_limit.py:12-33`); 5/60 alertas, 10/60 login, 5/60 registro. D-043/Q-10: AUD-05. |
| Uploads | ⚠️ | MIME whitelist, 5 MB, UUID y anti path traversal (`adapters/storage.py:11-49`). No valida magic bytes, lee completo antes del límite y sirve `/uploads` sin autenticación (AUD-11, AUD-12). |
| N+1 | ⚠️ | Pushdown de filtros/orden/paginación a SQL y métodos de lote verificados en `tests/test_sqlserver.py:574,613,668`. Queda un N+1 residual en `repositories/sqlserver.py:783-796,798-810,1485-1499`: tres métodos de lote no aplican `selectinload` y `_mascota()` lee 5 relaciones (AUD-24). |
| Acoplamiento a memoria | ✅ | Servicios tipados contra `Repositorio` (D-020); `build_container` decide la implementación (`container.py:25-35`). Producción prohíbe `memory` (`config.py:184-192`). |

### 6.2 PII y logging

**[HECHO]** Los DTO públicos no incluyen hash de contraseña, `googleId` ni DNI ajeno. `/auth/me` devuelve el DNI propio (`schemas.py:291-300`), coherente con la política.

**[HECHO]** El handler 500 registra solo la ruta (`app.py:105-115`). La excepción es el notificador de alertas, que escribe el `contacto` en claro (`adapters/notifications.py:12`, AUD-13).

### 6.3 Conclusión de seguridad

**[HECHO]** No hay P0 confirmado. El backend es adecuado para la demostración local. **No está listo para producción**: AUD-01, AUD-02 y Q-08/Q-09/Q-10 deben resolverse antes de cualquier despliegue.

---

## 7. Persistencia y migraciones

### 7.1 Modelo y DDL

- **[HECHO]** 20 tablas de dominio modeladas (`app/db/models/`, `env.py:19` confirma el registro de las 20); `Base.metadata` expone 23 FKs, 19 CHECK, 20 índices, 6 UNIQUE y 34 relaciones (`app/db/models/__init__.py:10-53`). Alembic añade `alembic_version`; `sysdiagrams` es artefacto de SSMS filtrado por `_incluir_objeto` (`migrations/env.py:30-38`, D-034). Total físico observado en G5/G6: 22 tablas en `LeonsDB` y 21 en `LeonsDB_Test`.
- **[HECHO]** Los 20 modelos están declarados en `catalogos.py:14-35`, `usuarios.py:22-63`, `refugios.py:23-82`, `mascotas.py:24-212`, `solicitudes.py:22-160`, `social.py:21-65` y `contenido.py:18-42`. `db/schema.sql:23-402` contiene los 20 `CREATE TABLE`, generados por `db/export_schema.py:60-77`.
- **[HECHO]** Convenciones: `NVARCHAR` + `CHECK` en lugar de `ENUM`, `BIT` en lugar de `BOOLEAN`, `Unicode` para tildes, collation `Modern_Spanish_CI_AI` (`db/base.py:1-15`, `AGENTS.md` §8.4/§8.5).
- **[HECHO]** Revisiones presentes: `0001` … `0009` (`Backend/migrations/versions/`). `0008` recrea `IX_mascotas_catalogo` con `INCLUDE`; `0009` añade `refugios.orden` (D-034, D-035).

### 7.2 Motor y sesiones

- `crear_engine` usa `pool_pre_ping=True`, `pool_recycle=1800` y URL desde `Settings` (`db/session.py:15-25`); nunca URL hardcodeada.
- `crear_fabrica` usa `expire_on_commit=False` (`db/session.py:28-29`).
- `SqlServerRepository` implementa el protocolo y centraliza rollback/close (`repositories/sqlserver.py:237-255`).
- `env.py` selecciona destino con `-x target=main|test` **antes** del subcomando (`env.py:41-57`). Existe una nota engañosa en `env.py:5-8` que muestra el orden inverso (AUD-19).

### 7.3 Migración ya ejecutada (G5/G6)

| Verificación | Evidencia histórica | Estado |
|---|---|---|
| Backup previo verificado | `docs/G5-comparacion.md`, `docs/G6-seed.md:16-20` | ✅ |
| `compare_metadata` sin diferencias antes de migrar | `docs/G5-comparacion.md:11-30` | ✅ |
| 50 operaciones, todas aditivas salvo `DROP/CREATE INDEX` | `docs/G5-comparacion.md:72-80` | ✅ |
| `upgrade head` → `0009`, `check` limpio, `sysdiagrams` intacto | `docs/G5-comparacion.md:248-305`, `docs/G6-seed.md:79-81` | ✅ |
| Seed idempotente: 16/9/3/3 + 6 distritos/11 pasos/6 FAQ | `docs/G6-seed.md:29-44,112-114` | ✅ |
| 0 huérfanos (16 FK), 19 CHECK, sin duplicados, IDENTITY 16 | `docs/G6-seed.md:73-81` | ✅ |
| Paridad memoria ↔ SQL Server en rutas GET | `docs/G6-seed.md:83-87` | ✅ |

**[HECHO]** Estado actual verificado en esta auditoría con `SELECT`: `LeonsDB` y `LeonsDB_Test` ambos en head `0009`; conteos listados en §2.2. `LeonsDB` permanece con los datos demo y sin contaminación de pruebas.

**[HECHO]** Riesgo operativo menor ya documentado: `uv run alembic -x target=main check` imprime «No new upgrade operations detected.» pero el wrapper `uv` termina con código 1 (`AGENTS.md:257-260`). No es un diff de esquema.

### 7.4 Plan propuesto para cualquier cambio de esquema

1. No tocar `LeonsDB` en esta auditoría ni en Fase 4.
2. Crear la revisión Alembic nueva; nunca editar una ya aplicada (`AGENTS.md` §8.6).
3. Validar en `LeonsDB_Test` con `-x target=test upgrade head` y `check`.
4. Verificar backup y `RESTORE VERIFYONLY` antes de `-x target=main`.
5. Confirmar huella antes/después y paridad de rutas GET.
6. Documentar la decisión en `docs/decisiones.md` **solo con autorización explícita** (fuera del alcance actual).

---

## 8. Pruebas y evidencias

### 8.1 Suites (conteo estático del código; resultados históricos)

| Suite | Pruebas | Cobertura representativa |
|---|---:|---|
| `Backend/tests/test_api.py` | 28 | Paginación/filtros, stats, refugios, auth, duplicados, cancelación/PDF, favoritos, uploads, rate limits, S1/S6/S10, A-14/A-15/A-16 |
| `Backend/tests/test_config.py` | 21 | CORS producción, TLS/`TrustServerCertificate`, JWT, rate limits, cuenta desactivada |
| `Backend/tests/test_sqlserver.py` | 47 | Aislamiento `DB_NAME()`, idempotencia seed, paridad, pushdown SQL, no N+1, autoría, fechas, transaccionalidad, deadlock/stats SQL |
| **Total backend** | **96** | Coincide con `AGENTS.md:742` e `INFORME-5.6.3.2D.md:25` |
| Frontend `Leons/src/**/*.spec.ts` | 132 | Services, guard SSR, interceptores, auth, páginas; `INFORME-5.6.3.2D.md:29` |
| Playwright E2E | 13 | A1–A5, B1, B2, B2b, B3, Z, L1–L3; `INFORME-5.6.3.2D.md:38,69` |
| Evidencia JSONL | 18 PASS / 0 FAIL / 0 BLOCKED | `e2e20261120221842z1fr.jsonl:1-18`, `INFORME-5.6.3.2D.md:70-72` |

**[HECHO]** Ninguna de estas ejecuciones se repitió en esta auditoría. El informe 5.6.3.2D registra la corrida definitiva del 20/11/2026, 22:18–22:20, con aceptación independiente del usuario (`INFORME-5.6.3.2D.md:3-5`).

### 8.1b Regresiones posteriores (S4-B/S4-C, 20/11/2026)

La tabla anterior conserva el conteo histórico de la auditoría original. Tras la corrección autorizada de AUD-01/AUD-02 se ejecutaron, en procesos nuevos:

| Ejecución | Resultado |
|---|---|
| `uv run pytest -p no:warnings -o addopts="" -q` (S4-B) | **105/105** backend (`test_api` 30, `test_config` 27, `test_sqlserver` 48) |
| `npm test -- --watch=false` (S4-B) | **132/132**, 22 archivos |
| `npm run build` (S4-B) | OK, 5 rutas prerenderizadas |
| Peticiones HTTP aisladas en `:8020` (S4-C) | **13/13** comprobaciones |
| Pruebas específicas AUD-01/AUD-02 aisladas (S4-C) | **8/8** |
| SELECT final en `LeonsDB` / `LeonsDB_Test` | baseline `0009`; conteos y hash de `dbo.usuarios` idénticos antes y después |

**[HECHO]** S4-C no repitió las fixtures SQL de `test_sqlserver.py`: solo las inspeccionó. Esas fixtures son *write-capable* (`alembic upgrade head` + seed idempotente sobre `LeonsDB_Test`); en S4-B se ejecutaron dentro de la autorización de escrituras temporales, con `DB_NAME()`, limpieza por ID exacto en `finally` e igualdad de huella antes/después. El estado neto fue sin cambios.

### 8.2 Aislamiento y limpieza

- Fail-closed: `tests/test_sqlserver.py:82-85` omite la suite si `DB_TEST_URL` no apunta a `LeonsDB_Test`.
- Guardias `DB_NAME() = 'LeonsDB_Test'` en `:148,384,765,1258,1841` y dentro de los context managers de limpieza.
- Huella antes/después con `count` + `sha256` por tabla (`_huella_tablas_sql`, `:787-809`) y `assert despues == antes` (`:818/847/854`, `:866/885/892`).
- Borrados solo por ID exacto, con `finally` (`:826-845`, `:873-883`, `:918-932`, `:956-960`, `:1279-1308`). Registrado como 5.6.3.3B en `AGENTS.md:740`.
- Manifiesto `e2e20261120221842z1fr.json:6,416-417`: `status=closed`, `coincide_con_baseline=true`, `leonsdb_intacta=true`; hashes baseline/final idénticos.

### 8.3 Defectos históricos cerrados

- `INC-E2E-01` (concurrencia; antes `DEFECTO E2E-02`): `[409,409]` sin deadlock 1205 (`INFORME-5.6.3.2D.md:11-13,71`).
- `D-E2E-01` (carga directa de `/mis-solicitudes`): `http=200`, sin datos privados antes de `/auth/me` (`INFORME-5.6.3.2D.md:13,72`).
- **[HECHO]** No existe un `INC-E2E-02` independiente (`INFORME-5.6.3.2D.md:7`). No se reabren decisiones ya aprobadas.

---

## 9. Hallazgos

**[HECHO]** No se modificó código. Todo lo siguiente es una propuesta de corrección o verificación. La severidad `alto` significa impacto funcional/de seguridad antes de producción; `medio`, mantenibilidad o funcionalidad latente; `bajo`, estilo o deuda técnica.

**[HECHO]** La tabla siguiente es el snapshot original de la auditoría y se conserva íntegra como evidencia histórica. AUD-01 y AUD-02 tienen un estado posterior registrado en §9.1 tras S4-B/S4-C; el resto de filas no cambiaron.

| ID | Sev. | Tipo | Archivo:línea | Problema | Impacto | Fix propuesto | Fase |
|---|---|---|---|---|---|---|---|
| AUD-01 | alto | defecto | `app/schemas.py:272-273`, `app/services/auth.py:20-26` | Registro público permite `rol="refugio"` con `refugio_id` existente | Un anónimo obtiene permisos para administrar mascotas y solicitudes ajenas | Alta de refugio por invitación/aprobación admin o verificación de correo | 4 / 8 |
| AUD-02 | alto | defecto | `app/data/loader.py:186-220`, `db/seed.py:127-171,493-495`, `app/config.py:170-193` | Cuentas demo, incluida admin, sembradas también en SQL Server | La puerta de producción prohíbe `memory`, pero no impide reutilizar una BD con credenciales públicas | Separar seed demo de producción; deshabilitar/rotar cuentas; gate de arranque | 4 / 8 |
| AUD-03 | alto | riesgo Q-08 | `app/config.py:123-154`, `app/app.py:61-67`, `.env.example:6-11` | Dominios CORS reales no acordados | La app no arranca en producción sin `CORS_ORIGINS`; hoy no hay dominio autorizado | Responder Q-08 y configurar solo el entorno de despliegue | 8 |
| AUD-04 | alto | riesgo Q-09 | `app/config.py:34-59,156-168`, `.env.example:32-39` | Se valida la cadena, no el certificado real; `sqlcmd` requirió `-C` en esta auditoría | Conexión insegura o fallida en producción | Responder Q-09: certificado de CA confiable y prueba real | 8 |
| AUD-05 | alto si réplicas / medio si una | riesgo D-043/Q-10 | `app/adapters/rate_limit.py:12-33`, `app/container.py:37-44` | Limitador local por proceso; la clave usa `request.client.host` | Con N workers se multiplican intentos; detrás de proxy puede compartirse IP | Autorizar store compartido, clave IP+endpoint, `INCR`/`EXPIRE` atómicos | 8 |
| AUD-06 | medio | defecto | `app/modules/alertas.py:34-35`, `app/schemas.py:451-454`, `services/social.py:45-51` | `PageAlertas` omite `page`, `limit`, `totalPages`; slicing en Python | Respuesta paginada inconsistente con el contrato | Alinear esquema y paginación en repositorio | 4 / 7 |
| AUD-07 | medio | defecto latente | `core/data/initial-data.service.ts:124`, `modules/mascotas.py:37`, `mascotas.service.ts:36-47` | Catálogo se precarga con `limit=50` sin paginación en UI | A partir de 51 mascotas la UI no mostrará el resto | Exponer paginación o ampliar carga inicial | 7 |
| AUD-08 | medio | mejora | `schemas.py:381`, `mapper.py:602-604`, `services/solicitudes.service.ts:163-217` | `fotosSeguimiento` se produce pero no se muestra en «Mis solicitudes» | Funcionalidad de seguimiento invisible para el adoptante | Declarar el campo en TS y renderizarlo sin cambiar el HTML base | 7 |
| AUD-09 | medio | defecto | `schemas.py:399-400`, `modules/solicitudes.py:93-101` | «Cancelar exige motivo» no es estricto: body opcional, default «No especificado» | Regla de negocio documentada no se cumple literalmente | Hacer `CancelarSolicitudRequest` obligatorio con motivo mínimo real | 4 |
| AUD-10 | medio | defecto | `schemas.py:403-405`, `services/solicitudes.py:196-208` | `PATCH /etapa` acepta 1–5 sin validar transiciones | Regresos o saltos inválidos en el flujo de 5 pasos | Máquina de estados permitida | 4 |
| AUD-11 | medio | mejora seguridad | `adapters/storage.py:31-41`, `modules/solicitudes.py:154` | MIME declarado por el cliente; `read()` completo antes del límite | Subida de no-imágenes y presión de memoria | Validar magic bytes y leer por chunks / `Content-Length` | 4 |
| AUD-12 | medio | mejora seguridad | `app.py:139-143`, `adapters/storage.py:43-49` | `/uploads` público sin autorización por solicitud | Posible exposición si las fotos se consideran privadas | Endpoint autorizado o URLs firmadas con expiración | 4 / 8 |
| AUD-13 | bajo | mejora | `adapters/notifications.py:12`, `modules/alertas.py:22-25` | Contacto de alerta en logs en claro | Exposición de PII en registros | Loguear ID o contacto enmascarado | 4 |
| AUD-14 | bajo | mejora | `security.py:26-44`, `dependencies.py:31-53` | JWT sin `aud`, `iss`, `jti`, refresh ni revocación | Tokens robados válidos hasta expiración; la desactivación mitiga | Añadir claims y estrategia de revocación/refresh | 8 |
| AUD-15 | bajo | mejora | `security.py:16,21`, `schemas.py:269,277` | bcrypt trunca a 72 **bytes**; validación permite 72 caracteres | Passwords multibyte pueden truncarse silenciosamente | Limitar a 72 bytes UTF-8 o prehash | 4 |
| AUD-16 | bajo | mejora | `adapters/rate_limit.py:16,21-33` | Claves de IPs nunca se eliminan | Crecimiento de memoria con IPs únicas | Limpiar claves vacías o usar TTL | 4 |
| AUD-17 | bajo | mejora | `dependencies.py:23,27,56` | `get_repo`, `get_app_settings`, `get_optional_user` sin uso | Código muerto | Retirar en limpieza autorizada | 4 |
| AUD-18 | bajo | mejora | `Backend/Backend/_tmp_conn.py:1-10` | Artefacto temporal con `print` y consulta a `DB_TEST_URL` | Ruido en el árbol del backend | Retirar en limpieza autorizada | 4 |
| AUD-19 | bajo | mejora | `migrations/env.py:5-8` vs `AGENTS.md` §8.6 y `db/export_schema.py:40-41` | El docstring muestra `alembic upgrade head -x target=test`, orden que Alembic rechaza | Documentación engañosa; el parser real se lee en `env.py:43` | Corregir el docstring | 5 / 4 |
| AUD-20 | bajo | mejora | `modules/mascotas.py:79-82` | `ids` inválido se sustituye por `[1,2,3,4]` y responde 200 | El cliente recibe datos no solicitados sin error | Validar y devolver 422 | 4 |
| AUD-21 | medio | documental | `AGENTS.md:24,721` vs `729-732,742` | Snapshot desactualizado: 58 pruebas / G7 pendiente vs 96 / G7 completado | Confusión para el docente o el equipo | Actualizar el cuadro de estado con autorización | 8 |
| AUD-22 | bajo | documental | `docs/G5-comparacion.md:248-306` | Mojibake (`Fecha de ejecuciÃ³n`, `â†’`) y numeración duplicada | Legibilidad del informe G5 | Normalizar codificación y encabezados | 8 |
| AUD-23 | bajo | documental | `docs/G6-seed.md:103-104`, `AGENTS.md:658` | Informe histórico cita D-036 con su significado antiguo | Requiere leer la tabla de correspondencia | Mantener la nota de correspondencia D-036→D-040…D-043 | 8 |
| AUD-24 | medio | mejora (N+1 residual) | `repositories/sqlserver.py:783-796,798-810,1485-1499` | Tres métodos de lote no aplican `.options(*self._opciones_mascota())`, pero `_mascota()` (`:280-340`) lee `salud`, `fotos`, `rasgos`, `refugio` y `refugio.distrito` con `lazy="select"` | Hasta ~5 SELECT extra por mascota en `/mascotas/destacadas`, `/refugios/{id}/mascotas` y favoritos | Añadir `selectinload` igual que en `:459-463` | 4.2 / 4.3 |
| AUD-25 | medio | mejora | `services/solicitudes.py:114-123`, `services/catalogo.py:142`, `modules/mascotas.py:109,124`, `modules/refugios.py:41`, `modules/solicitudes.py:24-36` | Pese a P1/P3/P6, varias rutas materializan catálogos completos; el chequeo de duplicados carga todas las solicitudes en cada creación | Coste innecesario; la corrección ya está garantizada por `UX_solicitudes_activa` y el mapeo de `IntegrityError` | Método `existe_solicitud_activa()` con `select(exists())` y consultas por ids | 4.2 |
| AUD-26 | bajo | defecto | `repositories/sqlserver.py:1144-1151` | Cualquier `IntegrityError` en `flush()` se reporta como `SOLICITUD_DUPLICADA` | Puede enmascarar violaciones de CHECK (`etapa`, `estado`, `motivo`) o FK | Inspeccionar `error.orig` por nombre de constraint, como en `crear_usuario` (`:1016-1030`) | 4 |
| AUD-27 | bajo | convención | `db/seed.py:48-55,425-428` | SQL construido con f-strings para `SET IDENTITY_INSERT` y `DBCC CHECKIDENT` | No hay inyección (constantes internas / `int`), pero diverge de la regla «sin SQL concatenado» | Usar `identifier_preparer`/`quoted_name` o documentar la excepción | 5 / 6 |
| AUD-28 | bajo | riesgo de downgrade | `migrations/versions/0003_nvarchar_max.py:58-86` | El `downgrade()` reintroduce `NTEXT`, tipo obsoleto que el `upgrade()` evita | Un downgrade más allá de `0003` puede dejar tipos obsoletos | Documentar que ese downgrade no es recomendable en SQL Server moderno | 5 |

### 9.1 Estado posterior de AUD-01 y AUD-02 (S4-B/S4-C, 20/11/2026)

**[HECHO]** El usuario aprobó la validación S4-C para entorno de desarrollo y
demostración universitaria local. No se declaró cierre de producción ni se
resolvieron Q-08/Q-09/Q-10. Los hallazgos originales de §9 permanecen intactos.

| ID | Estado final | Evidencia | Limitaciones |
|---|---|---|---|
| AUD-01 | **Corregido y validado para desarrollo local** | `app/services/auth.py:15-19` rechaza `rol != "adoptante"` con 403 `FORBIDDEN` y fuerza `refugio_id=None`; `schemas.py` intacto (admin → 422). S4-C: adoptante **201**, refugio **403**, admin **422**, token sin permisos **403/403**, rechazados **401/401**, login demo **200/200/200**. | OpenAPI sigue mostrando `refugio` como valor aceptado; corregirlo exige una decisión de contrato. |
| AUD-02 | **Mitigado mediante comprobación de arranque** | `app/seguridad_arranque.py`: SELECT parametrizado sobre los correos de `DEMO_USERS`, fail-closed y mensajes genéricos; `app.py:51-55,66`: `lifespan` antes de aceptar solicitudes. Solo con `APP_ENV=production` y `REPOS_BACKEND=sqlserver`. Validado con stubs y SQLite aislado (8/8 pruebas S4-C). | **No probado en despliegue real de producción**; detecta correos, no DNIs ni hashes; **no reemplaza la rotación/eliminación de credenciales**. No modifica la BD. |

**REPORTADO:** D-016 permanece vigente; el guard complementa esa decisión sin
sustituir la eliminación o rotación de cuentas demo prevista para producción.
No se crearon nuevos ADR: las opciones A aplicadas ya estaban autorizadas en S4-A.

**[PROPUESTA]** Priorizar AUD-01 y AUD-02 antes que cualquier mejora de estilo. AUD-06 a AUD-28 pueden agruparse en un único turno de Fase 4 complementaria si el usuario lo autoriza; este informe no ejecuta ninguna.

---

## 10. Riesgos y plan propuesto

| Riesgo | Severidad | Evidencia | Mitigación / plan |
|---|---|---|---|
| Autoasignación de rol refugio | alto (histórico) | AUD-01 | Aprobación admin para rol privilegiado; prueba de regresión en `test_api.py`. **Estado S4-C:** corregido y validado en local (§9.1). |
| Credenciales demo en BD sembrada | alto (histórico) | AUD-02 | Seed de producción separado; rotación/deshabilitación; gate de arranque. **Estado S4-C:** gate implementado y validado con stubs; rotación/eliminación sigue pendiente (§9.1). |
| Dominios CORS desconocidos | alto | AUD-03, Q-08 | Responder Q-08; configurar entorno de despliegue; no inventar dominios |
| Certificado SQL no confiable | alto | AUD-04, Q-09; error real de `sqlcmd` sin `-C` | Responder Q-09; instalar CA confiable y probar conexión cifrada real |
| Rate limit multiplicado por réplicas | alto si réplicas | AUD-05, D-043/Q-10 | Decidir backend compartido; no implementar sin autorización |
| Regresión de migración/seed | medio | G5/G6, `AGENTS.md` §8.6 | Plan de 6 pasos de §7.4; nunca aplicar directamente a `LeonsDB` |
| Pérdida de paridad memoria ↔ SQL | medio | `docs/G6-seed.md:83-87` | Repetir comparación de 18 rutas GET tras cualquier cambio de mapper o repo |
| N+1 residual en lotes | medio | AUD-24, AUD-25 | Añadir `selectinload` y reemplazar cargas completas por `exists()`/ids |
| Downgrade a `NTEXT` | bajo | AUD-28 | Documentar `0003` como límite seguro de downgrade |
| Documentación desactualizada | medio | AUD-21, AUD-22 | Actualizar snapshots en una fase documental autorizada |
| Falsificación de MIME en uploads | medio | AUD-11, AUD-12 | Validación de bytes y control de acceso a `/uploads` |
| Dependencia de servidores manuales | medio | `INFORME-5.6.3.2D.md:205-206` | Documentar arranque; reiniciar `:8010` invalida tokens por `JWT_SECRET` aleatorio |
| Cierre interpretado como producción | alto | `AGENTS.md:736,747` | Mantener explícito que 5.6.3 es solo desarrollo/demostración local |

**[PROPUESTA]** Orden de ejecución si se autoriza una Fase 4 complementaria: AUD-01 → AUD-02 → AUD-09/AUD-10 → AUD-11/AUD-12 → AUD-06/AUD-07/AUD-08 → mejoras bajas. Q-08/Q-09/Q-10 quedan fuera de esa secuencia hasta respuesta del usuario.

**[HECHO]** El orden propuesto se cumplió solo para los dos primeros pasos: AUD-01 y AUD-02 se ejecutaron en S4-B/S4-C. Los demás hallazgos siguen sin corregirse.

---

## 11. Limitaciones

1. **No se repitieron pruebas.** 96/96, 132/132, 13/13 y 18/18 son resultados históricos aceptados, no ejecutados aquí (`AGENTS.md:738,742`; `INFORME-5.6.3.2D.md:5`).
2. **E2E no repetido en 5.6.3.3.** La evidencia de 13/13 y 18/18 se conserva históricamente (`AGENTS.md:738`).
3. **Q-08, Q-09 y Q-10 siguen abiertas** (`AGENTS.md:744`); bloquean despliegue, no la demostración local.
4. **TLS verificado solo como configuración**, no contra un certificado real (`config.py:42-59`, D-042). El intento de `sqlcmd` sin `-C` falló por certificado no confiable.
5. **Rate limit local** (D-043). No hay backend compartido.
6. **Google OAuth y recuperación son stubs** respondidos con 501/202 (Q-04, D-001…D-006).
7. **Cobertura frontend parcial**: hay endpoints backend sin consumidor actual (§4.3).
8. **`alembic check` con wrapper `uv`** puede terminar con código 1 pese a no tener diferencias (`AGENTS.md:257-260`).
9. **Sin control de versiones en el PATH**: no hay `git` disponible; este informe no puede adjuntar un diff, solo declarar el alcance de escritura.
10. **Aprobación limitada al cierre documental S4-C.** El usuario aprobó los resultados de validación S4-C para desarrollo/demostración local y autorizó actualizar `AGENTS.md` y este informe (20/11/2026). No se otorgó aprobación de producción ni cierre definitivo; las referencias `AGENTS.md:723`/`:745` se ajustaron a ese alcance.
11. **No se resolvieron inconsistencias documentales** AUD-21/AUD-22/AUD-23: se documentan, no se corrigen.
12. **Sin prueba de despliegue real para AUD-02:** la comprobación de producción se validó con stubs y SQLite aislado, nunca contra una instancia desplegada.

---

## 12. Conclusiones

**[HECHO]** El backend LeonS cumple el entregable académico para entorno local: contrato `/api/v1` completo, arquitectura por capas, persistencia SQL Server migrada y sembrada con backup verificado, autenticación y roles reales, errores consistentes, optimizaciones P1/P2/P3/P6 y evidencia de regresiones aceptadas. El estado en vivo confirmado en esta auditoría (`/health` 200; `LeonsDB` y `LeonsDB_Test` en `0009` con las huellas esperadas) es coherente con el cierre técnico de 5.6.3.

**[HECHO]** No se encontró un P0. No obstante, **LeonS no está listo para producción**: existen dos riesgos altos accionables (AUD-01, AUD-02) y tres preguntas abiertas (Q-08, Q-09, Q-10) que el protocolo exige resolver antes de cualquier despliegue. La validación de TLS es de cadena de conexión, no de certificado real, y el limitador es local al proceso.

**[HECHO]** La auditoría respetó estrictamente el modo solo lectura: no se modificaron código, configuración, esquemas, contratos, bases de datos, `AGENTS.md` ni `docs/decisiones.md`. El único archivo creado es este informe.

**[PROPUESTA]** Mantener el alcance de cierre en «desarrollo y demostración local»; presentar AUD-01/AUD-02 y Q-08/Q-09/Q-10 como próximas puertas de decisión; no iniciar nuevas fases sin aprobación explícita.

### Estado posterior (S4-B/S4-C, 20/11/2026)

**[HECHO]** AUD-01 está corregido y validado para desarrollo local; AUD-02 está
mitigado mediante una comprobación de arranque fail-closed, con las limitaciones
explicitadas en §9.1. Las conclusiones originales de esta sección se conservan
como evidencia histórica de la auditoría.

**[HECHO]** LeonS **no está listo para producción**: Q-08/Q-09/Q-10 siguen abiertas,
la rotación/eliminación de credenciales demo continúa pendiente y AUD-03…AUD-28
permanecen sin corregirse. El alcance aprobado sigue siendo desarrollo y
demostración universitaria local.

### Cierre de la fase (AGENTS.md §2.8)

```text
Hecho: docs/REVISION-BACKEND.md creado como auditoría formal de solo lectura del backend LeonS,
       con 12 secciones, inventario de endpoints, checklist de seguridad, hallazgos AUD-01…AUD-28
       y registro del cierre técnico 5.6.3 para desarrollo/demostración local.

Verificado: GET /health -> 200 (env=development, backend=sqlserver);
            SELECT en LeonsDB -> 16/9/3/3/0, revision 0009;
            SELECT en LeonsDB_Test -> 16/9/74/3/71/72/74, revision 0009.
            No se ejecutaron pruebas, migraciones, seeds ni escrituras.

Decisiones tomadas: ninguna en esta auditoría. Se conservan D-040 a D-043 y Q-08/Q-09/Q-10 abiertas.
                    No se marca como aprobado este informe en AGENTS.md:723 ni :745.

Siguiente fase: requiere aprobación explícita para (a) corregir AUD-01/AUD-02 y las mejoras
                autorizadas de Fase 4, o (b) responder Q-08/Q-09/Q-10 antes de plantear despliegue.
                Sin esa aprobación, el proyecto permanece en cierre técnico local.
```

### Cierre documental S4-C (AGENTS.md §2.8)

```text
Hecho: registro documental de AUD-01 (corregido y validado en local) y AUD-02
       (mitigado con guard de arranque, no probado en producción real) en
       AGENTS.md §4.6/§17.4 y docs/REVISION-BACKEND.md §8.1b/§9.1/§10/§11/§12.

Verificado: 105/105 backend y 132/132 frontend en S4-B; 13/13 HTTP y 8/8 pruebas
            aisladas en S4-C; LeonsDB y LeonsDB_Test en baseline 0009. Esta fase
            documental no ejecutó pruebas, migraciones, seeds ni escrituras.

Decisiones tomadas: ninguna nueva. No se modificaron D-xxx ni docs/decisiones.md;
                    Q-08/Q-09/Q-10 y AUD-03…AUD-28 conservan su estado.

Siguiente fase: no se inicia automáticamente. Requiere aprobación explícita para
                cualquier corrección adicional o para responder Q-08/Q-09/Q-10.
```
