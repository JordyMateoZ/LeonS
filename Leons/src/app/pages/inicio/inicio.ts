import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MascotasService } from '../../services/mascotas.service';

@Component({
  selector: 'app-inicio',
  imports: [RouterLink],
  templateUrl: './inicio.html',
  styleUrl: './inicio.css',
})
export class Inicio {
  private readonly mascotasService = inject(MascotasService);

  distritos = ['Todos', '📍 Huancayo Centro', '📍 El Tambo', '📍 Chilca', '📍 San Jerónimo'];
  categorias = ['🐶 Perros', '🐱 Gatos', '🐾 Cachorros', '🌾 Adultos tranquilos'];
  distritoActivo = signal('Todos');
  categoriaActiva = signal('');

  readonly mascotas = computed(() => this.mascotasService.destacadas([1, 2, 3, 4]));

  get totalMascotas(): number {
    return this.mascotasService.total;
  }

  pasos = [
    {
      num: '01',
      caja: 'bg-primary-fixed text-primary',
      icono: 'search',
      nota: 'Filtros según tu espacio',
      titulo: 'Elige con el corazón',
      texto:
        'Explora los perritos y gatitos filtrados por distrito (Huancayo, El Tambo o Chilca). Evalúa su nivel de energía, tamaño y afinidad con tu hogar y tiempo diario.',
    },
    {
      num: '02',
      caja: 'bg-secondary-container text-secondary',
      icono: 'schedule',
      nota: 'Respuesta en 48 horas',
      titulo: 'Solicita la adopción',
      texto:
        'Llena una ficha responsable simple sobre las condiciones de tu vivienda. El albergue o rescatista evaluará tu postulación y te responderá en menos de 48 horas.',
    },
    {
      num: '03',
      caja: 'bg-primary-fixed-dim text-primary-container',
      icono: 'home_pin',
      nota: 'Encuentro presencial seguro',
      titulo: 'Conoce a tu compañero',
      texto:
        'Coordina una visita presencial en el refugio o casa de acogida para el primer encuentro, comprobación de compatibilidad y firma del compromiso de tenencia responsable.',
    },
  ];

  readonly metricas = computed(() => [
    {
      icono: 'home',
      color: 'text-primary-fixed-dim',
      valor: `${this.mascotasService.totalAdoptadas}`,
      texto: 'Mascotas con hogar definitivo',
    },
    {
      icono: 'volunteer_activism',
      color: 'text-secondary-fixed',
      valor: `${this.mascotasService.refugios.length}`,
      texto: 'Refugios y rescatistas aliados',
    },
    {
      icono: 'health_and_safety',
      color: 'text-primary-fixed-dim',
      valor: `${this.mascotasService.totalEnAcogida}`,
      texto: 'Mascotas en acogida temporal',
    },
    {
      icono: 'map',
      color: 'text-secondary-fixed',
      valor: `${this.mascotasService.totalDistritos}`,
      texto: 'Distritos unidos en el Valle',
    },
  ]);

  elegirDistrito(d: string) {
    this.distritoActivo.set(d);
  }
  elegirCategoria(c: string) {
    this.categoriaActiva.set(c === this.categoriaActiva() ? '' : c);
  }
}
