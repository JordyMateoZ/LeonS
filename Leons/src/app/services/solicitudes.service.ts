import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { AuthService } from '../core/auth/auth.service';
import { API_BASE_URL } from '../core/api/api.config';
import { ApiError } from '../core/api/api-error';
import { Mascota } from '../data/mascotas.data';
import { Refugio } from '../data/refugios.data';
import { Solicitud } from '../data/solicitudes.data';

export interface ResultadoSolicitud {
  creada: boolean;
  solicitud?: Solicitud;
  error?: string;
}

const ESTADO_BACKEND_A_FRONTEND: Record<string, Solicitud['estado']> = {
  active: 'active',
  completed: 'completed',
  cancelled: 'cancelled',
};

@Injectable({ providedIn: 'root' })
export class SolicitudesService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly baseUrl = inject(API_BASE_URL);

  private readonly _solicitudes = signal<Solicitud[]>([]);
  private readonly _cargando = signal(false);
  private readonly _error = signal<string | null>(null);
  private readonly _enviando = new Set<number>();

  readonly solicitudes = this._solicitudes.asReadonly();
  readonly cargando = this._cargando.asReadonly();
  readonly error = this._error.asReadonly();
  readonly total = computed(() => this._solicitudes().length);
  readonly activas = computed(() => this._solicitudes().filter((s) => s.estado === 'active').length);
  readonly finalizadas = computed(() => this._solicitudes().filter((s) => s.estado === 'completed').length);
  readonly canceladas = computed(() => this._solicitudes().filter((s) => s.estado === 'cancelled').length);

  constructor() {
    // No se carga automáticamente: las solicitudes son privadas y requieren
    // sesión. Los componentes invocan cargar() cuando corresponda.
    this.auth.registrarLimpieza?.(() => this.limpiarPrivados());
  }

  /** Limpieza invocada al cerrar sesión; evita filtrar datos entre usuarios. */
  limpiarPrivados(): void {
    this._solicitudes.set([]);
    this._enviando.clear();
    this._cargando.set(false);
    this._error.set(null);
  }

  async cargar(): Promise<void> {
    if (!this.auth.isAuthenticated()) {
      this.limpiarPrivados();
      return;
    }
    this._cargando.set(true);
    this._error.set(null);
    try {
      const respuesta = await firstValueFrom(
        this.http.get<{ items?: unknown[]; total?: number }>(
          `${this.baseUrl}/solicitudes?limit=50&incluirCanceladas=true`,
        ),
      );
      const items = Array.isArray(respuesta?.items) ? respuesta.items : (Array.isArray(respuesta) ? (respuesta as unknown[]) : []);
      this._solicitudes.set(items.map((item) => this.mapear(item as Record<string, unknown>)));
    } catch (error) {
      this._error.set(error instanceof ApiError ? error.message : 'No se pudieron cargar las solicitudes.');
      this._solicitudes.set([]);
    } finally {
      this._cargando.set(false);
    }
  }

  solicitudActivaPara(mascotaId: number): Solicitud | undefined {
    return this._solicitudes().find(
      (solicitud) => solicitud.fichaId === mascotaId && solicitud.estado === 'active',
    );
  }

  async crearDesdeMascota(
    mascota: Mascota,
    refugio?: Refugio,
    mensaje?: string | null,
  ): Promise<ResultadoSolicitud> {
    const existente = this.solicitudActivaPara(mascota.id);
    if (existente) {
      return { creada: false, solicitud: existente };
    }
    if (this._enviando.has(mascota.id)) {
      return { creada: false, error: 'ENVIO_EN_CURSO' };
    }

    this._enviando.add(mascota.id);
    this._error.set(null);
    try {
      const respuesta = await firstValueFrom(
        this.http.post<Record<string, unknown>>(`${this.baseUrl}/solicitudes`, {
          mascotaId: mascota.id,
          // A-12: el mensaje libre del formulario sí forma parte del contrato.
          // `telefono` sigue sin enviarse: no se persiste y el refugio usa el
          // WhatsApp de la ficha; el perfil ya está en /auth/me.
          mensaje: mensaje?.trim() || null,
          telefono: null,
        }),
      );
      const solicitud = this.mapear(respuesta);
      this._solicitudes.update((lista) => [solicitud, ...lista]);
      return { creada: true, solicitud };
    } catch (error) {
      const codigo = error instanceof ApiError ? error.code : 'ERROR';
      // Ante un duplicado solo se consulta el estado real; nunca se reenvía el POST.
      if (codigo === 'SOLICITUD_DUPLICADA') {
        await this.cargar();
        const dup = this.solicitudActivaPara(mascota.id);
        if (dup) {
          return { creada: false, solicitud: dup, error: codigo };
        }
      }
      const mensaje =
        error instanceof ApiError && error.message
          ? error.message
          : 'No se pudo enviar la solicitud. Intenta de nuevo más tarde.';
      this._error.set(mensaje);
      return { creada: false, error: codigo === 'ERROR' ? mensaje : codigo };
    } finally {
      this._enviando.delete(mascota.id);
    }
  }

  async cancelar(id: number, motivo = 'No especificado'): Promise<boolean> {
    this._error.set(null);
    try {
      const respuesta = await firstValueFrom(
        this.http.patch<Record<string, unknown>>(
          `${this.baseUrl}/solicitudes/${id}/cancelar`,
          { motivo },
        ),
      );
      const actualizada = this.mapear(respuesta);
      this._solicitudes.update((lista) => lista.map((s) => (s.id === id ? actualizada : s)));
      return true;
    } catch (error) {
      this._error.set(
        error instanceof ApiError && error.message
          ? error.message
          : 'No se pudo cancelar la solicitud. Intenta de nuevo más tarde.',
      );
      return false;
    }
  }

  restaurarCanceladas(): void {
    // Las cancelaciones se conservan en la API; se recarga la lista completa.
    void this.cargar();
  }

  private mapear(item: Record<string, unknown>): Solicitud {
    const etapas = Array.isArray(item['etapas'])
      ? (item['etapas'] as { titulo: string; detalle: string; destacado?: boolean }[]).map((e) => ({
          titulo: e.titulo,
          detalle: e.detalle,
          destacado: e.destacado,
        }))
      : [];
    const cita = (item['cita'] as { fecha: string; direccion: string; coordinadora: string } | null) ?? null;
    const mensaje = (item['mensaje'] as { iniciales: string; nombre: string; rol: string; texto: string } | null) ?? null;
    const cierre = (item['cierre'] as { titulo: string; texto: string; controlTitulo: string; controlFecha: string; controlLugar: string } | null) ?? null;

    return {
      id: Number(item['id']),
      estado: ESTADO_BACKEND_A_FRONTEND[String(item['estado'] ?? 'active')] ?? 'active',
      nombre: String(item['nombre'] ?? ''),
      fichaId: Number(item['fichaId'] ?? item['ficha_id'] ?? 0),
      fotoSrc: String(item['fotoSrc'] ?? item['foto_src'] ?? ''),
      fotoAlt: String(item['fotoAlt'] ?? item['foto_alt'] ?? ''),
      chipTexto: String(item['chipTexto'] ?? item['chip_texto'] ?? ''),
      chipClase: String(item['chipClase'] ?? item['chip_clase'] ?? ''),
      refugio: String(item['refugio'] ?? ''),
      lugar: String(item['lugar'] ?? ''),
      exp: String(item['exp'] ?? ''),
      fechaTexto: String(item['fechaTexto'] ?? item['fecha_texto'] ?? ''),
      badgeTexto: String(item['badgeTexto'] ?? item['badge_texto'] ?? ''),
      badgeClase: String(item['badgeClase'] ?? item['badge_clase'] ?? ''),
      puntoClase: String(item['puntoClase'] ?? item['punto_clase'] ?? ''),
      pasoTexto: String(item['pasoTexto'] ?? item['paso_texto'] ?? ''),
      pasoTextoClase: String(item['pasoTextoClase'] ?? item['paso_texto_clase'] ?? ''),
      headerClase: String(item['headerClase'] ?? item['header_clase'] ?? ''),
      iconoMini: String(item['iconoMini'] ?? item['icono_mini'] ?? ''),
      iconoMiniClase: String(item['iconoMiniClase'] ?? item['icono_mini_clase'] ?? ''),
      paso: Number(item['paso'] ?? 0),
      barraClase: String(item['barraClase'] ?? item['barra_clase'] ?? ''),
      etapas,
      cita: cita
        ? { fecha: cita.fecha, direccion: cita.direccion, coordinadora: cita.coordinadora }
        : undefined,
      mensaje: mensaje
        ? { iniciales: mensaje.iniciales, nombre: mensaje.nombre, rol: mensaje.rol, texto: mensaje.texto }
        : undefined,
      tiempoRespuesta: (item['tiempoRespuesta'] ?? item['tiempo_respuesta']) as string | undefined,
      whatsapp: (item['whatsapp'] as string | undefined) ?? undefined,
      cierre: cierre
        ? {
            titulo: cierre.titulo,
            texto: cierre.texto,
            controlTitulo: cierre.controlTitulo,
            controlFecha: cierre.controlFecha,
            controlLugar: cierre.controlLugar,
          }
        : undefined,
      motivoCancelacion: (item['motivoCancelacion'] ?? item['motivo_cancelacion']) as string | undefined,
    };
  }
}
