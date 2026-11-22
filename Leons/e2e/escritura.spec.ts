import { expect, test, type Page } from '@playwright/test';

import {
  API_BASE,
  anadirRegistro,
  api,
  chooseSource,
  codigoError,
  createAdoptantes,
  createMascota,
  createRoleUsers,
  evidencia,
  guard,
  healthApi,
  identifiers,
  init,
  inspeccionar,
  limpiar,
  nuevoRunId,
  rollbackFixture,
  trackDistritos,
  trackSolicitudes,
  verificarMarcador,
} from './support';

/**
 * 5.6.3.2B: escrituras controladas SOLO contra LeonsDB_Test.
 *
 * Cada prueba verifica la base efectiva antes de escribir, usa datos propios
 * registrados en un manifiesto y cierra con limpieza por ids exactos.
 * No se usan las solicitudes ni los mensajes históricos de LeonsDB_Test.
 */

const PASSWORD = 'E2ePass2026!'; // Nunca se escribe en manifiestos ni evidencias.
const PUERTO_PRINCIPAL = ':8000';
const PUERTO_E2E = ':8010';
const FUENTES_EXTERNAS = /fonts\.(googleapis|gstatic)\.com|net::ERR_/i;

interface Identificador {
  email: string;
  dni: string;
  id?: number;
  token?: string;
}

interface MascotaE2E {
  id: number;
  nombre: string;
  refugio_id: string;
}

interface UsuarioRol {
  id: number;
  email: string;
  rol: string;
  refugio_id?: string;
  token?: string;
}

interface SolicitudSql {
  id: number;
  codigo: string;
  usuario_id: number;
  mascota_id: number;
  estado: string;
  etapa: number;
  motivo_cancelacion: string | null;
}

interface MensajeSql {
  id: number;
  solicitud_id: number;
  autor_id: number;
  texto: string;
}

interface CitaSql {
  id: number;
  solicitud_id: number;
  fecha_hora: string;
  lugar: string | null;
  notas: string | null;
  coordinadora: string | null;
}

interface EventoSql {
  id: number;
  solicitud_id: number;
  etapa: number;
}

interface Inspeccion {
  usuarios: Array<{ id: number; email: string; rol: string; refugio_id: string | null }>;
  mascotas: Array<{ id: number; nombre: string; estado: string }>;
  solicitudes: SolicitudSql[];
  mensajes: MensajeSql[];
  citas: CitaSql[];
  solicitud_eventos: EventoSql[];
  favoritos: Array<{ usuario_id: number; mascota_id: number }>;
}

interface Contexto {
  runId: string;
  adoptantes: Identificador[];
  roles: { refugio: UsuarioRol; admin: UsuarioRol };
  mascotas: MascotaE2E[];
  solicitudes: { ui: number; api: number[] };
  ganador?: number;
  perdedor?: number;
}

interface Diagnostico {
  urls: string[];
  metodosApi: string[];
  errores: string[];
}

let ctx: Contexto;

function observar(page: Page): Diagnostico {
  const diagnostico: Diagnostico = { urls: [], metodosApi: [], errores: [] };
  page.on('request', (peticion) => {
    diagnostico.urls.push(peticion.url());
    if (peticion.url().includes(PUERTO_E2E)) {
      diagnostico.metodosApi.push(`${peticion.method()} ${new URL(peticion.url()).pathname}`);
    }
  });
  page.on('console', (mensaje) => {
    if (mensaje.type() === 'error') diagnostico.errores.push(mensaje.text());
  });
  page.on('pageerror', (error) => diagnostico.errores.push(`pageerror: ${error.message}`));
  return diagnostico;
}

function sinContaminacion(diagnostico: Diagnostico): void {
  expect(
    diagnostico.urls.filter((url) => url.includes(PUERTO_PRINCIPAL)),
    'ninguna petición debe ir al backend principal :8000',
  ).toEqual([]);
  expect(
    diagnostico.urls.filter((url) => url.includes('/api/v1/') && !url.includes(PUERTO_E2E)),
    'todas las peticiones /api/v1 deben ir a :8010',
  ).toEqual([]);
  const erroresApp = diagnostico.errores.filter((texto) => !FUENTES_EXTERNAS.test(texto));
  expect(
    erroresApp.filter((texto) => /cors|pageerror|:8000/i.test(texto)),
    'sin errores de CORS, backend principal ni excepciones JS',
  ).toEqual([]);
}

async function adjuntar(diagnostico: Diagnostico, sufijo = ''): Promise<void> {
  await test.info().attach(`peticiones-e2e${sufijo}.txt`, {
    body: diagnostico.urls.join('\n'),
    contentType: 'text/plain',
  });
  await test.info().attach(`diagnostico-e2e${sufijo}.json`, {
    body: JSON.stringify(diagnostico, null, 2),
    contentType: 'application/json',
  });
}

