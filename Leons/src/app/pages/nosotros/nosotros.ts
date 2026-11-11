import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MascotasService } from '../../services/mascotas.service';

type Tab = 'adopters' | 'shelters';

@Component({
  selector: 'app-nosotros',
  imports: [RouterLink],
  templateUrl: './nosotros.html',
  styleUrl: './nosotros.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Nosotros {
  private readonly mascotasService = inject(MascotasService);
  private readonly document = inject(DOCUMENT);

  readonly whatsappUrl = 'https://wa.me/51964892110';

  readonly activeTab = signal<Tab>('adopters');
  readonly openFaq = signal<number | null>(null);

  readonly totalAdoptadas = computed(() =>
    this.mascotasService.refugios.reduce((total, refugio) => total + refugio.adoptadas, 0),
  );
  readonly totalRefugios = computed(() => this.mascotasService.refugios.length);
  readonly totalDistritos = computed(
    () => new Set(this.mascotasService.refugios.map((refugio) => refugio.distrito)).size,
  );

  setTab(tab: Tab) {
    this.activeTab.set(tab);
  }

  toggleFaq(index: number) {
    this.openFaq.update((current) => (current === index ? null : index));
  }

  scrollTo(id: string) {
    const elemento = this.document.getElementById(id);
    elemento?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
  }

  readonly trustBadges = [
    {
      icon: 'volunteer_activism',
      iconColor: 'text-primary',
      title: '100% Gratuito',
      text: 'Sin cobro por adopción',
      wide: false,
    },
    {
      icon: 'terrain',
      iconColor: 'text-secondary',
      title: 'Valle del Mantaro',
      text: 'El Tambo, Chilca y Huancayo',
      wide: false,
    },
    {
      icon: 'favorite',
      iconColor: 'text-tertiary',
      title: 'Compromiso',
      text: 'Acta de tenencia ética',
      wide: true,
    },
  ];

  readonly founders = [
    {
      name: 'Lucía Quispe Mayta',
      role: 'Co-fundadora & Coordinadora Veterinaria',
      img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBS8CXa33ltDz-eLtWfhqwQ-CdlbtOKu-wesOhHqGsVUQH3wrN5ZnM6nB0HIAb5JY5HEm0Qrj-38I-TBczgSXKmQg8nrTG4miEua4M5B4DV087vB_V8bCrOTgptmarNV2BP1FnSeGyoDQRUZuMQuAJmW_ZAITcq-9lqwZqky9ehJ54-DwcxlNlbIAX3nZOfOarle0OtT4Ecedc3SemWz1N_5dRWafqJ2fajxP7F0Gpx',
      imgAlt:
        'Dra. Lucía Quispe Mayta, Co-fundadora y Coordinadora Veterinaria de LeonS Huancayo',
      badgeIcon: 'medication',
      badgeLabel: 'Salud Animal',
      badgeClass: 'bg-secondary text-on-secondary',
      bio: 'Egresada de Medicina Veterinaria y Zootecnia (UNCP Huancayo). Lidera las jornadas de esterilización barrial, verificación médica pre-adopción y protocolos de prevención frente a las heladas del valle.',
      footIcon: 'verified_user',
      footLabel: 'UNCP Junín',
    },
    {
      name: 'Diego Huamán Alanya',
      role: 'Co-fundador & Coordinador de Tecnología',
      img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCwfaLmvRjttIRgBSJlKz4gqH6L2GJjVos7xuZllL9Tu1lKXIs2Ep777It7OtKK-wlObFGZlX8JstJhIeGI6X-9z1cRqTer9v_uMrMGaeTB8UpXTpfiYjoHrAg_fr0d_bhkPxeRJC42NvbUYuAFbwAYQfaCnI3NCOk7wcrLtgqLP9M3sTS8k9HTkvjyMtLDm_Ep2gKjQBIDYLG4JFQk7H8r7a6o1EgGWPPVCqI9XkVE',
      imgAlt:
        'Ing. Diego Huamán Alanya, Co-fundador y Coordinador de Tecnología Comunitaria de LeonS Huancayo',
      badgeIcon: 'code',
      badgeLabel: 'Tecnología Social',
      badgeClass: 'bg-primary text-on-primary',
      bio: 'Ingeniero de Sistemas de la comunidad wanka y activista animalista en El Tambo. Diseñó el sistema de filtrado accesible de fichas de rescate para conectar albergues vulnerables con vecinos solidarios.',
      footIcon: 'devices',
      footLabel: 'El Tambo, Huancayo',
    },
  ];

  readonly pillars = [
    {
      icon: 'pets',
      iconBg: 'bg-primary-fixed',
      iconColor: 'text-primary',
      title: 'Adopción Responsable',
      before:
        'Priorizamos el bienestar animal permanente. Evaluamos el espacio físico seguro, la capacidad afectiva y el compromiso familiar ',
      bold: 'anti-heladas andinas',
      after: ' (cero mascotas durmiendo a la intemperie en azoteas).',
      footIcon: 'done_all',
      footLabel: 'Seguimiento a 1, 3 y 6 meses',
      footColor: 'text-primary',
    },
    {
      icon: 'balance',
      iconBg: 'bg-secondary-container',
      iconColor: 'text-secondary',
      title: 'Transparencia Radical',
      before: '',
      bold: 'Cero intermediación lucrativa',
      after:
        '. Información verificable de cada rescatista, trazabilidad de historias clínicas veterinarias con número de colegiatura y libre acceso público a los expedientes de donación.',
      footIcon: 'verified',
      footLabel: 'Médicos veterinarios colegiados',
      footColor: 'text-secondary',
    },
    {
      icon: 'groups_3',
      iconBg: 'bg-tertiary-container/30',
      iconColor: 'text-tertiary',
      title: 'Comunidad Solidaria',
      before:
        'Fortalecemos el tejido social del Valle del Mantaro. Creamos una red activa entre albergues de base, clínicas veterinarias aliadas y familias adoptantes para campañas masivas de esterilización y auxilio.',
      bold: '',
      after: '',
      footIcon: 'handshake',
      footLabel: 'Red vecinal en El Tambo y Chilca',
      footColor: 'text-tertiary',
    },
  ];

  readonly adopterSteps = [
    {
      n: '01',
      icon: 'search',
      iconBg: 'bg-primary-fixed',
      iconColor: 'text-primary',
      title: 'Explora las mascotas',
      text: 'Filtra por especie (perros y gatos), tamaño, edad y distrito (Huancayo, El Tambo, Chilca).',
      tag: 'Catálogo actualizado',
      tagClass: 'text-primary bg-primary-fixed/40',
    },
    {
      n: '02',
      icon: 'assignment',
      iconBg: 'bg-primary-fixed',
      iconColor: 'text-primary',
      title: 'Llena la ficha',
      text: 'Formulario digital guiado de 5 pasos para conocer las condiciones de tu vivienda y estilo de vida.',
      tag: 'Toma menos de 4 min',
      tagClass: 'text-primary bg-primary-fixed/40',
    },
    {
      n: '03',
      icon: 'check_circle',
      iconBg: 'bg-secondary-container',
      iconColor: 'text-secondary',
      title: 'Revisión del refugio',
      text: 'El rescatista evalúa tu perfil ético y te contacta vía WhatsApp o llamada en 24 a 48 horas.',
      tag: 'Respuesta oportuna',
      tagClass: 'text-secondary bg-secondary-container/50',
    },
    {
      n: '04',
      icon: 'volunteer_activism',
      iconBg: 'bg-secondary-container',
      iconColor: 'text-secondary',
      title: 'Conoce a tu mascota',
      text: 'Encuentro presencial en el albergue temporal o visita amigable para evaluar afinidad mutua.',
      tag: 'Firma de compromiso',
      tagClass: 'text-secondary bg-secondary-container/50',
    },
    {
      n: '05',
      icon: 'verified_user',
      iconBg: 'bg-tertiary-container/30',
      iconColor: 'text-tertiary',
      title: 'Seguimiento continuo',
      text: 'Carné digital con historial de vacunas, acta de tenencia y asesoría de adaptación sin costo.',
      tag: 'Seguimiento 6m',
      tagClass: 'text-tertiary bg-tertiary-container/20',
    },
  ];

  readonly shelterPhases = [
    {
      icon: 'how_to_reg',
      iconBg: 'bg-secondary-container',
      iconColor: 'text-secondary',
      label: 'Fase 1',
      title: 'Registro Verificado Gratuito',
      text: 'Inscribe tu albergue u hogar de rescate. Nuestro equipo coordina una visita amigable de validación sanitaria y legal en Huancayo, El Tambo o Chilca.',
    },
    {
      icon: 'post_add',
      iconBg: 'bg-primary-fixed',
      iconColor: 'text-primary',
      label: 'Fase 2',
      title: 'Publicación y Difusión de Fichas',
      text: 'Crea los perfiles de tus rescatados con fotografía, carné de vacunas y descripción de temperamento. Accede a difusión directa en redes de Junín.',
    },
    {
      icon: 'fact_check',
      iconBg: 'bg-tertiary-container/30',
      iconColor: 'text-tertiary',
      label: 'Fase 3',
      title: 'Gestión Integral de Solicitudes',
      text: 'Recibe postulaciones pre-filtradas, califica expedientes, coordina citas por WhatsApp y genera el acta formal de adopción con valor legal.',
    },
  ];

  readonly faqs: {
    q: string;
    before?: string;
    bold?: string;
    link?: string;
    after?: string;
    items?: { strong?: string; text: string }[];
  }[] = [
    {
      q: '¿Tiene costo adoptar una mascota a través de LeonS?',
      bold: 'La adopción a través de LeonS es 100% gratuita.',
      after:
        ' Ningún albergue verificado ni rescatista independiente cobra un solo sol por la entrega de un animalito. En casos donde la mascota requiera completar refuerzos de vacunas quíntuples o antirrábicas, se puede coordinar directamente la atención voluntaria en una clínica veterinaria con tarifa solidaria.',
    },
    {
      q: '¿Qué requisitos necesito para postular a una adopción?',
      before: 'Los requisitos básicos son:',
      items: [
        {
          text: 'Ser mayor de 18 años y portar DNI vigente con residencia en la provincia de Huancayo o aledaños del Valle del Mantaro.',
        },
        {
          text: 'Contar con un espacio seguro cerrado (muros y rejas adecuadas) que impida escapes a la vía pública.',
        },
        {
          strong: 'Filtro ético anti-heladas:',
          text: 'Compromiso formal de no tener a la mascota en azoteas desprotegidas durante las heladas nocturnas de Huancayo (temperaturas menores a 5°C).',
        },
        {
          text: 'Consentimiento unánime de todos los miembros del hogar familiar.',
        },
      ],
    },
    {
      q: '¿Cuánto demora la respuesta a mi ficha de adopción?',
      before: 'Los albergues y rescatistas gestionan las solicitudes en un plazo promedio de ',
      bold: '24 a 48 horas hábiles',
      after:
        '. Te contactarán directamente al número de WhatsApp o llamada telefónica ingresado en tu ficha para coordinar una breve entrevista telefónica o presencial.',
    },
    {
      q: '¿Qué sucede si por una emergencia de fuerza mayor no puedo seguir cuidando a mi mascota?',
      before: 'El acta de adopción responsable estipula que ',
      bold:
        'bajo ninguna circunstancia el animal debe ser abandonado, regalado a terceros sin previo aviso ni vendido',
      after:
        '. El adoptante debe notificar de inmediato a LeonS o al refugio de origen para activar la red de reubicación responsable y brindarle un hogar temporal seguro.',
    },
    {
      q: '¿Cómo puedo registrar mi refugio o rescate independiente en la plataforma?',
      before: 'Puedes acceder al módulo de ',
      link: 'Refugios Aliados',
      after:
        ' y hacer clic en "Registrar mi refugio". Nuestro equipo voluntario revisará tus datos y coordinará una visita de conocimiento mutuo para habilitar tu panel administrativo y publicar a tus rescatados de forma 100% gratuita.',
    },
  ];
}
