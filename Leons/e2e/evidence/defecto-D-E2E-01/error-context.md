# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: escritura.spec.ts >> A2 - catálogo, favoritos, doble envío y persistencia tras recarga
- Location: e2e\escritura.spec.ts:378:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('E2E-32p96a-UI').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('E2E-32p96a-UI').first() with timeout 10000ms
  - waiting for getByText('E2E-32p96a-UI').first()

```

```yaml
- banner:
  - link "LeonS Logo LeonS Adopción Huancayo":
    - /url: /
    - img "LeonS Logo"
    - text: LeonS Adopción Huancayo
  - navigation:
    - link "Inicio":
      - /url: /
    - link "Mascotas en Adopción":
      - /url: /mascotas
    - link "Cómo Funciona":
      - /url: /como-funciona
    - link "Refugios Aliados":
      - /url: /refugios
    - link "Impacto":
      - /url: /impacto
    - link "Sobre Nosotros":
      - /url: /sobre-nosotros
  - link "Quiero Adoptar":
    - /url: /mascotas
  - link "Mis solicitudes de adopción":
    - /url: /mis-solicitudes
    - img "Perfil"
    - text: Mis solicitudes
  - button "Cerrar sesión"
- main:
  - text: volunteer_activism Red Solidaria Junín
  - heading "Cada colita adoptada alegra el Valle del Mantaro." [level=1]
  - paragraph: Conectamos corazones en Huancayo, El Tambo y Chilca con albergues y rescatistas transparentes. Sin cobros indebidos, con amor genuino.
  - img "Pareja andina abrazando a un perro rescatado y a un gato naranja con el paisaje del Valle del Mantaro al fondo"
  - text: pets Adopción ética en Huancayo
  - paragraph: "\"Chaska encontró un hogar seguro y cálido en El Tambo gracias a LeonS.\""
  - text: diversity_3 +1,200 Familias y Rescatistas Comunidad activa en Huancayo, San Jerónimo y El Tambo. verified 100% Sin Fines de Lucro Prohibida la venta de animales. Todo proceso es gratuito. medical_services Apoyo Veterinario Solidario Campañas de esterilización y vacunación en Junín. star star star star star
  - paragraph: "\"Pudimos postular conociendo la historia médica de nuestro perrito. Sin burocracia, con seguimiento por WhatsApp y apoyo de voluntarios de la UNCP.\""
  - text: Familia Meza Orihuela Urb. Los Eucaliptos, El Tambo
  - tablist:
    - tab "person_add Crear Cuenta" [selected]
    - tab "login Iniciar Sesión"
  - heading "Crea tu cuenta en LeonS" [level=2]
  - paragraph: "Sé parte del cambio por los animalitos desamparados de Huancayo. Elige cómo deseas participar:"
  - text: favorite Adoptante
  - heading "Quiero Adoptar" [level=3]
  - paragraph: Busco darle un hogar seguro y lleno de cariño a un perro o gato en el valle.
  - text: check_circle Seleccionado
  - radio "favorite Adoptante Quiero Adoptar Busco darle un hogar seguro y lleno de cariño a un perro o gato en el valle. check_circle Seleccionado" [checked]
  - text: home_work Rescatista
  - heading "Soy Refugio o Rescatista" [level=3]
  - paragraph: Publico mascotas, gestiono solicitudes de adopción y coordino con voluntarios.
  - text: radio_button_unchecked Elegir rol
  - radio "home_work Rescatista Soy Refugio o Rescatista Publico mascotas, gestiono solicitudes de adopción y coordino con voluntarios. radio_button_unchecked Elegir rol" [disabled]
  - paragraph: El registro de refugios o rescatistas está temporalmente no disponible. Por ahora puedes registrarte como adoptante.
  - text: Nombre completo o de la organización Requerido badge
  - textbox "Nombre completo o de la organización Requerido":
    - /placeholder: Ej. María Mayta Cárdenas / Albergue San Francisco
  - text: Correo electrónico mail
  - textbox "Correo electrónico":
    - /placeholder: tu.correo@ejemplo.com
  - text: WhatsApp / Celular Para coordinar visita chat
  - textbox "WhatsApp / Celular Para coordinar visita":
    - /placeholder: +51 964 123 456
  - text: DNI badge
  - textbox "DNI":
    - /placeholder: "12345678"
  - text: Distrito de residencia o sede location_city
  - combobox "Distrito de residencia o sede":
    - option "Selecciona tu distrito en Junín..." [disabled] [selected]
    - option "El Tambo"
    - option "Huancayo Centro"
    - option "Chilca"
    - option "Pilcomayo"
    - option "San Agustín de Cajas"
    - option "Sapallanga"
    - option "San Jerónimo de Tunán"
    - option "Huancán"
    - option "Concepción (Valle)"
    - option "Chupaca (Valle)"
  - text: expand_more Contraseña segura Mínimo 8 caracteres lock
  - textbox "Contraseña segura Mínimo 8 caracteres":
    - /placeholder: ••••••••••••
  - button "Ver u ocultar contraseña": visibility
  - text: Básica
  - checkbox "Acepto el Compromiso de Bienestar Animal y Adopción Ética de LeonS Huancayo, promoviendo esterilización y cuidado responsable."
  - text: Acepto el
  - link "Compromiso de Bienestar Animal y Adopción Ética":
    - /url: /como-funciona
  - text: de LeonS Huancayo, promoviendo esterilización y cuidado responsable.
  - button "Crear mi cuenta gratis arrow_forward" [disabled]
  - text: o regístrate con
  - button "Continuar con Google"
  - text: verified_user
  - paragraph:
    - strong: "Compromiso Wanka:"
    - text: LeonS nunca cobra por registrarse ni por adoptar. Tus datos personales son tratados con estricta confidencialidad bajo la Ley N° 29733 de Protección de Datos Personales del Perú.
  - text: home_pin
  - heading "Cercanía y Validación" [level=4]
  - paragraph: Priorizamos visitas domiciliarias y adopciones responsables dentro de la provincia de Huancayo y el Valle del Mantaro.
  - text: receipt_long
  - heading "Compromiso Notarial Solidario" [level=4]
  - paragraph: Firma un acta simple de tenencia responsable con compromiso de esterilización y vacunas anuales.
  - text: volunteer_activism
  - heading "Red de Rescate Colectivo" [level=4]
  - paragraph: Si eres albergue o rescatista independiente de Junín, LeonS te brinda visibilidad gratuita y filtros de candidatos.
