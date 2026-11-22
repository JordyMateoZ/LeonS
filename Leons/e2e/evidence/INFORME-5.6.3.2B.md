# Informe Fase 5.6.3.2B — E2E controladas con escrituras en `LeonsDB_Test`

Fecha: 20/11/2026 (ejecución final 21:19–21:21). Estado: **ejecutada, pendiente de validación independiente y aprobación explícita**. No se inició 5.6.3.3.

## 1. HECHO

- [HECHO] Todas las escrituras se dirigieron a `LeonsDB_Test`; `LeonsDB` solo se consultó en modo lectura para verificar no contaminación.
- [HECHO] Antes de cada escritura y de la limpieza, el helper exigió `SELECT DB_NAME() = 'LeonsDB_Test'` (fail-closed) y ausencia de `pytest` SQL activo.
- [HECHO] El navegador usó `http://localhost:4300`, la API `http://localhost:8010`; no se registraron peticiones a `:8000`.
- [HECHO] Los registros temporales llevaron el prefijo de ejecución `e2e202611202119579kfn` y fueron creados por esta fase.
- [HECHO] No se tocaron las 74 solicitudes, 72 mensajes, 74 eventos ni 71 alertas preexistentes de `LeonsDB_Test`.

## 2. VERIFICADO

Comandos y resultados finales:

```powershell
cd Leons
npx playwright test --config=playwright.e2e.config.ts --reporter=list
# 11 passed (1.4m)
```

```text
manifiesto e2e202611202119579kfn.json: status=closed
diff baseline vs final: 0 tablas (21/21 idénticas)
trazas=11, capturas=8, evidencia=18 líneas
health :8010 -> env=development backend=sqlserver
```

Verificación READ ONLY adicional contra el baseline 2A:

```text
LeonsDB_Test: efectiva=LeonsDB_Test; head=0009; 12/12 conteos iguales
LeonsDB:      efectiva=LeonsDB;      head=0009; 12/12 conteos iguales
```

## 3. Escenarios ejecutados

| ID | Escenario | Tipo |
|---|---|---|
| A1 | Registro público, login por DNI, persistencia aislada | navegador + API + SQL |
| A2 | Catálogo, favoritos, doble envío y persistencia tras recarga | navegador + API + SQL |
| A3 | Fallo forzado del POST sin solicitud ficticia | navegador + SQL |
| A4 | Aislamiento de solicitudes entre dos usuarios | navegador + API |
| B1 | Mensajes con autor real, citas válidas/inválidas, eventos | API + SQL |
| B2 | Autorización, 409, concurrencia, transacción, idempotencia | API + SQL |
| B3 | Rollback aislado ante fallo de commit | SQL |
| Z | Manifiesto, puertos y ausencia de contaminación | SQL |
| L1–L3 | Lectura: inicio, catálogo y detalle solo contra `:8010` | navegador |

## 4. PASS / FAIL / BLOCKED

- **Playwright: 11/11 PASS.**
- **Evidencia JSONL: 17 PASS, 1 FAIL, 0 BLOCKED.**
- El único FAIL es `B2-CONCURRENCIA` (defecto E2E-02), documentado y aislado; la finalización transaccional e idempotente se verificó afterward en secuencia.

## 5. Evidencias de navegador

- 11 trazas `trace.zip` y 8 capturas `.png` en `Leons/test-results/` (config `trace: 'on'`, `screenshot: 'on'`).
- Archivo de evidencia: `Leons/e2e/evidence/e2e202611202119579kfn.jsonl`.
- Manifiesto: `Leons/e2e/manifests/e2e202611202119579kfn.json`.
- Evidencia del defecto D-E2E-01: `Leons/e2e/evidence/defecto-D-E2E-01/` (`trace.zip`, `test-failed-1.png`, `error-context.md`).
- Cada prueba adjunta además el diagnóstico de red (`peticiones-e2e*.txt`, `diagnostico-e2e*.json`).

## 6. Evidencias de SQL Server

- Helper: `Backend/scripts/e2e_support.py`, con `guard`, `verify-marker`, `track-solicitudes`, `track-distritos`, `inspect`, `rollback-fixture` y `cleanup`.
- IDs temporales del run final: mascotas `117–120`, usuarios `152–157` (2 de rol + 4 adoptantes), solicitudes `186–189`. No se crearon distritos nuevos en la corrida definitiva.
- Borrados por ID exacto: `solicitudes=4`, `mensajes=9`, `eventos=6`, `mascotas=4`, `usuarios=6`, `historia=12`, `cuidados=12`, `salud=8`, `favoritos=1`, `citas=1`.
- Sin `DROP`, `TRUNCATE`, borrados por rango ni limpiezas globales.

## 7. Autenticación

- A1: registro público creó al usuario id `157` con `rol=adoptante`; la pestaña de refugio permaneció deshabilitada.
- Login por DNI respondió 200 y devolvió token válido.
- Cuentas de refugio y administrador creadas por fixture controlada; el endpoint público no fue ampliado.
- Las cuentas auxiliares se crearon por fixture para no agotar el límite de 5 registros/minuto.

## 8. Favoritos

- `POST /favoritos` respondió 201; `GET /favoritos` devolvió el id de mascota propia.
- La fila fue encontrada en SQL y persistió tras recarga de `/mascotas`.
- A4 verificó que los favoritos pertenecen solo a usuarios del run.

