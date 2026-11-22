# Registro de decisiones — LeonS

Formato ADR-lite: `ID`, fecha, contexto, opciones, decisión y consecuencias.
Las decisiones D-001 a D-012 están resumidas en `AGENTS.md` §16.1; aquí se
documentan con el detalle que exige el protocolo de la sección 2.5.

Fecha de las decisiones iniciales: **2026-11-17**.
Fecha de las decisiones de implementación (Fases 0–3): **2026-11-17**.
Fecha de las decisiones de modelado (Fase 5): **2026-11-18**.
Fecha de las decisiones de la Fase 6: **2026-11-18**.

## Resumen

| ID | Decisión | Estado |
|---|---|---|
| D-001 | Backend nuevo, no recuperar el anterior | Aceptada |
| D-002 | Ubicación `Backend/` en la raíz | Aceptada |
| D-003 | FastAPI + Uvicorn | Aceptada |
| D-004 | SQLAlchemy 2.0 + Alembic + pyodbc | Aceptada |
| D-005 | SQL Server `LeonsDB` y `LeonsDB_Test` | Aceptada |
| D-006 | Contrato `/api/v1` completo | Aceptada |
| D-007 | JSON camelCase compatible con Angular | Aceptada |
| D-008 | Campos de presentación calculados, no persistidos | Aceptada |
| D-009 | Seed exportado desde las constantes de Angular | Aceptada |
| D-010 | `LeonS-Mateo/` intacto | Aceptada |
| D-011 | Fases con puertas de aprobación | Aceptada |
| D-012 | Auditoría antes de SQL Server | Aceptada |
| D-013 | Fijar Python 3.13 con `.python-version` | Aceptada |
| D-014 | La paginación devuelve la clave `items` | Aceptada |
| D-015 | PDF mínimo propio, sin dependencias | Aceptada |
| D-016 | Credenciales demo en el loader, no en el seed | Aceptada |
| D-017 | Una solicitud nueva nace en la etapa 2 | Aceptada |
| D-018 | Overrides editoriales del seed para la ficha de Chaska | Aceptada |
| D-019 | Migraciones aditivas `0002` y `0003` sobre el esquema existente | Aceptada |
| D-020 | Los servicios dependen del protocolo `Repositorio` | Aceptada |
| D-021 | `contenido_pasos.tipo` con `orden` único global | Aceptada |
| D-022 | Alembic usa `alembic_version`; `migraciones` es funcional | Aceptada |
| D-023 | `fichaId` derivado del `id`, no persistido | Aceptada |
| D-024 | `alertas_rescate.estado` ↔ `atendida` calculado | Aceptada |
| D-025 | `crear_*()` inserta y devuelve la entidad con id de SQL Server | Aceptada |
| D-026 | `alertas_rescate.nombre` y `mensaje` en una migración aditiva | Aceptada |
| D-027 | Comparar `LeonsDB` con `0001` antes de cualquier `stamp` | Aceptada |
| D-028 | Matriz de mapeo dominio ↔ tablas como base de la Fase 6 | Aceptada |
| D-029 | Distrito, `etiqueta_clase` e iconos de rasgo con columnas propias | Aceptada |
| D-030 | `mascota_historia` y `mascota_cuidados` normalizadas; cita en `mascotas` | Aceptada |
| D-031 | `cierre` y `destacado` de una postulación se derivan, no se persisten | Aceptada |
| D-032 | `mascotas.vacunado` y `esterilizado` se persisten; NULL se deriva de salud | Aceptada |
| D-033 | Los textos editoriales de las solicitudes demo se derivan y se documentan | Aceptada |
| D-034 | `alembic check` limpio: `sysdiagrams` filtrado e `IX_mascotas_catalogo` con `INCLUDE` | Aceptada |
| D-035 | `refugios.orden` conserva el orden editorial del listado | Aceptada |
| D-036 | Aceptar el prefijo doble de nombres de CHECK de Alembic SQL Server | Aceptada |
| D-040 | G5/G6: migrar y sembrar `LeonsDB` con backup verificado | Aceptada |
| D-041 | CORS explícito en producción (`CORS_ORIGINS`) | Aceptada |
| D-042 | TLS obligatorio en producción (`Encrypt=yes`, sin `TrustServerCertificate`) | Aceptada |
| D-043 | Rate limit distribuido: evaluado, **no implementado** | Aceptada |

