import { Injectable } from '@angular/core';
import { MASCOTAS, Mascota, Foto } from '../data/mascotas.data';
import { REFUGIOS, Refugio } from '../data/refugios.data';

@Injectable({
  providedIn: 'root',
})
export class MascotasService {
  readonly mascotas = MASCOTAS;
  readonly refugios = REFUGIOS;
  readonly total = MASCOTAS.length;

  porId(id: number): Mascota | undefined {
    return this.mascotas.find((m) => m.id === id);
  }

  destacadas(ids: number[]): Mascota[] {
    return ids
      .map((id) => this.porId(id))
      .filter((m): m is Mascota => m !== undefined);
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
