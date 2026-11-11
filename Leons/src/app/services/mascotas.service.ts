import { Injectable } from '@angular/core';
import { ESTADOS_MASCOTA, EstadoMascota, Foto, MASCOTAS, Mascota } from '../data/mascotas.data';
import { REFUGIOS, Refugio } from '../data/refugios.data';

export interface ResumenRefugio {
  total: number;
  disponibles: number;
  adoptadas: number;
  enAcogida: number;
}

@Injectable({
  providedIn: 'root',
})
export class MascotasService {
  /** Registro completo: incluye mascotas disponibles, adoptadas y en acogida. */
  readonly todas = MASCOTAS;
  readonly refugios = REFUGIOS;

  /** Mascotas visibles en el catálogo público (solo estado disponible). */
  readonly mascotas = MASCOTAS.filter((m) => m.estado === 'disponible');
  readonly total = this.mascotas.length;
  readonly totalRegistradas = MASCOTAS.length;

  readonly totalAdoptadas = REFUGIOS.reduce((total, refugio) => total + refugio.adoptadas, 0);
  readonly totalEnAcogida = REFUGIOS.reduce((total, refugio) => total + refugio.enAcogida, 0);
  readonly totalDistritos = new Set(REFUGIOS.map((refugio) => refugio.distrito)).size;

  porId(id: number): Mascota | undefined {
    return this.todas.find((m) => m.id === id);
  }

  refugioPorId(id: string): Refugio | undefined {
    return this.refugios.find((refugio) => refugio.id === id);
  }

  /** Todas las mascotas asociadas a un refugio, sin importar su estado. */
  mascotasDeRefugio(refugioId: string): Mascota[] {
    return this.todas.filter((mascota) => mascota.refugioId === refugioId);
  }

  /** Solo las mascotas del refugio que pueden adoptarse hoy. */
  mascotasDisponiblesDeRefugio(refugioId: string): Mascota[] {
    return this.mascotas.filter((mascota) => mascota.refugioId === refugioId);
  }

  resumenDeRefugio(refugioId: string): ResumenRefugio {
    const mascotas = this.mascotasDeRefugio(refugioId);
    const contar = (estado: EstadoMascota) =>
      mascotas.filter((mascota) => mascota.estado === estado).length;

    return {
      total: mascotas.length,
      disponibles: contar('disponible'),
      adoptadas: contar('adoptada'),
      enAcogida: contar('en_acogida'),
    };
  }

  estadoDe(mascota: Mascota) {
    return ESTADOS_MASCOTA[mascota.estado];
  }

  destacadas(ids: number[]): Mascota[] {
    return ids.map((id) => this.porId(id)).filter((m): m is Mascota => m !== undefined);
  }

  refugioDe(m: Mascota): Refugio {
    return this.refugios.find((r) => r.id === m.refugioId) ?? this.refugios[0];
  }

  galeriaDe(m: Mascota): Foto[] {
    return m.galeria ?? [{ src: m.foto, alt: m.alt }];
  }

  similares(m: Mascota, limite = 3): Mascota[] {
    const puntaje = (otra: Mascota): number =>
      (otra.especie === m.especie ? 2 : 0) + (otra.distrito === m.distrito ? 1 : 0);

    return this.mascotas
      .filter((otra) => otra.id !== m.id)
      .sort((a, b) => puntaje(b) - puntaje(a))
      .slice(0, limite);
  }
}