async function loginApi(identificador: string): Promise<string> {
  const respuesta = await api('POST', '/auth/login', { body: { identificador, password: PASSWORD } });
  expect(respuesta.status, 'login API').toBe(200);
  expect(respuesta.body.token, 'token de login API').toBeTruthy();
  return respuesta.body.token as string;
}

async function loginUi(page: Page, identificador: string): Promise<void> {
  await page.goto('/login');
  await page.getByRole('tab', { name: /Iniciar Sesión/i }).click();
  await page.locator('#login-user').fill(identificador);
  await page.locator('#login-password').fill(PASSWORD);
  await Promise.all([
    page.waitForURL(/\/mis-solicitudes/),
    page.getByRole('button', { name: /Ingresar a LeonS/i }).click(),
  ]);
}

/** Espera a que la sesión almacenada quede confirmada contra /auth/me. */
async function gotoAuth(page: Page, ruta: string): Promise<void> {
  await Promise.all([
    page.waitForResponse(
      (respuesta) =>
        respuesta.url().includes(`${PUERTO_E2E}/api/v1/auth/me`) && respuesta.status() === 200,
      { timeout: 15_000 },
    ),
    page.goto(ruta),
  ]);
}

/** Navegación interna: evita el prerender de `/mis-solicitudes` sin sesión. */
async function irASolicitudes(page: Page): Promise<void> {
  await page.getByRole('link', { name: /Mis solicitudes de adopción/i }).first().click();
  await expect(page).toHaveURL(/\/mis-solicitudes/);
}

/** Inyecta un token ya obtenido por API: la autenticación real se prueba en A1. */
async function sesionUi(page: Page, token: string, ruta: string): Promise<void> {
  await page.addInitScript((valor) => localStorage.setItem('leons.token.v1', valor), token);
  await gotoAuth(page, ruta);
}

async function tokenUi(page: Page): Promise<string> {
  const token = await page.evaluate(() => localStorage.getItem('leons.token.v1'));
  if (!token) throw new Error('No hay token de sesión E2E en el navegador.');
  return token;
}

function sql(): Inspeccion {
  return inspeccionar() as Inspeccion;
}

function solsDe(informe: Inspeccion, usuarioId: number, mascotaId: number): SolicitudSql[] {
  return informe.solicitudes.filter(
    (s) => s.usuario_id === usuarioId && s.mascota_id === mascotaId,
  );
}

function evidenciaApi(
  id: string,
  status: number | null,
  persistencia: string,
  detalle: string,
  error?: string,
): void {
  evidencia({
    id,
    resultado: error ? 'FAIL' : 'PASS',
    tipo: 'api',
    base: 'LeonsDB_Test',
    http: status,
    persistencia,
    detalle,
    error,
  });
}

test.beforeAll(async () => {
  ctx = {
    runId: nuevoRunId(),
    adoptantes: [],
    roles: { refugio: {} as UsuarioRol, admin: {} as UsuarioRol },
    mascotas: [],
    solicitudes: { ui: 0, api: [] },
  };

  const inicial = init(ctx.runId);
  expect(inicial.db_pruebas).toBe('LeonsDB_Test');
  expect(inicial.db_principal).toBe('LeonsDB');
  expect((await healthApi()).status).toBe(200);

  guard('beforeAll:identificadores');
  const ids = identifiers(ctx.runId, 6);
  ctx.adoptantes = ids.slice(0, 4).map((id) => ({ ...id }));

  const fuente = chooseSource();
  ctx.roles.refugio = {
    id: 0,
    email: ids[4].email,
    rol: 'refugio',
    refugio_id: fuente.refugio_id,
  };
  ctx.roles.admin = { id: 0, email: ids[5].email, rol: 'admin' };

  ctx.roles = createRoleUsers({
    runId: ctx.runId,
    refugioId: fuente.refugio_id,
    emailRefugio: ids[4].email,
    dniRefugio: ids[4].dni,
    emailAdmin: ids[5].email,
    dniAdmin: ids[5].dni,
    password: PASSWORD,
  }) as Contexto['roles'];

  for (const nombre of ['UI', 'Fallo', 'API', 'Aislamiento']) {
    ctx.mascotas.push(
      createMascota({
        runId: ctx.runId,
        sourceId: fuente.id,
        nombre: `E2E-${ctx.runId.slice(-6)}-${nombre}`,
      }),
    );
  }

  // Cuentas auxiliares por fixture: el registro público se ejerce una sola vez
  // en A1, para no agotar el rate limit de /auth/registro (5 por minuto).
  const auxiliares = createAdoptantes({
    runId: ctx.runId,
    correos: ctx.adoptantes.slice(0, 3).map((a) => a.email),
    dnis: ctx.adoptantes.slice(0, 3).map((a) => a.dni),
    password: PASSWORD,
  });
  for (const indice of [0, 1, 2]) {
    ctx.adoptantes[indice].id = auxiliares[indice].id;
    verificarMarcador(ctx.adoptantes[indice].email);
    ctx.adoptantes[indice].token = await loginApi(ctx.adoptantes[indice].email);
  }

  ctx.roles.refugio.token = await loginApi(ctx.roles.refugio.email);
  ctx.roles.admin.token = await loginApi(ctx.roles.admin.email);

  evidencia({
    id: 'SETUP',
    resultado: 'PASS',
    tipo: 'sql',
    base: 'LeonsDB_Test',
    persistencia: 'baseline capturado; 4 mascotas propias, 2 usuarios de rol y 3 adoptantes de fixture',
    detalle: `run_id=${ctx.runId}; mascotas=${ctx.mascotas.map((m) => m.id).join(',')}`,
  });
});

