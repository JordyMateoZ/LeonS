import { PLATFORM_ID, TransferState, makeStateKey } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  TestRequest,
  provideHttpClientTesting,
} from '@angular/common/http/testing';

import { API_BASE_URL } from '../api/api.config';
import { InitialDataService } from './initial-data.service';

const API = 'http://localhost:8000/api/v1';
const CLAVE = makeStateKey<{
  mascotas: unknown[];
  refugios: unknown[];
  contenido: unknown | null;
  impacto: unknown | null;
}>('leons.initial');

const MASCOTA = { id: 101, nombre: 'Recuperada' };
const REFUGIO = { id: 'recuperado', nombre: 'Refugio recuperado' };

let peticionesVistas = 0;

function ronda(httpMock: HttpTestingController): TestRequest[] {
  const actuales = httpMock.match(() => true);
  peticionesVistas += actuales.length;
  return actuales;
}

function responderBien(peticiones: TestRequest[]): void {
  for (const peticion of peticiones) {
    if (peticion.cancelled) {
      continue;
    }
    if (peticion.request.url.includes('/mascotas')) {
      peticion.flush({ items: [MASCOTA] });
    } else if (peticion.request.url.includes('/refugios')) {
      peticion.flush([REFUGIO]);
    } else if (peticion.request.url.includes('/contenido')) {
      peticion.flush({ faqs: [] });
    } else {
      peticion.flush({ totalAdoptadas: 702 });
    }
  }
}

function fallar(peticiones: TestRequest[], status: number): void {
  for (const peticion of peticiones) {
    peticion.flush('fallo simulado', {
      status,
      statusText: status >= 500 ? 'Server Error' : 'Bad Request',
    });
  }
}

async function microtareas(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

function drenar(httpMock: HttpTestingController): void {
  for (let intento = 0; intento < 4; intento++) {
    const pendientes = httpMock.match(() => true);
    if (pendientes.length === 0) {
      break;
    }
    responderBien(pendientes);
  }
  httpMock.verify();
}

function configurar(plataforma: string) {
  TestBed.configureTestingModule({
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      { provide: PLATFORM_ID, useValue: plataforma },
      { provide: API_BASE_URL, useValue: API },
      { provide: TransferState, useValue: new TransferState() },
    ],
  });
}

