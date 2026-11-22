import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { vi } from 'vitest';

import { ApiError } from '../api/api-error';
import { AuthService } from '../auth/auth.service';
import { authInterceptor } from './auth.interceptor';
import { errorInterceptor } from './error.interceptor';

const API = 'http://localhost:8000/api/v1';

describe('Interceptores de autenticación', () => {
  let cliente: HttpClient;
  let http: HttpTestingController;
  let invalidar: ReturnType<typeof vi.fn>;
  let token: string | null;

  beforeEach(() => {
    invalidar = vi.fn();
    token = 'token-valido';
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
        provideHttpClientTesting(),
        {
          provide: AuthService,
          useValue: {
            token: () => token,
            invalidarPor401: invalidar,
          },
        },
      ],
    });
    cliente = TestBed.inject(HttpClient);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('asocia el Bearer y convierte un 401 en ApiError invalidando la sesión', async () => {
    const promesa = firstValueFrom(cliente.get(`${API}/solicitudes`));
    const peticion = http.expectOne(`${API}/solicitudes`);
    expect(peticion.request.headers.get('Authorization')).toBe('Bearer token-valido');
    peticion.flush(
      { code: 'UNAUTHORIZED', message: 'Token vencido', details: null },
      { status: 401, statusText: 'Unauthorized' },
    );

    await expect(promesa).rejects.toBeInstanceOf(ApiError);
    expect(invalidar).toHaveBeenCalledTimes(1);
  });

  it('no invalida la sesión por un 403 ni por un 401 sin Bearer', async () => {
    const conPermisos = firstValueFrom(cliente.get(`${API}/solicitudes`));
    http.expectOne(`${API}/solicitudes`).flush(
      { code: 'FORBIDDEN', message: 'Sin permisos', details: null },
      { status: 403, statusText: 'Forbidden' },
    );
    await expect(conPermisos).rejects.toMatchObject({ status: 403, code: 'FORBIDDEN' });

    token = null;
    const sinToken = firstValueFrom(cliente.post(`${API}/auth/login`, {}));
    http.expectOne(`${API}/auth/login`).flush(
      { code: 'UNAUTHORIZED', message: 'Credenciales inválidas', details: null },
      { status: 401, statusText: 'Unauthorized' },
    );
    await expect(sinToken).rejects.toMatchObject({ status: 401 });

    expect(invalidar).not.toHaveBeenCalled();
  });

  it('conserva el código de error del contrato', async () => {
    const promesa = firstValueFrom(cliente.get(`${API}/favoritos`));
    http.expectOne(`${API}/favoritos`).flush(
      { code: 'RATE_LIMIT', message: 'Demasiadas peticiones', details: { limite: 5 } },
      { status: 429, statusText: 'Too Many Requests' },
    );

    await expect(promesa).rejects.toMatchObject({
      code: 'RATE_LIMIT',
      status: 429,
      details: { limite: 5 },
    });
  });
});
