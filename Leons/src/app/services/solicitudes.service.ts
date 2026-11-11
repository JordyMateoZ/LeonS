import { isPlatformBrowser } from '@angular/common';
import { Injectable, PLATFORM_ID, computed, inject, signal } from '@angular/core';
import { Mascota } from '../data/mascotas.data';
import { Refugio } from '../data/refugios.data';
import { HEADER_SOLICITUD_ACTIVA, SOLICITUDES_DEMO, Solicitud } from '../data/solicitudes.data';

const STORAGE_KEY = 'leons.solicitudes.v1';
const STORAGE_VERSION = 1;

interface Persistencia {
  version: number;
  enviadas: Solicitud[];
  canceladas: number[];
}

export interface ResultadoSolicitud {
  creada: boolean;
  solicitud: Solicitud;
}

@Injectable({
  providedIn: 'root',
})
export class SolicitudesService {
  private readonly platformId = inject(PLATFORM_ID);

  /** Solicitudes creadas desde la ficha de una mascota. */
  private readonly enviadas = signal<Solicitud[]>([]);
  /** Ids cancelados por el usuario (incluye solicitudes demo). */
  private readonly canceladas = signal<ReadonlySet<number>>(new Set<number>());

  /** Registro completo: demo + enviadas, sin las canceladas. */
  readonly solicitudes = computed<Solicitud[]>(() =>
    [...[...this.enviadas()].reverse(), ...SOLICITUDES_DEMO].filter(
      (solicitud) => !this.canceladas().has(solicitud.id),
    ),
  );

  readonly total = computed(() => this.solicitudes().length);
  readonly activas = computed(
    () => this.solicitudes().filter((solicitud) => solicitud.estado === 'active').length,
  );
  readonly finalizadas = computed(
    () => this.solicitudes().filter((solicitud) => solicitud.estado === 'completed').length,
  );

  constructor() {
    this.cargar();
  }

  /** Evita duplicar una postulación activa para la misma mascota. */
  solicitudActivaPara(mascotaId: number): Solicitud | undefined {
    return this.solicitudes().find(
      (solicitud) => solicitud.fichaId === mascotaId && solicitud.estado === 'active',
    );
  }

  crearDesdeMascota(mascota: Mascota, refugio?: Refugio): ResultadoSolicitud {
    const existente = this.solicitudActivaPara(mascota.id);
    if (existente) {
      return { creada: false, solicitud: existente };
    }

    const id = this.siguienteId();
    const hoy = new Date();
    const fechaLarga = hoy.toLocaleDateString('es-PE', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
    const fechaCorta = hoy.toLocaleDateString('es-PE', { day: 'numeric', month: 'short' });
    const anio = hoy.getFullYear();
    const whatsapp = refugio?.whatsapp ? `https://wa.me/${refugio.whatsapp}` : undefined;

    const solicitud: Solicitud = {
      id,
      estado: 'active',
      nombre: mascota.nombre,
      fichaId: mascota.id,
      fotoSrc: mascota.foto,
      fotoAlt: mascota.alt,
      chipTexto: `${mascota.edadTexto} • ${mascota.sexo}`,
      chipClase: 'bg-surface-container text-on-surface-variant',
      refugio: mascota.refugio,
      lugar: mascota.lugar,
      exp: `#SOL-HYO-${anio}-${String(id).padStart(3, '0')}`,
      fechaTexto: `Enviada el ${fechaLarga}`,
      badgeTexto: 'En Revisión Inicial',
      badgeClase: 'bg-primary-fixed text-primary',
      puntoClase: 'bg-primary animate-pulse',
      pasoTexto: 'Paso 2 de 5',
      pasoTextoClase: 'text-primary',
      headerClase: HEADER_SOLICITUD_ACTIVA,
      iconoMini: 'pets',
      iconoMiniClase: 'bg-surface-container-lowest text-primary',
      paso: 2,
      barraClase: 'bg-primary',
      etapas: [
        { titulo: '1. Enviada', detalle: fechaCorta },
        { titulo: '2. En Revisión', detalle: 'Evaluando ficha' },
        { titulo: '3. Visita / Entrevista', detalle: 'Pendiente' },
        { titulo: '4. Aprobación', detalle: 'Pendiente' },
        { titulo: '5. Adopción Feliz', detalle: 'Pendiente' },
      ],
      tiempoRespuesta: '24 a 48 horas',
      whatsapp,
    };

    this.enviadas.update((lista) => [...lista, solicitud]);
    this.persistir();
    return { creada: true, solicitud };
  }

  cancelar(id: number) {
    const nuevo = new Set(this.canceladas());
    nuevo.add(id);
    this.canceladas.set(nuevo);
    this.persistir();
  }

  /** Restaura las solicitudes canceladas (usado por la vista de demostración). */
  restaurarCanceladas() {
    this.canceladas.set(new Set<number>());
    this.persistir();
  }

  private siguienteId(): number {
    const ids = [
      ...SOLICITUDES_DEMO.map((solicitud) => solicitud.id),
      ...this.enviadas().map((solicitud) => solicitud.id),
    ];
    return Math.max(0, ...ids) + 1;
  }

  private cargar() {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    try {
      const crudo = localStorage.getItem(STORAGE_KEY);
      if (!crudo) {
        return;
      }
      const datos = JSON.parse(crudo) as Partial<Persistencia>;
      if (Array.isArray(datos.enviadas)) {
        this.enviadas.set(datos.enviadas.filter((solicitud) => solicitud?.id > 0));
      }
      if (Array.isArray(datos.canceladas)) {
        this.canceladas.set(new Set(datos.canceladas.filter((id) => typeof id === 'number')));
      }
    } catch {
      // Si el almacenamiento está corrupto, la vista sigue funcionando con los datos demo.
    }
  }

  private persistir() {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    const datos: Persistencia = {
      version: STORAGE_VERSION,
      enviadas: this.enviadas(),
      canceladas: [...this.canceladas()],
    };

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(datos));
    } catch {
      // Sin almacenamiento disponible (modo privado o cuota llena), la sesión sigue en memoria.
    }
  }
}