test.afterAll(async () => {
  let resultado: any;
  try {
    resultado = limpiar();
    evidencia({
      id: 'CLEANUP',
      resultado: 'PASS',
      tipo: 'sql',
      base: 'LeonsDB_Test',
      persistencia: JSON.stringify(resultado.borrados),
      detalle: 'baseline de LeonsDB_Test restaurado; LeonsDB sin cambios',
    });
  } catch (error) {
    evidencia({
      id: 'CLEANUP',
      resultado: 'FAIL',
      tipo: 'sql',
      base: 'LeonsDB_Test',
      persistencia: 'manifiesto conservado',
      error: error instanceof Error ? error.message : String(error),
    });
    throw error;
  }
  expect(resultado.baseline).toBe('restaurado');
});

test('A1 - registro público, login por DNI y persistencia aislada', async ({ page }) => {
  const diagnostico = observar(page);
  const adoptante = ctx.adoptantes[3];
  guard('A1:registro-publico');

  await page.goto('/login');
  await page.getByRole('tab', { name: /Crear Cuenta/i }).click();
  await page.locator('#reg-name').fill(`E2E UI ${ctx.runId.slice(-6)}`);
  await page.locator('#reg-email').fill(adoptante.email);
  await page.locator('#reg-phone').fill('900000099');
  await page.locator('#reg-dni').fill(adoptante.dni);
  await page.locator('#reg-district').selectOption({ index: 1 });
  await page.locator('#reg-password').fill(PASSWORD);
  await page.locator('input[name="terms"]').check();
  await page.getByRole('button', { name: /Crear mi cuenta gratis/i }).click();
  await page.waitForURL(/\/mis-solicitudes/);

  // La respuesta del registro no se inspecciona en la UI: se consulta /auth/me.
  const token = await tokenUi(page);
  const perfil = await api('GET', '/auth/me', { token });
  expect(perfil.status).toBe(200);
  expect(perfil.body.email).toBe(adoptante.email);
  expect(perfil.body.rol).toBe('adoptante');
  adoptante.id = Number(perfil.body.id);
  adoptante.token = token;
  anadirRegistro('users', { id: adoptante.id, email: adoptante.email, rol: 'adoptante' });
  trackDistritos();
  verificarMarcador(adoptante.email);

  // La pestaña de refugio sigue bloqueada en el registro público.
  await page.evaluate(() => localStorage.removeItem('leons.token.v1'));
  await page.goto('/login');
  await page.getByRole('tab', { name: /Crear Cuenta/i }).click();
  await expect(page.locator('input[value="shelter"]')).toBeDisabled();
  // El login por DNI se verifica por API: evita un segundo login UI y su rate limit.
  const porDni = await api('POST', '/auth/login', {
    body: { identificador: adoptante.dni, password: PASSWORD },
  });
  expect(porDni.status, 'login por DNI').toBe(200);
  expect(porDni.body.token, 'token por DNI').toBeTruthy();

  sinContaminacion(diagnostico);
  await adjuntar(diagnostico);
  evidencia({
    id: 'A1',
    resultado: 'PASS',
    tipo: 'navegador',
    base: 'LeonsDB_Test',
    http: perfil.status,
    persistencia: `usuario id=${adoptante.id} en LeonsDB_Test; ausente en LeonsDB`,
    captura: 'trace/screenshot automáticos ante fallo',
    detalle: 'registro público creó solo rol adoptante; login por DNI correcto',
  });
});

