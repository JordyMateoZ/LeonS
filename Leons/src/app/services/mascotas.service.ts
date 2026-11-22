import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { ESTADOS_MASCOTA, EstadoMascota, Foto, MASCOTAS, Mascota, Rasgo, SaludItem } from '../data/mascotas.data';
import { Refugio } from '../data/refugios.data';
import { InitialDataService } from '../core/data/initial-data.service';
import { RefugiosService } from './refugios.service';

export interface ResumenRefugio {
  total: number;
  disponibles: number;
  adoptadas: number;
  enAcogida: number;
}

/**
 * Servicio de mascotas.
 *
 * Mantiene la API pública síncrona existente (arreglos y métodos) para no
 * romper los componentes, pero la fuente de datos pasa a ser la carga inicial
 * real (InitialDataService, alimentada por la API y TransferState) cuando el
 * backend está disponible, con respaldo en las constantes simuladas.
 *
 * Los arreglos conservan su referencia y se actualizan en sitio cuando la API
 * vuelve a estar disponible; los contadores son getters derivados.
 */
@Injectable({
  providedIn: 'root',
})
export class MascotasService {
  private readonly initialData = inject(InitialDataService);
  private readonly refugiosService = inject(RefugiosService);

  private readonly _version = signal(0);
  private readonly _todasCache: Mascota[] = [];
  private readonly _visiblesCache: Mascota[] = [];

  private readonly _calculadas = computed<Mascota[]>(() => {
    const reales = this.initialData.mascotas();
    if (Array.isArray(reales) && reales.length > 0) {
      return reales.map((item) => this.mapear(item as Record<string, unknown>));
    }
    return [...MASCOTAS];
  });

  constructor() {
    this.aplicar(this._calculadas());
    effect(() => this.aplicar(this._calculadas()));
  }

  /** Registro completo: incluye mascotas disponibles, adoptadas y en acogida. */
  get todas(): Mascota[] {
    this._version();
    return this._todasCache;
  }

  /** Mascotas visibles en el catálogo público (solo estado disponible). */
  get mascotas(): Mascota[] {
    this._version();
    return this._visiblesCache;
  }

  get refugios(): Refugio[] {
    return this.refugiosService.refugios;
  }

  get total(): number {
    return this.mascotas.length;
  }

  get totalRegistradas(): number {
    return this.todas.length;
  }

  get totalAdoptadas(): number {
    return this.refugios.reduce((total, refugio) => total + refugio.adoptadas, 0);
  }

  get totalEnAcogida(): number {
    return this.refugios.reduce((total, refugio) => total + refugio.enAcogida, 0);
  }

  get totalDistritos(): number {
    return new Set(this.refugios.map((refugio) => refugio.distrito)).size;
  }

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

  private aplicar(todas: Mascota[]): void {
    this._todasCache.splice(0, this._todasCache.length, ...todas);
    const visibles = todas.filter((mascota) => mascota.estado === 'disponible');
    this._visiblesCache.splice(0, this._visiblesCache.length, ...visibles);
    this._version.update((version) => version + 1);
  }

  private mapear(item: Record<string, unknown>): Mascota {
    const salud = Array.isArray(item['salud'])
      ? (item['salud'] as { texto: string; ok: boolean }[]).map(
          (s): SaludItem => ({ texto: s.texto, ok: s.ok }),
        )
      : [];
    const galeria = Array.isArray(item['galeria'])
      ? (item['galeria'] as { src: string; alt: string }[]).map(
          (f): Foto => ({ src: f.src, alt: f.alt }),
        )
      : undefined;
    const rasgos = Array.isArray(item['rasgos'])
      ? (item['rasgos'] as { icono: string; texto: string; clase: string; iconoClase?: string }[]).map(
          (r): Rasgo => ({
            icono: r.icono,
            texto: r.texto,
            clase: r.clase,
            iconoClase: r.iconoClase ?? '',
          }),
        )
      : undefined;

    return {
      id: Number(item['id']),
      nombre: String(item['nombre'] ?? ''),
      nombreCorto: String(item['nombreCorto'] ?? item['nombre'] ?? ''),
      especie: (item['especie'] as 'perro' | 'gato') ?? 'perro',
      sexo: (item['sexo'] as 'Macho' | 'Hembra') ?? 'Macho',
      generoTexto: String(item['generoTexto'] ?? ''),
      badgeClase: String(item['badgeClase'] ?? ''),
      raza: String(item['raza'] ?? ''),
      edadTexto: String(item['edadTexto'] ?? ''),
      edadAnios: Number(item['edadAnios'] ?? 0),
      tamano: (item['tamano'] as 'Pequeño' | 'Mediano' | 'Grande') ?? 'Mediano',
      tamanoTexto: String(item['tamanoTexto'] ?? ''),
      distrito: String(item['distrito'] ?? ''),
      lugar: String(item['lugar'] ?? ''),
      foto: String(item['foto'] ?? ''),
      alt: String(item['alt'] ?? ''),
      descripcion: String(item['descripcion'] ?? ''),
      etiqueta: String(item['etiqueta'] ?? ''),
      etiquetaIcono: String(item['etiquetaIcono'] ?? 'pets'),
      etiquetaClase: String(item['etiquetaClase'] ?? ''),
      salud,
      esterilizado: Boolean(item['esterilizado']),
      vacunado: Boolean(item['vacunado']),
      urgente: Boolean(item['urgente']),
      refugio: String(item['refugio'] ?? ''),
      refugioId: String(item['refugioId'] ?? ''),
      energia: String(item['energia'] ?? ''),
      fichaId: String(item['fichaId'] ?? ''),
      actualizado: String(item['actualizado'] ?? ''),
      estado: (item['estado'] as EstadoMascota) ?? 'disponible',
      galeria,
      rasgos,
    };
  }
}