---

## Correspondencia de identificadores (5.6.3.3B)

D-036 conserva su significado histórico: la decisión sobre el prefijo doble de
nombres de CHECK creado por el dialecto MSSQL de Alembic. Está documentada más
abajo y citada en `docs/G5-comparacion.md` y `docs/G6-seed.md`.

Los identificadores que `AGENTS.md` usó temporalmente para otras decisiones se
regularizan sin reasignar el registro histórico:

| ID anterior | ID actual | Decisión |
|---|---|---|
| D-036 (migración/seed) | D-040 | G5/G6: migrar y sembrar `LeonsDB` con backup verificado |
| D-037 | D-041 | CORS explícito en producción |
| D-038 | D-042 | TLS obligatorio en producción |
| D-039 | D-043 | Rate limit distribuido: evaluado, no implementado |

Los informes E2E de 5.6.3.2B y 5.6.3.2D conservan sus referencias originales
por ser evidencia histórica; no se modificaron.

---

## D-013 — Fijar Python 3.13

**Contexto:** `uv` eligió Python 3.15 y `uvicorn[standard]` arrastró `pyyaml`, que
no tiene wheel para 3.15 y exige Visual C++ Build Tools en Windows.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Fijar 3.13 con `.python-version` | Wheels disponibles; nadie necesita compilar | Una versión menos que la última |
| B. Quitar `uvicorn[standard]` | Menos dependencias | Se pierde `--reload` con watchfiles |

**Decisión:** A. Se añade `Backend/.python-version` con `3.13`.

**Consecuencias:** `uv sync` funciona en cualquier máquina con `uv`; si el docente
exige otra versión, se cambia el archivo y se vuelve a sincronizar.

---

## D-014 — La paginación usa `items`

**Contexto:** `AGENTS.md` fija `page`, `limit`, `total` y `totalPages`, pero no el
nombre del arreglo. El frontend todavía no consume la API, así que se puede elegir.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. `items` | Convención común en APIs REST | Hay que mapearlo en Angular |
| B. `mascotas` / `solicitudes` | Más explícito | Rompe la uniformidad entre endpoints |

**Decisión:** A. Todos los listados paginados devuelven `{ items, page, limit,
total, totalPages }`.

**Consecuencias:** En la Fase 7 el service de Angular lee `respuesta.items`.

---

## D-015 — PDF mínimo propio

**Contexto:** `test_cancelar_y_documentos_pdf` exige un PDF. Añadir ReportLab o
WeasyPrint es una dependencia pesada para una constancia simple (Q-05).

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Generador PDF propio (`adapters/pdf.py`) | Cero dependencias, determinista | Solo texto plano, sin estilos complejos |
| B. ReportLab | PDFs elaborados | Dependencia y curva de aprendizaje |

**Decisión:** A. Si el curso pide un carnet diseñado, se reemplaza el adaptador sin
tocar routers ni tests.

**Consecuencias:** El endpoint devuelve `application/pdf` con una constancia de la
postulación; el nombre del archivo incluye el código.

---

## D-016 — Credenciales demo fuera del seed

**Contexto:** El seed debe salir de Angular y no contener contraseñas. Las cuentas
demo son necesarias para probar login, solicitudes y panel de refugio.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Usuarios demo en `app/data/loader.py`, hash al iniciar | Sin texto plano en disco ni en BD | Las claves están en el código |
| B. `passwordHash` dentro de `seed.json` | Un solo archivo de datos | El seed deja de ser exportable desde Angular |

**Decisión:** A. Los hashes se calculan una vez por proceso con `lru_cache`.

**Consecuencias:** Las cuentas demo son solo para desarrollo; en producción se
eliminan o se cambian por variables de entorno.

---

## D-017 — La solicitud nueva nace en la etapa 2

**Contexto:** El frontend actual (`solicitudes.service.ts`) crea la postulación con
`paso: 2` y el texto “En Revisión Inicial”. El backend debe respetar ese contrato.