test('A2 - catálogo, favoritos, doble envío y persistencia tras recarga', async ({ page }) => {
  const diagnostico = observar(page);
  const adoptante = ctx.adoptantes[0];
  const mascota = ctx.mascotas[0];
  guard('A2:sesion-ui');
  await sesionUi(page, adoptante.token!, '/mascotas');

  guard('A2:catalogo');
  await page.getByPlaceholder(/Buscar por nombre/i).fill(mascota.nombre);
  await page.getByRole('button', { name: /Buscar mascota/i }).click();
  await expect(page.getByText(mascota.nombre, { exact: false }).first()).toBeVisible();

  guard('A2:favorito');
  const respuestaFavorito = page.waitForResponse(
    (respuesta) =>
      respuesta.url().includes(`${PUERTO_E2E}/api/v1/favoritos`) &&
      respuesta.request().method() === 'POST',
  );
  await page
    .getByRole('button', { name: `Guardar a ${mascota.nombre} en favoritos` })
    .first()
    .click();
  expect((await respuestaFavorito).status()).toBe(201);
  const favoritos = await api('GET', '/favoritos', { token: adoptante.token! });
  expect(favoritos.status).toBe(200);
  expect(favoritos.body.ids).toContain(mascota.id);
  await gotoAuth(page, '/mascotas');
  await page.getByPlaceholder(/Buscar por nombre/i).fill(mascota.nombre);
  await page.getByRole('button', { name: /Buscar mascota/i }).click();
  await expect(
    page.getByRole('button', { name: `Guardar a ${mascota.nombre} en favoritos` }).first(),
  ).toHaveClass(/text-primary/);
  const favoritosTrasRecarga = await api('GET', '/favoritos', { token: adoptante.token! });
  expect(favoritosTrasRecarga.body.ids).toContain(mascota.id);
  const favoritoSql = sql().favoritos.find(
    (f) => f.usuario_id === adoptante.id && f.mascota_id === mascota.id,
  );
  expect(favoritoSql, 'favorito persistido en SQL').toBeTruthy();

  guard('A2:doble-envio');
  await gotoAuth(page, `/mascotas/${mascota.id}`);
  await page.getByRole('button', { name: `Solicitar adopción de ${mascota.nombre}` }).click();
  await page.locator('#adopt-message').fill('E2E doble envío controlado');
  await page.locator('#terms-check').check();
  // Dos clics nativos seguidos: el guardián de la UI debe impedir el segundo POST.
  await page.evaluate(() => {
    const boton = Array.from(document.querySelectorAll('button')).find((b) =>
      (b.textContent ?? '').includes('Enviar Solicitud'),
    );
    if (!boton) throw new Error('No aparece el botón Enviar Solicitud.');
    boton.click();
    boton.click();
  });
  await expect(page.getByText(/¡Solicitud enviada!/)).toBeVisible();

  trackSolicitudes();
  const creations = solsDe(sql(), adoptante.id!, mascota.id);
  expect(creations, 'una sola solicitud pese al doble clic').toHaveLength(1);
  ctx.solicitudes.ui = creations[0].id;
  expect(creations[0].estado).toBe('activa');

  await irASolicitudes(page);
  await expect(page.getByText(mascota.nombre, { exact: false }).first()).toBeVisible();
  // 5.6.3.2D: la carga directa ya no se evita con el workaround D-E2E-01.
  await gotoAuth(page, '/mis-solicitudes');
  await expect(page.getByText(mascota.nombre, { exact: false }).first()).toBeVisible();

  sinContaminacion(diagnostico);
  await adjuntar(diagnostico);
  evidencia({
    id: 'A2',
    resultado: 'PASS',
    tipo: 'navegador',
    base: 'LeonsDB_Test',
    http: favoritos.status,
    persistencia: `favorito y solicitud id=${ctx.solicitudes.ui} persistidos tras recarga`,
    captura: 'trace/screenshot automáticos ante fallo',
    detalle: 'catálogo con filtro propio; doble clic generó una sola fila SQL',
  });
});

test('A5 - carga directa y recarga de /mis-solicitudes sin redirección prematura', async ({ page }) => {
  const diagnostico = observar(page);
  const adoptante = ctx.adoptantes[0];
  const mascota = ctx.mascotas[0];

  guard('A5:carga-directa');
  await sesionUi(page, adoptante.token!, '/mis-solicitudes');
  await expect(page).toHaveURL(/\/mis-solicitudes/);
  await expect(page.getByText(mascota.nombre, { exact: false }).first()).toBeVisible();
  await expect(page.getByText('No se mostrarán datos privados')).toHaveCount(0);

  guard('A5:recarga');
  await Promise.all([
    page.waitForResponse(
      (respuesta) =>
        respuesta.url().includes(`${PUERTO_E2E}/api/v1/auth/me`) && respuesta.status() === 200,
      { timeout: 15_000 },
    ),
    page.reload(),
  ]);
  await expect(page).toHaveURL(/\/mis-solicitudes/);
  await expect(page.getByText(mascota.nombre, { exact: false }).first()).toBeVisible();
  expect(await tokenUi(page)).toBe(adoptante.token!);

  sinContaminacion(diagnostico);
  await adjuntar(diagnostico, '-carga-directa');
  evidencia({
    id: 'A5',
    resultado: 'PASS',
    tipo: 'navegador',
    base: 'LeonsDB_Test',
    http: 200,
    persistencia: 'sin datos privados antes de /auth/me; sesión conservada tras recarga',
    captura: 'trace/screenshot automáticos ante fallo',
    detalle: 'carga directa y recarga de /mis-solicitudes sin redirección a /login',
  });
});

