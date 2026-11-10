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
import { isPlatformBrowser } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';
import { Foto, Rasgo } from '../../data/mascotas.data';
import { MascotasService } from '../../services/mascotas.service';
import {
  Cita,
  Cuidado,
  Pregunta,
  REQUISITOS,
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

@Component({
  selector: 'app-detalle-mascota',
  imports: [RouterLink],
  templateUrl: './detalle-mascota.html',
  styleUrl: './detalle-mascota.css',
})
export class DetalleMascota implements OnDestroy {
  readonly fill0 = "'FILL' 0";
  readonly fill1 = "'FILL' 1";

  private readonly route = inject(ActivatedRoute);
  private readonly servicio = inject(MascotasService);
  private readonly platformId = inject(PLATFORM_ID);
  private toastTimer?: ReturnType<typeof setTimeout>;

  readonly id = toSignal(
    this.route.paramMap.pipe(map((p) => Number(p.get('id')))),
    { initialValue: Number(this.route.snapshot.paramMap.get('id')) || 0 },
  );

  readonly mascota = computed(() => this.servicio.porId(this.id()));

  readonly refugio = computed(() => {
    const m = this.mascota();
    return m ? this.servicio.refugioDe(m) : undefined;
  });

  readonly fotos = computed<Foto[]>(() => {
    const m = this.mascota();
    return m ? this.servicio.galeriaDe(m) : [];
  });

  readonly fotoActiva = linkedSignal({
    source: () => this.mascota()?.id ?? 0,
    computation: () => 0,
  });

  readonly fotoPrincipal = computed<Foto>(() => {
    const fotos = this.fotos();
    return fotos[this.fotoActiva()] ?? fotos[0] ?? { src: '', alt: '' };
  });

  readonly esFavorito = linkedSignal({
    source: () => this.mascota()?.id ?? 0,
    computation: () => false,
  });

  readonly favoritos = computed(() => 14 + (this.esFavorito() ? 1 : 0));
  readonly modalAbierto = signal(false);
  readonly mensaje = signal('');

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
      { etiqueta: 'Edad', icono: 'cake', iconoClase: 'text-primary', valor: m.edadTexto, extra: '' },
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
    const m = this.mascota();
    return m ? cuidadosDe(m) : [];
  });

  readonly rasgos = computed<Rasgo[]>(() => {
    const m = this.mascota();
    return m ? rasgosDe(m) : [];
  });

  readonly historia = computed<string[]>(() => {
    const m = this.mascota();
    return m ? historiaDe(m) : [];
  });

  readonly cita = computed<Cita | undefined>(() => {
    const m = this.mascota();
    return m ? citaDe(m) : undefined;
  });

  readonly preguntas = computed<Pregunta[]>(() => {
    const m = this.mascota();
    return m ? preguntasDe(m) : [];
  });

  readonly requisitos = REQUISITOS;

  readonly similares = computed(() => {
    const m = this.mascota();
    return m ? this.servicio.similares(m) : [];
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

  alternarFavorito() {
    this.esFavorito.update((v) => !v);
  }

  abrirModal() {
    this.modalAbierto.set(true);
  }

  cerrarModal() {
    this.modalAbierto.set(false);
  }

  enviarSolicitud(e: Event) {
    e.preventDefault();
    const m = this.mascota();
    this.cerrarModal();
    this.avisar(
      `¡Solicitud enviada! ${m?.refugio ?? 'El refugio'} te contactará por WhatsApp para coordinar la visita.`,
    );
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
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
  }

  private avisar(texto: string) {
    this.mensaje.set(texto);
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
    this.toastTimer = setTimeout(() => this.mensaje.set(''), 4000);
  }
}
