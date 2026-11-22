# Informe Fase 5.6.3.2D — Corrección de deadlock concurrente y acceso directo a `/mis-solicitudes`

Fecha: 20/11/2026 (ejecución definitiva 22:18–22:20). Estado: **cerrada documentalmente** el 20/11/2026, tras validación independiente y aprobación explícita del usuario. No se inició 5.6.3.3.

> **Acta de cierre documental (20/11/2026):** el usuario verificó de forma independiente los archivos modificados y la presencia de los mecanismos de corrección de concurrencia SQL Server y autenticación Angular SSR. Aceptó 96/96 pruebas backend, 132/132 pruebas frontend, 13/13 E2E, 18/18 evidencias funcionales PASS, `LeonsDB_Test` restaurada sin diferencias y `LeonsDB` intacta. Autorizó **únicamente** el cierre documental: sin modificaciones adicionales ni pruebas con escritura sin autorización separada.
>
> **Observación de nomenclatura [HECHO]:** la evidencia de esta fase registra dos defectos: `INC-E2E-01` (concurrencia; llamado `DEFECTO E2E-02` en 5.6.3.2B) y `D-E2E-01` (acceso directo a `/mis-solicitudes`). No consta un `INC-E2E-02` independiente en los archivos de esta fase; la aprobación se aplica a esos dos defectos corregidos.

## 1. HECHO

- [HECHO] INC-E2E-01 y D-E2E-01 tenían evidencia reproducible en la corrida 5.6.3.2B: `[500,409]` en B2 y redirección a `/login` en la carga directa.
- [HECHO] El usuario aprobó **opción A** para INC-E2E-01: conservar A-15 y corregir bloqueos/errores transitorios sin relajar la regla de negocio para satisfacer `[200,409]`.
- [HECHO] El usuario aprobó **opción A** para D-E2E-01: guard asíncrono con `/auth/me` como única autoridad y render SSR neutro; se rechazaron cookies, refresh tokens y cambios de contrato.
- [HECHO] Todas las escrituras E2E se dirigieron a `LeonsDB_Test`; `LeonsDB` solo se leyó para verificar no contaminación.
- [HECHO] El manifiesto definitivo `e2e20261120221842z1fr` quedó `status=closed`, `coincide_con_baseline=true`, `leonsdb_intacta=true`.
- [HECHO] No se reabrieron D-001…D-039; `AGENTS.md` y `docs/decisiones.md` no se modificaron.

## 2. VERIFICADO

Comandos y resultados finales:

```powershell
cd Backend
uv run pytest -p no:warnings -q
# 96 passed (90 baseline + 6 nuevas)

cd ..\Leons
npm test -- --watch=false
# Test Files 22 passed; Tests 132 passed (120 baseline + 12 nuevas)

npm run build
# Application bundle generation complete; 5 rutas prerenderizadas

npm run build -- --configuration=e2e
# Application bundle generation complete; 5 rutas prerenderizadas

npx playwright test --config=playwright.e2e.config.ts
# 13 passed (1.5m)
```

Verificación adicional de aislamiento (solo lectura, **después** de Playwright, sin SQL en paralelo):

```text
DB_PRUEBAS=LeonsDB_Test
DB_PRINCIPAL=LeonsDB
LeonsDB_Test tablas=21 diferencias=0   # 20 de dominio + alembic_version
LeonsDB      diferencias=0
health :8010 -> env=development backend=sqlserver
```

## 3. Escenarios ejecutados

| ID | Escenario | Tipo |
|---|---|---|
| A1 | Registro público, login por DNI, persistencia aislada | navegador + API + SQL |
| A2 | Catálogo, favoritos, doble envío y persistencia tras recarga | navegador + API + SQL |
| **A5** | **Carga directa y recarga de `/mis-solicitudes` sin redirección prematura** | navegador |
| A3 | Fallo forzado del POST sin solicitud ficticia | navegador + SQL |
| A4 | Aislamiento de solicitudes entre dos usuarios | navegador + API |
| B1 | Mensajes con autor real, citas válidas/inválidas, eventos | API + SQL |
| **B2** | **Dos finalizaciones concurrentes: ambas 409, sin escritura** | API + SQL |
| **B2b** | **Cancelación autorizada, finalización y idempotencia** | API + SQL |
| B3 | Rollback aislado ante fallo de commit | SQL |
| Z | Manifiesto, puertos y ausencia de contaminación | SQL |
| L1–L3 | Lectura: inicio, catálogo y detalle solo contra `:8010` | navegador |

