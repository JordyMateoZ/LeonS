# G6 — Ejecución del seed en `LeonsDB`

**Fase:** 6, puerta G6.
**Fecha de ejecución:** 18/11/2026.
**Base:** `LeonsDB` (head `0009`, migrada en G5).

## 1. Inspección previa (solo lectura)

- `AGENTS.md` y `docs/decisiones.md` leídos.
- Mecanismo identificado: `Backend/db/seed.py` (`sembrar()`, idempotente, transacción única, `--force` para bases que no terminan en `_Test`, `--url` para elegir la base).
- Fuentes: `Backend/app/data/seed.json` (16 mascotas, 9 refugios, 3 solicitudes demo, contenido, detalles) + `DEMO_USERS` en `app/data/loader.py` (3 usuarios).
- Modelos y relaciones revisados; dependencias y orden de inserción verificados en el código (`_resolver_distritos` → refugios → usuarios → mascotas → contenido → solicitudes).
- Restricciones CHECK, FK, IDENTITY y UNIQUE compatibles con los datos del seed (verificado en G3/G4 en `LeonsDB_Test` y ahora en `LeonsDB`).
- Idempotencia: busca por clave natural (`id` de refugio, `email` de usuario, `codigo` de solicitud, `orden` de contenido) y no sobrescribe.

## 2. Respaldo previo

- Archivo: `C:\Program Files\Microsoft SQL Server\MSSQL17.SQLEXPRESS\MSSQL\Backup\LeonsDB_preG6_20261118_210007.bak`
- `BACKUP DATABASE [LeonsDB] TO DISK = ... WITH FORMAT, INIT, CHECKSUM` → éxito (690 páginas).
- `RESTORE VERIFYONLY ... WITH CHECKSUM` → "The backup set on file 1 is valid."

## 3. Ejecución

Comando ejecutado:
```
uv run python db/seed.py --url "mssql+pyodbc://@localhost\SQLEXPRESS/LeonsDB?..." --force
```

Resultado:
```
Siembra completada:
  contenido_faqs: 6
  contenido_pasos: 11
  mascotas: 16
  mascotas_existentes: 0
  refugios: 9
  refugios_existentes: 0
  solicitudes: 3
  solicitudes_existentes: 0
  usuarios: 3
  usuarios_existentes: 0
```

Segunda ejecución (idempotencia): todos los contadores de inserción en 0 y los de existentes coinciden (16 mascotas, 9 refugios, 3 solicitudes, 3 usuarios). Sin duplicados.

## 4. Verificaciones posteriores

### 4.1 Conteos por tabla

| Tabla | Filas |
|---|---|
| mascotas | 16 |
| refugios | 9 |
| usuarios | 3 |
| solicitudes | 3 |
| contenido_pasos | 11 |
| contenido_faqs | 6 |
| distritos | 6 |
| refugio_especies | 15 |
| mascota_salud | 33 |
| mascota_fotos | 5 |
| mascota_rasgos | 6 |
| mascota_historia | 48 |
| mascota_cuidados | 49 |
| citas | 1 |
| mensajes | 1 |
| solicitud_eventos | 3 |
| alertas_rescate | 0 |
| favoritos | 0 |
| seguimiento_fotos | 0 |
| migraciones | 0 |

### 4.2 Integridad

- **FK:** 16 comprobaciones de orfandad → 0 huérfanos (todas las relaciones válidas).
- **CHECK:** 19 restricciones intactas (sin violaciones; el seed las superó).
- **Duplicados:** ninguno en `solicitudes` (codigo), `usuarios` (email), `refugios` (id), `mascotas` (id), `contenido_pasos`/`contenido_faqs` (orden).
- **IDENTITY:** `mascotas` seed=1, increment=1, last_value=16.
- **alembic_version:** `0009` (sin cambios).
- **sysdiagrams:** tabla presente + 7 procedimientos intactos.
- **Estructura:** 22 tablas (sin cambios).

### 4.3 Comparación MemoryRepository vs SqlServerRepository

Endpoints públicos comparados (`/mascotas`, `/refugios`, `/mascotas/stats`, `/estadisticas/impacto`, `/contenido/pasos`, `/contenido/faqs`): totales y conjuntos de ids idénticos; respuesta completa de `/mascotas` idéntica (16/16 items, 0 diferencias de campo).

`/solicitudes` (autenticado): 3 solicitudes en ambos; campos core (id, codigo, mascotaId, usuarioId, refugioId, estado, etapa, creadoEn, actualizadoEn, motivoCancelacion) idénticos. Las diferencias son solo en campos editoriales derivados (fotoSrc, fotoAlt, etapas, mensaje, whatsapp, cierre), documentadas como cosméticas en D-033.

### 4.4 Pruebas automatizadas

- `uv run pytest -p no:warnings` → **28/28** (memoria + integración).
- `uv run pytest tests/test_sqlserver.py -p no:warnings` → **13/13** (contra `LeonsDB_Test`).
- `uv run alembic -x target=main check` → sin diferencias.

## 5. Incidencias

- Ninguna. El seed se ejecutó en la primera pasada sin errores.
- La idempotencia se verificó con una segunda ejecución (0 inserciones).
- Sin modificaciones a `alembic_version`, `sysdiagrams`, modelos, contratos ni frontend.

## 6. Decisiones

- Ninguna nueva decisión arquitectónica. Se aplicó D-036 (prefijo doble de CHECK) sin cambios.
- No se creó D-037 (no fue necesario).

## 7. Estado final

G6 cerrada. `LeonsDB` poblada con los datos demo y lista para Fase 7 (integración del frontend Angular). G7 requiere aprobación independiente y no se ejecutó.

---

**Hecho:** seed ejecutado en `LeonsDB` (16 mascotas, 9 refugios, 3 solicitudes, 3 usuarios, 6 distritos, 11 pasos, 6 FAQ). Idempotente.
**Verificado:** backup verificado; 0 huérfanos (16 FK); 19 CHECK; sin duplicados; IDENTITY 16; alembic 0009; sysdiagrams intacto; 28+13 tests verdes; memoria vs SQL idénticos en core.
**Decisiones tomadas:** ninguna nueva.
**Siguiente fase:** G6 cerrada. Fase 4 (auditoría) y Fase 7 (frontend) pendientes de aprobación independiente.
