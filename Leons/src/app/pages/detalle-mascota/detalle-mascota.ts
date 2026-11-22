import {
  Component,
  HostListener,
  OnDestroy,
  PLATFORM_ID,
  computed,
  inject,
  linkedSignal,
  signal,
} from '@angular/core';
import { HttpErrorResponse, HttpClient } from '@angular/common/http';
import { isPlatformBrowser } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  Subject,
  catchError,
  distinctUntilChanged,
  map,
  merge,
  of,
  switchMap,
  takeUntil,
  tap,
  timeout,
} from 'rxjs';
import { Foto, Rasgo } from '../../data/mascotas.data';
import { MascotasService } from '../../services/mascotas.service';
import { ContenidoService } from '../../services/contenido.service';
import { FavoritosService } from '../../services/favoritos.service';
import { SolicitudesService } from '../../services/solicitudes.service';
import { AuthService } from '../../core/auth/auth.service';
import { API_BASE_URL } from '../../core/api/api.config';
import { ApiError } from '../../core/api/api-error';
import { InitialDataService } from '../../core/data/initial-data.service';
import {
  FOTO_PLACEHOLDER,
  FotoFallbackDirective,
} from '../../core/imagenes/foto-fallback.directive';
import {
  Cita,
  Cuidado,
  Pregunta,
  Requisito,
  citaDe,
  cuidadosDe,
  historiaDe,
  preguntasDe,
  rasgosDe,
} from '../../data/detalle.data';

interface Dato {
  etiqueta: string;
  icono: string;
  iconoClase: string;
  valor: string;
  extra: string;
}

/** Mascota incluida en `GET /api/v1/mascotas/{id}/detalle` (camelCase). */
export interface MascotaDetalleApi {
  id?: number;
  rasgos?: { icono: string; texto: string; clase: string; iconoClase?: string }[];
}

/** Contrato tipado de `GET /api/v1/mascotas/{id}/detalle` (camelCase). */
export interface DetalleMascotaApi {
  mascota?: MascotaDetalleApi;
  refugio?: unknown;
  historia?: string[];
  cuidados?: Cuidado[];
  requisitos?: Requisito[];
  preguntas?: Pregunta[];
  cita?: Cita | null;
  galeria?: Foto[];
  similares?: unknown[];
}

/** Estados observables de la carga del detalle en el navegador. */
export type EstadoDetalle = 'inicial' | 'cargando' | 'api' | 'respaldo' | 'error';

type ResultadoDetalle =
  | { id: number; tipo: 'api'; datos: DetalleMascotaApi }
  | { id: number; tipo: 'respaldo' | 'error' };

/** 4xx (incluidos 400/401/403/404) nunca se reintentan; 5xx, red y timeout sí. */
function esTransitorioDetalle(error: unknown): boolean {
  if (error instanceof HttpErrorResponse || error instanceof ApiError) {
    return error.status === 0 || error.status >= 500;
  }
  return true;
}

function esDetalleValido(valor: unknown): valor is DetalleMascotaApi {
  if (!valor || typeof valor !== 'object') {
    return false;
  }
  const datos = valor as DetalleMascotaApi;
  return (
    Array.isArray(datos.historia) ||
    Array.isArray(datos.cuidados) ||
    Array.isArray(datos.galeria) ||
    Array.isArray(datos.preguntas)
  );
}

/** Rasgos registrados en la respuesta de detalle; `null` si el campo no viene. */
function rasgosDeApi(mascota: MascotaDetalleApi | undefined): Rasgo[] | null {
  const valores = mascota?.rasgos;
  if (!Array.isArray(valores)) {
    return null;
  }
  return valores.map((r) => ({
    icono: String(r.icono ?? ''),
    texto: String(r.texto ?? ''),
    clase: String(r.clase ?? ''),
    iconoClase: String(r.iconoClase ?? ''),
  }));
}

@Component({
  selector: 'app-detalle-mascota',
  imports: [RouterLink, FotoFallbackDirective],
  templateUrl: './detalle-mascota.html',
  styleUrl: './detalle-mascota.css',
})
export class DetalleMascota implements OnDestroy {
  readonly fill0 = "'FILL' 0";
  readonly fill1 = "'FILL' 1";