## 4. PASS / FAIL / BLOCKED

- **Playwright: 13/13 PASS.**
- **Evidencia JSONL: 18 PASS, 0 FAIL, 0 BLOCKED.** No se declaró PASS ningún escenario con HTTP 500.
- El evidencial de concurrencia es explícito: `B2-CONCURRENCIA`, `http=409`, `estados=[409,409]`, `ambos ADOPCION_EN_CURSO; sin deadlock 1205`.
- El acceso directo quedó registrado como `A5`, `http=200`, `sin datos privados antes de /auth/me; sesión conservada tras recarga`.

## 5. Evidencias de navegador

- 13 trazas `trace.zip` y 9 capturas `.png` en `Leons/test-results/` (`trace: 'on'`, `screenshot: 'on'`, `workers: 1`).
- Archivo de evidencia definitivo: `Leons/e2e/evidence/e2e20261120221842z1fr.jsonl`.
- Manifiesto definitivo: `Leons/e2e/manifests/e2e20261120221842z1fr.json`.
- Evidencia histórica del defecto ya corregido se conserva en `Leons/e2e/evidence/defecto-D-E2E-01/`.
- A5 usa `gotoAuth(page, '/mis-solicitudes')` y `page.reload()` directos; **ya no usa el workaround `irASolicitudes`**.

## 6. Evidencias de SQL Server

- Helper: `Backend/scripts/e2e_support.py` (`guard`, `verify-marker`, `track-solicitudes`, `track-distritos`, `inspect`, `rollback-fixture`, `cleanup`).
- IDs temporales del run definitivo: mascotas `18–21`, usuarios `164–169` (2 de rol + 4 adoptantes), solicitudes `253–256`.
- 37 guardias registrados en el manifiesto; cada escritura verificó `SELECT DB_NAME() = 'LeonsDB_Test'` (fail-closed).
- Borrados por ID exacto: `solicitudes=4`, `mensajes=9`, `eventos=6`, `citas=1`, `favoritos=1`, `mascotas=4`, `historia=12`, `cuidados=12`, `salud=8`, `usuarios=6`.
- Sin `DROP`, `TRUNCATE`, borrados por rango ni limpiezas globales.

## 7. Autenticación y acceso directo

- `auth.guard.ts` es asíncrono: en SSR devuelve `true` sin leer `localStorage`; en navegador espera `auth.inicializar()` cuando la sesión está `pendiente`.
- `/auth/me` es la única autoridad: sin sesión confirmada hay redirección a `/login`; 401 invalida la sesión; 403, error de red y 5xx **no autorizan datos privados pero conservan credenciales**.
- `mis-solicitudes` pasó a `RenderMode.Server`; el componente usa `effect()` y solo llama a `SolicitudesService.cargar()` cuando `auth.isAuthenticated()`.
- El HTML muestra un banner neutro mientras se verifica la sesión y otro cuando no está confirmada; no se renderizan solicitudes por SSR.
- A5 verificó carga directa **y** recarga con token válido, sin redirección prematura y sin banner de «No se mostrarán datos privados» al finalizar.

## 8. Favoritos

- `POST /favoritos` respondió 201; `GET /favoritos` devolvió el id de mascota propia.
- La fila se encontró en SQL y persistió tras recarga de `/mascotas`.
- La fila temporal fue borrada por ID exacto en la limpieza.

## 9. Solicitudes

- Doble clic nativo en «Enviar Solicitud» generó una sola fila SQL.
- POST forzado a 500 mediante `page.route` no creó ninguna solicitud.
- Dos contextos de navegador distintos produjeron listas disjuntas.
- B1 creó tres solicitudes propias sobre una mascota propia; B2/B2b trabajaron sobre esas mismas filas.

## 10. Mensajes y citas

