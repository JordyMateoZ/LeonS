import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { InitialDataService } from '../core/data/initial-data.service';
import { MascotasService } from './mascotas.service';
import { RefugiosService } from './refugios.service';

/**
 * Reproducción controlada de "datos obsoletos": cuando FastAPI vuelve a estar
 * disponible, InitialDataService actualiza sus signals, pero los servicios de
 * lectura copiaron arreglos en el constructor.
 */
describe('Servicios de lectura — recuperación sin recarga (reproducción Fase 5.5.5)', () => {
  const initial = {
    cargado: signal(true),
    mascotas: signal<unknown[]>([]),
    refugios: signal<unknown[]>([]),
    contenido: signal<unknown | null>(null),
    impacto: signal<unknown | null>(null),
    cargar: async () => undefined,
  };

  beforeEach(() => {
    initial.mascotas.set([{ id: 101, nombre: 'Antes', estado: 'disponible', refugioId: 'r1' }]);
    initial.refugios.set([{ id: 'r1', nombre: 'Antes' }]);

    TestBed.configureTestingModule({
      providers: [{ provide: InitialDataService, useValue: initial }],
    });
  });

  it('MascotasService refleja los datos recuperados sin recrear el servicio', () => {
    const servicio = TestBed.inject(MascotasService);
    const copiaDelComponente = servicio.mascotas;
    expect(servicio.mascotas.map((m) => m.id)).toEqual([101]);

    initial.mascotas.set([
      { id: 102, nombre: 'Después A', estado: 'disponible', refugioId: 'r1' },
      { id: 103, nombre: 'Después B', estado: 'disponible', refugioId: 'r1' },
    ]);
    TestBed.flushEffects();

    expect(servicio.mascotas.map((m) => m.id)).toEqual([102, 103]);
    expect(servicio.total).toBe(2);
    expect(servicio.totalRegistradas).toBe(2);
    // Los componentes que copiaron el arreglo en su constructor también lo ven.
    expect(copiaDelComponente).toBe(servicio.mascotas);
    expect(copiaDelComponente.map((m) => m.id)).toEqual([102, 103]);
  });

  it('RefugiosService refleja los datos recuperados sin recrear el servicio', () => {
    const servicio = TestBed.inject(RefugiosService);
    const copiaDelComponente = servicio.refugios;
    expect(servicio.refugios.map((r) => r.id)).toEqual(['r1']);

    initial.refugios.set([
      { id: 'r1', nombre: 'Después' },
      { id: 'r2', nombre: 'Nuevo' },
    ]);
    TestBed.flushEffects();

    expect(servicio.refugios.map((r) => r.id)).toEqual(['r1', 'r2']);
    expect(copiaDelComponente).toBe(servicio.refugios);
    expect(copiaDelComponente.map((r) => r.id)).toEqual(['r1', 'r2']);
  });

  it('los contadores derivados de refugios se actualizan con la recuperación', () => {
    const mascotas = TestBed.inject(MascotasService);
    expect(mascotas.totalAdoptadas).toBe(0);

    initial.refugios.set([
      { id: 'r1', nombre: 'Después', adoptadas: 7, enAcogida: 2, distrito: 'El Tambo' },
    ]);
    TestBed.flushEffects();

    expect(mascotas.totalAdoptadas).toBe(7);
    expect(mascotas.totalEnAcogida).toBe(2);
    expect(mascotas.totalDistritos).toBe(1);
  });
});
