import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { PLATFORM_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { API_BASE_URL } from '../api/api.config';
import { AuthService } from '../auth/auth.service';
import { authInterceptor } from '../interceptors/auth.interceptor';
import { authGuard } from './auth.guard';

const API = 'http://localhost:8000/api/v1';
const CLAVE = 'leons.token.v1';
const USUARIO = { id: 1, nombre: 'Demo', email: 'demo@leons.pe', rol: 'adoptante' };

function jwt(exp: number): string {
  const payload = btoa(JSON.stringify({ sub: '1', exp }))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
  return `header.${payload}.firma`;
}

function tokenVigente(): string {
  return jwt(Math.floor(Date.now() / 1000) + 600);
}

describe('authGuard — 5.6.3.2D', () => {
  let http: HttpTestingController;
  let auth: AuthService;
  let router: Router;

  function configurar(plataforma: 'browser' | 'server' = 'browser'): void {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: PLATFORM_ID, useValue: plataforma },
        { provide: API_BASE_URL, useValue: API },
      ],
    });
    http = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
  }

  function ejecutar(): unknown {
    return TestBed.runInInjectionContext(() => authGuard(null as never, null as never));
  }

  function urlDe(resultado: unknown): string {
    return resultado === true ? '' : String(resultado);
  }

  beforeEach(() => localStorage.removeItem(CLAVE));
  afterEach(() => {
    localStorage.removeItem(CLAVE);
    http.verify();
  });

  it('permite el acceso con sesión confirmada sin repetir /auth/me', async () => {
    localStorage.setItem(CLAVE, tokenVigente());
    configurar();
    const verificacion = auth.inicializar();
    http.expectOne(`${API}/auth/me`).flush(USUARIO);
    await verificacion;

    expect(await ejecutar()).toBe(true);
    http.expectNone(`${API}/auth/me`);
  });

  it('espera a /auth/me cuando la sesión está pendiente', async () => {
    localStorage.setItem(CLAVE, tokenVigente());
    configurar();

    const resultado = ejecutar();
    http.expectOne(`${API}/auth/me`).flush(USUARIO);

    expect(await resultado).toBe(true);
    expect(auth.isAuthenticated()).toBe(true);
  });

  it('redirige a login sin token sin consultar /auth/me', async () => {
    configurar();

    const resultado = await ejecutar();
    expect(resultado).toBeTruthy();
    expect(urlDe(resultado)).toContain('/login');
    http.expectNone(`${API}/auth/me`);
  });

  it('redirige a login con JWT vencido', async () => {
    localStorage.setItem(CLAVE, jwt(Math.floor(Date.now() / 1000) - 60));
    configurar();

    expect(urlDe(await ejecutar())).toContain('/login');
    expect(auth.token()).toBeNull();
    expect(localStorage.getItem(CLAVE)).toBeNull();
  });

  it('redirige a login e invalida credenciales ante 401', async () => {
    localStorage.setItem(CLAVE, tokenVigente());
    configurar();

    const resultado = ejecutar();
    http.expectOne(`${API}/auth/me`).flush(
      { code: 'UNAUTHORIZED', message: 'Token expirado', details: null },
      { status: 401, statusText: 'Unauthorized' },
    );

    expect(urlDe(await resultado)).toContain('/login');
    expect(auth.token()).toBeNull();
  });

  it('no autoriza datos privados ante 403 pero mantiene la sesión pendiente', async () => {
    localStorage.setItem(CLAVE, tokenVigente());
    configurar();

    const resultado = ejecutar();
    http.expectOne(`${API}/auth/me`).flush(
      { code: 'FORBIDDEN', message: 'Sin permisos', details: null },
      { status: 403, statusText: 'Forbidden' },
    );

    expect(await resultado).toBe(true);
    expect(auth.isAuthenticated()).toBe(false);
    expect(auth.sesionPendiente()).toBe(true);
    expect(auth.token()).not.toBeNull();
  });

  it('conserva credenciales ante 500 sin afirmar autenticación', async () => {
    localStorage.setItem(CLAVE, tokenVigente());
    configurar();

    const resultado = ejecutar();
    http.expectOne(`${API}/auth/me`).flush(
      { code: 'INTERNAL_ERROR', message: 'Fallo', details: null },
      { status: 500, statusText: 'Error' },
    );

    expect(await resultado).toBe(true);
    expect(auth.isAuthenticated()).toBe(false);
    expect(auth.sesionPendiente()).toBe(true);
    expect(auth.errorSesion()).toBeTruthy();
  });

  it('recupera la sesión tras un 500 mediante revalidar()', async () => {
    localStorage.setItem(CLAVE, tokenVigente());
    configurar();

    const primera = ejecutar();
    http.expectOne(`${API}/auth/me`).flush(
      { code: 'INTERNAL_ERROR', message: 'Fallo', details: null },
      { status: 500, statusText: 'Error' },
    );
    await primera;

    const segunda = auth.revalidar();
    http.expectOne(`${API}/auth/me`).flush(USUARIO);
    await segunda;

    expect(auth.isAuthenticated()).toBe(true);
    expect(await ejecutar()).toBe(true);
  });

  it('en SSR no lee localStorage, no bloquea y no emite /auth/me', async () => {
    localStorage.setItem(CLAVE, tokenVigente());
    configurar('server');

    expect(await ejecutar()).toBe(true);
    expect(auth.token()).toBeNull();
    http.expectNone(`${API}/auth/me`);
  });

  it('devuelve un UrlTree de Router para la ruta sin sesión', async () => {
    configurar();
    const esperado = router.createUrlTree(['/login']).toString();

    expect(String(await ejecutar())).toBe(esperado);
  });
});
