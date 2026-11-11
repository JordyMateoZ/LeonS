import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Refugio } from '../../data/refugios.data';
import { MascotasService } from '../../services/mascotas.service';

type TipoFiltro = 'all' | 'constituido' | 'independiente';
type EspecieFiltro = 'todas' | 'perro' | 'gato';
type Orden = 'activity' | 'rescues' | 'available';

interface RefugioVista extends Refugio {
  foto: string;
  alt: string;
  tipoEtiqueta: string;
  tipoClase: string;
  especiesTexto: string;
  adopciones: number;
  disponibles: number;
  totalMascotas: number;
  dispTexto: string;
}

interface Estadistica {
  icono: string;
  fondo: string;
  iconoClase: string;
  valorClase: string;
  valor: string;
  texto: string;
}

interface Cobertura {
  punto: string;
  distrito: string;
  aliados: string;
}

interface Paso {
  num: number;
  fondo: string;
  titulo: string;
  texto: string;
}

const PUNTOS_COBERTURA = [
  'bg-primary',
  'bg-secondary',
  'bg-tertiary',
  'bg-outline',
  'bg-on-surface-variant',
  'bg-primary-container',
];

@Component({
  selector: 'app-refugios',
  imports: [RouterLink],
  templateUrl: './refugios.html',
  styleUrl: './refugios.css',
})
export class Refugios {
  private readonly mascotasService = inject(MascotasService);

  readonly mapaUrl =
    'https://lh3.googleusercontent.com/aida-public/AB6AXuAAefRWJXQk06vFtI_VlOer-n-fy68hFTW7GYQm0jCt_DuBvjM7E7vAyC29sBFWF1N20lUh-8-gA7qGqTC9L_J8Rm32DUJAvGKcBiEwmWDMc_LmB756K7Tb361VdFFAYdrv_3rueFGqkkuSCk81uwO7gJb7WnjifETXC9uPn_gx987bzhJwQ6dHVBdNR-HlEf53OsuZfdesFx1SiXvFOD4SPOHe3p2iDtX3mDIH64NB';

  // Opciones de filtros
  readonly distritos = computed(() => [
    'Todos',
    ...new Set(this.mascotasService.refugios.map((refugio) => refugio.distrito)),
  ]);
  readonly tipos: { valor: TipoFiltro; etiqueta: string }[] = [
    { valor: 'all', etiqueta: 'Todos' },
    { valor: 'constituido', etiqueta: 'Refugios constituidos' },
    { valor: 'independiente', etiqueta: 'Rescatistas independientes' },
  ];
  readonly especies: { valor: EspecieFiltro; etiqueta: string }[] = [
    { valor: 'todas', etiqueta: 'Perros y Gatos' },
    { valor: 'perro', etiqueta: 'Perros' },
    { valor: 'gato', etiqueta: 'Gatos' },
  ];

  readonly estadisticas = computed<Estadistica[]>(() => [
    {
      icono: 'home_work',
      fondo: 'bg-primary-fixed',
      iconoClase: 'text-primary',
      valorClase: 'text-primary',
      valor: `${this.mascotasService.refugios.length}`,
      texto: 'Refugios y Rescatistas Verificados',
    },
    {
      icono: 'favorite',
      fondo: 'bg-secondary-fixed',
      iconoClase: 'text-secondary',
      valorClase: 'text-secondary',
      valor: `${this.mascotasService.totalAdoptadas}`,
      texto: 'Vidas Transformadas en Hogares',
    },
    {
      icono: 'health_and_safety',
      fondo: 'bg-surface-container',
      iconoClase: 'text-on-surface',
      valorClase: 'text-on-surface',
      valor: `${this.mascotasService.totalEnAcogida}`,
      texto: 'Mascotas en Acogida Temporal',
    },
    {
      icono: 'map',
      fondo: 'bg-tertiary-container/30',
      iconoClase: 'text-tertiary',
      valorClase: 'text-tertiary',
      valor: `${this.mascotasService.totalDistritos}`,
      texto: 'Distritos Cubiertos en Junín',
    },
  ]);

