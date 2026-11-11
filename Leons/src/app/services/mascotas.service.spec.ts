import { TestBed } from '@angular/core/testing';
import { MASCOTAS } from '../data/mascotas.data';
import { REFUGIOS } from '../data/refugios.data';
import { MascotasService } from './mascotas.service';

describe('MascotasService', () => {
  let service: MascotasService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MascotasService);
  });

  it('should expose the 9 real refugios and the network totals', () => {
    expect(service.refugios.length).toBe(9);
    expect(service.totalAdoptadas).toBe(702);
    expect(service.totalEnAcogida).toBe(96);
    expect(service.totalDistritos).toBe(6);
  });

  it('should keep unique ids and ficha codes (no duplicated seed rows)', () => {
    expect(new Set(MASCOTAS.map((m) => m.id)).size).toBe(MASCOTAS.length);
    expect(new Set(MASCOTAS.map((m) => m.fichaId)).size).toBe(MASCOTAS.length);
    expect(new Set(REFUGIOS.map((r) => r.id)).size).toBe(REFUGIOS.length);
  });

  it('should expose only available pets in the public catalogue', () => {
    expect(service.totalRegistradas).toBe(16);
    expect(service.mascotas.length).toBe(12);
    expect(service.mascotas.every((m) => m.estado === 'disponible')).toBe(true);
    expect(service.total).toBe(12);
  });

  it('should find refugios by their original string id', () => {
    expect(service.refugioPorId('huellitas-wanka')?.nombre).toBe('Albergue Huellitas Wanka');
    expect(service.refugioPorId('mantaro-felino')?.distrito).toBe('Huancayo Centro');
    expect(service.refugioPorId('no-existe')).toBeUndefined();
  });

  it('should associate every pet with an existing refugio and cover all refugios', () => {
    for (const refugio of REFUGIOS) {
      expect(service.mascotasDeRefugio(refugio.id).length).toBeGreaterThan(0);
    }
    expect(MASCOTAS.every((m) => service.refugioPorId(m.refugioId) !== undefined)).toBe(true);
  });

  it('should keep pets isolated between refugios', () => {
    const huellitas = new Set(service.mascotasDeRefugio('huellitas-wanka').map((m) => m.id));
    const sanRoque = service.mascotasDeRefugio('hogar-san-roque').map((m) => m.id);

    expect(huellitas.size).toBe(2);
    expect(sanRoque.length).toBe(2);
    expect(sanRoque.some((id) => huellitas.has(id))).toBe(false);
  });

  it('should report disponible, adoptada and en_acogida states', () => {
    const estados = new Set(MASCOTAS.map((m) => m.estado));
    expect(estados).toEqual(new Set(['disponible', 'adoptada', 'en_acogida']));

    const resumen = service.resumenDeRefugio('amigos-4-patas');
    expect(resumen.total).toBe(3);
    expect(resumen.disponibles).toBe(1);
    expect(resumen.adoptadas).toBe(1);
    expect(resumen.enAcogida).toBe(1);
  });

  it('should calculate each refugio summary from its own pets', () => {
    for (const refugio of REFUGIOS) {
      const resumen = service.resumenDeRefugio(refugio.id);
      expect(resumen.total).toBe(resumen.disponibles + resumen.adoptadas + resumen.enAcogida);
      expect(resumen.disponibles).toBe(service.mascotasDisponiblesDeRefugio(refugio.id).length);
    }
  });
});