**Decisión:** `POST /solicitudes` crea la solicitud en `etapa = 2`, estado `activa`,
código `#SOL-HYO-<año>-<NNN>`.

**Consecuencias:** “Enviada” (etapa 1) queda como paso histórico; el refugio puede
retroceder con `PATCH /solicitudes/{id}/etapa` si lo necesita.

---

## D-018 — Overrides editoriales del seed

**Contexto:** `detalle.data.ts` define una historia, una cita y cuidados especiales
solo para Chaska (id 1). El resto de fichas se generan con plantillas.

**Decisión:** El seed guarda esos textos editoriales en `detalles`. `mapper.py` los
usa si existen y, si no, genera historia, cuidados y preguntas con las plantillas
del frontend.

**Consecuencias:** La ficha de Chaska conserva su contenido exacto sin duplicar
lógica en el backend.

---

## D-019 — Migraciones aditivas sobre el esquema existente

**Contexto:** `LeonsDB` ya tenía 18 tablas con datos y la Fase 5 prohíbe
recrearlas. El contrato JSON necesita columnas que no existían (`peso_kg`,
`energia`, `etiqueta`, `contacto`, `tipo`, `coordinadora`, etc.).

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. `0001` base + `0002`/`0003` aditivas | No se recrea nada; `LeonsDB` se actualiza sin perder datos | Tres revisiones en lugar de una |
| B. Una sola `0001` que incluya todo y `DROP`/recarga | Un solo archivo | Perdería datos y contradice la restricción de la fase |

**Decisión:** A. `0001` refleja el esquema previo; `0002` solo agrega columnas,
CHECK e índices; `0003` normaliza `NTEXT` → `NVARCHAR(MAX)`. Ninguna revisión
borra tablas ni columnas del modelo aprobado.

**Consecuencias:** La Fase 6 puede aplicar `upgrade head` sobre `LeonsDB` sin
`DROP`. `alembic check` confirma que modelos y base coinciden. Si se detecta
una columna faltante, se agrega en una revisión nueva.

---

## D-020 — Los servicios dependen del protocolo `Repositorio`

**Contexto:** Las Fases 0–3 tipaban los servicios contra `MemoryRepository`.
La Fase 6 introduce `SqlServerRepository`; si los servicios conocen la clase
concreta, migrar obliga a editar routers, servicios y dependencias.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. `Protocol` `Repositorio` en `domain.py` | Los servicios no cambian al migrar; contrato explícito | Hay que mantener el protocolo sincronizado |
| B. Clase base abstracta | Herencia explícita | Acopla los repositorios a una jerarquía |

**Decisión:** A. `app/domain.py` declara `Repositorio` con el contrato completo
(`listar_*`, `obtener_*`, `crear_*`, `guardar_*`, `eliminar_*`,
`siguiente_*_id`). Servicios, `Container` y `dependencies.get_repo` se tipan
contra el protocolo; solo `container.py` instancia la implementación.

**Consecuencias:** La Fase 6 añade `repositories/sqlserver.py` y cambia una
línea en el contenedor (`REPOS_BACKEND`). Los 15 tests no se tocan.

---

## D-021 — `contenido_pasos.tipo` con `orden` único global

**Contexto:** El frontend maneja tres listas: 4 pasos de adopción, 3 pasos para
refugios y 4 requisitos. El modelo aprobado tiene 18 tablas y no incluye
`contenido_requisitos`.

**Decisión:** Se añade `contenido_pasos.tipo` (`adopcion`, `refugio`,
`requisito`) con `CHECK`, y `orden` sigue siendo único **global** con rangos
reservados: 1–4 adopción, 5–7 refugio, 8–11 requisito (ver
`docs/modelo-datos.md` §4.3).

**Consecuencias:** No se crea una tabla 19. `mapper.py` separa las tres listas
filtrando por `tipo`. El seed debe respetar los rangos o el `INSERT` falla por
`UX_contenido_pasos_orden`.

---

## D-022 — `alembic_version` y la tabla `migraciones`

**Contexto:** El esquema ya tenía una tabla `migraciones` de negocio. Alembic
necesita su propio registro de revisiones.

**Decisión:** Alembic usa su tabla estándar `alembic_version`, con el nombre
por defecto. `migraciones` se conserva como registro funcional del equipo y
**no** se usa para versionar el esquema.

