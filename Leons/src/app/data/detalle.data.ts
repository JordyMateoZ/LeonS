import { Mascota, Rasgo } from './mascotas.data';

export interface Cuidado {
  icono: string;
  titulo: string;
  texto: string;
}

export interface Requisito {
  icono: string;
  titulo: string;
  texto: string;
}

export interface Pregunta {
  pregunta: string;
  respuesta: string;
}

export interface Cita {
  texto: string;
  autor: string;
}

const RASGO_BASE = 'inline-flex items-center gap-1.5 font-label-md text-label-md px-4 py-2.5 rounded-full ';

const RASGOS_POR_ESPECIE: Record<'perro' | 'gato', Rasgo[]> = {
  perro: [
    { icono: 'toys', texto: 'Juguetón y cariñoso', clase: RASGO_BASE + 'bg-primary-fixed text-on-primary-fixed shadow-sm', iconoClase: '' },
    { icono: 'chair', texto: 'Tranquilo en interiores', clase: RASGO_BASE + 'bg-surface-container text-on-surface', iconoClase: 'text-secondary' },
    { icono: 'family_restroom', texto: 'Excelente con niños', clase: RASGO_BASE + 'bg-secondary-container text-on-secondary-container shadow-sm', iconoClase: '' },
    { icono: 'group', texto: 'Sociable con otros perros', clase: RASGO_BASE + 'bg-surface-container text-on-surface', iconoClase: 'text-primary' },
    { icono: 'nordic_walking', texto: 'Acostumbrado a paseos con correa', clase: RASGO_BASE + 'bg-surface-container text-on-surface', iconoClase: 'text-secondary' },
  ],
  gato: [
    { icono: 'favorite', texto: 'Cariñoso y ronroneador', clase: RASGO_BASE + 'bg-primary-fixed text-on-primary-fixed shadow-sm', iconoClase: '' },
    { icono: 'chair', texto: 'Disfruta espacios tranquilos', clase: RASGO_BASE + 'bg-surface-container text-on-surface', iconoClase: 'text-secondary' },
    { icono: 'group', texto: 'Sociable con otros gatos', clase: RASGO_BASE + 'bg-surface-container text-on-surface', iconoClase: 'text-primary' },
    { icono: 'cleaning_services', texto: 'Limpio con su arenero', clase: RASGO_BASE + 'bg-secondary-container text-on-secondary-container shadow-sm', iconoClase: '' },
    { icono: 'apartment', texto: 'Se adapta a departamento', clase: RASGO_BASE + 'bg-surface-container text-on-surface', iconoClase: 'text-secondary' },
  ],
};

export const REQUISITOS: Requisito[] = [
  {
    icono: 'home_work',
    titulo: 'Vivienda con cerco perimétrico seguro:',
    texto: 'Casa con portón cerrado o departamento propio / alquilado pet-friendly en Huancayo, El Tambo, Chilca o zonas aledañas.',
  },
  {
    icono: 'roofing',
    titulo: 'Sin cadenas ni techos desprotegidos:',
    texto: 'Compromiso firmado de no mantener a la mascota a la intemperie, amarrada ni en azoteas expuestas al frío o la lluvia.',
  },
  {
    icono: 'handshake',
    titulo: 'Visita previa y seguimiento respetuoso:',
    texto: 'Conocer a la mascota en persona y permitir seguimiento virtual fotográfico a los 1, 3 y 6 meses de integración.',
  },
  {
    icono: 'badge',
    titulo: 'Documentación básica ciudadana:',
    texto: 'DNI original de la persona mayor de edad titular y copia de recibo de servicios (luz o agua) para acreditar domicilio.',
  },
];

const HISTORIAS_ESPECIALES: Record<number, string[]> = {
  1: [
    'Chaska fue encontrada en noviembre cerca de la ribera del Río Shullcas, en El Tambo. Estaba protegiendo con valentía a sus cuatro cachorritos bajo un cobertizo precario de calamina, buscando abrigo contra las heladas nocturnas del valle.',
    'Gracias a una alerta ciudadana coordinada con la red de voluntarias de Albergue Huellitas Wanka, Chaska y su camada fueron puestas a salvo. Sus pequeños ya fueron adoptados en hogares responsables y ahora le toca a ella encontrar a su propia familia.',
    'Busca una familia comprometida en el Valle del Mantaro que comprenda que un perro no es una alarma de azotea ni un vigilante de garaje, sino un miembro más del hogar.',
  ],
};

