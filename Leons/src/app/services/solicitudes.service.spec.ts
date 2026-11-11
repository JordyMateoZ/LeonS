import { TestBed } from '@angular/core/testing';
import { MASCOTAS } from '../data/mascotas.data';
import { REFUGIOS } from '../data/refugios.data';
import { SolicitudesService } from './solicitudes.service';

const STORAGE_KEY = 'leons.solicitudes.v1';

describe('SolicitudesService', () => {
  let service: SolicitudesService;

  beforeEach(() => {
    localStorage.removeItem(STORAGE_KEY);
    TestBed.configureTestingModule({});
    service = TestBed.inject(SolicitudesService);
  });

  afterEach(() => {
    localStorage.removeItem(STORAGE_KEY);
  });

  it('should expose the three demo requests', () => {
    expect(service.total()).toBe(3);
    expect(service.activas()).toBe(2);
    expect(service.finalizadas()).toBe(1);
    expect(service.solicitudes().map((s) => s.nombre)).toEqual(['Chaska', 'Inti', 'Wanka']);
  });

  it('should create a request from a pet detail', () => {
    const sumaq = MASCOTAS.find((m) => m.id === 4)!;
    const refugio = REFUGIOS.find((r) => r.id === 'red-animalista-wanka')!;
    const resultado = service.crearDesdeMascota(sumaq, refugio);

    expect(resultado.creada).toBe(true);
    expect(resultado.solicitud.nombre).toBe('Sumaq');
    expect(resultado.solicitud.fichaId).toBe(4);
    expect(resultado.solicitud.refugio).toBe('Red Animalista Wanka');
    expect(resultado.solicitud.estado).toBe('active');
    expect(resultado.solicitud.paso).toBe(2);
    expect(resultado.solicitud.etapas.length).toBe(5);
    expect(service.total()).toBe(4);
    expect(service.activas()).toBe(3);
  });

  it('should not duplicate an active request for the same pet', () => {
    const chaska = MASCOTAS.find((m) => m.id === 1)!;
    const resultado = service.crearDesdeMascota(chaska);

    expect(resultado.creada).toBe(false);
    expect(resultado.solicitud.id).toBe(1);
    expect(service.total()).toBe(3);

    const sumaq = MASCOTAS.find((m) => m.id === 4)!;
    expect(service.crearDesdeMascota(sumaq).creada).toBe(true);
    expect(service.crearDesdeMascota(sumaq).creada).toBe(false);
    expect(service.total()).toBe(4);
  });

  it('should cancel a request and update the counters', () => {
    service.cancelar(2);

    expect(service.total()).toBe(2);
    expect(service.activas()).toBe(1);
    expect(service.solicitudes().map((s) => s.nombre)).toEqual(['Chaska', 'Wanka']);
  });

  it('should restore cancelled requests for the demo view', () => {
    service.cancelar(2);
    service.restaurarCanceladas();

    expect(service.total()).toBe(3);
    expect(service.activas()).toBe(2);
  });

  it('should persist created requests and cancellations in localStorage', () => {
    const sumaq = MASCOTAS.find((m) => m.id === 4)!;
    service.crearDesdeMascota(sumaq);
    service.cancelar(2);

    const guardado = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}');
    expect(guardado.version).toBe(1);
    expect(guardado.enviadas.length).toBe(1);
    expect(guardado.enviadas[0].nombre).toBe('Sumaq');
    expect(guardado.canceladas).toContain(2);

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({});
    const recargado = TestBed.inject(SolicitudesService);

    expect(recargado.total()).toBe(3);
    expect(recargado.solicitudes().map((s) => s.nombre)).toContain('Sumaq');
    expect(recargado.solicitudes().map((s) => s.nombre)).not.toContain('Inti');
  });
});
