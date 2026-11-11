import { Component, OnDestroy, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Solicitud } from '../../data/solicitudes.data';
import { SolicitudesService } from '../../services/solicitudes.service';

type Filtro = 'all' | 'active' | 'completed';

interface Consejo {
  icono: string;
  iconoClase: string;
  titulo: string;
  texto: string;
}

@Component({
  selector: 'app-mis-solicitudes',
  imports: [RouterLink],
  templateUrl: './mis-solicitudes.html',
  styleUrl: './mis-solicitudes.css',
})
export class MisSolicitudes implements OnDestroy {
  private readonly servicio = inject(SolicitudesService);

  readonly fill1 = "'FILL' 1";
  readonly soporteWhatsapp = 'https://wa.me/51964000111';
  readonly fotoVacio =
    'https://lh3.googleusercontent.com/aida-public/AB6AXuCwYyWQSshlFfF7n7Nhdx7IgeFeWREuo0Un4UyWJBjtt59B2gt5BPw9H_Mv3_MRoGvg1JjM0DCmmLABvyawXLOn42yBcxnD0o7wZ9Rm9n17tEQLEzyr9Y30Jqyl7IejsuQptCtina3sVAj37UVCzYtsB0vMrFhQp0soAeFLIep-b53MLcz40paPtBTeGP_y8FJyyauW8Bk7Yg9oGdu9DELSb5vMtYUshfkbCt3fOeHH';

  readonly motivos = [
    'Inconveniente de espacio o tiempo',
    'Adopté a otro perrito/gatito',
    'Mudanza fuera de Huancayo',
    'Otro motivo personal',
  ];

  readonly consejos: Consejo[] = [
    {
      icono: 'id_card',
      iconoClase: 'text-secondary',
      titulo: 'Ten tu DNI a la mano',
      texto: 'Copia simple y recibo de luz o agua de tu domicilio en Huancayo, Chilca o El Tambo.',
    },
    {
      icono: 'ac_unit',
      iconoClase: 'text-primary',
      titulo: 'Prepara el abrigo nocturno',
      texto:
        'Las noches en el Valle del Mantaro bajan de 4°C. Todo peludito debe dormir bajo techo y sobre camita abrigada.',
    },
    {
      icono: 'verified_user',
      iconoClase: 'text-secondary',
      titulo: 'LeonS nunca cobra por trámites',
      texto:
        'La adopción es un acto 100% gratuito. Solo pagas las vacunas directamente en la veterinaria de tu elección.',
    },
    {
      icono: 'groups',
      iconoClase: 'text-primary',
      titulo: 'Consenso con toda la familia',
      texto:
        'Asegúrate de que todos los integrantes del hogar estén de acuerdo con la llegada de la mascota.',
    },
  ];

  filtro = signal<Filtro>('all');
  vacio = signal(false);
  aCancelar = signal<Solicitud | null>(null);
  mensaje = signal('');

  private mensajeTimer?: ReturnType<typeof setTimeout>;

  readonly solicitudes = this.servicio.solicitudes;
  readonly visibles = computed(() =>
    this.solicitudes().filter((s) => this.filtro() === 'all' || s.estado === this.filtro()),
  );
  readonly total = this.servicio.total;
  readonly enProceso = this.servicio.activas;
  readonly finalizadas = this.servicio.finalizadas;
  readonly mostrarVacio = computed(() => this.vacio() || this.visibles().length === 0);

  readonly pestanas = computed<{ valor: Filtro; etiqueta: string }[]>(() => [
    { valor: 'all', etiqueta: `Todas (${this.total()})` },
    { valor: 'active', etiqueta: `En proceso (${this.enProceso()})` },
    { valor: 'completed', etiqueta: `Finalizadas (${this.finalizadas()})` },
  ]);

  cambiarFiltro(f: Filtro) {
    this.vacio.set(false);
    this.filtro.set(f);
  }

  alternarVacio() {
    if (this.vacio()) {
      this.vacio.set(false);
      this.servicio.restaurarCanceladas();
      this.filtro.set('all');
    } else {
      this.vacio.set(true);
    }
  }

  abrirCancelar(s: Solicitud) {
    this.aCancelar.set(s);
  }

  cerrarCancelar() {
    this.aCancelar.set(null);
  }

  confirmarCancelacion() {
    const s = this.aCancelar();
    if (!s) {
      return;
    }
    this.servicio.cancelar(s.id);
    this.cerrarCancelar();
    this.avisar('Tu solicitud fue cancelada y el albergue será notificado.');
  }

  ngOnDestroy() {
    if (this.mensajeTimer) {
      clearTimeout(this.mensajeTimer);
    }
  }

  private avisar(texto: string) {
    this.mensaje.set(texto);
    if (this.mensajeTimer) {
      clearTimeout(this.mensajeTimer);
    }
    this.mensajeTimer = setTimeout(() => this.mensaje.set(''), 4000);
  }
}