## 9. Solicitudes

- Doble clic nativo en «Enviar Solicitud» generó **una sola fila SQL** (id `186`).
- POST forzado a 500 mediante `page.route` no creó ninguna solicitud.
- Dos contextos de navegador distintos produjeron listas disjuntas.
- B1 creó tres solicitudes propias (ids `187–189`) sobre una mascota propia.

## 10. Mensajes y citas

- Mensajes de adoptante, refugio y administrador con `autor_id` auténtico verificado en SQL.
- Cita inválida (`31 de febrero`) → HTTP 422, `FECHA_CITA_INVALIDA`, 0 filas y etapa sin cambios.
- Cita válida → 200, con lugar y coordinadora persistidos.
- Cambio a etapa 3 generó evento y nota con autor refugio correcto.

## 11. Finalización transaccional

- `PATCH etapa=5` con token de adoptante → 403.
- Finalización con otras postulaciones activas → 409 `ADOPCION_EN_CURSO`, 0 escrituras.
- Cancelación por otro adoptante → 403; por administrador → 200 con motivo.
- Idempotencia: segunda finalización → 200 sin eventos ni mensajes duplicados.
- B3: inserción aislada forzada a fallar antes del commit → 0 filas persistidas.
- Concurrencia: **defecto E2E-02**, ver sección 12.

## 12. Errores y regresiones

1. **DEFECTO E2E-02 (funcional, no corregido).** Dos finalizaciones simultáneas sobre postulaciones distintas de una misma mascota respondieron `[500, 409]`. El 500 es `INTERNAL_ERROR`; el 409 es `ADOPCION_EN_CURSO`. No hubo escritura parcial. Se documentó en `B2-CONCURRENCIA` y se verificó la ruta transaccional en secuencia. No se modificó la aplicación.
2. **DEFECTO D-E2E-01 (funcional, no corregido).** La carga directa de `/mis-solicitudes` con sesión válida redirige a `/login` porque la ruta está prerenderizada y el guard actúa antes de la confirmación de sesión. Se sortea con navegación interna; evidencia preservada en `defecto-D-E2E-01/`.
3. **Infraestructura de prueba corregida (no aplicación):** `/health` consultado en la raíz, tracking de distritos creados por registro, fixture de adoptantes, espera de respuesta `POST /favoritos`, reintento ante socket cerrado, salida UTF-8 del helper y reducción de logins para respetar el límite 10/60 s.
4. Durante las iteraciones intermedias aparecieron 429 de `/auth/registro` y `/auth/login`; la corrida final respetó los límites.
5. El hash legacy `hash_solicitudes` del baseline 2A no es reproducible con el algoritmo actual del helper; se usaron conteos y los 21 hashes de tabla del manifiesto como criterio.

## 13. Archivos

Modificados (solo infraestructura E2E):

- `Backend/scripts/e2e_support.py`
- `Leons/e2e/support.ts`
- `Leons/e2e/escritura.spec.ts`
- `Leons/playwright.e2e.config.ts`

Generados:

- `Leons/e2e/manifests/e2e202611202119579kfn.json`
- `Leons/e2e/evidence/e2e202611202119579kfn.jsonl`
- `Leons/e2e/evidence/defecto-D-E2E-01/`
- `Leons/test-results/` (trazas y capturas)

No modificados: `Backend/.env`, `LeonsDB`, migraciones, seeds, contrato `/api/v1`, reglas de negocio, `AGENTS.md`, `docs/decisiones.md`, `Leons/src/`.

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
- Resultado: `baseline restaurado`; manifiesto `closed`; `CLEANUP PASS` en el JSONL.

## 17. Riesgos

- El defecto de concurrencia (E2E-02) puede implicar un deadlock en la consulta con `UPDLOCK, HOLDLOCK`; requiere análisis del equipo antes de cualquier cambio.
- D-E2E-01 afecta la recarga directa de rutas autenticadas; no se corrigió por estar fuera de alcance.
- El rate limit es local al proceso; varias instancias multiplicarían el límite (D-039/Q-10).
- `JWT_SECRET` del servidor E2E es aleatorio por corrida: reiniciar `:8010` invalida tokens.
- La cobertura depende de servidores manuales `:8010` y `:4300`; no los levanta ni detiene la configuración de Playwright.

## 18. Propuesta para 5.6.3.3

**No se inicia.** Para la siguiente subfase se propone, con aprobación explícita previa:

1. Triage de E2E-02 y D-E2E-01 con evidencia reproducible y decisión ADR-lite separada.
2. Solo si se autoriza, corregir la aplicación y repetir 5.6.3.2B completa contra `LeonsDB_Test`.
3. Validación independiente del informe y respuesta a Q-08/Q-09/Q-10.
4. Cierre de Fase 8 con `npm test`, `npm run build`, `uv run pytest -p no:warnings` y verificación final de ambas bases.

**Hecho:** 11/11 pruebas E2E pasan; limpieza restauró 21/21 tablas; `LeonsDB` intacta.
**Verificado:** `npx playwright test --config=playwright.e2e.config.ts --reporter=list` → 11 passed; manifiesto `closed`, diff=0.
**Decisiones tomadas:** ninguna nueva; D-001…D-039 sin reabrir.
**Siguiente fase:** 5.6.3.3 queda detenida a la espera de validación y aprobación.
