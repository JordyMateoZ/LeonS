# Migración futura a SQL

El backend ya está separado en tres capas:

1. **Dominio** (`app/domain.py`): tipos y protocolos `UsuarioRepo`, `MascotaRepo`, etc. Todo es `async`.
2. **Rutas / casos de uso** (`app/modules/*.py`): solo conocen esos protocolos.
3. **Implementación** (`app/repositories/in_memory.py`): hoy memoria.

Para conectar SQL no hay que tocar las rutas: basta una nueva implementación de `Repositorios` y cambiarla en `app/container.py`.

## Modelo sugerido

```text
usuarios
  id uuid PK, nombre, apellido, email UNIQUE, dni UNIQUE,
  password_hash, rol, telefono, distrito, terminos_aceptados,
  google_id UNIQUE NULL, activo, creado_en, actualizado_en

refugios
  id slug PK, nombre, distrito, direccion, tipo, desde,
  descripcion, contacto, cargo, telefono, whatsapp, logo,
  adoptadas, en_acogida, verificado, especies

mascotas
  id serial PK, ficha_id UNIQUE, nombre, nombre_corto, especie, sexo,
  genero_texto, raza, edad_anios, edad_texto, tamano, tamano_texto,
  distrito, lugar, foto, alt, descripcion, etiqueta, etiqueta_icono,
  esterilizado, vacunado, urgente, refugio_id FK, energia,
  actualizado, estado, creado_en

mascota_salud      mascota_id FK, texto, ok
mascota_foto       mascota_id FK, src, alt, orden
mascota_rasgo      mascota_id FK, icono, texto, orden

solicitudes
  id serial PK, estado, paso, mascota_id FK, usuario_id FK NULL,
  exp UNIQUE, nombre, refugio, lugar, solicitante_nombre,
  solicitante_telefono, solicitante_distrito, solicitante_vivienda,
  solicitante_acepta_compromiso, solicitante_email, solicitante_dni,
  tiempo_respuesta, whatsapp, cita_fecha, cita_direccion, cita_coordinadora,
  mensaje_*, cierre_*, motivo_cancelacion, creada_en, actualizada_en

favoritos
  usuario_id FK, mascota_id FK, creado_en, PK(usuario_id, mascota_id)

seguimiento_fotos
  id uuid PK, solicitud_id FK, nombre, url, mime_type, tamanio, creado_en

alertas_rescate
  id uuid PK, nombre, email, telefono, distrito, direccion,
  descripcion, especie, cantidad, urgente, atendida, creado_en

contenido_paso      tipo, icono, titulo, texto, nota, orden
contenido_faq       pregunta, respuesta, orden
```

## Reglas que debe conservar la capa SQL

- `mascotas.ficha_id` y `solicitudes.exp` son únicos.
- No guardar clases CSS: se derivan en `app/mapper.py`.
- `solicitudes.estado = 'active'` no debe duplicarse para la misma mascota y solicitante. En PostgreSQL se puede garantizar con un índice parcial:

```sql
CREATE UNIQUE INDEX ux_solicitud_activa
  ON solicitudes (mascota_id, lower(coalesce(solicitante_email, '')),
                  lower(coalesce(solicitante_dni, '')),
                  regexp_replace(solicitante_telefono, '\D', '', 'g'))
  WHERE estado = 'active';
```

- `favoritos` ya tiene clave primaria compuesta, así que `POST /favoritos` puede traducirse a un `INSERT` y mapear violación de PK a `409`.
- Las fotos de seguimiento deben guardarse en almacenamiento de objetos; la URL se persiste en `seguimiento_fotos`.

## Pasos de sustitución

```python
# app/container.py
def create_dependencies(overrides: dict[str, Any] | None = None) -> Dependencies:
    valores = overrides or {}
    return Dependencies(
        repos=valores.get("repos") or crear_repositorios_sql(session_factory),
        storage=valores.get("storage") or LocalStorageAdapter(),
        notificaciones=valores.get("notificaciones") or LogNotificacionesAdapter(),
        auth_limiter=valores.get("auth_limiter") or RateLimiter(...),
        alertas_limiter=valores.get("alertas_limiter") or RateLimiter(...),
    )
```

Luego:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app
```

Los tests actuales usan `create_app(create_dependencies({ ... }))`, por lo que también pueden inyectar el repositorio SQL en un entorno de prueba.
