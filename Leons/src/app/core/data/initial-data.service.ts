import { HttpErrorResponse, HttpClient } from '@angular/common/http';
import { isPlatformBrowser } from '@angular/common';
import {
  Injectable,
  PLATFORM_ID,
  TransferState,
  inject,
  makeStateKey,
  signal,
} from '@angular/core';
import { firstValueFrom, timeout } from 'rxjs';

import { API_BASE_URL } from '../api/api.config';
import { ApiError } from '../api/api-error';

interface DatosIniciales {
  mascotas: unknown[];
  refugios: unknown[];
  contenido: unknown | null;
  impacto: unknown | null;
}

export type OrigenDatosIniciales = 'inicial' | 'transferencia' | 'real' | 'parcial' | 'error';

const CLAVE_ESTADO = makeStateKey<DatosIniciales>('leons.initial');
const TIEMPO_ESPERA_MS = 3000;
const VACIO: DatosIniciales = { mascotas: [], refugios: [], contenido: null, impacto: null };

/** 4xx no se reintenta; 5xx, red y timeout sí (una sola vez). */
function esTransitorio(error: unknown): boolean {
  if (error instanceof HttpErrorResponse || error instanceof ApiError) {
    return error.status === 0 || error.status >= 500;
  }
  return true;
}

/**
 * Prepara la carga inicial de datos compartidos entre SSR e hidratación.
 *
 * - En el servidor: consulta la API y guarda el resultado en `TransferState`
 *   para que el navegador no repita la petición al hidratar.
 * - En el navegador: si `TransferState` ya trae los datos, los reutiliza y
 *   evita la petición duplicada; si no, consulta la API.
 *
 * No lanza en caso de error: la aplicación sigue funcionando con los datos
 * simulados. Expone `origen`, `error` y `parcial` para que esos datos no se
 * presenten como registros verificados de SQL Server.
 */
@Injectable({ providedIn: 'root' })
export class InitialDataService {
  private readonly http = inject(HttpClient);
  private readonly platformId = inject(PLATFORM_ID);
  private readonly transferState = inject(TransferState);
  private readonly baseUrl = inject(API_BASE_URL);

  private inicializado = false;
  private enVuelo: Promise<void> | null = null;

  readonly cargado = signal(false);
  readonly parcial = signal(false);
  readonly origen = signal<OrigenDatosIniciales>('inicial');
  readonly error = signal<string | null>(null);
  readonly mascotas = signal<unknown[]>([]);
  readonly refugios = signal<unknown[]>([]);
  readonly contenido = signal<unknown | null>(null);
  readonly impacto = signal<unknown | null>(null);

  /** Carga inicial idempotente: varias llamadas simultáneas comparten la misma promesa. */
  cargar(): Promise<void> {
    if (this.enVuelo) {
      return this.enVuelo;
    }
    if (this.inicializado) {
      return Promise.resolve();
    }

    const esNavegador = isPlatformBrowser(this.platformId);

    // Producción sin URL configurada: no se contacta al backend ni se simula éxito.
    if (this.baseUrl.includes('REPLACE_WITH')) {
      this.origen.set('error');
      this.error.set('API no configurada; se muestran datos de respaldo.');
      return Promise.resolve();
    }

    if (esNavegador && this.transferState.hasKey(CLAVE_ESTADO)) {
      this.aplicarTransferencia();
      return Promise.resolve();
    }

    this.enVuelo = this.cargarDesdeApi(esNavegador).finally(() => {
      this.enVuelo = null;
    });
    return this.enVuelo;
  }

  /** Reintento manual: fuerza una nueva consulta sin quedar atrapado en la promesa anterior. */
  recargar(): Promise<void> {
    this.inicializado = false;
    if (this.enVuelo) {
      return this.enVuelo;
    }
    return this.cargar();
  }

  private aplicarTransferencia(): void {
    const datos = this.transferState.get(CLAVE_ESTADO, VACIO);
    this.mascotas.set(Array.isArray(datos.mascotas) ? datos.mascotas : []);
    this.refugios.set(Array.isArray(datos.refugios) ? datos.refugios : []);
    this.contenido.set(datos.contenido ?? null);
    this.impacto.set(datos.impacto ?? null);
    this.cargado.set(true);
    this.parcial.set(false);
    this.origen.set('transferencia');
    this.error.set(null);
    this.inicializado = true;
    this.transferState.remove(CLAVE_ESTADO);
    // eslint-disable-next-line no-console
    console.info('[InitialDataService] TransferState reutilizado: sin petición HTTP duplicada.');
  }

  private async cargarDesdeApi(esNavegador: boolean): Promise<void> {
    const [mascotas, refugios, contenido, impacto] = await Promise.allSettled([
      this.obtener<{ items?: unknown[] }>(`${this.baseUrl}/mascotas?limit=50`, esNavegador),
      this.obtener<unknown[]>(`${this.baseUrl}/refugios`, esNavegador),
      this.obtener<unknown>(`${this.baseUrl}/contenido`, esNavegador),
      this.obtener<unknown>(`${this.baseUrl}/estadisticas/impacto`, esNavegador),
    ]);

    // Solo se sobrescribe el signal cuyo endpoint respondió: se preservan los válidos.
    if (mascotas.status === 'fulfilled') {
      const valor = mascotas.value;
      this.mascotas.set(
        Array.isArray(valor?.items) ? valor.items : Array.isArray(valor) ? valor : [],
      );
    }
    if (refugios.status === 'fulfilled') {
      this.refugios.set(Array.isArray(refugios.value) ? refugios.value : []);
    }
    if (contenido.status === 'fulfilled') {
      this.contenido.set(contenido.value ?? null);
    }
    if (impacto.status === 'fulfilled') {
      this.impacto.set(impacto.value ?? null);
    }

    const correctas = [mascotas, refugios, contenido, impacto].filter(
      (resultado) => resultado.status === 'fulfilled',
    ).length;

    if (correctas === 4) {
      this.cargado.set(true);
      this.parcial.set(false);
      this.origen.set('real');
      this.error.set(null);
      this.inicializado = true;
      if (!esNavegador) {
        this.transferState.set(CLAVE_ESTADO, {
          mascotas: this.mascotas(),
          refugios: this.refugios(),
          contenido: this.contenido(),
          impacto: this.impacto(),
        });
        // eslint-disable-next-line no-console
        console.info('[InitialDataService] Datos cargados en SSR y guardados en TransferState.');
      } else {
        // eslint-disable-next-line no-console
        console.info('[InitialDataService] Datos cargados en el navegador (sin TransferState previo).');
      }
      return;
    }

    // Carga parcial o total: nunca se reporta como conexión totalmente recuperada.
    this.cargado.set(false);
    this.parcial.set(correctas > 0);
    this.origen.set(correctas > 0 ? 'parcial' : 'error');
    this.error.set(
      correctas > 0
        ? 'Carga parcial: algunos datos no pudieron actualizarse.'
        : 'No se pudo conectar con la API; se muestran datos de respaldo.',
    );
    // eslint-disable-next-line no-console
    console.warn('[InitialDataService] Carga incompleta; se conservan las respuestas válidas.');
  }

  /** Un único reintento para fallos transitorios; nunca en SSR. */
  private obtener<T>(url: string, reintentar: boolean): Promise<T> {
    const consultar = () =>
      firstValueFrom(this.http.get<T>(url).pipe(timeout(TIEMPO_ESPERA_MS)));

    if (!reintentar) {
      return consultar();
    }
    return consultar().catch((error: unknown) => {
      if (!esTransitorio(error)) {
        throw error;
      }
      return consultar();
    });
  }
}