- contentinfo:
  - img "LeonS Logo"
  - text: LeonS
  - paragraph: Conectando corazones en el Valle del Mantaro. Fomentamos la adopción responsable y apoyamos a los rescatistas locales.
  - text: place Huancayo, Junín • Perú
  - heading "Adopción" [level=3]
  - link "Perros en adopción":
    - /url: /mascotas
  - link "Gatos en adopción":
    - /url: /mascotas
  - link "Requisitos de adopción":
    - /url: /como-funciona
  - link "Mis solicitudes de adopción":
    - /url: /mis-solicitudes
  - link "Guía de tenencia responsable":
    - /url: /como-funciona
  - heading "Para Refugios" [level=3]
  - link "Registrar Albergue":
    - /url: /refugios
  - link "Publicar Mascota":
    - /url: /login
  - link "Guía de Rescate y Acogida":
    - /url: /como-funciona
  - link "Red de Veterinarias Aliadas":
    - /url: /refugios
  - heading "Contacto y Comunidad" [level=3]
  - paragraph: Valle del Mantaro, Junín
  - link "chat WhatsApp de ayuda comunitaria":
    - /url: https://wa.me/51964892110
  - link "group Comunidad en Redes":
    - /url: /sobre-nosotros
  - link "mail Contacto directo":
    - /url: mailto:hola@leons.pe
  - text: pets
  - paragraph: LeonS © 2026 • Iniciativa comunitaria sin fines de lucro para Huancayo
  - text: Valle del Mantaro Solidario
