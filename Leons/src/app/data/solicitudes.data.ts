export type EstadoSolicitud = 'active' | 'completed';

export interface Etapa {
  titulo: string;
  detalle: string;
  destacado?: boolean;
}

export interface Cita {
  fecha: string;
  direccion: string;
  coordinadora: string;
}

export interface Mensaje {
  iniciales: string;
  nombre: string;
  rol: string;
  texto: string;
}

export interface Cierre {
  titulo: string;
  texto: string;
  controlTitulo: string;
  controlFecha: string;
  controlLugar: string;
}

export interface Solicitud {
  id: number;
  estado: EstadoSolicitud;
  nombre: string;
  fichaId: number;
  fotoSrc: string;
  fotoAlt: string;
  chipTexto: string;
  chipClase: string;
  refugio: string;
  lugar: string;
  exp: string;
  fechaTexto: string;
  badgeTexto: string;
  badgeClase: string;
  puntoClase: string;
  pasoTexto: string;
  pasoTextoClase: string;
  headerClase: string;
  iconoMini: string;
  iconoMiniClase: string;
  paso: number;
  barraClase: string;
  etapas: Etapa[];
  cita?: Cita;
  mensaje?: Mensaje;
  tiempoRespuesta?: string;
  whatsapp?: string;
  cierre?: Cierre;
}

export const HEADER_SOLICITUD_ACTIVA =
  'from-surface-container-lowest via-surface-container-low/40 to-surface-container-lowest';

const G = 'https://lh3.googleusercontent.com/aida-public/';

/**
 * Solicitudes de demostración. Son la base de la vista "Mis Solicitudes";
 * las enviadas desde la ficha de una mascota se guardan por encima de estas.
 */
