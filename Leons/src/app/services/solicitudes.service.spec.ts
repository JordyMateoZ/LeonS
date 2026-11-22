import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { AuthService } from '../core/auth/auth.service';
import { API_BASE_URL } from '../core/api/api.config';
import { SolicitudesService } from './solicitudes.service';

describe('SolicitudesService', () => {
  let service: SolicitudesService;
  let httpMock: HttpTestingController;
  let limpieza: (() => void) | null;

  beforeEach(() => {
    limpieza = null;
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: 'http://localhost:8000/api/v1' },
        {
          provide: AuthService,
          useValue: {
            isAuthenticated: () => true,
            token: () => 'token',
            registrarLimpieza: (fn: () => void) => {
              limpieza = fn;
              return () => (limpieza = null);
            },
          },
        },
      ],
    });
    service = TestBed.inject(SolicitudesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  function solicitudBase(id: number, nombre: string, estado: string): Record<string, unknown> {
    return {
      id,
      estado,
      nombre,
      fichaId: id,
      fotoSrc: '',
      fotoAlt: '',
      chipTexto: '',
      chipClase: '',
      refugio: '',
      lugar: '',
      exp: '',
      fechaTexto: '',
      badgeTexto: '',
      badgeClase: '',
      puntoClase: '',
      pasoTexto: '',
      pasoTextoClase: '',
      headerClase: '',
      iconoMini: '',
      iconoMiniClase: '',
      paso: 2,
      barraClase: '',
      etapas: [],
      cita: null,
      mensaje: null,
      tiempoRespuesta: null,
      whatsapp: null,
      cierre: null,
      motivoCancelacion: null,
      fotosSeguimiento: [],
      creadaEn: '2025-01-01T00:00:00',
    };
  }

  it('carga las solicitudes reales y actualiza los contadores', async () => {
    const promesa = service.cargar();
    const req = httpMock.expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true');
    expect(req.request.method).toBe('GET');
    req.flush({
      items: [solicitudBase(1, 'Chaska', 'active')],
      total: 1,
      page: 1,
      limit: 50,
      totalPages: 1,
    });
    await promesa;

    expect(service.total()).toBe(1);
    expect(service.activas()).toBe(1);
    expect(service.solicitudes()[0].nombre).toBe('Chaska');
  });

  it('no duplica una solicitud activa para la misma mascota', async () => {
    const promesa = service.cargar();
    const req = httpMock.expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true');
    req.flush({ items: [], total: 0, page: 1, limit: 50, totalPages: 0 });
    await promesa;

    const sumaq = { id: 4, nombre: 'Sumaq' } as any;

    const promesaCreacion = service.crearDesdeMascota(sumaq);
    const postReq = httpMock.expectOne('http://localhost:8000/api/v1/solicitudes');
    expect(postReq.request.method).toBe('POST');
    postReq.flush(solicitudBase(4, 'Sumaq', 'active'));
    const resultado = await promesaCreacion;
    expect(resultado.creada).toBe(true);
    expect(service.total()).toBe(1);

    // segunda vez: ya existe activa -> no POST
    const resultado2 = await service.crearDesdeMascota(sumaq);
    expect(resultado2.creada).toBe(false);
    expect(service.total()).toBe(1);
  });

  it('A-12: envía el mensaje opcional y no envía teléfono', async () => {
    const sumaq = { id: 5, nombre: 'Sumaq' } as any;
    const promesa = service.crearDesdeMascota(sumaq, undefined, '  Quiero adoptarla.  ');
    const postReq = httpMock.expectOne('http://localhost:8000/api/v1/solicitudes');
    expect(postReq.request.body).toEqual({
      mascotaId: 5,
      mensaje: 'Quiero adoptarla.',
      telefono: null,
    });
    postReq.flush(solicitudBase(5, 'Sumaq', 'active'));
    await promesa;
  });

  it('cancela una solicitud y actualiza el estado', async () => {
    const promesa = service.cargar();
    const req = httpMock.expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true');
    req.flush({
      items: [solicitudBase(2, 'Inti', 'active')],
      total: 1,
      page: 1,
      limit: 50,
      totalPages: 1,
    });
    await promesa;

    const promesaCancelacion = service.cancelar(2, 'Mudanza fuera de Huancayo');
    const cancelReq = httpMock.expectOne('http://localhost:8000/api/v1/solicitudes/2/cancelar');
    expect(cancelReq.request.method).toBe('PATCH');
    expect(cancelReq.request.body).toEqual({ motivo: 'Mudanza fuera de Huancayo' });
    cancelReq.flush(solicitudBase(2, 'Inti', 'cancelled'));

    expect(await promesaCancelacion).toBe(true);
    expect(service.solicitudes().find((s) => s.id === 2)?.estado).toBe('cancelled');
  });

  it('no inventa una solicitud ni reintenta cuando falla el POST', async () => {
    const carga = service.cargar();
    httpMock.expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true').flush({
      items: [],
      total: 0,
      page: 1,
      limit: 50,
      totalPages: 0,
    });
    await carga;

    const promesa = service.crearDesdeMascota({ id: 9, nombre: 'Prueba' } as any);
    const req = httpMock.expectOne('http://localhost:8000/api/v1/solicitudes');
    expect(req.request.method).toBe('POST');
    req.flush(
      { code: 'SERVER_ERROR', message: 'Fallo del servidor', details: null },
      { status: 500, statusText: 'Server Error' },
    );

    const resultado = await promesa;
    expect(resultado.creada).toBe(false);
    expect(resultado.solicitud).toBeUndefined();
    expect(service.total()).toBe(0);
    expect(service.error()).toBeTruthy();
  });

  it('impide un segundo POST simultáneo para la misma mascota', async () => {
    const carga = service.cargar();
    httpMock.expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true').flush({
      items: [],
      total: 0,
      page: 1,
      limit: 50,
      totalPages: 0,
    });
    await carga;

    const mascota = { id: 10, nombre: 'Prueba' } as any;
    const primera = service.crearDesdeMascota(mascota);
    const postReq = httpMock.expectOne('http://localhost:8000/api/v1/solicitudes');
    const segunda = await service.crearDesdeMascota(mascota);
    expect(segunda.creada).toBe(false);
    expect(segunda.error).toBe('ENVIO_EN_CURSO');

    postReq.flush(solicitudBase(10, 'Prueba', 'active'));
    expect((await primera).creada).toBe(true);
  });

  it('no cambia el estado local cuando falla la cancelación', async () => {
    const carga = service.cargar();
    httpMock.expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true').flush({
      items: [solicitudBase(3, 'Inti', 'active')],
      total: 1,
      page: 1,
      limit: 50,
      totalPages: 1,
    });
    await carga;

    const promesa = service.cancelar(3, 'Otro motivo personal');
    httpMock
      .expectOne('http://localhost:8000/api/v1/solicitudes/3/cancelar')
      .flush({ code: 'SERVER_ERROR', message: 'Fallo', details: null }, { status: 500, statusText: 'Error' });

    expect(await promesa).toBe(false);
    expect(service.solicitudes().find((s) => s.id === 3)?.estado).toBe('active');
    expect(service.error()).toBeTruthy();
  });

  it('conserva las solicitudes canceladas tras recargar', async () => {
    const primera = service.cargar();
    httpMock
      .expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true')
      .flush({
        items: [solicitudBase(7, 'Chaska', 'cancelled')],
        total: 1,
        page: 1,
        limit: 50,
        totalPages: 1,
      });
    await primera;
    expect(service.canceladas()).toBe(1);

    service.limpiarPrivados();
    expect(service.total()).toBe(0);

    const segunda = service.cargar();
    httpMock
      .expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true')
      .flush({
        items: [solicitudBase(7, 'Chaska', 'cancelled')],
        total: 1,
        page: 1,
        limit: 50,
        totalPages: 1,
      });
    await segunda;

    expect(service.solicitudes()[0].estado).toBe('cancelled');
    expect(service.canceladas()).toBe(1);
  });

  it('no filtra solicitudes de un usuario al cambiar de sesión', async () => {
    const primera = service.cargar();
    httpMock
      .expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true')
      .flush({ items: [solicitudBase(11, 'Inti', 'active')], total: 1 });
    await primera;
    expect(limpieza).not.toBeNull();

    limpieza?.();
    expect(service.total()).toBe(0);

    const segunda = service.cargar();
    httpMock
      .expectOne('http://localhost:8000/api/v1/solicitudes?limit=50&incluirCanceladas=true')
      .flush({ items: [solicitudBase(12, 'Sumaq', 'active')], total: 1 });
    await segunda;

    expect(service.solicitudes().map((s) => s.nombre)).toEqual(['Sumaq']);
  });
});