**Consecuencias:** `LeonsDB_Test` tiene 19 tablas: 18 de dominio +
`alembic_version`. El export `db/schema.sql` documenta solo las 18 de dominio
y advierte de la tabla técnica.

---

## D-023 — `fichaId` derivado del `id`

**Contexto:** El frontend muestra `LS-HYO-0482` y usa `fichaId` como
identificador visible. La clave real es `mascotas.id`; guardar la ficha como
columna duplicaría una regla de presentación.

**Decisión:** `fichaId` no se persiste. Se deriva del `id`:
`LS-HYO-{481 + id}` para la semilla (ids 1–16 → 0482–0497) y
`LS-HYO-{5000 + id}` para altas nuevas, de modo que no colisionen con el rango
editorial.

**Consecuencias:** El mapper expone `fichaId`; las solicitudes guardan
`mascota_id`. Renumerar la semilla obliga a regenerar `seed.json`, no a migrar
la base.

---

## D-024 — `alertas_rescate.estado` y el booleano `atendida`

**Contexto:** El DTO de alertas expone `atendida` como booleano, mientras la
base modela un ciclo de vida de tres estados (`nueva`, `atendida`, `cerrada`).

**Decisión:** Se conserva `estado` con `CHECK` y el mapper calcula
`atendida = estado <> 'nueva'`. No se agrega una columna booleana redundante.

**Consecuencias:** El contrato `/api/v1` no cambia y la base mantiene la
diferencia entre "atendida" y "cerrada". Si el frontend necesita distinguirlas,
se expone `estado` en una versión futura del DTO, no antes.

---

## D-025 — Identificadores generados por el repositorio

**Contexto:** El repositorio en memoria asignaba ids con `siguiente_*_id()` y
guardaba con un upsert (`guardar_*`). SQL Server genera el id al insertar, así
que el código de la solicitud y la ficha no pueden calcularse antes.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. `crear_*()` inserta y devuelve la entidad con el id definitivo | Coincide con `IDENTITY`; sin `IDENTITY_INSERT` en operaciones normales | Cambia la firma de cuatro servicios |
| B. `IDENTITY_INSERT` con id calculado en Python | No cambia los servicios | Dos escritores pueden elegir el mismo id; viola el diseño de SQL Server |

**Decisión:** A. El protocolo expone `crear_mascota`, `crear_usuario`,
`crear_solicitud`, `crear_alerta`, `actualizar_mascota` y
`actualizar_solicitud`. Las entidades viajan con `id = 0`; para las solicitudes
el repositorio fija `codigo = #SOL-HYO-{año}-{id:03d}` dentro de la misma
transacción. `ficha_id` se deriva del id (D-023).

**Consecuencias:** Los servicios dejan de calcular ids y códigos. El seed
conserva `IDENTITY_INSERT` porque debe preservar los ids 1–16; es la única
excepción y está acotada a `db/seed.py`.

---

## D-026 — `alertas_rescate.nombre` y `mensaje`

**Contexto:** El contrato de alertas de rescate pide `nombre` obligatorio y
`mensaje` opcional, pero la tabla solo tenía `contacto` y `descripcion`.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Migración `0004` aditiva con `nombre` y `mensaje` | Conserva el contrato y no toca datos existentes | Dos columnas nuevas |
| B. Reutilizar `contacto` como nombre | Cero cambios de esquema | Mezcla identidad con medio de contacto; el contrato miente |

**Decisión:** A. `nombre NVARCHAR(120) NOT NULL` y
`mensaje NVARCHAR(1000) NULL`. Para bases con filas se agrega `nombre` como
NULL, se rellena con cadena vacía (no se copia `contacto`) y luego se marca
NOT NULL. No se inventan mensajes.

**Consecuencias:** `0004` es reversible con `downgrade`, que elimina solo sus
propias columnas. El mapper sigue exponiendo `atendida` (D-024).

---

## D-027 — Comparar `LeonsDB` con `0001` antes de cualquier `stamp`