export const SOLICITUDES_DEMO: readonly Solicitud[] = [
  {
    id: 1,
    estado: 'active',
    nombre: 'Chaska',
    fichaId: 1,
    fotoSrc:
      G +
      'AB6AXuCN4t9m_piF3CfB4-5hq6Vc_VR6kZNN9Hysjkm4mc_sVX117gSdvWIEiJ804dZaz43ShyxKVnU-U0ypzoJR9TC95uzZ14tpfTWfZ2GaloqM1KvEy6HbP-mzfJXsxkYxZhIJgPQljzyqZYArK4A1ooqZjjz2RMd8bVRAKAg-z85Tkx0mpkzMTp6JbOQ7Z9Zs0hkQf0if1DU1wz3ia5JKlBzgy8vVbVSJeCmUb4rd603L',
    fotoAlt: 'Chaska, perrita mestiza dorada y amigable, descansando al sol entre plantas',
    chipTexto: '1.5 años • Hembra',
    chipClase: 'bg-surface-container text-on-surface-variant',
    refugio: 'Albergue Huellitas Wanka',
    lugar: 'El Tambo, Huancayo',
    exp: '#SOL-HYO-2025-084',
    fechaTexto: 'Enviada el 18 de Mayo, 2025 (Hace 2 días)',
    badgeTexto: 'Visita Programada',
    badgeClase: 'bg-secondary-fixed text-secondary',
    puntoClase: 'bg-secondary animate-ping',
    pasoTexto: 'Paso 3 de 5',
    pasoTextoClase: 'text-secondary',
    headerClase: HEADER_SOLICITUD_ACTIVA,
    iconoMini: 'pets',
    iconoMiniClase: 'bg-surface-container-lowest text-primary',
    paso: 3,
    barraClase: 'bg-secondary',
    etapas: [
      { titulo: '1. Enviada', detalle: '18 May' },
      { titulo: '2. Revisión de Ficha', detalle: 'Aprobada', destacado: true },
      { titulo: '3. Entrevista / Visita', detalle: '¡Agendada!' },
      { titulo: '4. Aprobación', detalle: 'Pendiente' },
      { titulo: '5. Adopción Feliz', detalle: 'Pendiente' },
    ],
    cita: {
      fecha: 'Sábado 24 Mayo • 10:30 am',
      direccion: 'Jr. Nemesio Ráez, El Tambo',
      coordinadora: 'Silvia Mallqui',
    },
    mensaje: {
      iniciales: 'SM',
      nombre: 'Silvia Mallqui',
      rol: 'Coord. Huellitas Wanka',
      texto:
        '¡Hola! Revisamos tus datos y el cerco de tu jardín es completamente apto para Chaska. Nos vemos este sábado para la visita y conocer a la familia en persona.',
    },
    whatsapp: 'https://wa.me/51964123456',
  },
  {
    id: 2,
    estado: 'active',
    nombre: 'Inti',
    fichaId: 2,
    fotoSrc:
      G +
      'AB6AXuCTURF4JodBK6Jc1TEBwTesPDSNbdVF4oOCYd-gS8cf7TrDoFUAbGyalPjmYA3R2GIZUFeRgxeFfSACjNwjoNuYgc4H3aQXA5t1N2qhve0mn6rtVnPicY1jiI3GxCWjFbrdhsj3VLkP4YnS3lG5UeUohbTA4JtStLyQex1LPpJ_JBYQDeCsH-nLpwHULziK9DNYVkQ1QCUzI8NCbAKZ15Mz147Uq9r_V1k14raWwLQH',
    fotoAlt: 'Inti, gatito atigrado de ojos verdes sentado sobre una manta tejida',
    chipTexto: '11 meses • Macho',
    chipClase: 'bg-surface-container text-on-surface-variant',
    refugio: 'Hogar San Roque Chilca',
    lugar: 'Chilca Alta, Huancayo',
    exp: '#SOL-HYO-2025-091',
    fechaTexto: 'Enviada el 19 de Mayo, 2025 (Ayer)',
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
      { titulo: '1. Enviada', detalle: '19 May' },
      { titulo: '2. En Revisión', detalle: 'Evaluando ficha' },
      { titulo: '3. Visita / Entrevista', detalle: 'Pendiente' },
      { titulo: '4. Aprobación', detalle: 'Pendiente' },
      { titulo: '5. Adopción Feliz', detalle: 'Pendiente' },
    ],
    tiempoRespuesta: '24 a 48 horas',
    whatsapp: 'https://wa.me/51954987654',
  },
  {
    id: 3,
    estado: 'completed',
    nombre: 'Wanka',
    fichaId: 3,
    fotoSrc:
      G +
      'AB6AXuBzeGTWKcimqX9IKXy9LJ9A9gahTjBqGakSVZOd0_A42_c-YJ5ztsWtuQpknhCZuhqaiHEpVvWl-r2yLCDnJDp_dtIPPBJN1PyVD5r0cWdDonyJy00zV0TSG-YDU4TOIPlVpsOMFs1GcS5ED9nfpEoAIXpFgiB2CBXZ-LXqfp3KlMrHyC3ZlH0o1cKduqds6_mPMzBaVkoAQhmjmn_quj-yxXRYGHkYJkC-l7NtdZvl',
    fotoAlt: 'Wanka, perro pastor mestizo con un pañuelo andino de colores, sentado en un patio',
    chipTexto: '¡Adoptado en Casa!',
    chipClase: 'bg-secondary-fixed text-secondary font-bold',
    refugio: 'Refugio Corazón Canino Huancayo',
    lugar: 'El Tambo',
    exp: '#SOL-HYO-2025-012',
    fechaTexto: 'Adopción concretada: 12 de Febrero, 2025',
    badgeTexto: 'Adopción Concluida',
    badgeClase: 'bg-secondary text-on-secondary',
    puntoClase: '',
    pasoTexto: 'Proceso finalizado',
    pasoTextoClase: 'text-secondary',
    headerClase: 'from-secondary-fixed/20 via-surface-container-lowest to-surface-container-lowest',
    iconoMini: 'verified',
    iconoMiniClase: 'bg-secondary text-on-secondary',
    paso: 5,
    barraClase: 'bg-secondary',
    etapas: [],
    cierre: {
      titulo: '¡Wanka ya es parte de tu familia!',
      texto:
        'Gracias por abrir tu corazón y brindarle un hogar cálido en el Valle del Mantaro. Tu contrato de adopción digital y certificado veterinario están disponibles en tu perfil.',
      controlTitulo: 'Control Veterinario Trimestral',
      controlFecha: 'Junio 2025',
      controlLugar: 'Veterinaria El Tambo',
    },
  },
];