test('A3 - fallo forzado del POST no crea solicitud ficticia', async ({ page }) => {
  const diagnostico = observar(page);
  const adoptante = ctx.adoptantes[1];
  const mascota = ctx.mascotas[1];
  guard('A3:sesion-ui');
  await sesionUi(page, adoptante.token!, `/mascotas/${mascota.id}`);

  guard('A3:post-fallido');
  const patron = '**/api/v1/solicitudes';
  await page.route(patron, async (ruta) => {
    if (ruta.request().method() === 'POST') {
      await ruta.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ code: 'E2E_FORZADO', message: 'fallo inyectado' }),
      });
      return;
    }
    await ruta.continue();
  });

  await page.getByRole('button', { name: `Solicitar adopción de ${mascota.nombre}` }).click();
  await page.locator('#adopt-message').fill('No debe persistir');
  await page.locator('#terms-check').check();
  await page.getByRole('button', { name: 'Enviar Solicitud' }).click();
  await expect(page.getByText(/E2E_FORZADO|fallo inyectado/i)).toBeVisible();
  await page.unroute(patron);

  trackSolicitudes();
  const filas = solsDe(sql(), adoptante.id!, mascota.id);
  expect(filas, 'no debe existir solicitud tras el POST fallido').toHaveLength(0);

  sinContaminacion(diagnostico);
  await adjuntar(diagnostico);
  evidencia({
    id: 'A3',
    resultado: 'PASS',
    tipo: 'navegador',
    base: 'LeonsDB_Test',
    http: 500,
    persistencia: '0 filas en solicitudes para usuario/mascota E2E',
    captura: 'trace/screenshot automáticos ante fallo',
    detalle: 'POST forzado a fallar mediante route de Playwright; sin solicitud ficticia',
  });
});

test('A4 - aislamiento de solicitudes entre dos usuarios', async ({ browser }) => {
  const primero = await browser.newContext();
  const segundo = await browser.newContext();
  const paginaUno = await primero.newPage();
  const paginaDos = await segundo.newPage();
  const diagUno = observar(paginaUno);
  const diagDos = observar(paginaDos);
  guard('A4:sesion-ui');
  await sesionUi(paginaUno, ctx.adoptantes[0].token!, '/mascotas');
  await sesionUi(paginaDos, ctx.adoptantes[2].token!, '/mascotas');

  const propio = ctx.mascotas[0].nombre;
  const ajeno = ctx.mascotas[2].nombre;
  await irASolicitudes(paginaUno);
  await expect(paginaUno.getByText(propio, { exact: false }).first()).toBeVisible();
  await expect(paginaUno.getByText(ajeno, { exact: false })).toHaveCount(0);

  await irASolicitudes(paginaDos);
  await expect(paginaDos.getByText(propio, { exact: false })).toHaveCount(0);

  const listaUno = await api('GET', '/solicitudes', { token: ctx.adoptantes[0].token! });
  const listaDos = await api('GET', '/solicitudes', { token: ctx.adoptantes[2].token! });
  expect(listaUno.status).toBe(200);
  expect(listaDos.status).toBe(200);
  const idsUno = new Set<number>(listaUno.body.items.map((s: any) => Number(s.id)));
  const idsDos = new Set<number>(listaDos.body.items.map((s: any) => Number(s.id)));
  expect([...idsUno].some((id) => idsDos.has(id))).toBe(false);

  sinContaminacion(diagUno);
  sinContaminacion(diagDos);
  await adjuntar(diagUno, '-usuario-uno');
  await adjuntar(diagDos, '-usuario-dos');
  await primero.close();
  await segundo.close();
  evidencia({
    id: 'A4',
    resultado: 'PASS',
    tipo: 'navegador',
    base: 'LeonsDB_Test',
    http: listaUno.status,
    persistencia: 'listas de solicitudes disjuntas por usuario',
    captura: 'trace/screenshot automáticos ante fallo',
    detalle: 'dos contextos de navegador con sesiones distintas',
  });
});

