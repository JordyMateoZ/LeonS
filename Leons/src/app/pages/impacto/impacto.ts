import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MascotasService } from '../../services/mascotas.service';

@Component({
  selector: 'app-impacto',
  imports: [RouterLink],
  templateUrl: './impacto.html',
  styleUrl: './impacto.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Impacto {
  private readonly mascotasService = inject(MascotasService);
  private readonly document = inject(DOCUMENT);

  readonly whatsappShareUrl =
    'https://api.whatsapp.com/send?text=' +
    encodeURIComponent('¡Conoce el impacto de LeonS Huancayo y adopta una mascota rescatada!');

  readonly volunteerNotice = signal(false);

  readonly totalAdoptadas = computed(() =>
    this.mascotasService.refugios.reduce((total, refugio) => total + refugio.adoptadas, 0),
  );
  readonly totalRefugios = computed(() => this.mascotasService.refugios.length);
  readonly totalEnAcogida = computed(() =>
    this.mascotasService.refugios.reduce((total, refugio) => total + refugio.enAcogida, 0),
  );
  readonly totalDistritos = computed(
    () => new Set(this.mascotasService.refugios.map((refugio) => refugio.distrito)).size,
  );
  readonly totalMascotas = computed(() => this.mascotasService.total);
  readonly totalPerros = computed(
    () => this.mascotasService.mascotas.filter((mascota) => mascota.especie === 'perro').length,
  );
  readonly totalGatos = computed(
    () => this.mascotasService.mascotas.filter((mascota) => mascota.especie === 'gato').length,
  );

  toggleVolunteerNotice() {
    this.volunteerNotice.update((v) => !v);
  }

  scrollTo(id: string) {
    const elemento = this.document.getElementById(id);
    elemento?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
  }

  readonly kpis = computed(() => [
    {
      icon: 'pets',
      iconBg: 'bg-primary-fixed',
      iconColor: 'text-primary',
      chip: 'Red consolidada',
      chipClass: 'text-secondary bg-secondary-container/40 font-bold',
      value: `${this.totalAdoptadas()}`,
      valueColor: 'text-primary',
      title: 'Mascotas adoptadas',
      text: 'Hogares cálidos formados en Junín con seguimiento integral.',
      footIcon: 'volunteer_activism',
      footLabel: 'Segundas oportunidades reales',
      footColor: 'text-primary',
    },
    {
      icon: 'home_work',
      iconBg: 'bg-secondary-container',
      iconColor: 'text-secondary',
      chip: 'Red activa',
      chipClass: 'text-on-surface-variant bg-surface-container-low',
      value: `${this.totalRefugios()}`,
      valueColor: 'text-secondary',
      title: 'Refugios aliados',
      text: 'Organizaciones y rescatistas comunitarios verificados.',
      footIcon: 'handshake',
      footLabel: 'Cooperación distrital',
      footColor: 'text-secondary',
    },
    {
      icon: 'health_and_safety',
      iconBg: 'bg-surface-container-high',
      iconColor: 'text-primary-container',
      chip: 'Hogares temporales',
      chipClass: 'text-primary bg-primary-fixed/60 font-bold',
      value: `${this.totalEnAcogida()}`,
      valueColor: 'text-primary-container',
      title: 'Mascotas en acogida',
      text: 'Peluditos que esperan una familia definitiva en la red.',
      footIcon: 'family_restroom',
      footLabel: 'Acompañamiento temporal',
      footColor: 'text-on-surface-variant',
    },
    {
      icon: 'pin_drop',
      iconBg: 'bg-secondary-fixed',
      iconColor: 'text-on-secondary-fixed',
      chip: 'Cobertura Valle',
      chipClass: 'text-secondary bg-secondary-container/40 font-bold',
      value: `${this.totalDistritos()}`,
      valueColor: 'text-secondary',
      title: 'Distritos en la red',
      text: 'Huancayo, El Tambo, Chilca y distritos vecinos.',
      footIcon: 'verified',
      footLabel: 'Presencia en el Valle del Mantaro',
      footColor: 'text-secondary',
    },
  ]);

  private readonly months = [
    { m: 'Ene', v: 45 },
    { m: 'Feb', v: 58 },
    { m: 'Mar', v: 62 },
    { m: 'Abr', v: 74 },
    { m: 'May', v: 92 },
    { m: 'Jun', v: 97 },
  ];

  readonly yTicks = [0, 25, 50, 75, 100].map((v) => ({ v, y: 180 - v * 1.5 }));

  readonly bars = computed(() => {
    const max = Math.max(...this.months.map((d) => d.v));
    return this.months.map((d, i) => ({
      ...d,
      x: 65 + i * 80,
      cx: 88 + i * 80,
      h: d.v * 1.5,
      y: 180 - d.v * 1.5,
      record: d.v === max,
    }));
  });

  readonly species = computed(() => {
    const total = this.totalMascotas() || 1;
    const perros = this.totalPerros();
    const gatos = this.totalGatos();
    const pctPerros = Math.round((perros / total) * 100);

    return [
      {
        name: 'Caninos',
        pct: pctPerros,
        detail: `${perros} perritos en adopción`,
        stroke: 'stroke-primary',
        dot: 'bg-primary',
        color: 'text-primary',
      },
      {
        name: 'Felinos',
        pct: 100 - pctPerros,
        detail: `${gatos} gatitos en adopción`,
        stroke: 'stroke-secondary',
        dot: 'bg-secondary',
        color: 'text-secondary',
      },
    ];
  });

  readonly donutSegments = computed(() => {
    const c = 2 * Math.PI * 38;
    let acc = 0;
    return this.species().map((s) => {
      const len = (s.pct / 100) * c;
      const seg = { stroke: s.stroke, dash: `${len} ${c}`, offset: -acc };
      acc += len;
      return seg;
    });
  });

  readonly districts = computed(() => {
    const refugios = this.mascotasService.refugios;
    const total = this.totalAdoptadas() || 1;
    const suma = (distritos: string[]) =>
      refugios
        .filter((refugio) => distritos.includes(refugio.distrito))
        .reduce((acumulado, refugio) => acumulado + refugio.adoptadas, 0);

    const elTambo = suma(['El Tambo']);
    const huancayo = suma(['Huancayo Centro']);
    const chilca = suma(['Chilca']);
    const otros = total - elTambo - huancayo - chilca;
    const pct = (cantidad: number) => Math.round((cantidad / total) * 100);

    return [
      {
        name: 'El Tambo',
        icon: 'location_city',
        iconColor: 'text-primary',
        labelColor: 'text-primary',
        count: elTambo,
        pct: pct(elTambo),
        bar: 'bg-primary',
      },
      {
        name: 'Huancayo Centro',
        icon: 'domain',
        iconColor: 'text-primary',
        labelColor: 'text-on-surface',
        count: huancayo,
        pct: pct(huancayo),
        bar: 'bg-primary-container',
      },
      {
        name: 'Chilca',
        icon: 'park',
        iconColor: 'text-secondary',
        labelColor: 'text-secondary',
        count: chilca,
        pct: pct(chilca),
        bar: 'bg-secondary',
      },
      {
        name: 'Pilcomayo, San Agustín y otros',
        icon: 'terrain',
        iconColor: 'text-outline',
        labelColor: 'text-on-surface-variant',
        count: otros,
        pct: pct(otros),
        bar: 'bg-outline-variant',
      },
    ];
  });

  readonly stories = [
    {
      name: 'Chaska',
      adopter: 'Valeria',
      place: 'Palián, Huancayo',
      badge: 'Adoptada',
      img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBvROcCZmQQMyd4iS_mLbyl0aU8uWzpORG5cQsvBXhnOS1oxjcs1WBgJcWytmlhT-42bYzn5-tG7hE8Ppiotkh4dzqwQHGa2QxHEVlJpMhiNBBqc9Y-4ItfgmRuEPqanHjJQwq0kJ3nCO_tiHpPseysZxtwFqqWON8QrYRk9EiAnsErdXUYhXlpngrLUCekKCzHtHid0SCqpqzqXV1I7IOOiLjYb4zqORxvYVbwadZx',
      alt: 'Perrita mestiza andina de color caramelo con pañuelo azul mirando feliz desde el porche de una casa en Palián, Huancayo',
      before: 'Rescatada en la ribera del Río Shullcas con frío, desnutrición y temor.',
      after:
        'Ahora duerme abrigada junto a la chimenea y pasea feliz todas las mañanas por Palián.',
      footIcon: 'verified_user',
      footLabel: 'Vacunada y esterilizada en albergue San Roque',
      footColor: 'text-primary',
    },
    {
      name: 'Negrito',
      adopter: 'Carlos',
      place: 'El Tambo',
      badge: 'Adoptado',
      img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAuV6l1P9JQqB7n1zO0hOb18uK6zLtBVXKCU5CugANf6BoScY2QrEMzKQB1X3-LDbHCT8z3oMhRU6ydqAOoiHClf8zQRpgOf1he8_TeeRuRb-BkrV4U8TUlkL0luoSSyVXkRcqjTtb-NtbcQZ7T6ikbN15_24GI4wVxtQd1MnigBn8szA6XEWbYetnj3brmykICYWZqDD11sy8Tll9UvKLHnEJqSY67hrFbxpgC1vyo',
      alt: 'Perro negro mediano con pelaje brillante jugando en un jardín con césped verde en El Tambo, junto a una pelota roja y una familia cariñosa',
      before: 'Callejero en el mercado de Chilca con patita lastimada y desconfianza.',
      after: 'Guardián amoroso de una familia con jardín amplio y niños que lo adoran.',
      footIcon: 'favorite',
      footLabel: 'Recuperación motriz completa al 100%',
      footColor: 'text-secondary',
    },
    {
      name: 'Michi Wanka',
      adopter: 'Sonia',
      place: 'San Carlos, Huancayo',
      badge: 'Adoptado',
      img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCC8k2c3-P0ZIxhqaVdzhq4xwyZ_yTQv9HIyyDijh9pAjZTwBIeFAXTjo-ZYd0mhCB-xpiWqoKHiDsg2bJldJnyifIV8hu6Aq9dY0efm_a2pfHrvumfkDz9ZHRApGMxI7n_rMD8naCgr1dbveNgQhaiPbieCVxQjqzin3NFUBUs7RQqPFkU7ftKj-QvpEYTbIMZn26XTmks-qZvdlJUYNqt3dkj6n9EskuNIdqLjvOJ',
      alt: 'Gatito calicó tricolor descansando en un alféizar soleado con vista al valle andino de Huancayo, sobre una manta de lana andina',
      before: 'Gatito huérfano de 2 meses rescatado en una caja cerca de San Carlos.',
      after: 'El compañero inseparable de juegos y tareas escolares de una niña de 7 años.',
      footIcon: 'cruelty_free',
      footLabel: 'Nutrición clínica y esquema triple felina al día',
      footColor: 'text-primary-container',
    },
  ];
}