- Mensajes de adoptante, refugio y administrador con `autor_id` auténtico verificado en SQL.
- Cita inválida (`31 de febrero`) → 422, `FECHA_CITA_INVALIDA`, 0 filas y etapa sin cambios.
- Cita válida → 200, con lugar y coordinadora persistidos.
- Cambio a etapa 3 generó evento y nota con autor refugio correcto.

## 11. Finalización transaccional y concurrencia

- `PATCH etapa=5` con token de adoptante → 403.
- Con otras postulaciones activas → 409 `ADOPCION_EN_CURSO`, sin escrituras.
- **Dos finalizaciones concurrentes sobre solicitudes distintas de una misma mascota → `[409,409]`; ambas activas; mascota disponible; cero eventos y cero mensajes de finalización.**
- Backend: orden determinista de bloqueos (`mascota → solicitudes por id ascendente → hijos`), una sola transacción y commit, `UPDLOCK/HOLDLOCK`, autorización refugio/admin.
- Error 1205/1222 se detecta de forma específica; reintento interno acotado (1) solo antes de confirmación; si persiste, `TransitorioError` → 503 controlado sin detalles internos. Un `DBAPIError` sin firma de deadlock se propaga: no se convierte en 409 ni en 503.
- B2b (escenario separado): cancelar la otra postulación → 200; finalizar la restante → 200; repetir finalización → 200 sin duplicar eventos ni mensajes.
- B3: inserción aislada forzada a fallar antes del commit → 0 filas persistidas.

## 12. Errores y regresiones

1. **INC-E2E-01 — resuelto.** El 500 por deadlock (1205 envuelto en `DBAPIError`) ya no aparece: la corrida definitiva registró `[409,409]` y ningún `INTERNAL_ERROR`.
2. **D-E2E-01 — resuelto.** La carga directa y la recarga de `/mis-solicitudes` funcionan sin workaround. Se descartó envolver secciones con `@if` por errores `NG5002`; la protección real está en `SolicitudesService.cargar()`.
3. **Regresión de idempotencia concurrente corregida.** Causa: identity map obsoleto al cargar la entidad completa antes de los candados; la lectura inicial ahora selecciona solo `mascota_id`.
4. **Infraestructura, no aplicación:** la primera corrida falló en A1 con `fetch failed` porque el proceso en segundo plano del servidor `:8010` fue terminado por el timeout del shell (120 s). Se reinició con timeout 1800 s; la corrida definitiva pasó 13/13. El manifiesto de la corrida interrumpida quedó `closed` y en baseline.
5. **Ruido de tests preexistentes:** `test_ciclo_de_solicitud` y `test_alertas_de_rescate` insertan filas sin limpiar. Antes de E2E se restauró el baseline borrando únicamente esas filas por ID exacto (dos corridas: `190/211/198/217/72/73` y `232/211/237/74`). No se modificaron esos tests por estar fuera de alcance.

## 13. Archivos

Modificados:

- `Backend/app/errors.py` — `TransitorioError` → `SERVICIO_NO_DISPONIBLE` (503).
- `Backend/app/repositories/sqlserver.py` — orden de bloqueos, reintento 1205, flag `confirmacion`.
- `Backend/tests/test_sqlserver.py` — 6 pruebas nuevas de deadlock, 409, idempotencia y 503.
- `Leons/src/app/core/guards/auth.guard.ts` y su spec (10 pruebas).
- `Leons/src/app/app.routes.server.ts` — `mis-solicitudes` en `RenderMode.Server`.
- `Leons/src/app/pages/mis-solicitudes/mis-solicitudes.ts`, `.html` y su spec (2 pruebas).
- `Leons/e2e/escritura.spec.ts` — B2 dividido en B2/B2b, nueva A5, sin workaround.
- `Backend/scripts/e2e_support.py`, `Leons/e2e/support.ts`, `Leons/playwright.e2e.config.ts` (infraestructura E2E de 5.6.3.2B, sin cambios nuevos en esta subfase salvo el uso de la spec).

Generados:

- `Leons/e2e/manifests/e2e20261120221842z1fr.json`
- `Leons/e2e/evidence/e2e20261120221842z1fr.jsonl`
- `Leons/e2e/evidence/INFORME-5.6.3.2D.md`
- `Leons/test-results/` (trazas y capturas)

