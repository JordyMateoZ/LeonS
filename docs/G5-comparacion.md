# G5 — Comparación estructural de `LeonsDB` vs. migraciones `0001`–`0009`

**Fase:** 6, puerta G5 (paso 1: solo lectura; paso 2: informe).
**Fecha de la comparación:** 18/11/2026.
**Base analizada:** `LeonsDB` (DB_URL por defecto, `localhost\SQLEXPRESS`).
**Herramientas:** `alembic.autogenerate.compare_metadata` (compare_type=True, compare_server_default=False), `Inspector`, `sys.*`, replay de las migraciones sobre `MetaData` en memoria. **Sin escrituras en la BD.**
**Arneses (temporales, no versionados):** `C:\Users\INTEL\AppData\Local\Temp\opencode\g5_compare.py`, `g5_defaults.py`.

---

## 1. Resumen ejecutivo

`LeonsDB` coincide exactamente con la migración `0001` según Alembic (0 diferencias). Los 18 defaults, las 15 columnas IDENTITY y las PK/FK/UNIQUE/índices coinciden. Las 8 migraciones `0002`–`0009` son aplicables sobre la estructura real (50 operaciones, todas aditivas). Tras el `upgrade head`, el delta contra el modelo actual es de **37 objetos añadidos y 0 eliminados/modificados**, es decir: **no se recrea ninguna tabla ni se pierde dato**. La única desviación física real son 2 nombres de CHECK en `alertas_rescate` (legado) y el orden de las columnas `INCLUDE` del índice del catálogo (mismo conjunto).

## 2. Coincidencias

| Aspecto | Real (`LeonsDB`) | `0001` / modelo | Resultado |
|---|---|---|---|
| Tablas de dominio | 18 | 18 | ✅ idénticas |
| Collation de la base | `Modern_Spanish_CI_AI` | esperada | ✅ |
| Filas en las 18 tablas | 0 en todas | (seed pendiente G6) | ✅ vacías |
| `compare_metadata` (compare_type=True) | — | — | **0 diferencias** |
| DEFAULT (23 columnas) | — | — | 0 diferencias |
| IDENTITY (15 columnas, todas `(1,1)`) | — | — | 0 diferencias |
| PK, FK, UNIQUE, índices | — | — | 0 diferencias |
| Tipos y nulabilidad | — | — | 0 diferencias reales (ver §3.1) |
| `NTEXT` | 0 columnas | 0 | ✅ (0003 será no-op de re-alter) |
| `sysdiagrams` | 1 tabla + 7 procedimientos | — | excluida por `_incluir_objeto` en `env.py` (ambas llamadas a `context.configure`) |

Tablas reales (19): 18 de dominio + `sysdiagrams`. PK/FK/índices por tabla coinciden con `0001`.

## 3. Diferencias

### 3.1 Artefacto de comparación (NO es diferencia real)

El script ingenuo reportó 53 "diferencias de tipo", todas del mismo patrón:

- `nvarchar(300)collate"modern_spanish_ci_ai"` vs `nvarchar(300)` (sufijo de collation reflejado).
- `nvarcharcollate"modern_spanish_ci_ai"` vs `nvarchar(max)` (render de `NVARCHAR(MAX)`).

`alembic.compare_metadata` con `compare_type=True` reporta **0 diferencias**, lo que prueba que los tipos y la nulabilidad son idénticos. La collation de columna hereda la de la base (`Modern_Spanish_CI_AI`), coherente con §8.1 de `AGENTS.md`.

### 3.2 Desviaciones reales (4 CHECK del 0002 + 2 nombres legado)

**CHECK constraints:** 15 reales vs 19 en el modelo.

Faltan (se añaden con `0002`, tablas vacías → sin riesgo de violación):

| Tabla | CHECK pendiente |
|---|---|
| `mascotas` | `CK_mascotas_sexo`, `CK_mascotas_tamano` |
| `refugios` | `CK_refugios_tipo` |
| `contenido_pasos` | `CK_contenido_pasos_tipo` |

