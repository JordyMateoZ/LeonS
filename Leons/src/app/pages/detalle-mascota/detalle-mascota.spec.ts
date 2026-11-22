import { PLATFORM_ID, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, ParamMap, convertToParamMap, provideRouter } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import { vi } from 'vitest';

import { API_BASE_URL } from '../../core/api/api.config';
import { AuthService } from '../../core/auth/auth.service';
import { InitialDataService } from '../../core/data/initial-data.service';
import { FOTO_PLACEHOLDER } from '../../core/imagenes/foto-fallback.directive';
import { MASCOTAS } from '../../data/mascotas.data';
import { REFUGIOS } from '../../data/refugios.data';
import { FavoritosService } from '../../services/favoritos.service';
import { SolicitudesService, ResultadoSolicitud } from '../../services/solicitudes.service';
import { DetalleMascota, DetalleMascotaApi } from './detalle-mascota';

const API = 'http://localhost:8000/api/v1';
function crearAuthStub(autenticado = false) {
  const usuario = signal(
    autenticado
      ? {
          id: 1,
          nombre: 'Carmen Quispe',
          email: 'carmen@example.com',
          dni: null,
          telefono: '987654321',
          distrito: 'El Tambo',
          rol: 'adoptante' as const,
          refugioId: null,
          creadoEn: '2026-01-01T00:00:00Z',
        }
      : null,
  );
  return {
    usuario: usuario.asReadonly(),
    setUsuario: (valor: Parameters<typeof usuario.set>[0]) => usuario.set(valor),
    isAuthenticated: () => usuario() !== null,
    registrarLimpieza: () => () => {},
  };
}

const initialDataStub = {
  mascotas: signal<unknown[]>([]),
  refugios: signal<unknown[]>([]),
  contenido: signal<unknown | null>(null),
  impacto: signal<unknown | null>(null),
  cargado: signal(false),
  recargar: async () => undefined,
};

function respuestaDetalle(nombre: string): DetalleMascotaApi {
  return {
    mascota: {},
    refugio: {},
    historia: [`Historia de ${nombre}`],
    cuidados: [{ icono: 'check', titulo: `Cuidado de ${nombre}`, texto: 'Texto de ejemplo' }],
    requisitos: [],
    preguntas: [{ pregunta: `¿Pregunta de ${nombre}?`, respuesta: 'Respuesta de ejemplo' }],
    cita: { texto: `Cita de ${nombre}`, autor: 'Veterinaria LeonS' },
    galeria: [{ src: `/${nombre}.jpg`, alt: nombre }],
    similares: [],
  };
}

function urlDetalle(id: number): string {
  return `${API}/mascotas/${id}/detalle`;
}

describe('DetalleMascota', () => {
  let component: DetalleMascota;
  let fixture: ComponentFixture<DetalleMascota>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DetalleMascota],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: API },
        { provide: AuthService, useFactory: () => crearAuthStub() },
        { provide: InitialDataService, useValue: initialDataStub },
      ],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(DetalleMascota);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  afterEach(() => httpMock.verify());

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show the not-found state when there is no id', () => {
    expect(fixture.nativeElement.textContent).toContain('No encontramos esta mascota');
    httpMock.expectNone(urlDetalle(0));
  });
});

