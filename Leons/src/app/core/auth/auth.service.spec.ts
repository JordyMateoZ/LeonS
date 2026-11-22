import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { PLATFORM_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { vi } from 'vitest';

import { API_BASE_URL } from '../api/api.config';
import { authInterceptor } from '../interceptors/auth.interceptor';
import { AuthService } from './auth.service';

const API = 'http://localhost:8000/api/v1';
const CLAVE = 'leons.token.v1';
const USUARIO = {
  id: 1,
  nombre: 'Demo',
  email: 'demo@leons.pe',
  rol: 'adoptante',
};

function jwt(exp: number): string {
  const payload = btoa(JSON.stringify({ sub: '1', exp }))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
  return `header.${payload}.firma`;
}

describe('AuthService — sesión y expiración', () => {
  let service: AuthService;
  let http: HttpTestingController;
  let cliente: HttpClient;

  function configurar() {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: PLATFORM_ID, useValue: 'browser' },
        { provide: API_BASE_URL, useValue: API },
      ],
    });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
    cliente = TestBed.inject(HttpClient);
  }

  beforeEach(() => {
    localStorage.removeItem(CLAVE);
  });

  afterEach(() => {
    localStorage.removeItem(CLAVE);
    http.verify();
  });

  it('descarta un JWT vencido almacenado sin consultar /auth/me', async () => {
    localStorage.setItem(CLAVE, jwt(Math.floor(Date.now() / 1000) - 60));
    configurar();

    await service.inicializar();

    expect(service.isAuthenticated()).toBe(false);
    expect(service.token()).toBeNull();
    expect(localStorage.getItem(CLAVE)).toBeNull();
    http.expectNone(`${API}/auth/me`);
  });

  it('descarta un token sin exp válida', () => {
    localStorage.setItem(CLAVE, 'token-sin-formato');
    configurar();

    expect(service.token()).toBeNull();
    expect(localStorage.getItem(CLAVE)).toBeNull();
  });

  it('confirma la sesión con un JWT vigente y /auth/me válido', async () => {
    const token = jwt(Math.floor(Date.now() / 1000) + 600);
    localStorage.setItem(CLAVE, token);
    configurar();

    const inicializacion = service.inicializar();
    const peticion = http.expectOne(`${API}/auth/me`);
    expect(peticion.request.headers.get('Authorization')).toBe(`Bearer ${token}`);
    peticion.flush(USUARIO);
    await inicializacion;

    expect(service.isAuthenticated()).toBe(true);
    expect(service.usuario()?.nombre).toBe('Demo');
    expect(service.token()).toBe(token);
  });

  it('invalida la sesión ante un 401 de /auth/me', async () => {
    localStorage.setItem(CLAVE, jwt(Math.floor(Date.now() / 1000) + 600));
    configurar();

    const inicializacion = service.inicializar();
    http.expectOne(`${API}/auth/me`).flush(
      { code: 'UNAUTHORIZED', message: 'Token expirado', details: null },
      { status: 401, statusText: 'Unauthorized' },
    );
    await inicializacion;

    expect(service.isAuthenticated()).toBe(false);
    expect(service.token()).toBeNull();
    expect(localStorage.getItem(CLAVE)).toBeNull();
    expect(service.errorSesion()).toContain('sesión venció');
  });

  it('conserva el token pero no afirma autenticación ante un 403', async () => {
    const token = jwt(Math.floor(Date.now() / 1000) + 600);
    localStorage.setItem(CLAVE, token);
    configurar();

    const inicializacion = service.inicializar();
    http.expectOne(`${API}/auth/me`).flush(
      { code: 'FORBIDDEN', message: 'Sin permisos', details: null },
      { status: 403, statusText: 'Forbidden' },
    );
    await inicializacion;

    expect(service.isAuthenticated()).toBe(false);
    expect(service.sesionPendiente()).toBe(true);
    expect(service.token()).toBe(token);
    expect(service.errorSesion()).toContain('permisos');
  });

  it.each([
    ['error de red', 0],
    ['HTTP 500', 500],
  ])('conserva credenciales ante %s de /auth/me', async (_nombre, status) => {
    const token = jwt(Math.floor(Date.now() / 1000) + 600);
    localStorage.setItem(CLAVE, token);
    configurar();

    const inicializacion = service.inicializar();
    http.expectOne(`${API}/auth/me`).flush(
      { code: 'INTERNAL_ERROR', message: 'Fallo', details: null },
      { status, statusText: 'Error' },
    );
    await inicializacion;

    expect(service.isAuthenticated()).toBe(false);
    expect(service.sesionPendiente()).toBe(true);
    expect(service.token()).toBe(token);
    expect(localStorage.getItem(CLAVE)).toBe(token);
  });

  it('recupera la sesión al revalidar después de un 500', async () => {
    const token = jwt(Math.floor(Date.now() / 1000) + 600);
    localStorage.setItem(CLAVE, token);
    configurar();

    const primera = service.inicializar();
    http.expectOne(`${API}/auth/me`).flush(
      { code: 'INTERNAL_ERROR', message: 'Fallo', details: null },
      { status: 500, statusText: 'Error' },
    );
    await primera;
    expect(service.sesionPendiente()).toBe(true);

    const segunda = service.revalidar();
    http.expectOne(`${API}/auth/me`).flush(USUARIO);
    await segunda;

    expect(service.isAuthenticated()).toBe(true);
    expect(service.errorSesion()).toBeNull();
  });

  it('cierra la sesión en todos los ámbitos y ejecuta la limpieza registrada', async () => {
    const limpieza = vi.fn();
    service = TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: PLATFORM_ID, useValue: 'browser' },
        { provide: API_BASE_URL, useValue: API },
      ],
    }).inject(AuthService);
    http = TestBed.inject(HttpTestingController);
    service.registrarLimpieza(limpieza);

    const inicio = firstValueFrom(
      service.login({ identificador: 'demo@leons.pe', password: 'demo12345' }),
    );
    http.expectOne(`${API}/auth/login`).flush({
      token: jwt(Math.floor(Date.now() / 1000) + 600),
      usuario: USUARIO,
    });
    await inicio;
    expect(service.isAuthenticated()).toBe(true);

    service.cerrarSesion();

    expect(limpieza).toHaveBeenCalledTimes(1);
    expect(service.token()).toBeNull();
    expect(service.usuario()).toBeNull();
    expect(service.isAuthenticated()).toBe(false);
    expect(localStorage.getItem(CLAVE)).toBeNull();
  });
});