**Contexto:** `LeonsDB` se creó antes de Alembic y no tiene `alembic_version`.
Marcarla como `0001` sin verificar podría dejar el historial mintiendo.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Comparar el esquema real con `0001` y detenerse si hay diferencias | Verificación reproducible antes de escribir | Un paso más antes de migrar |
| B. `stamp 0001` directo | Rápido | Si el esquema difiere, `check` nunca queda limpio |

**Decisión:** A. Comparación de solo lectura de tablas, columnas, tipos,
nulabilidad, identidad, PK, UNIQUE, FK, defaults e índices.

**Consecuencias:** Resultado: 18/18 tablas de dominio equivalentes a `0001`,
0 filas. Diferencias reales: `sysdiagrams` y 7 procedimientos de SSMS, nombres
de restricciones en `alertas_rescate` y `INCLUDE` en `IX_mascotas_catalogo`.
`stamp` y `upgrade` sobre `LeonsDB` siguen pendientes de autorización explícita.

---

## D-028 — Matriz de mapeo como base de la Fase 6

**Contexto:** El contrato expone campos que no tienen columna directa
(`fichaId`, `actualizado`, `esterilizado`, `vacunado`, `etiquetaClase`) y
columnas que no están en el contrato (`descripcion`, `estado` de la alerta).

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Matriz explícita campo → tabla.columna o regla derivada | Auditable; los `NULL` tienen comportamiento documentado | Hay que mantenerla |
| B. Resolver caso por caso en el repositorio | Menos papeleo | Reglas invisibles y difíciles de probar |

**Decisión:** A. Reglas acordadas: los `NULL` nunca se rellenan con texto
inventado (el mapper usa la plantilla que ya existía o `null`); vacunación y
esterilización se derivan de `mascota_salud.texto`; el distrito se resuelve por
`distritos`; ids, fichas y códigos se mantienen coherentes.

**Consecuencias:** La matriz vive en `docs/modelo-datos.md` y se verifica con
una prueba de paridad contra `seed.json` para las 16 mascotas.

---

## D-029 — Distrito, `etiqueta_clase` e iconos de rasgo

**Contexto:** `mascotas` no tiene distrito propio (2 de 16 fichas difieren del
distrito del refugio), `etiqueta_clase` tiene 4 valores editoriales no
derivables y `mascota_rasgos` solo guarda el texto del rasgo.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Columnas propias en `mascotas` y `mascota_rasgos` | Conserva 16/16 distritos y las 4 clases visuales | Cinco columnas nuevas |
| B. Derivar del refugio y de `urgente` | Cero cambios | Degrada datos reales del seed |
| C. Una columna JSON de presentación | Una sola columna | Datos opacos, contra la convención de tablas hijas |

**Decisión:** A. `mascotas.distrito_id` (FK `distritos`), `mascotas.etiqueta_clase`,
`mascota_rasgos.icono`, `mascota_rasgos.clase` y `mascota_rasgos.icono_clase`.
Los valores salen del seed o de datos reales.

**Consecuencias:** Migración `0005`, solo aditiva. Los campos siguen siendo de
presentación y se reconstruyen en el mapper.

---

## D-030 — `DetalleMascota` normalizado

**Contexto:** `historia`, `cuidados` y `cita` de la ficha no caben en las 18
tablas. `detalle.rasgos` no se serializa en ningún DTO, así que no necesita
persistencia.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. `mascota_historia` y `mascota_cuidados` + `cita_texto`/`cita_autor` | Legible en SSMS, consultable, fiel al seed | La base pasa de 18 a 20 tablas |
| B. Una tabla genérica con `tipo` | 19 tablas | Mezcla dos conceptos distintos |
| C. Solo en `seed.json` | Cero cambios | Degrada las 16 fichas |

**Decisión:** A. `mascota_historia(mascota_id, orden, texto)`,
`mascota_cuidados(mascota_id, orden, icono, titulo, texto)`,
`mascotas.cita_texto` y `mascotas.cita_autor`. Se conserva exactamente el texto
editorial del seed. `detalle.rasgos` no se persiste (dato muerto del seed).

**Consecuencias:** Migración `0005`. Hay que actualizar el conteo de tablas en
`AGENTS.md` §8.3 y el diccionario de `docs/modelo-datos.md`.

---

## D-031 — `cierre` y `destacado` derivados