describe('DetalleMascota con una mascota válida', () => {
  let component: DetalleMascota;
  let fixture: ComponentFixture<DetalleMascota>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    const paramMap = convertToParamMap({ id: '4' });

    await TestBed.configureTestingModule({
      imports: [DetalleMascota],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: API },
        { provide: AuthService, useFactory: () => crearAuthStub() },
        { provide: InitialDataService, useValue: initialDataStub },
        {
          provide: FavoritosService,
          useValue: {
            ids: signal<Set<number>>(new Set()).asReadonly(),
            esFavorito: () => false,
            alternar: async () => {},
            error: signal<string | null>(null).asReadonly(),
          },
        },
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(paramMap),
            snapshot: { paramMap, queryParamMap: convertToParamMap({}) },
          },
        },
        {
          provide: SolicitudesService,
          useFactory: () => {
            let llamadas = 0;
            const service = {
              solicitudes: () => [],
              total: () => 0,
              activas: () => 0,
              finalizadas: () => 0,
              solicitudActivaPara: () =>
                llamadas > 0 ? ({ id: 99, nombre: 'Sumaq' } as any) : undefined,
              crearDesdeMascota: async (
                _mascota: unknown,
                _refugio: unknown,
                mensaje?: string | null,
              ): Promise<ResultadoSolicitud> => {
                (service as any).ultimoMensaje = mensaje;
                llamadas++;
                if (llamadas === 1) {
                  return { creada: true, solicitud: { id: 99, nombre: 'Sumaq' } as any };
                }
                return {
                  creada: false,
                  solicitud: { id: 99, nombre: 'Sumaq' } as any,
                  error: 'SOLICITUD_DUPLICADA',
                };
              },
              cancelar: async () => true,
              restaurarCanceladas: () => {},
              cargar: async () => {},
            };
            return service;
          },
        },
      ],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(DetalleMascota);
    component = fixture.componentInstance;
    httpMock.expectOne(urlDetalle(4)).flush(respuestaDetalle('Sumaq'));
    await fixture.whenStable();
    fixture.detectChanges();
  });

  afterEach(() => httpMock.verify());

  it('A-12: envía el mensaje escrito y muestra los datos del perfil', async () => {
    const auth = TestBed.inject(AuthService) as any;
    auth.setUsuario({
      id: 1,
      nombre: 'Carmen Quispe',
      email: 'carmen@example.com',
      dni: null,
      telefono: '987654321',
      distrito: 'El Tambo',
      rol: 'adoptante',
      refugioId: null,
      creadoEn: '2026-01-01T00:00:00Z',
    });
    fixture.detectChanges();

    expect(component.mascota()?.nombre).toBe('Sumaq');
    expect(component.refugio()?.id).toBe('red-animalista-wanka');

    component.abrirModal();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Postulando como Carmen Quispe');
    const area = fixture.nativeElement.querySelector('#adopt-message') as HTMLTextAreaElement;
    expect(area).toBeTruthy();
    area.value = 'Tengo patio seguro en El Tambo.';
    area.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    await component.enviarSolicitud(new Event('submit'));
    const servicio = TestBed.inject(SolicitudesService) as any;
    expect(servicio.ultimoMensaje).toBe('Tengo patio seguro en El Tambo.');

    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Solicitud enviada');
    expect(texto).toContain('Ver mis solicitudes');
  });

  it('no muestra un contador inventado de favoritos', () => {
    const texto = fixture.nativeElement.textContent as string;

    expect(texto).not.toContain('14 personas');
    expect(texto).not.toContain('guardaron a');
    expect((component as any).favoritos).toBeUndefined();
  });

  it('should not duplicate an active request for the same pet', async () => {
    await component.enviarSolicitud(new Event('submit'));
    await component.enviarSolicitud(new Event('submit'));

    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Ya tienes una solicitud activa');
  });

  it('does not show a success confirmation when the request fails', async () => {
    const servicio = TestBed.inject(SolicitudesService);
    vi.spyOn(servicio, 'crearDesdeMascota').mockResolvedValue({
      creada: false,
      error: 'No se pudo conectar con el servidor.',
    });

    await component.enviarSolicitud(new Event('submit'));
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No se pudo conectar con el servidor.');
    expect(fixture.nativeElement.textContent).not.toContain('Ver mis solicitudes');
    expect(component.solicitudCreada()).toBe(false);
  });

  it('should use real pets and refugios from the existing catalogue', () => {
    const sumaq = MASCOTAS.find((m) => m.id === 4)!;
    const refugio = REFUGIOS.find((r) => r.id === sumaq.refugioId)!;

    expect(component.mascota()).toBe(sumaq);
    expect(component.refugio()?.nombre).toBe(refugio.nombre);
  });
});