  readonly cobertura = computed<Cobertura[]>(() => {
    const porDistrito = new Map<string, number>();
    for (const refugio of this.mascotasService.refugios) {
      porDistrito.set(refugio.distrito, (porDistrito.get(refugio.distrito) ?? 0) + 1);
    }

    return [...porDistrito.entries()].map(([distrito, cantidad], indice) => ({
      punto: PUNTOS_COBERTURA[indice % PUNTOS_COBERTURA.length],
      distrito,
      aliados: `${cantidad} ${cantidad === 1 ? 'aliado' : 'aliados'}`,
    }));
  });

  readonly pasos: Paso[] = [
    {
      num: 1,
      fondo: 'bg-primary-fixed text-primary',
      titulo: 'Constatación Presencial',
      texto:
        'Inspección directa de condiciones de albergue, salubridad, espacio y enriquecimiento ambiental en cada distrito.',
    },
    {
      num: 2,
      fondo: 'bg-secondary-fixed text-secondary',
      titulo: 'Cero Lucro Garantizado',
      texto:
        'Compromiso formal e inquebrantable: el proceso de adopción es 100% gratuito. No se comercializan vidas bajo ningún concepto.',
    },
    {
      num: 3,
      fondo: 'bg-surface-container text-on-surface',
      titulo: 'Aval Veterinario Colegiado',
      texto:
        'Cartilla de vacunación al día, desparasitación interna/externa y certificado de esterilización firmado por médicos colegiados de Junín.',
    },
    {
      num: 4,
      fondo: 'bg-tertiary-container text-on-tertiary',
      titulo: 'Acompañamiento & Acta',
      texto:
        'Firma de acta de tenencia responsable LeonS, con visitas de seguimiento y asesoría post-adopción permanente.',
    },
  ];

  readonly beneficios = [
    'Difusión comunitaria',
    'Validación de adoptantes',
    '100% Gratuito y sin comisiones',
  ];

  // Refugios reales del proyecto, enriquecidos con su disponibilidad actual
  readonly refugios = computed<RefugioVista[]>(() =>
    this.mascotasService.refugios.map((refugio) => {
      const mascotas = this.mascotasService.mascotasDeRefugio(refugio.id);
      const resumen = this.mascotasService.resumenDeRefugio(refugio.id);
      const foto = mascotas[0]?.foto ?? refugio.logo ?? '';

      return {
        ...refugio,
        foto,
        alt: `Refugio ${refugio.nombre} en ${refugio.distrito}`,
        tipoEtiqueta:
          refugio.tipo === 'independiente' ? 'Rescatista independiente' : 'Refugio constituido',
        tipoClase: refugio.tipo === 'independiente' ? 'text-tertiary' : 'text-primary',
        especiesTexto:
          refugio.especies.length === 2
            ? 'Caninos y Felinos'
            : refugio.especies[0] === 'perro'
              ? 'Caninos'
              : 'Felinos',
        adopciones: refugio.adoptadas,
        disponibles: resumen.disponibles,
        totalMascotas: resumen.total,
        dispTexto:
          resumen.disponibles > 0
            ? `${resumen.disponibles} en adopción`
            : `${resumen.total} en seguimiento`,
      };
    }),
  );

  busqueda = signal('');
  distrito = signal('Todos');
  tipo = signal<TipoFiltro>('all');
  especie = signal<EspecieFiltro>('todas');
  soloDisponibles = signal(false);
  orden = signal<Orden>('activity');

  readonly filtrados = computed(() => {
    const q = this.busqueda().trim().toLowerCase();
    const especie = this.especie();
    const lista = this.refugios().filter(
      (r) =>
        (!q ||
          [r.nombre, r.direccion, r.descripcion, r.distrito, r.especiesTexto].some((texto) =>
            texto.toLowerCase().includes(q),
          )) &&
        (this.distrito() === 'Todos' || r.distrito === this.distrito()) &&
        (this.tipo() === 'all' || r.tipo === this.tipo()) &&
        (especie === 'todas' || r.especies.includes(especie)) &&
        (!this.soloDisponibles() || r.disponibles > 0),
    );
    switch (this.orden()) {
      case 'rescues':
        return [...lista].sort((a, b) => b.adopciones - a.adopciones);
      case 'available':
        return [...lista].sort((a, b) => b.disponibles - a.disponibles);
      default:
        return lista;
    }
  });

  buscar(texto: string) {
    this.busqueda.set(texto);
  }

  cambiarOrden(valor: string) {
    this.orden.set(valor as Orden);
  }

  alternarDisponibles() {
    this.soloDisponibles.update((valor) => !valor);
  }
}