const CITAS_ESPECIALES: Record<number, Cita> = {
  1: {
    texto: 'Chaska es de esas perritas que te miran con absoluta gratitud. Le encanta apoyar suavemente su hocico en tu regazo mientras descansas. No ladra sin motivo, duerme en su manta y se porta como una dama en casa.',
    autor: 'Lic. Silvia Mallqui, Coordinadora de Acogida',
  },
};

const CUIDADOS_ESPECIALES: Record<number, Cuidado[]> = {
  1: [
    { icono: 'check', titulo: 'Esterilizada Certificada', texto: 'Campaña Municipal El Tambo (ene 2025). Cirugía limpia y cicatrización completada.' },
    { icono: 'vaccines', titulo: 'Vacunas al Día', texto: 'Séxtuple canina y antirrábica vigentes. Carnet físico original listo para entrega.' },
    { icono: 'verified', titulo: 'Desparasitación Completa', texto: 'Protección interna y externa al día. Tratamiento aplicado hace 15 días.' },
    { icono: 'fitness_center', titulo: 'Condición Física Óptima', texto: 'Recuperada de desnutrición. Peso ideal de 14 kg, pelaje brillante y excelente capacidad respiratoria para la altura.' },
  ],
};

export function rasgosDe(m: Mascota): Rasgo[] {
  return m.rasgos ?? RASGOS_POR_ESPECIE[m.especie];
}

export function historiaDe(m: Mascota): string[] {
  if (HISTORIAS_ESPECIALES[m.id]) {
    return HISTORIAS_ESPECIALES[m.id];
  }
  const rescatado = m.sexo === 'Hembra' ? 'rescatada' : 'rescatado';
  return [
    `${m.nombre} fue ${rescatado} en ${m.lugar} y desde entonces recibe atención veterinaria y mucho cariño en ${m.refugio}.`,
    `Hoy vive en un hogar de acogida temporal, donde se está recuperando y aprendiendo rutinas de convivencia. Su temperamento es ${m.energia.toLowerCase()} y ya comparte espacio con otras mascotas.`,
    'Busca una familia responsable en el Valle del Mantaro que le ofrezca un hogar seguro, alimentación adecuada, atención veterinaria y seguimiento post-adopción.',
  ];
}

export function citaDe(m: Mascota): Cita | undefined {
  return CITAS_ESPECIALES[m.id];
}

function iconoPara(texto: string): string {
  const t = texto.toLowerCase();
  if (t.includes('esteriliz')) return 'check';
  if (t.includes('vacun')) return 'vaccines';
  if (t.includes('desparasit')) return 'verified';
  if (t.includes('test felino')) return 'science';
  if (t.includes('compromiso')) return 'schedule';
  return 'health_and_safety';
}

function textoPara(texto: string): string {
  const t = texto.toLowerCase();
  if (t.includes('esteriliz')) return 'Procedimiento certificado y recuperación completada.';
  if (t.includes('vacun')) return 'Esquema de vacunas vigente y carnet listo para entrega.';
  if (t.includes('desparasit')) return 'Protección interna y externa al día.';
  if (t.includes('test felino')) return 'Resultado negativo en las pruebas felinas realizadas.';
  if (t.includes('compromiso')) return 'Se entrega con compromiso formal de esterilización gratuita.';
  return 'Revisión veterinaria y cuidados al día.';
}

export function cuidadosDe(m: Mascota): Cuidado[] {
  if (CUIDADOS_ESPECIALES[m.id]) {
    return CUIDADOS_ESPECIALES[m.id];
  }
  const cuidados = m.salud.map((s) => ({
    icono: iconoPara(s.texto),
    titulo: s.texto,
    texto: textoPara(s.texto),
  }));
  cuidados.push({
    icono: 'fitness_center',
    titulo: 'Condición física óptima',
    texto: 'Peso adecuado, pelaje sano y evaluación veterinaria satisfactoria.',
  });
  return cuidados;
}

export function preguntasDe(m: Mascota): Pregunta[] {
  return [
    {
      pregunta: `¿Puedo conocer a ${m.nombre} antes de decidir?`,
      respuesta: `¡Por supuesto! Coordinamos una visita al hogar temporal para conocer a ${m.nombre} y confirmar la compatibilidad antes de firmar el acta.`,
    },
    {
      pregunta: '¿Cómo es el proceso de entrega?',
      respuesta: `Una vez aprobada tu solicitud, una voluntaria de ${m.refugio} te acompaña en la entrega con el carnet de salud y los implementos básicos de ${m.nombre}.`,
    },
    {
      pregunta: '¿Si vivo en otro distrito del Valle puedo postular?',
      respuesta: 'Sí, recibimos postulaciones de todo el Valle del Mantaro. La única condición es que podamos coordinar la visita de verificación previa.',
    },
  ];
}