Divergencia de **nombres** (solo cosmética, no afecta el `upgrade` ni el `check`):

| Tabla | En `LeonsDB` | En modelo / `LeonsDB_Test` |
|---|---|---|
| `alertas_rescate` | `CK_alertas_especie`, `CK_alertas_estado` | `CK_alertas_rescate_especie`, `CK_alertas_rescate_estado` |

Alembic no compara CHECK constraints (ni por nombre ni por definición), por lo que `alembic check` puede estar limpio mientras esta diferencia de nombre exista. El conjunto de columnas cubiertas y las definiciones son equivalentes.

### 3.3 Índice del catálogo (`IX_mascotas_catalogo`)

| | `LeonsDB` | Modelo / `LeonsDB_Test` |
|---|---|---|
| Claves | `(estado, especie)` | `(estado, especie)` |
| INCLUDE | `(nombre, destacada)` | `(destacada, nombre)` |

Mismo conjunto de columnas incluidas; el orden del `INCLUDE` no afecta el comportamiento. La migración `0008` ejecutará `DROP INDEX` + `CREATE INDEX` con el nuevo orden (operación sobre índice, no sobre tabla).

## 4. Operaciones que ejecutaría cada migración

Total: **50 operaciones**, todas aditivas salvo el `DROP INDEX`/`CREATE INDEX` de `0008`.

| Rev. | Ops | Detalle |
|---|---|---|
| `0002` | 24 | 20 `add_column` (mascotas ×8, mascota_salud ×1, mascota_fotos ×1, refugios ×6, citas ×1, contenido_pasos ×3) + 4 `create_check` (`CK_mascotas_sexo`, `CK_mascotas_tamano`, `CK_refugios_tipo`, `CK_contenido_pasos_tipo`) |
| `0003` | 4 | `alter_column` a `NVARCHAR(MAX)` en `contenido_faqs.respuesta`, `contenido_pasos.descripcion`, `refugios.descripcion`, `mascotas.descripcion`. No-op real (0 `NTEXT`). |
| `0004` | 4 | `add_column alertas_rescate.nombre`, `UPDATE ... SET nombre = N'' WHERE nombre IS NULL` (0 filas), `alter_column ... NOT NULL`, `add_column alertas_rescate.mensaje` |
| `0005` | 12 | 4 `add_column` en `mascotas` (distrito_id, etiqueta_clase, cita_texto, cita_autor) + `create_fk FK_mascotas_distritos` + 3 `add_column` en `mascota_rasgos` (icono, clase, icono_clase) + `create_table mascota_historia` + su índice + `create_table mascota_cuidados` + su índice |
| `0006` | 1 | `alter_column mascota_rasgos.clase` (longitud) |
| `0007` | 2 | `add_column mascotas.vacunado`, `add_column mascotas.esterilizado` |
| `0008` | 2 | `drop_index IX_mascotas_catalogo`, `create_index IX_mascotas_catalogo` (con `INCLUDE (destacada, nombre)`) |
| `0009` | 1 | `add_column refugios.orden` |

Las 8 revisiones fueron **re-ejecutadas (replay) sobre la estructura real reflejada de `LeonsDB`** y todas aplicaron sin error.

## 5. Delta final (post-`upgrade head` vs. modelo actual)

`alembic check` sobre `LeonsDB` tras el replay reporta **37 objetos por añadir y 0 por eliminar/modificar**:

- 2 tablas nuevas: `mascota_cuidados`, `mascota_historia` (+ sus 2 índices).
- 32 columnas nuevas (20 de `0002` + 2 de `0004` + 7 de `0005` + 2 de `0007` + 1 de `0009`).
- 1 FK nueva: `FK_mascotas_distritos`.
- 1 recreación de índice: `IX_mascotas_catalogo` (0008).

No hay `remove_table`, `remove_column`, `modify_type`, `modify_nullable` ni `modify_default`. No se toca `sysdiagrams`.