**Contexto:** El seed trae un `cierre` para la solicitud completada y un
`destacado` que no coincide con `paso`. Ninguno de los dos es una regla de
negocio: son datos de demostración.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Derivarlos en el mapper | Cero columnas nuevas; el fallback ya existe | El texto del cierre demo difiere del seed en 1 registro |
| B. Persistir 5 columnas de cierre y `destacado` | Fidelidad total del seed | Columnas dedicadas a datos de demostración |

**Decisión:** A. Se documenta la diferencia y se verifica que el frontend no
dependa del texto exacto.

**Consecuencias:** Si la entrega exige fidelidad literal del seed, se cambia a
B antes de sembrar; es una migración aditiva más.

---

## D-032 — `vacunado` y `esterilizado` persistidos, con derivación de respaldo

**Contexto:** D-028 fijó que ambas banderas se derivan de
`mascota_salud.texto`. La prueba de paridad contra el seed demostró que la
premisa no se cumple en un caso: Misha (id 15) tiene `vacunado: true` y su
salud solo dice «Esterilizada» y «Test Felino Negativo». Derivar la dejaría
como no vacunada y el frontend mostraría un dato falso.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Columnas `BIT NULL` con derivación de respaldo | Paridad 16/16; las altas por API siguen funcionando sin obligar el dato | Dos columnas nuevas y una regla con dos caminos |
| B. Mantener solo la derivación | Cero esquema | Misha se muestra mal; contradice el seed |
| C. Persistir solo `vacunado` | Una columna | `esterilizado` queda con un criterio distinto al de su campo gemelo |

**Decisión:** A. Migración `0007` agrega `mascotas.vacunado` y
`mascotas.esterilizado` como `BIT NULL`. Si la columna es `NULL`, el
repositorio deriva de `mascota_salud.texto` (regla de D-028, vigente para
altas nuevas). El seed guarda el valor editorial de las 16 mascotas y solo
rellena `NULL` en bases ya sembradas: nunca sobrescribe.

**Consecuencias:** D-028 queda matizada: la derivación sigue existiendo como
respaldo, pero la columna tiene prioridad. La paridad de las 16 mascotas se
verifica en `tests/test_sqlserver.py`.

---

## D-033 — Textos editoriales de las solicitudes demo

**Contexto:** Las 3 solicitudes demo del seed traen `etapas` con títulos y
detalles propios («2. Revisión de Ficha / Aprobada»), `tiempoRespuesta` y
`whatsapp`. Ninguno es una regla de negocio y el mapper ya los deriva. Al
persistir solo `solicitudes`, `citas` y `mensajes`, esos textos no se
conservan literalmente.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Derivarlos en el mapper y documentar la diferencia | Cero columnas nuevas; el frontend funciona | Una solicitud demo muestra títulos de etapa genéricos |
| B. Persistir etapas y textos | Fidelidad literal del seed | Tabla hija y dos columnas dedicadas a datos de demostración |

**Decisión:** A, en la misma línea que D-031. Se conservan sin cambios el
código (`exp`), la mascota, el estado, la etapa, las fechas, la cita y el
texto del mensaje. Se derivan `etapas`, `tiempoRespuesta`, `whatsapp`,
`cierre` y los campos de presentación.

**Consecuencias:** Las diferencias son cosméticas y quedan verificadas por la
prueba de paridad de solicitudes demo (código, estado, etapa, fechas, cita y
mensaje). El rol del mensaje demo se normaliza a «Coordinación del refugio»
porque la base deriva el rol del usuario autor, no de un texto libre.

---

## D-034 — `alembic check` limpio y alineación del índice del catálogo

**Contexto:** D-027 comparó `LeonsDB` con `0001` y encontró tres diferencias
reales antes de cualquier `stamp`: la tabla `sysdiagrams` de SSMS con sus siete
procedimientos `sp_*diagram`, nombres de `CHECK` distintos en
`alertas_rescate` y un `IX_mascotas_catalogo` con
`INCLUDE (destacada, nombre)` que el modelo no declaraba. Las tres harían que
`alembic check` propusiera operaciones contra `LeonsDB` en G5.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. Filtrar lo ajeno al modelo y adoptar la definición real del índice | `check` limpio sin tocar datos; `LeonsDB` queda alineable | Una revisión nueva que recrea un índice |
| B. Ignorar todas las diferencias en `env.py` | Cero migraciones nuevas | Oculta diferencias legítimas y desactiva `check` como red de seguridad |
| C. Recrear `LeonsDB` desde `0001` | Esquema idéntico al modelo | Prohibido: implica `DROP` y pérdida de datos |