describe('DetalleMascota — carga reactiva del detalle', () => {
  let component: DetalleMascota;
  let fixture: ComponentFixture<DetalleMascota>;
  let httpMock: HttpTestingController;
  let paramMap$: BehaviorSubject<ParamMap>;

  beforeEach(async () => {
    paramMap$ = new BehaviorSubject<ParamMap>(convertToParamMap({ id: '1' }));

    await TestBed.configureTestingModule({
      imports: [DetalleMascota],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: API },
        { provide: AuthService, useFactory: () => crearAuthStub() },
        { provide: InitialDataService, useValue: initialDataStub },
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: paramMap$,
            snapshot: {
              paramMap: convertToParamMap({ id: '1' }),
              queryParamMap: convertToParamMap({}),
            },
          },
        },
      ],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(DetalleMascota);
    component = fixture.componentInstance;
  });

  afterEach(() => httpMock.verify());

  it('carga el contrato tipado, expone el estado api y pinta los datos reales', async () => {
    const peticion = httpMock.expectOne(urlDetalle(1));
    expect(peticion.request.method).toBe('GET');
    expect(component.cargandoDetalle()).toBe(true);
    expect(component.datosReales()).toBeNull();

    peticion.flush(respuestaDetalle('Chaska'));
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.datosReales()?.historia).toEqual(['Historia de Chaska']);
    expect(component.apiDisponible()).toBe(true);
    expect(component.usandoRespaldo()).toBe(false);
    expect(component.errorDetalle()).toBeNull();
    expect(component.historia()).toEqual(['Historia de Chaska']);
    expect(fixture.nativeElement.querySelector('[data-estado-detalle="api"]')).toBeTruthy();
  });

  it('cancela la petición anterior al cambiar de id y limpia los datos obsoletos', async () => {
    const anterior = httpMock.expectOne(urlDetalle(1));
    anterior.flush(respuestaDetalle('Chaska'));
    await fixture.whenStable();
    expect(component.apiDisponible()).toBe(true);

    component.recargarDetalle();
    const recarga = httpMock.expectOne(urlDetalle(1));
    expect(recarga).not.toBe(anterior);

    paramMap$.next(convertToParamMap({ id: '2' }));
    fixture.detectChanges();

    expect(recarga.cancelled).toBe(true);
    expect(component.id()).toBe(2);
    expect(component.datosReales()).toBeNull();
    expect(component.cargandoDetalle()).toBe(true);

    const nueva = httpMock.expectOne(urlDetalle(2));
    nueva.flush(respuestaDetalle('Sumaq'));
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.datosReales()?.historia).toEqual(['Historia de Sumaq']);
    expect(component.apiDisponible()).toBe(true);
  });

  it('usa el respaldo y expone el error cuando la API falla', async () => {
    httpMock.expectOne(urlDetalle(1)).flush('fallo', { status: 500, statusText: 'Server Error' });
    httpMock.expectOne(urlDetalle(1)).flush('fallo', { status: 500, statusText: 'Server Error' });
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.datosReales()).toBeNull();
    expect(component.apiDisponible()).toBe(false);
    expect(component.usandoRespaldo()).toBe(true);
    expect(component.errorDetalle()).toContain('No se pudo cargar');
    expect(component.historia().length).toBeGreaterThan(0);
    expect(fixture.nativeElement.querySelector('[data-estado-detalle="error"]')).toBeTruthy();
    expect(
      fixture.nativeElement.querySelector('[data-estado-respaldo="true"] button')?.textContent,
    ).toContain('Reintentar');
    // Dos intentos como máximo: el automático se agotó y no hay polling.
    expect(httpMock.match(() => true).length).toBe(0);
  });

  it('reintenta una sola vez ante 5xx y muestra los datos reales', async () => {
    httpMock.expectOne(urlDetalle(1)).flush('fallo', { status: 503, statusText: 'Unavailable' });
    httpMock.expectOne(urlDetalle(1)).flush(respuestaDetalle('Chaska'));
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.apiDisponible()).toBe(true);
    expect(component.datosReales()?.historia).toEqual(['Historia de Chaska']);
    expect(fixture.nativeElement.querySelector('[data-estado-respaldo="true"]')).toBeNull();
    expect(httpMock.match(() => true).length).toBe(0);
  });

  it('no reintenta automáticamente ante HTTP 404', async () => {
    httpMock
      .expectOne(urlDetalle(1))
      .flush('no encontrado', { status: 404, statusText: 'Not Found' });
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.errorDetalle()).toContain('No se pudo cargar');
    expect(httpMock.match(() => true).length).toBe(0);
  });

  it('no reintenta automáticamente ante HTTP 400', async () => {
    httpMock
      .expectOne(urlDetalle(1))
      .flush('solicitud inválida', { status: 400, statusText: 'Bad Request' });
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.errorDetalle()).toContain('No se pudo cargar');
    expect(httpMock.match(() => true).length).toBe(0);
  });

  it('permite reintento manual tras agotar el automático', async () => {
    httpMock.expectOne(urlDetalle(1)).flush('fallo', { status: 500, statusText: 'Server Error' });
    httpMock.expectOne(urlDetalle(1)).flush('fallo', { status: 500, statusText: 'Server Error' });
    await fixture.whenStable();
    fixture.detectChanges();

    const boton = fixture.nativeElement.querySelector(
      '[data-estado-respaldo="true"] button',
    ) as HTMLButtonElement | null;
    expect(boton).toBeTruthy();
    const recargarInicial = vi.spyOn(initialDataStub, 'recargar');
    boton?.click();
    fixture.detectChanges();

    expect(recargarInicial).toHaveBeenCalledTimes(1);
    recargarInicial.mockRestore();
    httpMock.expectOne(urlDetalle(1)).flush(respuestaDetalle('Chaska'));
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.apiDisponible()).toBe(true);
    expect(component.errorDetalle()).toBeNull();
    expect(httpMock.match(() => true).length).toBe(0);
  });

  it('cancela la petición en curso al destruir el componente', () => {
    const peticion = httpMock.expectOne(urlDetalle(1));
    fixture.destroy();

    expect(peticion.cancelled).toBe(true);
    component.recargarDetalle();
    httpMock.expectNone(urlDetalle(1));
  });
});