test('B1 - mensajes con autor real, citas válidas/inválidas e historial de eventos', async () => {
  const adoptantes = ctx.adoptantes.slice(0, 3);
  const mascota = ctx.mascotas[2];
  guard('B1:crear-solicitudes');

  const creadas = [];
  for (const adoptante of adoptantes) {
    const respuesta = await api('POST', '/solicitudes', {
      token: adoptante.token!,
      body: { mascotaId: mascota.id, mensaje: `E2E mensaje inicial ${adoptante.id}` },
    });
    expect(respuesta.status, `crear solicitud de ${adoptante.email}`).toBe(201);
    creadas.push(respuesta.body);
  }
  trackSolicitudes();
  ctx.solicitudes.api = creadas.map((s) => Number(s.id));
  expect(new Set(ctx.solicitudes.api).size).toBe(3);
  evidenciaApi('B1-CREAR', 201, `ids=${ctx.solicitudes.api.join(',')}`, 'tres solicitudes propias sobre mascota propia');

  const principal = ctx.solicitudes.api[0];
  guard('B1:mensajes');
  const autores = [
    { id: adoptantes[0].id!, token: adoptantes[0].token!, texto: 'mensaje adoptante E2E' },
    { id: ctx.roles.refugio.id, token: ctx.roles.refugio.token!, texto: 'mensaje refugio E2E' },
    { id: ctx.roles.admin.id, token: ctx.roles.admin.token!, texto: 'mensaje admin E2E' },
  ];
  for (const autor of autores) {
    const respuesta = await api('POST', `/solicitudes/${principal}/mensajes`, {
      token: autor.token,
      body: { texto: autor.texto },
    });
    expect(respuesta.status).toBe(200);
  }
  const mensajes = sql().mensajes.filter((m) => m.solicitud_id === principal);
  for (const autor of autores) {
    const encontrado = mensajes.find((m) => m.autor_id === autor.id && m.texto === autor.texto);
    expect(encontrado, `mensaje de ${autor.id} con autor_id real`).toBeTruthy();
  }
  evidenciaApi('B1-MENSAJES', 200, `${mensajes.length} mensajes con autor_id real`, 'adoptante, refugio y administrador');

  guard('B1:cita-invalida');
  const antes = sql();
  const citasAntes = antes.citas.filter((c) => c.solicitud_id === principal).length;
  const etapaAntes = antes.solicitudes.find((s) => s.id === principal)?.etapa;
  const invalida = await api('POST', `/solicitudes/${principal}/citas`, {
    token: ctx.roles.refugio.token!,
    body: { fecha: '31 de febrero', direccion: 'Sede E2E', coordinadora: 'Coordinadora E2E' },
  });
  expect(invalida.status).toBe(422);
  expect(codigoError(invalida.body)).toBe('FECHA_CITA_INVALIDA');
  const despuesInvalida = sql();
  expect(despuesInvalida.citas.filter((c) => c.solicitud_id === principal)).toHaveLength(citasAntes);
  expect(despuesInvalida.solicitudes.find((s) => s.id === principal)?.etapa).toBe(etapaAntes);
  evidenciaApi('B1-CITA-422', 422, '0 citas insertadas; etapa sin cambios', 'fecha inexistente rechazada');

  guard('B1:cita-valida');
  const valida = await api('POST', `/solicitudes/${principal}/citas`, {
    token: ctx.roles.refugio.token!,
    body: { fecha: '24 de mayo • 10:30 am', direccion: 'Sede E2E', coordinadora: 'Coordinadora E2E' },
  });
  expect(valida.status).toBe(200);
  const cita = sql().citas.find((c) => c.solicitud_id === principal);
  expect(cita).toBeTruthy();
  expect(cita!.lugar).toBe('Sede E2E');
  expect(cita!.coordinadora).toBe('Coordinadora E2E');

  guard('B1:etapa');
  const etapa = await api('PATCH', `/solicitudes/${principal}/etapa`, {
    token: ctx.roles.refugio.token!,
    body: { etapa: 3, nota: 'nota de etapa E2E' },
  });
  expect(etapa.status).toBe(200);
  const eventos = sql().solicitud_eventos.filter((e) => e.solicitud_id === principal);
  expect(eventos.some((e) => e.etapa === 3)).toBe(true);
  const notaSql = sql().mensajes.find((m) => m.solicitud_id === principal && m.texto === 'nota de etapa E2E');
  expect(notaSql?.autor_id).toBe(ctx.roles.refugio.id);
  evidenciaApi('B1-EVENTOS', 200, `${eventos.length} eventos; cita y nota persistidas`, 'historial de etapas verificado en SQL');
});