## 6. Riesgos detectados

| # | Riesgo | Severidad | Mitigación / nota |
|---|---|---|---|
| R1 | `stamp 0001` asume que la base coincide con `0001`. Si no, el baseline es falso. | alto | Evidencia: `compare_metadata` = 0 diferencias + defaults/identity/PK/FK/UNIQUE/índices verificados. Residual solo los 2 nombres de CHECK e INCLUDE (§3.2/3.3), que no afectan el `upgrade`. |
| R2 | `0008` hace `DROP`+`CREATE` del índice del catálogo. | bajo | Es un índice, no una tabla; tabla vacía → instantáneo; mismo conjunto de columnas incluidas. Toma bloqueo Sch-M breve. |
| R3 | `0003` ejecuta `ALTER COLUMN` sobre 4 columnas `NVARCHAR(MAX)`. | bajo | 0 `NTEXT` en la base → alter de mismo tipo; Sch-M lock; tablas vacías. No toca datos. |
| R4 | `0002` crea 4 CHECK constraints; fallaría si hubiera filas violando. | medio | Las 18 tablas están vacías → sin riesgo. **Consecuencia operativa:** el `upgrade` debe ejecutarse ANTES del seed de G6 (los datos del seed ya validan en `LeonsDB_Test`). |
| R5 | `0004` hace `UPDATE ... SET nombre = N''` y luego `ALTER ... NOT NULL`. | bajo | Tabla vacía → 0 filas afectadas. |
| R6 | `0005` añade FK `mascotas → distritos` (nullable). | bajo | Tabla vacía; `distritos` existe en `0001`. |
| R7 | No hay backup previo. | bajo | Las 18 tablas de dominio tienen 0 filas → riesgo de pérdida de datos nulo. Se ofrece `BACKUP DATABASE` opcional antes de escribir. |
| R8 | Fallo parcial a mitad del `upgrade`. | bajo | SQL Server soporta DDL transaccional → toda la cadena se revierte. Si se interrumpe, Alembic deja la BD en la revisión alcanzada y `upgrade head` es reanudable. |
| R9 | Tras el `upgrade`, `LeonsDB` tendrá 22 tablas (20 dominio + `sysdiagrams` + `alembic_version`) y head `0009`, igual que `LeonsDB_Test` salvo los 2 nombres de CHECK e INCLUDE. | info | `REPOS_BACKEND` sigue en `memory` por defecto → sin cambio de runtime. |
| R10 | Los 2 CHECK legado (`CK_alertas_especie`, `CK_alertas_estado`) sobreviven al `upgrade` porque ninguna migración los renombra. | bajo | Cosmético; cumplen la convención `CK_`. Paridad exacta requiere una nueva revisión `0010`. |
| R11 | `alembic check` será limpio tras el `upgrade`, pero no valida CHECK names ni INCLUDE. | info | Confirmar manualmente en la verificación de integridad. |

## 7. Confirmación de no recreación ni pérdida de datos

- **0** operaciones `create_table` sobre tablas existentes; las 2 `create_table` son tablas nuevas (`mascota_historia`, `mascota_cuidados`).
- **0** `drop_table`, **0** `drop_column`, **0** `modify_*`.
- El único `drop_*` es `drop_index IX_mascotas_catalogo`, que se recrea en la misma revisión `0008` con el mismo conjunto de columnas incluidas.
- Las 18 tablas de dominio tienen **0 filas** → no hay datos que perder.
- `sysdiagrams` y sus 7 procedimientos quedan fuera de Alembic (`_incluir_objeto`) y no se tocan.
- No se ejecuta seed, `DROP` ni `TRUNCATE`.

## 8. Autorización solicitada (paso 3)

Sin ejecutar nada hasta confirmación explícita, se propone:

1. `uv run alembic -x target=main stamp 0001` (crea `alembic_version` con `0001`; no toca tablas de dominio).
2. `uv run alembic -x target=main upgrade head` (aplica `0002`–`0009`, 50 operaciones).
3. Verificación de integridad + `uv run alembic -x target=main check` (debe ser limpio).
4. (Opcional, según respuesta) nueva revisión `0010` que renombre los 2 CHECK legado.
5. (Opcional) `BACKUP DATABASE LeonsDB` previo.

## 9. Conciliación de restricciones CHECK (solo lectura)

### 10.1 Las 4 CHECK pendientes de la migración `0002`

Ninguna existe en `LeonsDB` (ni con su nombre canónico ni con un nombre alternativo). Verificado contra `sys.check_constraints` filtrado por tabla y condición.

| # | Tabla | Nombre (migración) | Condición exacta (migración) | ¿Existe en `LeonsDB`? |
|---|---|---|---|---|
| 1 | `mascotas` | `CK_mascotas_sexo` | `sexo IS NULL OR sexo IN ('Macho', 'Hembra')` | No. `mascotas` solo tiene `CK_mascotas_edad`, `CK_mascotas_especie`, `CK_mascotas_estado`. |
| 2 | `mascotas` | `CK_mascotas_tamano` | `tamano IS NULL OR tamano IN ('Pequeño', 'Mediano', 'Grande')` | No. Ningún CHECK con esos literales. |
| 3 | `refugios` | `CK_refugios_tipo` | `tipo IS NULL OR tipo IN ('constituido', 'independiente')` | No. `refugios` solo tiene `CK_refugios_contadores`. (La columna `tipo` tampoco existe aún en `LeonsDB`; la añade `0002` antes del CHECK.) |
| 4 | `contenido_pasos` | `CK_contenido_pasos_tipo` | `tipo IN ('adopcion', 'refugio', 'requisito')` | No. `contenido_pasos` no tiene ningún CHECK en `LeonsDB`. (La columna `tipo` se añade en `0002` con default `'adopcion'`.) |

**Conclusión:** las 4 faltan realmente; no son renombrados. `0002` las creará sobre tablas vacías, sin riesgo de violación. No hay duplicación posible porque no existe equivalente.

### 10.2 `alertas_rescate`: nombres legado vs. canónicos

| Nombre en `LeonsDB` | Definición en `LeonsDB` | Nombre canónico (migración) | Definición canónica | ¿Misma condición? |
|---|---|---|---|---|
| `CK_alertas_especie` | `especie IS NULL OR (especie = 'gato' OR especie = 'perro')` | `CK_alertas_rescate_especie` | `especie IS NULL OR especie IN ('perro', 'gato')` | **Sí** (equivalente: `IN` vs `OR`, mismo conjunto; prefijo `N` es solo el render Unicode de SQL Server) |
| `CK_alertas_estado` | `estado = 'cerrada' OR estado = 'atendida' OR estado = 'nueva'` | `CK_alertas_rescate_estado` | `estado IN ('nueva', 'atendida', 'cerrada')` | **Sí** (equivalente) |

**Conclusión:** los 2 CHECK legado son funcionalmente idénticos a los canónicos. La única diferencia es el nombre (prefijo de sujeto: columna vs. tabla). Ambos cumplen la convención `CK_` de §13 de `AGENTS.md`. No hay impacto funcional, de rendimiento, de seed ni de `alembic check` (Alembic no compara CHECK).

### 10.3 Decisión de conciliación (propuesta)

- **No crear `0010`** para renombrar los 2 CHECK legado: no existe necesidad técnica demostrada (§7 de las condiciones). Renombrar implicaría `DROP CONSTRAINT` + `CREATE CONSTRAINT` sobre una BD que ya cumple la regla, sin beneficio funcional, solo por estética de nombre. Esto evitaría operaciones de escritura adicionales y mantendría el plan mínimo.
- **No crear CHECK duplicados:** dejar los legado tal cual evita tener dos restricciones con la misma condición sobre la misma tabla.
- **No eliminar restricciones existentes:** los 2 legado se conservan; cumplen la regla y no molestan.
- Resultado: tras el `upgrade head`, `LeonsDB` tendrá 19 CHECK (15 originales + 4 nuevos de `0002`), de los cuales 2 conservarán el nombre legado. `LeonsDB_Test` tendrá 19 con nombres canónicos. **Paridad funcional completa; paridad de nombres: 17/19.**