**Decisión:** A, con dos piezas:

1. `migrations/env.py` pasa `include_object=_incluir_objeto` a los dos
   `context.configure`. El filtro excluye `sysdiagrams`; los `sp_*diagram` son
   procedimientos y Alembic no los gestiona.
2. El modelo `Mascota` declara `mssql_include=["destacada", "nombre"]` y la
   revisión `0008` recrea el índice con esa cláusula. Es la definición que
   `LeonsDB` ya tenía, así que no cambia el rendimiento ni los datos.

**Consecuencias:** `uv run alembic -x target=test check` responde «No new
upgrade operations detected.» en `0008`, y el índice de `LeonsDB_Test`
coincide con el de `LeonsDB` (`INCLUDE (destacada, nombre)`). Los nombres de
`CHECK` de `alertas_rescate` siguen siendo distintos y se resuelven en G5 al
marcar `LeonsDB`; no afectan a la corrección del esquema.

---

## D-035 — `refugios.orden` para conservar el orden editorial del listado

**Contexto:** el cotejo de 18 rutas GET entre `memory` y `sqlserver` contra
`LeonsDB_Test` dio 17 respuestas idénticas. La única diferencia era el orden de
`GET /api/v1/refugios`: memoria devuelve el orden del seed (Huellitas Wanka,
Hogar San Roque, Mantaro Solidario…) y el repositorio SQL ordenaba por `nombre`
(Albergue Huellitas Wanka, Albergue San Agustín, Amigos de 4 Patas…). La página
`refugios` pinta el array tal cual, así que la Fase 7 habría cambiado el orden
visible sin que nadie lo pidiera. Además `especies` salía como
`['gato', 'perro']` porque la PK de `refugio_especies` es alfabética.

**Opciones:**

| Opción | Ventajas | Riesgos |
|---|---|---|
| A. `refugios.orden SMALLINT NULL` y ordenar por esa columna | El listado se ve igual que hoy; el orden pasa a ser dato explícito | Una columna y una migración aditiva |
| B. Aceptar el orden alfabético | Cero cambios de esquema | La página de refugios cambia de orden al conectar la Fase 7 |
| C. Ordenar también la memoria por `nombre` | Ambos backends coinciden | Cambia igual el orden actual y toca código estable |

**Decisión:** A. La revisión `0009` agrega `refugios.orden SMALLINT NULL`;
`db/seed.py` guarda la posición editorial (1–9) y rellena solo los `NULL`, así
que una base ya sembrada se corrige sin sobrescribir ajustes manuales. El
repositorio ordena por `COALESCE(orden, 999), nombre`: los refugios nuevos que
no fijen posición quedan al final, ordenados por nombre.

En la misma pasada se corrigió el orden de `especies`: el mapper del contrato
publica `perro` antes que `gato` (como `refugios.data.ts`), y el repositorio
ordena esa lista en memoria porque la tabla hija no guarda posición.

**Consecuencias:** las 18 rutas GET comparadas devuelven JSON idéntico entre
`memory` y `sqlserver`. La prueba `test_catalogo_y_refugios` verifica el orden
del listado contra el seed. El contrato JSON no cambia: `orden` no se expone.





## D-036 — Aceptar el prefijo doble de nombres de CHECK creado por el dialecto MSSQL de Alembic

**Fecha:** 18/11/2026
**Contexto:** Al ejecutar G5 (`stamp 0001` + `upgrade head`) sobre `LeonsDB`, las restricciones creadas por Alembic/SQLAlchemy en el dialecto MSSQL quedan con el nombre de tabla prefijado (`CONSTRAINT [CK_mascotas_CK_mascotas_sexo]`). Las restricciones originales de `LeonsDB` (creadas antes de Alembic) conservan sus nombres simples (`CK_mascotas_especie`, etc.).

