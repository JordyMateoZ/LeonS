export interface Paso {
  icono: string;
  titulo: string;
  texto: string;
  nota: string;
}

export interface PreguntaFrecuente {
  pregunta: string;
  respuesta: string;
}

export const PASOS_ADOPCION: Paso[] = [
  {
    icono: 'search',
    titulo: 'Explora y elige con el corazón',
    texto:
      'Revisa las fichas de perros y gatos disponibles en Huancayo, El Tambo, Chilca y distritos vecinos. Filtra por especie, tamaño, energía y distrito para encontrar una mascota compatible con tu hogar.',
    nota: 'Fichas verificadas por refugios aliados',
  },
  {
    icono: 'edit_document',
    titulo: 'Envía tu solicitud responsable',
    texto:
      'Completa la ficha de adopción con tus datos, las condiciones de tu vivienda y tu disponibilidad de tiempo. El refugio revisará tu postulación y te responderá por WhatsApp en un plazo máximo de 48 horas.',
    nota: 'Respuesta promedio en 48 horas',
  },
  {
    icono: 'handshake',
    titulo: 'Conoce a tu nuevo compañero',
    texto:
      'Coordina una visita presencial en el refugio o casa de acogida. La entrevista y el encuentro permiten confirmar la compatibilidad entre la mascota, tu familia y tu estilo de vida.',
    nota: 'Encuentro presencial y entrevista',
  },
  {
    icono: 'home_pin',
    titulo: 'Firma el compromiso y recibe seguimiento',
    texto:
      'Firma el acta de tenencia responsable, recibe el carnet de salud y los implementos básicos. El refugio hará seguimiento fotográfico a los 1, 3 y 6 meses para asegurar una adaptación feliz.',
    nota: 'Acompañamiento post-adopción',
  },
];

export const PASOS_REFUGIO: Paso[] = [
  {
    icono: 'app_registration',
    titulo: 'Registra tu albergue o rescate',
    texto:
      'Crea una cuenta como refugio o rescatista independiente con tu distrito, datos de contacto y una breve descripción de tu labor en el Valle del Mantaro.',
    nota: 'Registro gratuito',
  },
  {
    icono: 'pets',
    titulo: 'Publica mascotas con información completa',
    texto:
      'Agrega fotos, historia, estado de salud, temperamento y requisitos de adopción. Las fichas transparentes generan más confianza y mejores adopciones.',
    nota: 'Ficha guiada paso a paso',
  },
  {
    icono: 'fact_check',
    titulo: 'Evalúa y da seguimiento',
    texto:
      'Revisa las solicitudes, coordina visitas y acompaña la adaptación de cada mascota. LeonS te conecta con voluntarios y veterinarias solidarias de la zona.',
    nota: 'Red de apoyo local',
  },
];

export const FAQS: PreguntaFrecuente[] = [
  {
    pregunta: '¿La adopción tiene algún costo en LeonS?',
    respuesta:
      'No. LeonS es una iniciativa comunitaria sin fines de lucro. Ningún refugio aliado puede cobrar por la entrega de una mascota. Solo se solicita cubrir, si la familia puede, gastos veterinarios ya realizados y siempre de forma transparente.',
  },
  {
    pregunta: '¿Puedo adoptar si vivo en un departamento?',
    respuesta:
      'Sí. Evaluamos el espacio, el tiempo disponible y el temperamento de la mascota. Muchos gatos y perros adultos de energía baja se adaptan muy bien a departamentos con paseos diarios y enriquecimiento ambiental.',
  },
  {
    pregunta: '¿Qué documentos necesito para postular?',
    respuesta:
      'DNI original de la persona mayor de edad titular y una copia del recibo de luz o agua para acreditar domicilio. En el caso de alquileres, pedimos confirmar que la vivienda acepta mascotas.',
  },
  {
    pregunta: '¿Puedo adoptar si vivo fuera de Huancayo?',
    respuesta:
      'Recibimos postulaciones de todo el Valle del Mantaro. La condición es poder coordinar la visita de verificación y el seguimiento post-adopción de forma presencial o virtual.',
  },
  {
    pregunta: '¿Qué pasa si la adaptación no funciona?',
    respuesta:
      'La mascota nunca debe ser abandonada ni regalada sin avisar. El refugio de origen acompaña el proceso y, si es necesario, recibe nuevamente al animal para buscar una familia más compatible.',
  },
  {
    pregunta: '¿Cómo puedo ayudar si no puedo adoptar?',
    respuesta:
      'Puedes ser hogar temporal, donar alimentos o medicinas, apoyar en campañas de esterilización o difundir las fichas de adopción. Escríbenos por WhatsApp y te conectamos con un refugio aliado.',
  },
];