Si en el futuro se quisiera paridad exacta de nombres (p. ej. para un diff limpio en SSMS), bastaría una revisión `0010` con `op.drop_constraint` + `op.create_check_constraint` sobre tabla vacía o poblada; queda como opción documentada, no obligatoria.

## 10. Plan definitivo de ejecución (sin writes hasta confirmación)

**Objetivo:** llevar `LeonsDB` de su estado actual (estructura `0001`, 0 filas) a head `0009`, con paridad funcional frente a `LeonsDB_Test`, sin tocar datos ni `sysdiagrams`.

**Precondiciones verificadas (solo lectura):**
- `DB_URL` apunta a `LeonsDB` (default de `-x target=main`). Confirmado en `migrations/env.py` líneas 43–50.
- `LeonsDB` tiene 0 filas en las 18 tablas de dominio.
- `compare_metadata(LeonsDB, 0001)` = 0 diferencias.
- 8 revisiones `0002`–`0009` aplicables (replay verificado).

**Operaciones que se ejecutarían (en este orden):**

1. `uv run alembic -x target=main stamp 0001`
   - Crea la tabla `alembic_version` y registra la revisión `0001`.
   - No modifica ninguna tabla de dominio. No toca `sysdiagrams`.
   - Resultado: `LeonsDB` queda marcada como baseline `0001`.

2. `uv run alembic -x target=main upgrade head`
   - Aplica `0002` → `0009` en una sola transacción (SQL Server soporta DDL transaccional).
   - 50 operaciones, de las cuales 49 son aditivas y 1 es `DROP INDEX` + `CREATE INDEX` (`0008`).
   - Detalle por revisión: ver sección 4 de este informe.
   - Las 4 CHECK pendientes se crean en `0002` sobre tablas vacías.

3. Verificación de integridad (solo lectura):
   - `uv run alembic -x target=main check` → debe reportar 0 diferencias.
   - Conteo de tablas: 22 (20 dominio + `sysdiagrams` + `alembic_version`).
   - Conteo de filas: 0 en las 20 tablas de dominio.
   - Head registrado: `0009`.
   - `sysdiagrams` intacta (1 tabla + 7 procedimientos).
   - CHECK: 19 en total; 17 con nombre canónico, 2 con nombre legado (`CK_alertas_especie`, `CK_alertas_estado`).
   - `IX_mascotas_catalogo`: claves `(estado, especie)`, `INCLUDE (destacada, nombre)`.
   - IDENTITY intacto: 15 columnas `(1,1)`.

**Objetos que se crearían:**
- Tabla `alembic_version` (técnica, 1 fila).
- Tablas `mascota_historia`, `mascota_cuidados` (+ 2 índices).
- 32 columnas nuevas (20 en `0002`, 2 en `0004`, 7 en `0005`, 2 en `0007`, 1 en `0009`).
- FK `FK_mascotas_distritos`.
- 4 CHECK (`CK_mascotas_sexo`, `CK_mascotas_tamano`, `CK_refugios_tipo`, `CK_contenido_pasos_tipo`).
- Recreación de `IX_mascotas_catalogo` (mismo conjunto de columnas incluidas).

**Objetos que se modificarían:**
- 4 columnas `NVARCHAR(MAX)` re-alteradas en `0003` (mismo tipo, sin cambio real).
- `mascota_rasgos.clase` longitud en `0006`.
- `alertas_rescate.nombre` pasa de NULL a NOT NULL en `0004` (tabla vacía).

