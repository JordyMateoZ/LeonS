import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { PLATFORM_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { AuthService } from '../core/auth/auth.service';
import { API_BASE_URL } from '../core/api/api.config';
import { FavoritosService } from './favoritos.service';

const API = 'http://localhost:8000/api/v1';

describe('FavoritosService', () => {
  let service: FavoritosService;
  let httpMock: HttpTestingController;
  let limpieza: (() => void) | null;

  beforeEach(() => {
    limpieza = null;
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: PLATFORM_ID, useValue: 'server' },
        { provide: API_BASE_URL, useValue: API },
        {
          provide: AuthService,
          useValue: {
            isAuthenticated: () => true,
            registrarLimpieza: (fn: () => void) => {
              limpieza = fn;
              return () => (limpieza = null);
            },
          },
        },
      ],
    });
    service = TestBed.inject(FavoritosService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('evita dos POST simultáneos para la misma mascota', async () => {
    const primera = service.agregar(4);
    const segunda = service.agregar(4);

    const req = httpMock.expectOne(`${API}/favoritos`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ mascotaId: 4 });
    req.flush({ ids: [4] });

    await Promise.all([primera, segunda]);
    expect(service.ids().has(4)).toBe(true);
    expect(service.error()).toBeNull();
  });

  it('conserva el estado anterior y expone el error si falla', async () => {
    const carga = service.cargar();
    httpMock.expectOne(`${API}/favoritos`).flush({ ids: [7] });
    await carga;
    expect(service.ids().has(7)).toBe(true);

    const promesa = service.agregar(8);
    httpMock
      .expectOne(`${API}/favoritos`)
      .flush({ code: 'SERVER_ERROR', message: 'No se pudo guardar', details: null }, { status: 500, statusText: 'Error' });
    await promesa;

    expect(service.ids().has(7)).toBe(true);
    expect(service.ids().has(8)).toBe(false);
    expect(service.error()).toBeTruthy();
  });

  it('descarta los favoritos del usuario anterior al cerrar sesión', async () => {
    const primera = service.cargar();
    httpMock.expectOne(`${API}/favoritos`).flush({ ids: [4, 7] });
    await primera;
    expect(service.total()).toBe(2);
    expect(limpieza).not.toBeNull();

    limpieza?.();

    expect(service.total()).toBe(0);
    expect(service.error()).toBeNull();

    const segunda = service.cargar();
    httpMock.expectOne(`${API}/favoritos`).flush({ ids: [9] });
    await segunda;

    expect([...service.ids()]).toEqual([9]);
    expect(service.ids().has(4)).toBe(false);
  });
});
