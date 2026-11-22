import { Injectable, computed, inject } from '@angular/core';
import { InitialDataService } from '../core/data/initial-data.service';
import { FAQS, PASOS_ADOPCION, PASOS_REFUGIO, PreguntaFrecuente, Paso } from '../data/contenido.data';
import { REQUISITOS, Requisito } from '../data/detalle.data';

@Injectable({ providedIn: 'root' })
export class ContenidoService {
  private readonly initialData = inject(InitialDataService);

  private readonly _pasosAdopcion = computed<Paso[]>(() => this.extraer('pasosAdopcion', PASOS_ADOPCION));
  private readonly _pasosRefugio = computed<Paso[]>(() => this.extraer('pasosRefugio', PASOS_REFUGIO));
  private readonly _faqs = computed<PreguntaFrecuente[]>(() => this.extraer('faqs', FAQS));
  private readonly _requisitos = computed<Requisito[]>(() => this.extraer('requisitos', REQUISITOS));

  get pasosAdopcion(): Paso[] {
    return this._pasosAdopcion();
  }

  get pasosRefugio(): Paso[] {
    return this._pasosRefugio();
  }

  get faqs(): PreguntaFrecuente[] {
    return this._faqs();
  }

  get requisitos(): Requisito[] {
    return this._requisitos();
  }

  private extraer<T>(clave: string, respaldo: T[]): T[] {
    const contenido = this.initialData.contenido() as Record<string, unknown> | null;
    const lista = contenido?.[clave];
    if (Array.isArray(lista) && lista.length > 0) {
      return lista.map((item) => this.mapear<T>(item as Record<string, unknown>, clave));
    }
    return [...respaldo];
  }

  private mapear<T>(item: Record<string, unknown>, clave: string): T {
    if (clave === 'faqs') {
      return { pregunta: String(item['pregunta'] ?? ''), respuesta: String(item['respuesta'] ?? '') } as T;
    }
    if (clave === 'requisitos') {
      return { icono: String(item['icono'] ?? ''), titulo: String(item['titulo'] ?? ''), texto: String(item['texto'] ?? '') } as T;
    }
    return {
      icono: String(item['icono'] ?? ''),
      titulo: String(item['titulo'] ?? ''),
      texto: String(item['texto'] ?? ''),
      nota: String(item['nota'] ?? ''),
    } as T;
  }
}
