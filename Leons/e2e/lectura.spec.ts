import { expect, test, type Page } from '@playwright/test';

/**
 * Pruebas E2E de SOLO LECTURA (5.6.3.2A).
 * No inician sesión ni ejecutan POST/PATCH/PUT/DELETE.
 */

const PUERTO_PRINCIPAL = ':8000';
const PUERTO_E2E = ':8010';
const IGNORAR_ERRORES_EXTERNOS = /fonts\.(googleapis|gstatic)\.com|net::ERR_/i;

interface Diagnostico {
  peticiones: string[];
  metodosApi: string[];
  errores: string[];
  respuestasApi: number[];
}

function observar(page: Page): Diagnostico {
  const diagnostico: Diagnostico = {
    peticiones: [],
    metodosApi: [],
    errores: [],
    respuestasApi: [],
  };

  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') diagnostico.errores.push(mensaje.text());
  });
  page.on('pageerror', (error) => diagnostico.errores.push(`pageerror: ${error.message}`));
  page.on('request', (peticion) => {
    diagnostico.peticiones.push(peticion.url());
    if (peticion.url().includes(PUERTO_E2E)) diagnostico.metodosApi.push(peticion.method());
  });
  page.on('response', (respuesta) => {
    if (respuesta.url().includes(PUERTO_E2E)) diagnostico.respuestasApi.push(respuesta.status());
  });

  return diagnostico;
}

async function adjuntar(diagnostico: Diagnostico): Promise<void> {
  const info = test.info();
  await info.attach('peticiones.txt', {
    body: diagnostico.peticiones.join('\n'),
    contentType: 'text/plain',
  });
  await info.attach('diagnostico.txt', {
    body: JSON.stringify(
      {
        metodosApi: diagnostico.metodosApi,
        respuestasApi: diagnostico.respuestasApi,
        errores: diagnostico.errores,
      },
      null,
      2,
    ),
    contentType: 'application/json',
  });
}

function sinContaminacion(diagnostico: Diagnostico): void {
  expect(
    diagnostico.peticiones.filter((url) => url.includes(PUERTO_PRINCIPAL)),
    'ninguna petición debe ir al backend principal :8000',
  ).toEqual([]);

  const erroresApp = diagnostico.errores.filter(
    (texto) => !IGNORAR_ERRORES_EXTERNOS.test(texto),
  );
  expect(
    erroresApp.filter(
      (texto) => texto.includes(PUERTO_PRINCIPAL) || /cors|pageerror/i.test(texto),
    ),
    'sin errores de CORS, backend principal ni excepciones JS',
  ).toEqual([]);

  expect(
    diagnostico.metodosApi.filter((metodo) => metodo !== 'GET'),
    'todas las peticiones al API E2E deben ser GET',
  ).toEqual([]);
}

test('la página inicial abre en el frontend E2E y no usa el backend principal', async ({ page }) => {
  const diagnostico = observar(page);

  await page.goto('/', { waitUntil: 'networkidle' });

  await expect(page.locator('h1').first()).toContainText(
    'Dale un hogar a quien lo necesita en',
  );
  await expect(page.getByRole('link', { name: /Quiero adoptar/i }).first()).toBeVisible();

  sinContaminacion(diagnostico);
  await adjuntar(diagnostico);
});

test('el catálogo carga exclusivamente con GET contra el API E2E', async ({ page }) => {
  const diagnostico = observar(page);

  await page.goto('/mascotas', { waitUntil: 'networkidle' });

  await expect(page.locator('h1').first()).toContainText(
    'Peluditos buscando hogar en el Valle del Mantaro',
  );

  sinContaminacion(diagnostico);
  await adjuntar(diagnostico);
});

test('el detalle de mascota carga exclusivamente con GET contra el API E2E', async ({ page }) => {
  const diagnostico = observar(page);

  await page.goto('/mascotas/1', { waitUntil: 'networkidle' });

  await expect(page.locator('h1').first()).not.toBeEmpty();

  sinContaminacion(diagnostico);
  await adjuntar(diagnostico);
});
