# LeonS — Frontend Angular

Frontend de la plataforma de adopción responsable LeonS, desarrollado con Angular 22.2 y SSR. Consume la API FastAPI del repositorio en `Backend/`.

---

## Características

- Catálogo de mascotas con búsqueda, filtros, orden y paginación.
- Ficha de mascota con historia, rasgos, cuidados, similares y favoritos.
- Listado y detalle de refugios con resumen y mascotas asociadas.
- Registro, login por correo o DNI y perfil de usuario.
- Creación y cancelación de solicitudes de adopción.
- Panel de seguimiento de etapas, citas, mensajes y fotos.
- Alertas de rescate y estadísticas de impacto.
- SSR con `outputMode: "server"` y entrada `src/server.ts`.

---

## Requisitos

- Node.js 24.x y npm 11.x, o versión compatible con Angular 22.
- Backend FastAPI ejecutándose en `http://localhost:8000` para las funciones que consumen la API.
- Opcional: SQL Server configurado si el backend usa `REPOS_BACKEND=sqlserver`.

Versiones observadas en la máquina de desarrollo: Node `v24.22.0`, npm `11.19.1`.

---

## Instalación y arranque

```powershell
cd Leons
npm install
npm start
```

Abrir `http://localhost:4200`.

El backend debe estar iniciado por separado:

```powershell
cd ../Backend
uv run uvicorn app.main:app --reload --port 8000
```

El frontend de desarrollo usa `Leons/src/environments/environment.ts`:

- API: `http://localhost:8000/api/v1`

Para SSR local compilado:

```powershell
cd Leons
npm run build
npm run serve:ssr:Leons
```

---

## Comunicación con FastAPI

- Desarrollo: frontend `4200`, API `8000`.
- SSR local: el frontend puede servirse desde la salida compilada; la API sigue en `8000`.
- CORS del backend debe permitir `http://localhost:4200` y `http://localhost:4000`.
- `environment.prod.ts` contiene marcadores y no se ha configurado para despliegue.
- `environment.e2e.ts` apunta a un backend aislado en `http://localhost:8010`.

Los archivos de environment no contienen secretos.

---

## Flujo funcional básico

1. Desde el catálogo, filtrar mascotas por especie, distrito, tamaño, edad o estado.
2. Abrir la ficha de una mascota y revisar su refugio, historia y cuidados.
3. Marcar favoritos; requieren backend disponible y sesión cuando aplica.
4. Registrarse o iniciar sesión con correo o DNI.
5. Crear una solicitud de adopción para una mascota disponible.
6. Revisar `mis-solicitudes`, cancelar si es necesario y consultar etapas/citas.
7. Publicar una alerta de rescate.
8. Consultar `impacto`, `sobre-nosotros` y `como-funciona`.

Las credenciales demo son exclusivas de desarrollo; están definidas en `Backend/app/data/loader.py` y no deben reutilizarse en entornos reales.

---

## Comandos disponibles

Definidos en `package.json`:

| Comando | Acción |
|---|---|
| `npm start` | servidor de desarrollo Angular en `4200` |
| `npm run build` | compilación de producción/SSR |
| `npm run watch` | compilación development en modo observación |
| `npm test` | pruebas unitarias con Vitest |
| `npm run serve:e2e` | servidor E2E en `4300` con environment.e2e |
| `npm run e2e` | Playwright con `playwright.e2e.config.ts` |
| `npm run serve:ssr:Leons` | sirve la salida SSR compilada |

Ejecución típica:

```powershell
npm install
npm test
npm run build
npm start
```

`npm run e2e` usa una configuración aislada y no se ejecutó durante la preparación GITHUB-02.

---

## Generación del seed desde Angular

Si cambian las constantes de `src/app/data/`, regenerar `Backend/app/data/seed.json`:

```powershell
node_modules/.bin/esbuild scripts/export-seed.ts --bundle --platform=node --format=esm --outfile=scripts/.tmp/export-seed.mjs
node scripts/.tmp/export-seed.mjs ../Backend/app/data/seed.json
```

El directorio `scripts/.tmp/` está ignorado por Git. No editar `seed.json` a mano.

---

## Salud del entorno

Antes de la demostración:

- `http://localhost:8000/health` debe responder.
- `http://localhost:4200` debe abrir la aplicación.
- `Backend/.env` debe existir localmente y no estar versionado.
- Si se usa SQL Server, la base debe estar migrada a `0009` y sembrada.

Para más detalle, ver `[README.md](../README.md)`, `[Backend/README.md](../Backend/README.md)` y la documentación en `docs/`.
