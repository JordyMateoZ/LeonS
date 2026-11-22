import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { InitialDataService } from '../core/data/initial-data.service';
import { REFUGIOS, Refugio } from '../data/refugios.data';

/**
 * Servicio de refugios. Mantiene la misma forma de consumo que el resto del
 * proyecto (arreglo síncrono) para no romper los componentes existentes,
 * pero la fuente de datos pasa a ser la carga inicial real (InitialDataService)
 * cuando el backend está disponible, con respaldo en las constantes simuladas.
 *
 * El arreglo devuelto mantiene su referencia y se actualiza en sitio: así los
 * componentes que lo copiaron en su constructor también ven la recuperación.
 */
@Injectable({ providedIn: 'root' })
export class RefugiosService {
  private readonly initialData = inject(InitialDataService);
  private readonly _version = signal(0);
  private readonly _refugiosCache: Refugio[] = [];

  private readonly _calculados = computed<Refugio[]>(() => {
    const reales = this.initialData.refugios();
    if (Array.isArray(reales) && reales.length > 0) {
      return reales.map((item) => this.mapear(item as Record<string, unknown>));
    }
    return [...REFUGIOS];
  });

  constructor() {
    this.aplicar(this._calculados());
    effect(() => this.aplicar(this._calculados()));
  }

  get refugios(): Refugio[] {
    this._version();
    return this._refugiosCache;
  }

  porId(id: string): Refugio | undefined {
    return this.refugios.find((refugio) => refugio.id === id);
  }

  private aplicar(refugios: Refugio[]): void {
    this._refugiosCache.splice(0, this._refugiosCache.length, ...refugios);
    this._version.update((version) => version + 1);
  }

  private mapear(item: Record<string, unknown>): Refugio {
    return {
      id: String(item['id'] ?? ''),
      nombre: String(item['nombre'] ?? ''),
      distrito: String(item['distrito'] ?? ''),
      desde: Number(item['desde'] ?? 0),
      descripcion: String(item['descripcion'] ?? ''),
      contacto: String(item['contacto'] ?? ''),
      cargo: String(item['cargo'] ?? ''),
      telefono: String(item['telefono'] ?? ''),
      whatsapp: String(item['whatsapp'] ?? ''),
      logo: (item['logo'] as string | null | undefined) ?? undefined,
      adoptadas: Number(item['adoptadas'] ?? 0),
      enAcogida: Number(item['enAcogida'] ?? item['en_acogida'] ?? 0),
      verificado: Boolean(item['verificado']),
      especies: (item['especies'] as ('perro' | 'gato')[] | undefined) ?? [],
      direccion: String(item['direccion'] ?? ''),
      tipo: (item['tipo'] as 'constituido' | 'independiente') ?? 'constituido',
    };
  }
}
