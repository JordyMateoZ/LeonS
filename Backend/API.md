# API LeonS v1

Base URL: `http://localhost:3001/api/v1`
Documentación interactiva (FastAPI Swagger): `http://localhost:3001/docs`

## Convenciones

- Autenticación: `Authorization: Bearer <token>`.
- Éxito: `{ "data": ..., "meta": ... }`.
- Error: `{ "error": { "code", "message", "details?" } }`.
- Roles: `adopter`, `shelter`, `admin`.
- Las rutas marcadas como **auth** requieren token; **opcional** usa la sesión si se envía.
- Rate limit: 20 intentos/15 min en `/auth`, 10 alertas/15 min.

---

## Salud

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/health` | Estado del servicio (fuera del prefijo). |
| GET | `/api/v1` | Información general de la API. |

## Auth

| Método | Ruta | Auth | Descripción |
| --- | --- | --- | --- |
| POST | `/auth/registro` | no | Crea cuenta. Exige `terminos: true` y password ≥ 8. |
| POST | `/auth/login` | no | Login por `identificador` (email o DNI), `email` o `dni`. |
| POST | `/auth/google` | no | Devuelve `501` hasta configurar `GOOGLE_CLIENT_ID`. |
| POST | `/auth/recuperar` | no | Devuelve `202` siempre (no enumera usuarios). |
| GET | `/auth/me` | sí | Perfil sin `passwordHash`. |

Ejemplo de registro:

```json
{
  "nombre": "Rosa",
  "apellido": "Pérez",
  "email": "rosa@example.com",
  "dni": "12345678",
  "password": "claveSegura123",
  "terminos": true,
  "rol": "adopter"
}
```

## Mascotas

| Método | Ruta | Auth | Descripción |
| --- | --- | --- | --- |
| GET | `/mascotas` | no | Catálogo paginado (por defecto solo disponibles). |
| GET | `/mascotas/destacadas?limit=4` | no | Fichas 1–4. |
| GET | `/mascotas/stats` | no | Conteos por estado, especie y distrito. |
| GET | `/mascotas/:id` | no | Ficha completa. |
| GET | `/mascotas/:id/detalle` | no | Historia, cuidados, requisitos, preguntas y cita. |
| GET | `/mascotas/:id/similares?limit=3` | no | Similares por especie, tamaño y distrito. |
| POST | `/mascotas` | `shelter`/`admin` | Publica una nueva ficha. |

Query params de `/mascotas`:

`especie=perro|gato`, `tamano=Pequeño|Mediano|Grande`, `distrito`, `estado`, `refugioId`, `energia`, `urgente=true|false`, `q`, `orden=recientes|nombre|edad_asc|edad_desc`, `page`, `limit`, `todos=true`.

Ejemplo:

```http
GET /api/v1/mascotas?especie=gato&distrito=El%20Tambo&page=1&limit=8
```

## Refugios

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/refugios?distrito=&especie=&q=` | Lista con `resumen`. |
| GET | `/refugios/:id` | Detalle del refugio. |
| GET | `/refugios/:id/mascotas` | Todas sus mascotas. |

## Solicitudes

| Método | Ruta | Auth | Descripción |
| --- | --- | --- | --- |
| POST | `/solicitudes` | opcional | Crea solicitud. `409` si hay activa duplicada. |
| GET | `/solicitudes` | sí | Solicitudes del usuario. |
| GET | `/solicitudes/:id` | sí | Detalle (dueño o admin). |
| POST | `/solicitudes/:id/cancelar` | sí | Cancela con `motivo`. |
| PATCH | `/solicitudes/:id` | `shelter`/`admin` | Actualiza estado, paso, cita o mensaje. |
| GET | `/solicitudes/:id/documentos/carnet` | sí | PDF de carnet de salud. |
| GET | `/solicitudes/:id/documentos/contrato` | sí | PDF de acta de tenencia. |
| GET | `/solicitudes/:id/seguimiento` | sí | Fotos de seguimiento. |
| POST | `/solicitudes/:id/seguimiento/fotos` | sí | Sube hasta 5 imágenes (`multipart/form-data`, campo `fotos`). |

Ejemplo de creación:

```json
{
  "mascotaId": 4,
  "solicitante": {
    "nombre": "Carlos Quispe",
    "telefono": "51999111222",
    "distrito": "El Tambo",
    "vivienda": "Casa con cerco perimétrico y jardín",
    "aceptaCompromiso": true,
    "dni": "11223344"
  }
}
```

Respuesta (extracto):

```json
{
  "data": {
    "id": 4,
    "estado": "active",
    "paso": 2,
    "exp": "#SOL-HYO-2026-004",
    "tiempoRespuesta": "24 a 48 horas",
    "pasoTexto": "Paso 2 de 5",
    "etapas": []
  }
}
```

## Favoritos

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/favoritos` | Lista de mascotas favoritas. |
| GET | `/favoritos/:mascotaId/estado` | `{ favorito: boolean }`. |
| POST | `/favoritos` | Agrega `{ mascotaId }`. `409` si ya existe. |
| DELETE | `/favoritos/:mascotaId` | Elimina. `204`. |

## Alertas de rescate

| Método | Ruta | Auth | Descripción |
| --- | --- | --- | --- |
| POST | `/alertas-rescate` | no | Registra alerta y notifica a la red. |
| GET | `/alertas-rescate` | `admin`/`shelter` | Lista alertas. |

## Contenido

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/contenido` | Pasos de adopción, pasos de refugio y FAQs. |
| GET | `/contenido/pasos` | Solo pasos. |
| GET | `/contenido/faqs` | Solo FAQs. |

## Estadísticas

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/estadisticas/impacto` | KPIs, serie mensual, especies y distritos. |

---

## Códigos de error frecuentes

| Código | HTTP | Significado |
| --- | --- | --- |
| `BAD_REQUEST` | 400 | Validación Pydantic fallida. |
| `UNAUTHORIZED` | 401 | Falta token o es inválido. |
| `FORBIDDEN` | 403 | Rol insuficiente o recurso ajeno. |
| `NOT_FOUND` | 404 | Recurso inexistente. |
| `CONFLICT` | 409 | Duplicado o estado inválido. |
| `CREDENCIALES_INVALIDAS` | 401 | Login incorrecto. |
| `RATE_LIMITED` | 429 | Demasiadas peticiones. |
| `NOT_IMPLEMENTED` | 501 | Integración no configurada. |
| `INTERNAL_ERROR` | 500 | Error inesperado. |