  private readonly route = inject(ActivatedRoute);
  private readonly servicio = inject(MascotasService);
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);
  private readonly contenido = inject(ContenidoService);
  private readonly favoritosService = inject(FavoritosService);
  private readonly solicitudesService = inject(SolicitudesService);
  private readonly auth = inject(AuthService);
  private readonly initialData = inject(InitialDataService);
  private readonly platformId = inject(PLATFORM_ID);
  private readonly destroy$ = new Subject<void>();
  private readonly recargar$ = new Subject<void>();
  private readonly _errorDetalle = signal<string | null>(null);
  private reintentosAutomaticos = 0;
  private toastTimer?: ReturnType<typeof setTimeout>;

  readonly id = toSignal(this.route.paramMap.pipe(map((p) => Number(p.get('id')))), {
    initialValue: Number(this.route.snapshot.paramMap.get('id')) || 0,
  });

  readonly mascota = computed(() => this.servicio.porId(this.id()));

  /** Respuesta real de la API; `null` mientras se carga o cuando se usa respaldo. */
  readonly datosReales = signal<DetalleMascotaApi | null>(null);
  readonly estadoDetalle = signal<EstadoDetalle>('inicial');
  readonly errorDetalle = this._errorDetalle.asReadonly();
  readonly cargandoDetalle = computed(() => this.estadoDetalle() === 'cargando');
  readonly apiDisponible = computed(() => this.estadoDetalle() === 'api');
  readonly usandoRespaldo = computed(
    () => this.estadoDetalle() === 'respaldo' || this.estadoDetalle() === 'error',
  );

  constructor() {
    this.route.paramMap
      .pipe(
        map((params) => Number(params.get('id')) || 0),
        distinctUntilChanged(),
        // Un cambio de id cancela la suscripción interna anterior (y su petición).
        switchMap((id) => merge(of(id), this.recargar$.pipe(map(() => id)))),
        tap((id) => this.prepararCarga(id)),
        switchMap((id) => this.consultarDetalle(id)),
        takeUntil(this.destroy$),
      )
      .subscribe((resultado) => this.aplicarResultado(resultado));
  }

  /** Permite reintentar la carga del id activo (útil tras un error). */
  recargarDetalle(): void {
    if (!this.destroy$.closed) {
      this.recargar$.next();
    }
  }

  /** Reintento manual: recupera también la carga inicial compartida, sin recargar la página. */
  recargarTodo(): void {
    this.initialData.recargar();
    this.recargarDetalle();
  }

  private prepararCarga(id: number): void {
    // Limpiar primero evita pintar la mascota anterior con el id nuevo.
    this.datosReales.set(null);
    this._errorDetalle.set(null);
    this.reintentosAutomaticos = 0;
    if (!id) {
      this.estadoDetalle.set('inicial');
    } else if (!isPlatformBrowser(this.platformId)) {
      // SSR: la ficha se renderiza con los datos transferidos/constantes.
      this.estadoDetalle.set('respaldo');
    } else {
      this.estadoDetalle.set('cargando');
    }
  }

  private consultarDetalle(id: number) {
    if (!id || !isPlatformBrowser(this.platformId)) {
      return of<ResultadoDetalle>({ id, tipo: 'respaldo' });
    }

    const consultar = () =>
      this.http.get<unknown>(`${this.baseUrl}/mascotas/${id}/detalle`).pipe(
        timeout(3000),
        map(
          (respuesta): ResultadoDetalle =>
            esDetalleValido(respuesta)
              ? { id, tipo: 'api', datos: respuesta }
              : { id, tipo: 'error' },
        ),
      );

    // Como máximo un reintento por carga; se reinicia en prepararCarga().
    return consultar().pipe(
      catchError((error: unknown) => {
        if (this.reintentosAutomaticos >= 1 || !esTransitorioDetalle(error)) {
          return of<ResultadoDetalle>({ id, tipo: 'error' });
        }
        this.reintentosAutomaticos += 1;
        return consultar().pipe(
          catchError(() => of<ResultadoDetalle>({ id, tipo: 'error' })),
        );
      }),
    );
  }

  private aplicarResultado(resultado: ResultadoDetalle): void {
    // Defensa adicional: aunque una respuesta obsoleta llegue, se descarta.
    if (this.id() !== resultado.id) {
      return;
    }

    if (resultado.tipo === 'api') {
      this.datosReales.set(resultado.datos);
      this.estadoDetalle.set('api');
      this._errorDetalle.set(null);
      return;
    }

    this.datosReales.set(null);
    if (resultado.tipo === 'error') {
      this.estadoDetalle.set('error');
      this._errorDetalle.set(
        'No se pudo cargar el detalle desde la API. Se muestra la información de respaldo.',
      );
    } else if (resultado.id > 0) {
      this.estadoDetalle.set('respaldo');
    } else {
      this.estadoDetalle.set('inicial');
    }
  }

  readonly refugio = computed(() => {
    const m = this.mascota();
    return m ? this.servicio.refugioDe(m) : undefined;
  });

  readonly fotoActiva = linkedSignal({
    source: () => this.mascota()?.id ?? 0,
    computation: () => 0,
  });

  readonly fotoPrincipal = computed<Foto>(() => {
    const fotos = this.fotos();
    return (
      fotos[this.fotoActiva()] ??
      fotos[0] ?? { src: FOTO_PLACEHOLDER, alt: 'Imagen no disponible' }
    );
  });

  readonly esFavorito = computed(() => {
    const m = this.mascota();
    return m ? this.favoritosService.esFavorito(m.id) : false;
  });

  readonly modalAbierto = signal(false);
  /** A-12: único campo del formulario que viaja al backend (contrato existente). */
  readonly mensajeSolicitud = signal('');
  readonly perfil = this.auth.usuario;
  readonly mensaje = signal('');
  readonly solicitudCreada = signal(false);
  readonly enviandoSolicitud = signal(false);

  readonly ficha = computed<Dato[]>(() => {
    const m = this.mascota();
    if (!m) {
      return [];
    }
    return [
      {
        etiqueta: 'Especie',
        icono: 'pets',
        iconoClase: 'text-primary',
        valor: m.especie === 'perro' ? 'Canino' : 'Felino',
        extra: '',
      },
      {
        etiqueta: 'Edad',
        icono: 'cake',
        iconoClase: 'text-primary',
        valor: m.edadTexto,
        extra: '',
      },
      {
        etiqueta: 'Tamaño / Peso',
        icono: 'straighten',
        iconoClase: 'text-primary',
        valor: m.tamanoTexto,
        extra: '',
      },
      {
        etiqueta: 'Sexo',
        icono: m.sexo === 'Hembra' ? 'female' : 'male',
        iconoClase: 'text-primary',
        valor: m.sexo,
        extra: '',
      },
      {
        etiqueta: 'Energía',
        icono: 'bolt',
        iconoClase: 'text-secondary',
        valor: m.energia,
        extra: 'col-span-2 sm:col-span-1',
      },
    ];
  });

  readonly cuidados = computed<Cuidado[]>(() => {
    const d = this.datosReales();
    if (d && Array.isArray(d['cuidados'])) {
      return (d['cuidados'] as { icono: string; titulo: string; texto: string }[]).map((c) => ({
        icono: c.icono,
        titulo: c.titulo,
        texto: c.texto,
      }));
    }
    const m = this.mascota();
    return m ? cuidadosDe(m) : [];
  });

  readonly rasgos = computed<Rasgo[]>(() => {
    // La respuesta de detalle manda; el catálogo transferido/hidratado es el
    // respaldo. Ambos pasan por el mapper del backend, que ya no inventa rasgos.
    const desdeApi = rasgosDeApi(this.datosReales()?.mascota);
    if (desdeApi !== null) {
      return desdeApi;
    }
    const m = this.mascota();
    return m ? rasgosDe(m) : [];
  });

  readonly historia = computed<string[]>(() => {
    const d = this.datosReales();
    if (d && Array.isArray(d['historia'])) {
      return d['historia'] as string[];
    }
    const m = this.mascota();
    return m ? historiaDe(m) : [];
  });

  readonly cita = computed<Cita | undefined>(() => {
    const d = this.datosReales();
    if (d && d['cita']) {
      const c = d['cita'] as { texto: string; autor: string };
      return { texto: c.texto, autor: c.autor };
    }
    const m = this.mascota();
    return m ? citaDe(m) : undefined;
  });

  readonly preguntas = computed<Pregunta[]>(() => {
    const d = this.datosReales();
    if (d && Array.isArray(d['preguntas'])) {
      return (d['preguntas'] as { pregunta: string; respuesta: string }[]).map((p) => ({
        pregunta: p.pregunta,
        respuesta: p.respuesta,
      }));
    }
    const m = this.mascota();
    return m ? preguntasDe(m) : [];
  });

  readonly requisitos = this.contenido.requisitos;

  readonly similares = computed(() => {
    const m = this.mascota();
    return m ? this.servicio.similares(m) : [];
  });

  readonly fotos = computed<Foto[]>(() => {
    const d = this.datosReales();
    const m = this.mascota();
    const candidatas =
      d && Array.isArray(d['galeria'])
        ? (d['galeria'] as { src: string; alt: string }[]).map((f) => ({
            src: f.src,
            alt: f.alt,
          }))
        : m
          ? this.servicio.galeriaDe(m)
          : [];
    // INC-004: no se navega entre entradas sin `src`; la principal se respeta.
    return candidatas.filter((f) => !!f.src);
  });

  readonly totalMascotas = this.servicio.total;

  readonly whatsappUrl = computed(() => {
    const m = this.mascota();
    const r = this.refugio();
    if (!m || !r) {
      return '#';
    }
    const texto = encodeURIComponent(
      `¡Hola! Quisiera información sobre la adopción de ${m.nombre} (Ficha ${m.fichaId}) en LeonS`,
    );
    return `https://wa.me/${r.whatsapp}?text=${texto}`;
  });

  elegirFoto(i: number) {
    this.fotoActiva.set(i);
  }

  async alternarFavorito() {
    const m = this.mascota();
    if (!m) {
      return;
    }
    await this.favoritosService.alternar(m.id);
    const error = this.favoritosService.error();
    if (error) {
      this.avisar(error);
    }
  }

  abrirModal() {
    this.mensajeSolicitud.set('');
    this.modalAbierto.set(true);
  }

  cerrarModal() {
    this.modalAbierto.set(false);
  }

  async enviarSolicitud(e: Event) {
    e.preventDefault();
    const m = this.mascota();
    if (!m || this.enviandoSolicitud()) {
      return;
    }

    this.enviandoSolicitud.set(true);
    try {
      const resultado = await this.solicitudesService.crearDesdeMascota(
        m,
        this.refugio(),
        this.mensajeSolicitud(),
      );
      this.cerrarModal();

      if (resultado.creada) {
        this.avisar(
          `¡Solicitud enviada! ${m.refugio} te contactará por WhatsApp para coordinar la visita.`,
          true,
        );
      } else if (resultado.error === 'MASCOTA_NO_DISPONIBLE') {
        this.avisar('Esta mascota ya no está disponible para adopción.');
      } else if (resultado.error === 'SOLICITUD_DUPLICADA') {
        this.avisar(
          `Ya tienes una solicitud activa para ${m.nombre}. Puedes seguir su estado en Mis solicitudes.`,
        );
      } else if (resultado.error === 'ENVIO_EN_CURSO') {
        this.avisar('Ya hay un envío en curso para esta mascota. Espera la respuesta.');
      } else {
        this.avisar(
          resultado.error ?? 'No se pudo enviar la solicitud. Intenta de nuevo más tarde.',
        );
      }
    } catch {
      this.cerrarModal();
      this.avisar('No se pudo enviar la solicitud. Inicia sesión e inténtalo de nuevo.');
    } finally {
      this.enviandoSolicitud.set(false);
    }
  }

  async compartir() {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    const m = this.mascota();
    if (!m) {
      return;
    }
    const url = window.location.href;
    const datos = {
      title: `Adopta a ${m.nombre} en Huancayo - LeonS`,
      text: m.descripcion,
      url,
    };

    if (navigator.share) {
      try {
        await navigator.share(datos);
      } catch {
        // El usuario canceló la hoja de compartir.
      }
      return;
    }

    try {
      await navigator.clipboard.writeText(url);
      this.avisar('Enlace de la ficha copiado al portapapeles.');
    } catch {
      this.avisar('No se pudo copiar automáticamente. Copia la URL de la barra de direcciones.');
    }
  }

  @HostListener('document:keydown.escape')
  cerrarConEscape() {
    if (this.modalAbierto()) {
      this.cerrarModal();
    }
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
  }

  private avisar(texto: string, exito = false) {
    this.solicitudCreada.set(exito);
    this.mensaje.set(texto);
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
    this.toastTimer = setTimeout(() => {
      this.mensaje.set('');
      this.solicitudCreada.set(false);
    }, 6000);
  }
}