describe('InitialDataService — resiliencia (Fase 5.5.5)', () => {
  let servicio: InitialDataService;
  let httpMock: HttpTestingController;
  let transferState: TransferState;

  beforeEach(() => {
    peticionesVistas = 0;
    configurar('browser');
    servicio = TestBed.inject(InitialDataService);
    httpMock = TestBed.inject(HttpTestingController);
    transferState = TestBed.inject(TransferState);
  });

  afterEach(() => drenar(httpMock));

  it('reutiliza TransferState sin repetir peticiones en hidratación', async () => {
    transferState.set(CLAVE, {
      mascotas: [MASCOTA],
      refugios: [REFUGIO],
      contenido: null,
      impacto: null,
    });

    await servicio.cargar();

    expect(servicio.mascotas()).toEqual([MASCOTA]);
    expect(servicio.refugios()).toEqual([REFUGIO]);
    expect(servicio.cargado()).toBe(true);
    expect(servicio.origen()).toBe('transferencia');
    expect(transferState.hasKey(CLAVE)).toBe(false);
    expect(ronda(httpMock).length).toBe(0);
  });

  it('no relanza peticiones al llamar cargar() dos veces (idempotencia)', async () => {
    transferState.set(CLAVE, {
      mascotas: [MASCOTA],
      refugios: [REFUGIO],
      contenido: null,
      impacto: null,
    });

    await servicio.cargar();
    await servicio.cargar();
    await servicio.cargar();

    expect(ronda(httpMock).length).toBe(0);
  });

  it('dedupica llamadas concurrentes antes de que exista TransferState', async () => {
    const primera = servicio.cargar();
    const segunda = servicio.cargar();
    const primeras = ronda(httpMock);
    expect(primeras.length).toBe(4);

    responderBien(primeras);
    await Promise.all([primera, segunda]);

    expect(peticionesVistas).toBe(4);
    expect(servicio.origen()).toBe('real');
    expect(servicio.cargado()).toBe(true);
  });

  it('conserva las respuestas válidas cuando falla un endpoint con 4xx', async () => {
    const promesa = servicio.cargar();
    const primeras = ronda(httpMock);
    expect(primeras.length).toBe(4);

    for (const peticion of primeras) {
      if (peticion.request.url.includes('/mascotas')) {
        peticion.flush({ items: [MASCOTA] });
      } else {
        peticion.flush('fallo simulado', { status: 400, statusText: 'Bad Request' });
      }
    }
    await promesa;

    expect(servicio.mascotas()).toEqual([MASCOTA]);
    expect(servicio.cargado()).toBe(false);
    expect(servicio.parcial()).toBe(true);
    expect(servicio.origen()).toBe('parcial');
    expect(ronda(httpMock).length).toBe(0);
  });

  it('reintenta una sola vez ante 5xx y reporta conexión real si recupera', async () => {
    const promesa = servicio.cargar();
    fallar(ronda(httpMock), 500);
    await microtareas();

    const reintentos = ronda(httpMock);
    expect(reintentos.length).toBe(4);
    responderBien(reintentos);
    await promesa;

    expect(peticionesVistas).toBe(8);
    expect(servicio.origen()).toBe('real');
    expect(servicio.cargado()).toBe(true);
    expect(servicio.parcial()).toBe(false);
    expect(ronda(httpMock).length).toBe(0);
  });

  it('no reintenta automáticamente respuestas 4xx', async () => {
    const promesa = servicio.cargar();
    fallar(ronda(httpMock), 404);
    await promesa;

    expect(peticionesVistas).toBe(4);
    expect(servicio.origen()).toBe('error');
    expect(servicio.cargado()).toBe(false);
    expect(servicio.parcial()).toBe(false);
  });

  it('permite reintento manual tras agotar el automático', async () => {
    const primera = servicio.cargar();
    fallar(ronda(httpMock), 500);
    await microtareas();
    fallar(ronda(httpMock), 500);
    await microtareas();
    await primera;
    expect(servicio.origen()).toBe('error');
    expect(peticionesVistas).toBe(8);

    const segunda = servicio.recargar();
    responderBien(ronda(httpMock));
    await segunda;

    expect(peticionesVistas).toBe(12);
    expect(servicio.origen()).toBe('real');
    expect(servicio.mascotas()).toEqual([MASCOTA]);
  });

  it('no deja que una respuesta antigua sobrescriba la recuperación', async () => {
    const promesa = servicio.cargar();
    const primeras = ronda(httpMock);
    responderBien(primeras);
    await promesa;
    expect(servicio.origen()).toBe('real');

    // Una segunda llamada idempotente no genera nuevas peticiones ni datos viejos.
    await servicio.cargar();
    expect(ronda(httpMock).length).toBe(0);
    expect(servicio.mascotas()).toEqual([MASCOTA]);
  });
});

describe('InitialDataService en SSR', () => {
  let servicio: InitialDataService;
  let httpMock: HttpTestingController;
  let transferState: TransferState;

  beforeEach(() => {
    peticionesVistas = 0;
    configurar('server');
    servicio = TestBed.inject(InitialDataService);
    httpMock = TestBed.inject(HttpTestingController);
    transferState = TestBed.inject(TransferState);
  });

  afterEach(() => drenar(httpMock));

  it('guarda en TransferState y no inicia reintentos durante el renderizado', async () => {
    const promesa = servicio.cargar();
    responderBien(ronda(httpMock));
    await promesa;

    expect(peticionesVistas).toBe(4);
    expect(transferState.hasKey(CLAVE)).toBe(true);
    expect(
      transferState.get(CLAVE, { mascotas: [], refugios: [], contenido: null, impacto: null })
        .mascotas,
    ).toEqual([MASCOTA]);
    expect(servicio.origen()).toBe('real');
  });
});