test('B2 - dos finalizaciones concurrentes: ambas 409, sin escritura (INC-E2E-01)', async () => {
  const [principal, segundo, tercero] = ctx.solicitudes.api;
  guard('B2:autorizacion');
  const denegada = await api('PATCH', `/solicitudes/${principal}/etapa`, {
    token: ctx.adoptantes[0].token!,
    body: { etapa: 5, nota: 'intento no autorizado' },
  });
  expect(denegada.status).toBe(403);

  guard('B2:otras-activas');
  const conflictiva = await api('PATCH', `/solicitudes/${principal}/etapa`, {
    token: ctx.roles.refugio.token!,
    body: { etapa: 5, nota: 'finalización con otras activas' },
  });
  expect(conflictiva.status).toBe(409);
  expect(codigoError(conflictiva.body)).toBe('ADOPCION_EN_CURSO');
  const trasConflicto = sql();
  expect(trasConflicto.solicitudes.find((s) => s.id === principal)?.estado).toBe('activa');
  expect(trasConflicto.mascotas.find((m) => m.id === ctx.mascotas[2].id)?.estado).toBe('disponible');
  evidenciaApi('B2-409', 409, '0 escrituras: solicitud sigue activa y mascota disponible', 'otras postulaciones activas bloquean la finalización');

  guard('B2:cancelacion-no-autorizada');
  const noAutorizada = await api('PATCH', `/solicitudes/${tercero}/cancelar`, {
    token: ctx.adoptantes[0].token!,
    body: { motivo: 'intento ajeno' },
  });
  expect(noAutorizada.status).toBe(403);

  guard('B2:cancelacion-autorizada');
  const canceladaTercera = await api('PATCH', `/solicitudes/${tercero}/cancelar`, {
    token: ctx.roles.admin.token!,
    body: { motivo: 'E2E cancelación autorizada de otras postulaciones' },
  });
  expect(canceladaTercera.status).toBe(200);
  const filaTercera = sql().solicitudes.find((s) => s.id === tercero);
  expect(filaTercera?.estado).toBe('cancelada');
  expect(filaTercera?.motivo_cancelacion).toContain('E2E cancelación autorizada');
  evidenciaApi('B2-CANCELAR-OTRAS', 200, 'tercera postulación cancelada con motivo', 'administrador canceló una postulación ajena; adoptante recibió 403');

  // INC-E2E-01 (opción A): con dos solicitudes activas, AMBAS deben recibir
  // conflicto de negocio. Ninguna finaliza; la mascota sigue disponible.
  guard('B2:concurrencia');
  const resultados = await Promise.all([
    api('PATCH', `/solicitudes/${principal}/etapa`, {
      token: ctx.roles.refugio.token!,
      body: { etapa: 5, nota: 'finalización refugio E2E' },
    }),
    api('PATCH', `/solicitudes/${segundo}/etapa`, {
      token: ctx.roles.admin.token!,
      body: { etapa: 5, nota: 'finalización admin E2E' },
    }),
  ]);
  const estados = resultados.map((r) => r.status);
  // Un 500 nunca se acepta como PASS, aunque la base quede sin cambios.
  expect(estados, 'ninguna respuesta debe ser 500 INTERNAL_ERROR').not.toContain(500);
  expect(estados, 'ambas finalizaciones deben recibir 409').toEqual([409, 409]);
  for (const respuesta of resultados) {
    expect(codigoError(respuesta.body)).toBe('ADOPCION_EN_CURSO');
    expect(respuesta.body.details?.solicitudesActivas).toBe(1);
  }

  const trasConcurrencia = sql();
  expect(trasConcurrencia.mascotas.find((m) => m.id === ctx.mascotas[2].id)?.estado).toBe('disponible');
  for (const id of [principal, segundo]) {
    const fila = trasConcurrencia.solicitudes.find((s) => s.id === id);
    expect(fila?.estado).toBe('activa');
    expect(fila?.etapa).toBeLessThan(5);
    expect(trasConcurrencia.solicitud_eventos.some((e) => e.solicitud_id === id && e.etapa === 5)).toBe(false);
    expect(trasConcurrencia.mensajes.some((m) => m.solicitud_id === id && m.texto.startsWith('finalización'))).toBe(false);
  }
  evidenciaApi(
    'B2-CONCURRENCIA',
    409,
    '0 escrituras: ambas activas, mascota disponible, sin eventos ni mensajes de finalización',
    `estados=${JSON.stringify(estados)}; ambos ADOPCION_EN_CURSO; sin deadlock 1205`,
  );
});