**Objetos que NO se tocan:**
- Las 18 tablas base y sus datos (0 filas).
- `sysdiagrams` y sus 7 procedimientos.
- Los 2 CHECK legado de `alertas_rescate` (se conservan).
- El frontend (`Leons/`) y el backend anterior (`LeonS-Mateo/`).

**Riesgos residuales (ver sección 6):** R1–R11; los más relevantes son R4 (CHECK sobre tablas vacías → sin riesgo) y R7 (sin backup, pero 0 filas). Se ofrece `BACKUP DATABASE LeonsDB` opcional antes del paso 1.

**Lo que NO se ejecutará en esta puerta:** seed (`db/seed.py`), `LeonsDB_Test` (ya está en head), cambios en frontend, migración `0010`.

## 11. Autorización solicitada (G5, paso 3)

Se solicita autorización explícita para ejecutar, en este orden y sin saltos:

1. `uv run alembic -x target=main stamp 0001`
2. `uv run alembic -x target=main upgrade head`
3. Verificación de integridad + `uv run alembic -x target=main check`

**Opciones:**

- **(A) Autorizar la ejecución completa** (stamp + upgrade + check). Recomendado.
- **(B) Autorizar con `BACKUP DATABASE LeonsDB` previo** (el backup se genera con `sqlcmd`/SSMS; no requiere cambios en el código).
- **(C) No autorizar; solicitar ajustes al plan.**

G6 (seed en `LeonsDB`) sigue sin autorización y requerirá aprobación independiente tras verificar G5.

---

**Hecho:** conciliación de CHECK completada (solo lectura); 4 pendientes confirmados como realmente ausentes; 2 legado confirmados como funcionalmente idénticos a los canónicos; plan definitivo de ejecución presentado.
**Verificado:** definiciones exactas obtenidas de `sys.check_constraints` y de `0001_init.py`/`0002_contrato_catalogo.py`; equivalencia semántica comprobada (IN vs OR, prefijo `N`).
**Decisiones tomadas:** ninguna nueva; se propone no crear `0010` ni renombrar (pendiente de confirmación).
**Siguiente fase:** espera confirmación explícita (opción A/B/C) antes de cualquier escritura en `LeonsDB`.
---

## 12. EjecuciÃ³n realizada (G5 cerrada)

**Fecha de ejecuciÃ³n:** 18/11/2026 (tras autorizaciÃ³n explÃ­cita, opciÃ³n B).

### 12.1 Respaldo previo

- Archivo: `C:\Program Files\Microsoft SQL Server\MSSQL17.SQLEXPRESS\MSSQL\Backup\LeonsDB_preG5_20261118_205214.bak`
- `BACKUP DATABASE ... WITH FORMAT, INIT, CHECKSUM` â†’ Ã©xito (682 pÃ¡ginas).
- `RESTORE VERIFYONLY ... WITH CHECKSUM` â†’ "The backup set on file 1 is valid."

### 12.2 Migraciones ejecutadas

1. `uv run alembic -x target=main stamp 0001` â†’ `alembic_version` = `0001`.
2. `uv run alembic -x target=main upgrade head` â†’ aplicÃ³ `0002` â†’ `0009` en una sola transacciÃ³n (sin error).
3. `uv run alembic -x target=main check` â†’ "No new upgrade operations detected." (limpio).

### 12.3 VerificaciÃ³n de integridad (post-ejecuciÃ³n)

| VerificaciÃ³n | Resultado |
|---|---|
| `alembic_version` | `0009` |
| `alembic check` | 0 diferencias |
| Tablas totales | 22 (20 dominio + `sysdiagrams` + `alembic_version`) |
| Procedimientos `sysdiagrams` | 7 intactos |
| Filas en las 20 tablas de dominio | 0 (no se ejecutÃ³ seed) |
| CHECK heredados conservados | `CK_alertas_especie`, `CK_alertas_estado` (nombres originales) |
| CHECK nuevos creados | `CK_mascotas_CK_mascotas_sexo`, `CK_mascotas_CK_mascotas_tamano`, `CK_refugios_CK_refugios_tipo`, `CK_contenido_pasos_CK_contenido_pasos_tipo` (4) |
| IDENTITY | 18 columnas (17 de dominio + `sysdiagrams.diagram_id`) |
| `IX_mascotas_catalogo` | claves `(estado, especie)`, `INCLUDE (destacada, nombre)` |
| `NTEXT` | 0 columnas |