No modificados: `Backend/.env`, migraciones, `db/schema.sql`, contrato `/api/v1`, `AGENTS.md`, `docs/decisiones.md`, `LeonsDB`, pantallas nuevas ni dependencias.

## 14. Estado de `LeonsDB`

| Tabla | Antes | Después |
|---|---:|---:|
| mascotas | 16 | 16 |
| refugios | 9 | 9 |
| solicitudes | 3 | 3 |
| usuarios | 3 | 3 |
| citas | 1 | 1 |
| mensajes | 1 | 1 |
| eventos | 3 | 3 |
| alertas | 0 | 0 |
| head Alembic | 0009 | 0009 |

Sin escrituras. Verificado con `DB_NAME()` y conteos/hash en modo lectura.

## 15. Estado de `LeonsDB_Test` antes/después

| Tabla | Antes | Después |
|---|---:|---:|
| mascotas | 16 | 16 |
| refugios | 9 | 9 |
| solicitudes | 74 | 74 |
| usuarios | 3 | 3 |
| citas | 1 | 1 |
| mensajes | 72 | 72 |
| eventos | 74 | 74 |
| favoritos | 0 | 0 |
| alertas | 71 | 71 |
| pasos | 11 | 11 |
| FAQs | 6 | 6 |
| distritos | 6 | 6 |
| head Alembic | 0009 | 0009 |

21/21 tablas (20 de dominio + `alembic_version`) con el mismo `count` y `hash`.

## 16. Limpieza

- Ejecutada en `afterAll`, con `DB_NAME() = 'LeonsDB_Test'` y manifiesto abierto.
- Orden FK: eventos/mensajes/citas/seguimiento → solicitudes → mascotas → usuarios → distritos.
- Solo IDs exactos registrados en el manifiesto.
- Resultado: `baseline restaurado`; manifiesto `closed`; 18/18 evidencias PASS.

## 17. Riesgos

- El reintento de deadlock es interno y acotado a 1; no hay reintentos ciegos desde Angular. Con carga sostenida, una respuesta 503 controlada sigue siendo posible por diseño.
- El limitador sigue siendo local al proceso (D-039/Q-10); varias instancias multiplican el límite.
- `JWT_SECRET` del servidor E2E es aleatorio por corrida: reiniciar `:8010` invalida tokens.
- La cobertura depende de servidores manuales `:8010` y `:4300`; Playwright no los levanta ni los detiene. El proceso en segundo plano debe lanzarse con timeout suficiente.
- Los tests SQL preexistentes dejan una fila por corrida; requiere restauración explícita antes de cualquier E2E con escritura.
- Q-08/Q-09/Q-10 siguen abiertas y son bloqueantes para despliegue.

## 18. Cierre y propuesta para 5.6.3.3

**5.6.3.2D: cerrada documentalmente.** La validación independiente y la aprobación ya fueron otorgadas; no se requiere nueva ejecución. **5.6.3.3 no se inicia**: su apertura requiere una autorización separada.

Para la siguiente subfase se propone, con aprobación explícita previa:

1. Auditoría final de regresiones y cierre técnico, partiendo de los 13/13 E2E y 18/18 evidencias ya aceptadas.
2. Decidir por separado si se corrige la limpieza de los dos tests SQL preexistentes (fuera de alcance de esta subfase).
3. Responder Q-08/Q-09/Q-10 antes de cualquier despliegue.
4. Solo con autorización, actualizar el registro de decisiones con los ADR-lite pendientes.

**Hecho:** 13/13 E2E PASS, 18/18 evidencias PASS, 96/96 pytest, 132/132 unitarias, builds verdes; `LeonsDB` intacta y `LeonsDB_Test` en baseline. Cierre documental aprobado por el usuario el 20/11/2026.
**Verificado:** `npx playwright test --config=playwright.e2e.config.ts` → 13 passed; manifiesto `closed`, diff=0 en 21/21 tablas; validación independiente aceptada.
**Decisiones tomadas:** ninguna nueva; opciones A de INC-E2E-01 y D-E2E-01 ejecutadas; D-001…D-039 sin reabrir.
**Siguiente fase:** 5.6.3.3 — Auditoría final de regresiones y cierre técnico; **no iniciada**, a la espera de autorización separada.