test('B2b - cancelación autorizada, finalización y idempotencia (INC-E2E-01)', async () => {
  const [principal, segundo] = ctx.solicitudes.api;
  guard('B2b:cancelacion-autorizada');
  const cancelarSegundo = await api('PATCH', `/solicitudes/${segundo}/cancelar`, {
    token: ctx.roles.admin.token!,
    body: { motivo: 'E2E cancelación tras conflicto concurrente' },
  });
  expect(cancelarSegundo.status).toBe(200);

  guard('B2b:finalizacion');
  const finalizar = await api('PATCH', `/solicitudes/${principal}/etapa`, {
    token: ctx.roles.refugio.token!,
    body: { etapa: 5, nota: 'finalización refugio E2E' },
  });
  expect(finalizar.status).toBe(200);
  ctx.ganador = principal;
  ctx.perdedor = segundo;

  const informe = sql();
  const mascota = informe.mascotas.find((m) => m.id === ctx.mascotas[2].id);
  expect(mascota?.estado).toBe('adoptada');
  const ganadora = informe.solicitudes.find((s) => s.id === principal);
  const perdedora = informe.solicitudes.find((s) => s.id === segundo);
  expect(ganadora?.estado).toBe('completada');
  expect(ganadora?.etapa).toBe(5);
  expect(perdedora?.estado).toBe('cancelada');
  expect(perdedora?.etapa).toBeLessThan(5);
  expect(informe.solicitud_eventos.some((e) => e.solicitud_id === principal && e.etapa === 5)).toBe(true);
  expect(informe.solicitud_eventos.some((e) => e.solicitud_id === segundo && e.etapa === 5)).toBe(false);
  const notaGanadora = informe.mensajes.find((m) => m.solicitud_id === principal && m.texto.startsWith('finalización'));
  expect(notaGanadora?.autor_id).toBe(ctx.roles.refugio.id);
  evidenciaApi(
    'B2b-FINALIZACION',
    200,
    'una completada, dos canceladas; mascota adoptada',
    'secuencia controlada sin competencia: cancelación autorizada y finalización',
  );

  guard('B2b:idempotencia');
  const antes = sql();
  const antesEventos = antes.solicitud_eventos.filter((e) => e.solicitud_id === principal).length;
  const antesMensajes = antes.mensajes.filter((m) => m.solicitud_id === principal).length;
  const repeticion = await api('PATCH', `/solicitudes/${principal}/etapa`, {
    token: ctx.roles.refugio.token!,
    body: { etapa: 5, nota: 'finalización repetida E2E' },
  });
  expect(repeticion.status).toBe(200);
  const despues = sql();
  expect(despues.solicitud_eventos.filter((e) => e.solicitud_id === principal)).toHaveLength(antesEventos);
  expect(despues.mensajes.filter((m) => m.solicitud_id === principal)).toHaveLength(antesMensajes);
  expect(despues.mensajes.some((m) => m.solicitud_id === principal && m.texto === 'finalización repetida E2E')).toBe(false);
  evidenciaApi('B2b-IDEMPOTENCIA', 200, 'sin eventos ni mensajes duplicados', 'segunda finalización devolvió 200 con el mismo estado y textos');
});

test('B3 - rollback aislado ante fallo de commit', async () => {
  guard('B3:rollback');
  const objetivo = ctx.ganador ?? ctx.solicitudes.api[0];
  if (typeof objetivo !== 'number') {
    evidencia({
      id: 'B3',
      resultado: 'BLOCKED',
      tipo: 'sql',
      base: 'LeonsDB_Test',
      persistencia: 'sin solicitud propia disponible',
      detalle: 'B2 no produjo un ganador; rollback no evaluable',
    });
    return;
  }
  const autor = ctx.adoptantes[0].id!;
  const antes = sql().mensajes.length;
  const resultado = rollbackFixture(objetivo, autor);
  expect(resultado.rollback_verificado).toBe(true);
  expect(resultado.filas_persistidas).toBe(0);
  expect(sql().mensajes).toHaveLength(antes);
  evidencia({
    id: 'B3',
    resultado: 'PASS',
    tipo: 'sql',
    base: 'LeonsDB_Test',
    persistencia: '0 filas persistidas tras fallo simulado antes del commit',
    detalle: `inserción aislada en solicitud id=${objetivo} con rollback forzado`,
  });
});

test('Z - manifiesto, puertos y ausencia de contaminación', async () => {
  guard('Z:verificacion-final');
  expect(API_BASE).toContain(':8010');
  expect(API_BASE).not.toContain(':8000');
  const health = await healthApi();
  expect(health.status).toBe(200);
  const informe = sql();
  expect(informe.solicitudes.length).toBeGreaterThanOrEqual(4);
  expect(informe.favoritos.every((f) => ctx.adoptantes.some((a) => a.id === f.usuario_id))).toBe(true);
  evidencia({
    id: 'Z',
    resultado: 'PASS',
    tipo: 'sql',
    base: 'LeonsDB_Test',
    http: health.status,
    persistencia: 'manifiesto persistente con ids exactos; limpieza pendiente en afterAll',
    detalle: 'API solo :8010; navegador solo :4300; sin conexiones a :8000',
  });
});