### 12.4 ObservaciÃ³n: nombres de CHECK con prefijo de tabla (doble prefijo)

Las restricciones creadas por Alembic/SQLAlchemy en el dialecto MSSQL quedan con el nombre de tabla prefijado: `CONSTRAINT [CK_mascotas_CK_mascotas_sexo]`. Es un comportamiento consistente del dialecto (verificado con `alembic upgrade --sql`): tanto `LeonsDB` (post-upgrade) como `LeonsDB_Test` presentan el mismo doble prefijo en las restricciones creadas por Alembic.

Las restricciones originales de `LeonsDB` (creadas antes de Alembic) conservan sus nombres simples: `CK_mascotas_especie`, `CK_mascotas_estado`, `CK_mascotas_edad`, `CK_refugios_contadores`, `CK_alertas_especie`, `CK_alertas_estado`. Por ello, tras el upgrade, `LeonsDB` tiene una mezcla: 6 restricciones con nombre simple (originales) + 4 con doble prefijo (nuevas de `0002`), mientras que `LeonsDB_Test` tiene todas con doble prefijo.

**EvaluaciÃ³n:** no es un defecto funcional (mismas condiciones, `alembic check` limpio, seed valida idÃ©ntico). Renombrar las 6 originales al formato con doble prefijo requerirÃ­a una revisiÃ³n `0010` con `DROP`+`CREATE` sin justificaciÃ³n tÃ©cnica. **No se realiza acciÃ³n.** Queda documentado como diferencia cosmÃ©tica aceptada.

### 12.5 ConfirmaciÃ³n de no inserciÃ³n de registros

Las 20 tablas de dominio tienen **0 filas**. No se ejecutÃ³ `db/seed.py`. No se ejecutÃ³ `DROP`, `TRUNCATE` ni recreaciÃ³n de la base. `sysdiagrams` y sus 7 procedimientos permanecen intactos.

### 12.6 Restricciones respetadas

- Sin seed en `LeonsDB`.
- Sin `DROP DATABASE` ni `TRUNCATE`.
- Sin modificaciones a `Leons/` ni `LeonS-Mateo/`.
- Sin cambios a contratos API.
- Sin eliminar ni renombrar los 2 CHECK heredados.
- Sin migraciÃ³n `0010`.
- Sin operaciones adicionales fuera del plan aprobado.

---

**Hecho:** G5 ejecutada y cerrada en `LeonsDB`: backup verificado + `stamp 0001` + `upgrade head` (0002-0009) + `check` limpio. Head `0009`, 22 tablas, 0 filas, `sysdiagrams` intacto.
**Verificado:** backup `RESTORE VERIFYONLY` valido; `alembic_version=0009`; `alembic check` sin diferencias; 4 CHECK nuevos creados y 2 heredados conservados; `IX_mascotas_catalogo` con `INCLUDE (destacada, nombre)`; 18 columnas IDENTITY (17 dominio); 0 filas en las 20 tablas de dominio.
**Decisiones tomadas:** D-036 - se acepta la diferencia cosmetica de nombres de CHECK (prefijo doble en las creadas por Alembic vs. simples en las originales) sin crear `0010`; el backup previo se conserva como punto de restauracion.
**Siguiente fase:** G5 cerrada. **G6 (seed en `LeonsDB`) continÃºa sin autorizaciÃ³n** y requiere aprobaciÃ³n independiente. Fase 4 (auditorÃ­a) y Fase 7 (frontend) siguen pendientes.
