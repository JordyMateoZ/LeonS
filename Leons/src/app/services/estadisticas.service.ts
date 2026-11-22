import { Injectable, computed, inject } from '@angular/core';
import { InitialDataService } from '../core/data/initial-data.service';

export interface ImpactoReal {
  totalAdoptadas: number;
  totalRefugios: number;
  totalEnAcogida: number;
  totalDistritos: number;
  totalMascotas: number;
  totalPerros: number;
  totalGatos: number;
  adoptadasPorDistrito: Record<string, number>;
}

@Injectable({ providedIn: 'root' })
export class EstadisticasService {
  private readonly initialData = inject(InitialDataService);

  readonly impacto = computed<ImpactoReal | null>(() => {
    const raw = this.initialData.impacto() as Record<string, unknown> | null;
    if (!raw) {
      return null;
    }
    return {
      totalAdoptadas: Number(raw['totalAdoptadas'] ?? raw['total_adoptadas'] ?? 0),
      totalRefugios: Number(raw['totalRefugios'] ?? raw['total_refugios'] ?? 0),
      totalEnAcogida: Number(raw['totalEnAcogida'] ?? raw['total_en_acogida'] ?? 0),
      totalDistritos: Number(raw['totalDistritos'] ?? raw['total_distritos'] ?? 0),
      totalMascotas: Number(raw['totalMascotas'] ?? raw['total_mascotas'] ?? 0),
      totalPerros: Number(raw['totalPerros'] ?? raw['total_perros'] ?? 0),
      totalGatos: Number(raw['totalGatos'] ?? raw['total_gatos'] ?? 0),
      adoptadasPorDistrito: (raw['adoptadasPorDistrito'] ?? raw['adoptadas_por_distrito'] ?? {}) as Record<string, number>,
    };
  });
}