describe('DetalleMascota en SSR', () => {
  let component: DetalleMascota;
  let fixture: ComponentFixture<DetalleMascota>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    const paramMap = convertToParamMap({ id: '1' });

    await TestBed.configureTestingModule({
      imports: [DetalleMascota],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: API },
        { provide: AuthService, useFactory: () => crearAuthStub() },
        { provide: InitialDataService, useValue: initialDataStub },
        { provide: PLATFORM_ID, useValue: 'server' },
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(paramMap),
            snapshot: { paramMap, queryParamMap: convertToParamMap({}) },
          },
        },
      ],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(DetalleMascota);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => httpMock.verify());

  it('no consulta la API en el servidor y renderiza con datos de respaldo', () => {
    httpMock.expectNone(urlDetalle(1));
    expect(component.datosReales()).toBeNull();
    expect(component.usandoRespaldo()).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Chaska');
  });
});

describe('DetalleMascota — rasgos individuales', () => {
  let component: DetalleMascota;
  let fixture: ComponentFixture<DetalleMascota>;
  let httpMock: HttpTestingController;
  let paramMap$: BehaviorSubject<ParamMap>;

  beforeEach(async () => {
    paramMap$ = new BehaviorSubject<ParamMap>(convertToParamMap({ id: '1' }));

    await TestBed.configureTestingModule({
      imports: [DetalleMascota],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: API },
        { provide: AuthService, useFactory: () => crearAuthStub() },
        { provide: InitialDataService, useValue: initialDataStub },
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: paramMap$,
            snapshot: {
              paramMap: convertToParamMap({ id: '1' }),
              queryParamMap: convertToParamMap({}),
            },
          },
        },
      ],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(DetalleMascota);
    component = fixture.componentInstance;
  });

  afterEach(() => httpMock.verify());

  it('muestra los 6 rasgos registrados de Chaska', async () => {
    httpMock.expectOne(urlDetalle(1)).flush(respuestaDetalle('Chaska'));
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.rasgos().length).toBe(6);
    expect(component.rasgos().map((r) => r.texto)).toContain(
      'Tolerante con gatos (prueba básica OK)',
    );
    expect(fixture.nativeElement.textContent).not.toContain(
      'Temperamento pendiente de evaluación',
    );
  });

  it('muestra el estado pendiente para Killa sin mezclar rasgos al cambiar de id', async () => {
    httpMock.expectOne(urlDetalle(1)).flush(respuestaDetalle('Chaska'));
    await fixture.whenStable();
    expect(component.rasgos().length).toBe(6);

    paramMap$.next(convertToParamMap({ id: '12' }));
    fixture.detectChanges();
    const peticion = httpMock.expectOne(urlDetalle(12));
    expect(component.rasgos()).toEqual([]);

    peticion.flush(respuestaDetalle('Killa'));
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.mascota()?.nombre).toBe('Killa');
    expect(component.rasgos()).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain(
      'Temperamento pendiente de evaluación',
    );
    expect(fixture.nativeElement.textContent).not.toContain('Tolerante con gatos');
  });

  it('prioriza los rasgos registrados que devuelve la API de detalle', async () => {
    const respuesta = respuestaDetalle('Killa');
    respuesta.mascota = {
      rasgos: [
        { icono: 'pets', texto: 'Rasgo registrado A', clase: 'chip', iconoClase: '' },
        {
          icono: 'home',
          texto: 'Rasgo registrado B',
          clase: 'chip',
          iconoClase: 'text-secondary',
        },
      ],
    };

    httpMock.expectOne(urlDetalle(1)).flush(respuesta);
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.rasgos().map((r) => r.texto)).toEqual([
      'Rasgo registrado A',
      'Rasgo registrado B',
    ]);
    expect(fixture.nativeElement.textContent).not.toContain(
      'Temperamento pendiente de evaluación',
    );
  });

  it('ignora entradas sin src y muestra el placeholder cuando no hay foto principal', async () => {
    httpMock.expectOne(urlDetalle(1)).flush(respuestaDetalle('Michi'));
    await fixture.whenStable();
    fixture.detectChanges();

    const respuesta = respuestaDetalle('Michi');
    respuesta.galeria = [
      { src: '', alt: 'Sin foto' },
      { src: '/michi-2.jpg', alt: 'Michi dos' },
    ];
    component.datosReales.set(respuesta);
    fixture.detectChanges();

    expect(component.fotos().map((f) => f.src)).toEqual(['/michi-2.jpg']);
    expect(fixture.nativeElement.querySelectorAll('[role="tab"]').length).toBe(0);

    component.datosReales.set({
      ...respuesta,
      galeria: [{ src: '', alt: 'Sin foto' }],
    });
    fixture.detectChanges();

    expect(component.fotos()).toEqual([]);
    expect(component.fotoPrincipal().src).toBe(FOTO_PLACEHOLDER);
    expect(fixture.nativeElement.querySelectorAll('[role="tab"]').length).toBe(0);
  });
});