```

# Test source

```ts
  341 |   await page.getByRole('button', { name: /Crear mi cuenta gratis/i }).click();
  342 |   await page.waitForURL(/\/mis-solicitudes/);
  343 | 
  344 |   // La respuesta del registro no se inspecciona en la UI: se consulta /auth/me.
  345 |   const token = await tokenUi(page);
  346 |   const perfil = await api('GET', '/auth/me', { token });
  347 |   expect(perfil.status).toBe(200);
  348 |   expect(perfil.body.email).toBe(adoptante.email);
  349 |   expect(perfil.body.rol).toBe('adoptante');
  350 |   adoptante.id = Number(perfil.body.id);
  351 |   adoptante.token = token;
  352 |   anadirRegistro('users', { id: adoptante.id, email: adoptante.email, rol: 'adoptante' });
  353 |   trackDistritos();
  354 |   verificarMarcador(adoptante.email);
  355 | 
  356 |   // La pestaña de refugio sigue bloqueada en el registro público.
  357 |   await page.evaluate(() => localStorage.removeItem('leons.token.v1'));
  358 |   await page.goto('/login');
  359 |   await page.getByRole('tab', { name: /Crear Cuenta/i }).click();
  360 |   await expect(page.locator('input[value="shelter"]')).toBeDisabled();
  361 |   await loginUi(page, adoptante.dni);
  362 |   expect(page.url()).toContain('localhost:4300');
  363 | 
  364 |   sinContaminacion(diagnostico);
  365 |   await adjuntar(diagnostico);
  366 |   evidencia({
  367 |     id: 'A1',
  368 |     resultado: 'PASS',
  369 |     tipo: 'navegador',
  370 |     base: 'LeonsDB_Test',
  371 |     http: perfil.status,
  372 |     persistencia: `usuario id=${adoptante.id} en LeonsDB_Test; ausente en LeonsDB`,
  373 |     captura: 'trace/screenshot automáticos ante fallo',
  374 |     detalle: 'registro público creó solo rol adoptante; login por DNI correcto',
  375 |   });
  376 | });
  377 | 
  378 | test('A2 - catálogo, favoritos, doble envío y persistencia tras recarga', async ({ page }) => {
  379 |   const diagnostico = observar(page);
  380 |   const adoptante = ctx.adoptantes[0];
  381 |   const mascota = ctx.mascotas[0];
  382 |   guard('A2:login-ui');
  383 |   await loginUi(page, adoptante.email);
  384 | 
  385 |   guard('A2:catalogo');
  386 |   await gotoAuth(page, '/mascotas');
  387 |   await page.getByPlaceholder(/Buscar por nombre/i).fill(mascota.nombre);
  388 |   await page.getByRole('button', { name: /Buscar mascota/i }).click();
  389 |   await expect(page.getByText(mascota.nombre, { exact: false }).first()).toBeVisible();
  390 | 
  391 |   guard('A2:favorito');
  392 |   const respuestaFavorito = page.waitForResponse(
  393 |     (respuesta) =>
  394 |       respuesta.url().includes(`${PUERTO_E2E}/api/v1/favoritos`) &&
  395 |       respuesta.request().method() === 'POST',
  396 |   );
  397 |   await page
  398 |     .getByRole('button', { name: `Guardar a ${mascota.nombre} en favoritos` })
  399 |     .first()
  400 |     .click();
  401 |   expect((await respuestaFavorito).status()).toBe(201);
  402 |   const favoritos = await api('GET', '/favoritos', { token: adoptante.token! });
  403 |   expect(favoritos.status).toBe(200);
  404 |   expect(favoritos.body.ids).toContain(mascota.id);
  405 |   await gotoAuth(page, '/mascotas');
  406 |   await page.getByPlaceholder(/Buscar por nombre/i).fill(mascota.nombre);
  407 |   await page.getByRole('button', { name: /Buscar mascota/i }).click();
  408 |   await expect(
  409 |     page.getByRole('button', { name: `Guardar a ${mascota.nombre} en favoritos` }).first(),
  410 |   ).toHaveClass(/text-primary/);
  411 |   const favoritosTrasRecarga = await api('GET', '/favoritos', { token: adoptante.token! });
  412 |   expect(favoritosTrasRecarga.body.ids).toContain(mascota.id);
  413 |   const favoritoSql = sql().favoritos.find(
  414 |     (f) => f.usuario_id === adoptante.id && f.mascota_id === mascota.id,
  415 |   );
  416 |   expect(favoritoSql, 'favorito persistido en SQL').toBeTruthy();
  417 | 
  418 |   guard('A2:doble-envio');
  419 |   await gotoAuth(page, `/mascotas/${mascota.id}`);
  420 |   await page.getByRole('button', { name: `Solicitar adopción de ${mascota.nombre}` }).click();
  421 |   await page.locator('#adopt-message').fill('E2E doble envío controlado');
  422 |   await page.locator('#terms-check').check();
  423 |   // Dos clics nativos seguidos: el guardián de la UI debe impedir el segundo POST.
  424 |   await page.evaluate(() => {
  425 |     const boton = Array.from(document.querySelectorAll('button')).find((b) =>
  426 |       (b.textContent ?? '').includes('Enviar Solicitud'),
  427 |     );
  428 |     if (!boton) throw new Error('No aparece el botón Enviar Solicitud.');
  429 |     boton.click();
  430 |     boton.click();
  431 |   });
  432 |   await expect(page.getByText(/¡Solicitud enviada!/)).toBeVisible();
  433 | 
  434 |   trackSolicitudes();
  435 |   const creations = solsDe(sql(), adoptante.id!, mascota.id);
  436 |   expect(creations, 'una sola solicitud pese al doble clic').toHaveLength(1);
  437 |   ctx.solicitudes.ui = creations[0].id;
  438 |   expect(creations[0].estado).toBe('activa');
  439 | 
  440 |   await gotoAuth(page, '/mis-solicitudes');
> 441 |   await expect(page.getByText(mascota.nombre, { exact: false }).first()).toBeVisible();
      |                                                                          ^ Error: expect(locator).toBeVisible() failed
  442 |   await gotoAuth(page, '/mis-solicitudes');
  443 |   await expect(page.getByText(mascota.nombre, { exact: false }).first()).toBeVisible();
  444 | 
  445 |   sinContaminacion(diagnostico);
  446 |   await adjuntar(diagnostico);
  447 |   evidencia({
  448 |     id: 'A2',
  449 |     resultado: 'PASS',
  450 |     tipo: 'navegador',
  451 |     base: 'LeonsDB_Test',
  452 |     http: favoritos.status,
  453 |     persistencia: `favorito y solicitud id=${ctx.solicitudes.ui} persistidos tras recarga`,
  454 |     captura: 'trace/screenshot automáticos ante fallo',
  455 |     detalle: 'catálogo con filtro propio; doble clic generó una sola fila SQL',
  456 |   });
  457 | });
  458 | 
  459 | test('A3 - fallo forzado del POST no crea solicitud ficticia', async ({ page }) => {
  460 |   const diagnostico = observar(page);
  461 |   const adoptante = ctx.adoptantes[1];
  462 |   const mascota = ctx.mascotas[1];
  463 |   guard('A3:login-ui');
  464 |   await loginUi(page, adoptante.email);
  465 | 
  466 |   guard('A3:post-fallido');
  467 |   const patron = '**/api/v1/solicitudes';
  468 |   await page.route(patron, async (ruta) => {
  469 |     if (ruta.request().method() === 'POST') {
  470 |       await ruta.fulfill({
  471 |         status: 500,
  472 |         contentType: 'application/json',
  473 |         body: JSON.stringify({ code: 'E2E_FORZADO', message: 'fallo inyectado' }),
  474 |       });
  475 |       return;
  476 |     }
  477 |     await ruta.continue();
  478 |   });
  479 | 
  480 |   await gotoAuth(page, `/mascotas/${mascota.id}`);
  481 |   await page.getByRole('button', { name: `Solicitar adopción de ${mascota.nombre}` }).click();
  482 |   await page.locator('#adopt-message').fill('No debe persistir');
  483 |   await page.locator('#terms-check').check();
  484 |   await page.getByRole('button', { name: 'Enviar Solicitud' }).click();
  485 |   await expect(page.getByText(/E2E_FORZADO|fallo inyectado/i)).toBeVisible();
  486 |   await page.unroute(patron);
  487 | 
  488 |   trackSolicitudes();
  489 |   const filas = solsDe(sql(), adoptante.id!, mascota.id);
  490 |   expect(filas, 'no debe existir solicitud tras el POST fallido').toHaveLength(0);
  491 | 
  492 |   sinContaminacion(diagnostico);
  493 |   await adjuntar(diagnostico);
  494 |   evidencia({
  495 |     id: 'A3',
  496 |     resultado: 'PASS',
  497 |     tipo: 'navegador',
  498 |     base: 'LeonsDB_Test',
  499 |     http: 500,
  500 |     persistencia: '0 filas en solicitudes para usuario/mascota E2E',
  501 |     captura: 'trace/screenshot automáticos ante fallo',
  502 |     detalle: 'POST forzado a fallar mediante route de Playwright; sin solicitud ficticia',
  503 |   });
  504 | });
  505 | 
  506 | test('A4 - aislamiento de solicitudes entre dos usuarios', async ({ browser }) => {
  507 |   const primero = await browser.newContext();
  508 |   const segundo = await browser.newContext();
  509 |   const paginaUno = await primero.newPage();
  510 |   const paginaDos = await segundo.newPage();
  511 |   const diagUno = observar(paginaUno);
  512 |   const diagDos = observar(paginaDos);
  513 |   guard('A4:login-ui');
  514 |   await loginUi(paginaUno, ctx.adoptantes[0].email);
  515 |   await loginUi(paginaDos, ctx.adoptantes[2].email);
  516 | 
  517 |   const propio = ctx.mascotas[0].nombre;
  518 |   const ajeno = ctx.mascotas[2].nombre;
  519 |   await gotoAuth(paginaUno, '/mis-solicitudes');
  520 |   await expect(paginaUno.getByText(propio, { exact: false }).first()).toBeVisible();
  521 |   await expect(paginaUno.getByText(ajeno, { exact: false })).toHaveCount(0);
  522 | 
  523 |   await gotoAuth(paginaDos, '/mis-solicitudes');
  524 |   await expect(paginaDos.getByText(propio, { exact: false })).toHaveCount(0);
  525 | 
  526 |   const listaUno = await api('GET', '/solicitudes', { token: ctx.adoptantes[0].token! });
  527 |   const listaDos = await api('GET', '/solicitudes', { token: ctx.adoptantes[2].token! });
  528 |   expect(listaUno.status).toBe(200);
  529 |   expect(listaDos.status).toBe(200);
  530 |   const idsUno = new Set<number>(listaUno.body.items.map((s: any) => Number(s.id)));
  531 |   const idsDos = new Set<number>(listaDos.body.items.map((s: any) => Number(s.id)));
  532 |   expect([...idsUno].some((id) => idsDos.has(id))).toBe(false);
  533 | 
  534 |   sinContaminacion(diagUno);
  535 |   sinContaminacion(diagDos);
  536 |   await adjuntar(diagUno, '-usuario-uno');
  537 |   await adjuntar(diagDos, '-usuario-dos');
  538 |   await primero.close();
  539 |   await segundo.close();
  540 |   evidencia({
  541 |     id: 'A4',
```