**Opciones:**
- A) Renombrar las 6 restricciones originales al formato con doble prefijo en una nueva revisión `0010` (DROP + CREATE). Costo: operaciones de escritura sin beneficio funcional.
- B) Aceptar la diferencia cosmética y no crear `0010`. (Elegida)

**Decisión:** B. No se crea `0010`. Paridad funcional con `LeonsDB_Test` completa; `alembic check` limpio. La diferencia de nombres es cosmética y no afecta al seed, a las consultas ni al contrato.

**Consecuencias:** `LeonsDB` conserva nombres simples en las 6 restricciones originales y dobles en las 4 nuevas (de `0002`). `LeonsDB_Test` tiene todas con doble prefijo. Backup de pre-migración conservado en `C:\Program Files\Microsoft SQL Server\MSSQL17.SQLEXPRESS\MSSQL\Backup\LeonsDB_preG5_20261118_205214.bak`.

---

## D-040 — G5/G6: migrar y sembrar `LeonsDB` con backup verificado

**Fecha:** 18/11/2026
**Correspondencia:** registrada antes como D-036 en `AGENTS.md`.

**Contexto:** la Fase 6 requería llevar `LeonsDB` a la revisión `0009` y poblarla con el seed demo sin perder datos existentes.

**Opciones:**
- A) Migrar con `alembic -x target=main upgrade head` y sembrar de forma idempotente tras verificar el backup. (Elegida)
- B) Mantener `LeonsDB` sin migrar ni sembrar y usar solo `LeonsDB_Test`.

**Decisión:** A, según el registro previo de `AGENTS.md` (antes D-036).

**Consecuencias:** `LeonsDB` quedó en head `0009` con 16 mascotas, 9 refugios, 3 solicitudes y 3 usuarios. El seed es idempotente y las corridas E2E posteriores no escribieron en esa base.

## D-041 — CORS explícito en producción (`CORS_ORIGINS`)

**Fecha:** 20/11/2026
**Correspondencia:** registrada antes como D-037 en `AGENTS.md`.

**Contexto:** Fase 4.4, S2. El entorno de desarrollo usa `http://localhost:4200` y `http://localhost:4000`; producción no debe heredar esos orígenes ni aceptar `*` con credenciales.

**Opciones:**
- A) Exigir `CORS_ORIGINS` en producción, rechazar `*` y orígenes locales. (Elegida)
- B) Conservar la lista de desarrollo también en producción.

**Decisión:** A, según el registro previo de `AGENTS.md` (antes D-037).

**Consecuencias:** los dominios reales siguen pendientes en Q-08; esto bloquea el despliegue, no la demostración local.

## D-042 — TLS obligatorio en producción (`Encrypt=yes`, sin `TrustServerCertificate`)

**Fecha:** 20/11/2026
**Correspondencia:** registrada antes como D-038 en `AGENTS.md`.

**Contexto:** Fase 4.4, S3. ODBC Driver 18 cifra por defecto, pero `TrustServerCertificate=yes` desactiva la validación del certificado.

**Opciones:**
- A) Exigir `Encrypt=yes` y rechazar `TrustServerCertificate` en producción. (Elegida)
- B) Mantener la cadena de conexión de desarrollo en producción.

**Decisión:** A, según el registro previo de `AGENTS.md` (antes D-038).

**Consecuencias:** solo se validó la cadena de conexión; la existencia de un certificado válido y confiable queda pendiente en Q-09.

## D-043 — Rate limit distribuido: evaluado, no implementado

**Fecha:** 20/11/2026
**Correspondencia:** registrada antes como D-039 en `AGENTS.md`.

**Contexto:** Fase 4.4, S6. El limitador actual es local a cada proceso; con varias instancias el límite efectivo se multiplica.

**Opciones:**
- A) Implementar un backend compartido, por ejemplo Redis.
- B) Evaluar la opción y conservar el limitador en memoria. (Elegida)

**Decisión:** B, según el registro previo de `AGENTS.md` (antes D-039).

**Consecuencias:** la solución es suficiente para una sola instancia y para la demostración local. Q-10 queda abierta; cualquier cambio requiere autorización independiente, dependencia nueva e infraestructura.
