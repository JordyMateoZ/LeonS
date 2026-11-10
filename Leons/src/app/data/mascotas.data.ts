export interface SaludItem {
  texto: string;
  ok: boolean;
}

export interface Foto {
  src: string;
  alt: string;
}

export interface Rasgo {
  icono: string;
  texto: string;
  clase: string;
  iconoClase: string;
}

export interface Mascota {
  id: number;
  nombre: string;
  nombreCorto: string;
  especie: 'perro' | 'gato';
  sexo: 'Macho' | 'Hembra';
  generoTexto: string;
  badgeClase: string;
  raza: string;
  edadTexto: string;
  edadAnios: number;
  tamano: 'Pequeño' | 'Mediano' | 'Grande';
  tamanoTexto: string;
  distrito: string;
  lugar: string;
  foto: string;
  alt: string;
  descripcion: string;
  etiqueta: string;
  etiquetaIcono: string;
  etiquetaClase: string;
  salud: SaludItem[];
  esterilizado: boolean;
  vacunado: boolean;
  urgente: boolean;
  refugio: string;
  refugioId: string;
  energia: string;
  fichaId: string;
  actualizado: string;
  galeria?: Foto[];
  rasgos?: Rasgo[];
}

const IMG = 'https://lh3.googleusercontent.com/aida-public/';
const BADGE_PERRO = 'text-primary bg-primary-fixed';
const BADGE_GATO = 'text-secondary bg-secondary-fixed';
const ETQ_SEC = 'bg-secondary text-on-secondary';
const RASGO_BASE = 'inline-flex items-center gap-1.5 font-label-md text-label-md px-4 py-2.5 rounded-full ';

export const MASCOTAS: Mascota[] = [
  {
    id: 1, nombre: 'Chaska', nombreCorto: 'Chaska', especie: 'perro', generoTexto: 'Perra', badgeClase: BADGE_PERRO,
    sexo: 'Hembra', raza: 'Mestiza andina', tamano: 'Mediano', edadTexto: '1.5 años', edadAnios: 1.5,
    tamanoTexto: 'Mediana • 14 kg', distrito: 'El Tambo', lugar: 'El Tambo, Huancayo',
    foto: IMG + 'AB6AXuBlYZJsEt1sietDZeqk5kG3Y4SzQN_vYVzTtOUldONvWE_A9F84LFrc1lsETHa8C_oqBpwdgiCmTHayDy9W3N0DkYdDiSzLbv8mkUgOxJNMo-aBpFzDDhgUTNOfQMhPb5wsBCLGsEbOhRS-JQWjU4uLjBYM4TcHwUT-VrUWCsWC1Bg9ztbcqbEyfBZG78ZNVWg7IvaK82nwoDEQaenmgb7DS8RwYK8iYemzQb2MxtSD',
    alt: 'Chaska, perra mestiza de pelaje dorado, sentada en un jardín soleado de El Tambo',
    descripcion: 'Juguetona, sociable y muy cariñosa. Rescatada junto a sus cachorros, busca una familia que le dé paseos y mucho amor.',
    etiqueta: 'Urgente adopción', etiquetaIcono: 'favorite', etiquetaClase: 'bg-primary text-on-primary',
    salud: [{ texto: 'Esterilizada', ok: true }, { texto: 'Vacunas al día', ok: true }, { texto: 'Desparasitada', ok: true }],
    esterilizado: true, vacunado: true, urgente: true, refugio: 'Albergue Huellitas Wanka', refugioId: 'huellitas-wanka',
    energia: 'Medio-Activo', fichaId: 'LS-HYO-0482', actualizado: 'hace 2 días',
    galeria: [
      { src: IMG + 'AB6AXuBXfFH9WvJU0N9IwDZVMedAr82uorsW-HajzLfW0UqvBG-rwPupSZVuTczOFCfs0IsdXVuokTVlunyks6TnP4jB0oYKafuLKqjvyMQrmIxLrGtQXevk4F8ED3EdSWPdV_GiSyd37X2w-F97MWmQHuCaBcuRYs7DEn-SfP97P8D8ckELGqKkxoeZSmWKzUK1Ia4JW-7ju-w8jPjM1JKonH8VqkHXXTyMxhOL0I_ENtDo', alt: 'Chaska, perrita mestiza de pelaje dorado, al sol en un patio andino de El Tambo' },
      { src: IMG + 'AB6AXuDDu_FaoeWvD6d2vjKR4ij58aUqdrAF0YqGs8ghtdp917Oaf78gYLyv3FBdL6chjWalJeqXPruYFjSjDyYOqhygUglbRn_gIYByg-HdzPa6wwgNGWuWrRiLJ-R1bOAKpcmZWAlsCn_emtVPzhyZPQEjyHBGF1I2UW4vg4YJrwWniOeOR4il5RJ5uNE-9OcfVYGRBHD-u99RiOgXPCK9abLZaVWC1LeoiWfM-_Dtg9sA', alt: 'Primer plano de Chaska sonriendo a la cámara' },
      { src: IMG + 'AB6AXuBlYZJsEt1sietDZeqk5kG3Y4SzQN_vYVzTtOUldONvWE_A9F84LFrc1lsETHa8C_oqBpwdgiCmTHayDy9W3N0DkYdDiSzLbv8mkUgOxJNMo-aBpFzDDhgUTNOfQMhPb5wsBCLGsEbOhRS-JQWjU4uLjBYM4TcHwUT-VrUWCsWC1Bg9ztbcqbEyfBZG78ZNVWg7IvaK82nwoDEQaenmgb7DS8RwYK8iYemzQb2MxtSD', alt: 'Chaska descansando en el jardín del hogar temporal' },
      { src: IMG + 'AB6AXuAYNXvcDXicF4yGf99eYWuSW8r87j23Hg2SIxC-fpGq5xp61kjX6eOxibiRNy9LVYAZlIA8V-rKOUv4UntP_kwUpDnFio3n21Ip1uiUIX0GAPzJQfnuhxKHaL7fh5AcglxaB__yJXJFVmaSMDcdehoWZrb_2LWDjveHmfF8jyu8KkxU4Y-F3DsCXcI0I9Eb5FqN2mKTkyPPJazxGdbnyjZIXZrX6J0-pk7ASm-_AJU1', alt: 'Chaska durmiendo sobre una manta tejida andina' },
      { src: IMG + 'AB6AXuBaRLE5Umat742u89WNzGMuqoMH0HLEcUswO974CUPUgCmApk3a30-Km_NLfNd1HfKWdOkD0AmAbfa0fcf8VhGoi0_n1lcd75V5hpHzV1hjeXT1mVo_YSdqODf7mCne_MR6lrbI5kOuXdcBhAbDlGAazu5TcWoeiDe-13G0lH1KjrxL2TzxzcA8pxptifvkfb0o57dg6OH-wZVYRt2hcGbzQewPwHsrnwrlcrynvGBZ', alt: 'Chaska de pie junto a una voluntaria con montañas de fondo' },
    ],
    rasgos: [
      { icono: 'toys', texto: 'Juguetona y cariñosa', clase: RASGO_BASE + 'bg-primary-fixed text-on-primary-fixed shadow-sm', iconoClase: '' },
      { icono: 'chair', texto: 'Tranquila en interiores', clase: RASGO_BASE + 'bg-surface-container text-on-surface', iconoClase: 'text-secondary' },
      { icono: 'family_restroom', texto: 'Excelente con niños', clase: RASGO_BASE + 'bg-secondary-container text-on-secondary-container shadow-sm', iconoClase: '' },
      { icono: 'group', texto: 'Sociable con otros perros', clase: RASGO_BASE + 'bg-surface-container text-on-surface', iconoClase: 'text-primary' },
      { icono: 'nordic_walking', texto: 'Acostumbrada a paseos con correa', clase: RASGO_BASE + 'bg-surface-container text-on-surface', iconoClase: 'text-secondary' },
      { icono: 'cruelty_free', texto: 'Tolerante con gatos (prueba básica OK)', clase: RASGO_BASE + 'bg-tertiary-container text-on-tertiary-container shadow-sm', iconoClase: '' },
    ],
  },
  {
    id: 2, nombre: 'Inti', nombreCorto: 'Inti', especie: 'gato', generoTexto: 'Gato', badgeClase: BADGE_GATO,
    sexo: 'Macho', raza: 'Atigrado naranja', tamano: 'Pequeño', edadTexto: '11 meses', edadAnios: 0.9,
    tamanoTexto: 'Pequeño • 4 kg', distrito: 'Chilca', lugar: 'Chilca Alta, Huancayo',
    foto: IMG + 'AB6AXuCmgtLfLzJ8l2z1k6UJZq82Xsf6E_NG6GKHXWn3sSFgiS41hfjDOy18B5SeOiI-qUKtVKBh9NYDmaqe_elXpgH0J9EnapMdVRq75TYcolPISeTtaUDCVn6u7hnKDxMBEVyOfUj5DpvGQxuTfZN46Y5nyC3h0bqLnxs_5SjoNFmQfJG-n1WIHsfxl7sqenaV-FLJr-4qMVvGQ_jjDF2Dix0hL_FMHWZgSgc9jGLBev_V',
    alt: 'Inti, gato atigrado naranja con pecho blanco, mirando a la cámara junto a una ventana',
    descripcion: 'Curioso y tranquilo. Le encanta tomar sol junto a la ventana y dormir en un rincón cálido del hogar.',
    etiqueta: 'Listo para hogar', etiquetaIcono: 'eco', etiquetaClase: ETQ_SEC,
    salud: [{ texto: 'Esterilizado', ok: true }, { texto: 'Desparasitado', ok: true }],
    esterilizado: true, vacunado: false, urgente: false, refugio: 'Hogar San Roque Chilca', refugioId: 'hogar-san-roque',
    energia: 'Tranquilo', fichaId: 'LS-HYO-0483', actualizado: 'hace 3 días',
  },
  {
    id: 3, nombre: 'Wanka', nombreCorto: 'Wanka', especie: 'perro', generoTexto: 'Perro', badgeClase: BADGE_PERRO,
    sexo: 'Macho', raza: 'Mestizo pastor', tamano: 'Grande', edadTexto: '2 años', edadAnios: 2,
    tamanoTexto: 'Grande • 22 kg', distrito: 'Pilcomayo', lugar: 'Pilcomayo, Huancayo',
    foto: IMG + 'AB6AXuDqv7tZMJHPzeild1cUmtUNtxny5Xxkc-yd7ShlHWb4YmH7kL3-kZOHjCoYnBYolu5sc0arOfDJbjwZZYoREN5p-IM9tZS6gkWCPWCKRXIllXC2TC13L6SK8xTS8bNo0RHy6vQ-dI_tHahGqwwMnZx9OtvEcYlt4HhiI4NizFaXIFgjqLGcz8udqO9YQQ6VtagT3urYMmKUbcii_FuLlpNSl0gTLGIGWtsipMvdkZaL',
    alt: 'Wanka, perro mestizo pastor de color canela corriendo en un campo verde del Valle del Mantaro',
    descripcion: 'Leal, guardián noble y muy obediente. Disfruta las caminatas y busca una casa amplia con patio cercado.',
    etiqueta: 'Recuperado', etiquetaIcono: 'verified', etiquetaClase: ETQ_SEC,
    salud: [{ texto: 'Esterilizado', ok: true }, { texto: 'Vacunado', ok: true }],
    esterilizado: true, vacunado: true, urgente: false, refugio: 'Rescate Mantaro Solidario', refugioId: 'mantaro-solidario',
    energia: 'Activo', fichaId: 'LS-HYO-0484', actualizado: 'hace 1 día',
  },
  {
    id: 4, nombre: 'Sumaq', nombreCorto: 'Sumaq', especie: 'perro', generoTexto: 'Perra', badgeClase: BADGE_PERRO,
    sexo: 'Hembra', raza: 'Mestiza tricolor', tamano: 'Mediano', edadTexto: '5 meses', edadAnios: 0.4,
    tamanoTexto: 'Mediana • 8 kg', distrito: 'Huancayo Centro', lugar: 'Huancayo Centro',
    foto: IMG + 'AB6AXuBFyqR523mRwko1WqrpQZYXVoOQCWSlNF3w2fluPDUJqD5D2hloclnt_DlRFacOddNoBAavt9bxTk2GDc04WnfE6ONQEjuxGzZW58EwTLsQrkfNoDTRxmIeQmRD70Nwwnt8BSlYLBgwpsrIj77JLOSB1jqsncJ4PvDyBkjf-XtjPAnAgUssK80kxe9F8d-JrzNSh8t1Xt7gDp0gpkqkiEYSdBG9V1vZCED6LMlEjkT2',
    alt: 'Sumaq, cachorra mestiza tricolor de orejas caídas jugando sobre una manta artesanal',
    descripcion: 'Tierna y juguetona. Se lleva bien con niños y otros perros; ideal para una familia activa.',
    etiqueta: 'Cachorra', etiquetaIcono: 'child_care', etiquetaClase: 'bg-tertiary-container text-on-tertiary-container',
    salud: [{ texto: 'Vacunas al día', ok: true }, { texto: 'Compromiso esterilización', ok: false }],
    esterilizado: false, vacunado: true, urgente: false, refugio: 'Red Animalista Wanka', refugioId: 'red-animalista-wanka',
    energia: 'Activo', fichaId: 'LS-HYO-0485', actualizado: 'hace 4 días',
  },
  {
    id: 5, nombre: 'Michi Mantaro', nombreCorto: 'Michi', especie: 'gato', generoTexto: 'Gata', badgeClase: BADGE_GATO,
    sexo: 'Hembra', raza: 'Calicó', tamano: 'Pequeño', edadTexto: '1 año', edadAnios: 1,
    tamanoTexto: 'Pequeña • 3.5 kg', distrito: 'San Agustín de Cajas', lugar: 'San Agustín de Cajas',
    foto: IMG + 'AB6AXuCzLhpFOqD4Xq_NRjncjBl_MjDf8g7e4xSTNkwjHlKBKzFFguxA-1s4a63nR7Fo80bGzjMtUN0H6MAC0KnKWAt1Rmif-OVgRNQfSGDUepzEYASz-upw1b3kG8W95se8cW3p9H3oOYTj3BGCLHHlhixm-ZL7vcO2FujseLfVwjPlg4akPNz8dmAj9xAGw6mvNpuQQ3PUATWmVcQXSEHbvXI8ABOq-i-u4-w7090p2Dq',
    alt: 'Michi Mantaro, gata calicó de ojos verdes descansando en una repisa de madera',
    descripcion: 'Gata independiente y limpia. Usa su arenero a la perfección y disfruta de espacios tranquilos.',
    etiqueta: 'Hogar temporal', etiquetaIcono: 'roofing', etiquetaClase: ETQ_SEC,
    salud: [{ texto: 'Esterilizada', ok: true }, { texto: 'Vacunada', ok: true }],
    esterilizado: true, vacunado: true, urgente: false, refugio: 'Albergue San Agustín', refugioId: 'san-agustin',
    energia: 'Tranquila', fichaId: 'LS-HYO-0486', actualizado: 'hace 5 días',
  },
  {
    id: 6, nombre: 'Negrito', nombreCorto: 'Negrito', especie: 'perro', generoTexto: 'Perro', badgeClase: BADGE_PERRO,
    sexo: 'Macho', raza: 'Mestizo', tamano: 'Mediano', edadTexto: '3 años', edadAnios: 3,
    tamanoTexto: 'Mediano • 16 kg', distrito: 'El Tambo', lugar: 'El Tambo, Huancayo',
    foto: IMG + 'AB6AXuAcywY7vG_Aj3flrN3B_ao62GJwgRn3RUGoEMXcHX5WnKL1soR4G0J1254ao56A6vRGUgU18SqVBWpKGsmnMNI2pVyqfhBnX6iNV4wjJmIqu4FXYHko5MsSdAlw31Uaa2GN4a3s6O3jFBdrPWbHfQ6ZIRuHJdnVIXSZ92xouLh_upNeuVCv3A4Q9qChqFAt7-cC66YI309abegeKzeel_TvVoPTN4qK_YJLRVPLVPBw',
    alt: 'Negrito, perro negro de pecho blanco con un pañuelo andino rojo, sentado en una vereda',
    descripcion: 'Un perro sabio, tranquilo y muy amoroso. Perfecto para paseos calmados y tardes en familia.',
    etiqueta: 'Ideal para casa', etiquetaIcono: 'thumb_up', etiquetaClase: ETQ_SEC,
    salud: [{ texto: 'Esterilizado', ok: true }, { texto: 'Desparasitado', ok: true }],
    esterilizado: true, vacunado: false, urgente: false, refugio: 'Albergue Huellitas Wanka', refugioId: 'huellitas-wanka',
    energia: 'Tranquilo', fichaId: 'LS-HYO-0487', actualizado: 'hace 2 días',
  },
  {
    id: 7, nombre: 'Pukuna', nombreCorto: 'Pukuna', especie: 'perro', generoTexto: 'Perra', badgeClase: BADGE_PERRO,
    sexo: 'Hembra', raza: 'Mestiza miel', tamano: 'Pequeño', edadTexto: '4 años', edadAnios: 4,
    tamanoTexto: 'Pequeña • 7 kg', distrito: 'Sapallanga', lugar: 'Sapallanga, Huancayo',
    foto: IMG + 'AB6AXuDvshzE4YZmhbiTY-OLgqWJWhSBCf68CG0kzuq3h7hZWWugP4j0ciR38mN9XMmHOwjMeias4vaY4oN__CvHfPAAUE4S_7VADppKQzcUVRvefSaAg50tC9hcLzkNM6GBDXhb5F2b9V32nbq7KlRWwPaFCH5N1HWTGWG7N9letZ0iGhlWDmGtli2McsKWZyF2JEwPghCzDKMEhWr1gaLlXgvzB6uNHZuSQysWcbBKdQJ_',
    alt: 'Pukuna, perrita mestiza de pelaje miel sonriendo en un patio con pared de adobe',
    descripcion: 'Dulce y agradecida. Busca un hogar tranquilo donde pueda descansar y recibir cariño.',
    etiqueta: 'Urgente acogida', etiquetaIcono: 'schedule', etiquetaClase: 'bg-primary text-on-primary',
    salud: [{ texto: 'Esterilizada', ok: true }, { texto: 'Vacunas al día', ok: true }],
    esterilizado: true, vacunado: true, urgente: true, refugio: 'Refugio Esperanza Junín', refugioId: 'esperanza-junin',
    energia: 'Baja', fichaId: 'LS-HYO-0488', actualizado: 'hace 6 días',
  },
  {
    id: 8, nombre: 'Luna', nombreCorto: 'Luna', especie: 'gato', generoTexto: 'Gata', badgeClase: BADGE_GATO,
    sexo: 'Hembra', raza: 'Blanca semilargo', tamano: 'Pequeño', edadTexto: '2 años', edadAnios: 2,
    tamanoTexto: 'Pequeña • 3.8 kg', distrito: 'El Tambo', lugar: 'El Tambo, Huancayo',
    foto: IMG + 'AB6AXuBIOT_5nZqOmauN07S2gR2SdyIXBmkXSONePnCa331OhSWbLb0UbUewDWDYir2UDo955SCENQIGqXGyZFk0ckfayVeHqfB4ZWsE5u4Ax9SeYRaNYA9AIbUx1Lv_t4QIrK-D2mok4knAy7h3PAWySjXzz1RvzeEAPq3IMf4x0T8i9ex8EFDyXnPfQrWK2dgQh4dlJIQQVTXZAAb0z7iiGdhTfrwd0hbyCuCEmF0LCBvp',
    alt: 'Luna, gata blanca de pelo semilargo y ojos celestes sobre un cojín tejido andino',
    descripcion: 'Tranquila, hogareña y muy ronroneadora. Acostumbrada a vivir en departamento y usar arenero.',
    etiqueta: 'Tranquila', etiquetaIcono: 'sentiment_satisfied', etiquetaClase: ETQ_SEC,
    salud: [{ texto: 'Esterilizada', ok: true }, { texto: 'Test Felino Negativo', ok: true }],
    esterilizado: true, vacunado: false, urgente: false, refugio: 'Hogar Felino Wanka', refugioId: 'hogar-felino-wanka',
    energia: 'Tranquila', fichaId: 'LS-HYO-0489', actualizado: 'hace 3 días',
  },
  {
    id: 9, nombre: 'Raymi', nombreCorto: 'Raymi', especie: 'perro', generoTexto: 'Perro', badgeClase: BADGE_PERRO,
    sexo: 'Macho', raza: 'Mestizo atigrado', tamano: 'Mediano', edadTexto: '8 meses', edadAnios: 0.7,
    tamanoTexto: 'Mediano • 11 kg', distrito: 'Chilca', lugar: 'Chilca, Huancayo',
    foto: IMG + 'AB6AXuBZjJTCv_g32DZfDRqE3VCdQ_E17Yprv3LFx1qLF5M2Kp-CTri1G17ikEmoDmI19-fiWFLH7ASVtfTQSc8WbzAnE7HKOnfZuNczAnpPyy8Fi7xdpd7HFp3ILh4CSyqTRqB0j8T9XHZ7UzMWKqo1pEGk8eG_wJzuUv8_KlnisnbWXSnero7GxfvT2jd57wcISg4lWXLjGyHRhRAIh_I5tDkbh4tZgBHNtZkicoKvMxCs',
    alt: 'Raymi, perro mestizo atigrado saltando con una pelota en un parque de Chilca',
    descripcion: 'Energético y juguetón. Ideal para familias activas que amen correr y jugar con pelota.',
    etiqueta: 'Muy juguetón', etiquetaIcono: 'bolt', etiquetaClase: ETQ_SEC,
    salud: [{ texto: 'Vacunas al día', ok: true }, { texto: 'Desparasitado', ok: true }],
    esterilizado: false, vacunado: true, urgente: false, refugio: 'Hogar San Roque Chilca', refugioId: 'hogar-san-roque',
    energia: 'Muy activo', fichaId: 'LS-HYO-0490', actualizado: 'hace 1 día',
  },
  {
    id: 10, nombre: 'Tikita', nombreCorto: 'Tikita', especie: 'gato', generoTexto: 'Gata', badgeClase: BADGE_GATO,
    sexo: 'Hembra', raza: 'Carey', tamano: 'Pequeño', edadTexto: '1.2 años', edadAnios: 1.2,
    tamanoTexto: 'Pequeña • 3.2 kg', distrito: 'Pilcomayo', lugar: 'Pilcomayo, Huancayo',
    foto: IMG + 'AB6AXuAr94qroyXY0VNcqwJJCcC4oQG0hNgHnqVm87Fe4AUTLHk_AJm6j6wYk5BoWcHiUCgEtjl2Wqfl8ZXJuBA4voKSLXGKThWtpSOD4klFPDHNzdQWXk6FhEv6cp0461SJJf9wGoTdGkXbED6Vzx-J5AvwOL0itHfW8vOtUnce7U7z8jOfqHhXme7ToeNhMw0xF7RqK4LV3AQLIN8hUTOb70wPmMgIGtObzB89IaoyuP17',
    alt: 'Tikita, gata carey de pelaje moteado descansando en una canastilla tejida',
    descripcion: 'Dócil y sana. Disfruta de las siestas al sol y de un buen rincón para observar el jardín.',
    etiqueta: 'Sana y dócil', etiquetaIcono: 'health_and_safety', etiquetaClase: ETQ_SEC,
    salud: [{ texto: 'Esterilizada', ok: true }, { texto: 'Vacunada', ok: true }],
    esterilizado: true, vacunado: true, urgente: false, refugio: 'Rescate Mantaro Solidario', refugioId: 'mantaro-solidario',
    energia: 'Tranquila', fichaId: 'LS-HYO-0491', actualizado: 'hace 7 días',
  },
  {
    id: 11, nombre: 'Oso', nombreCorto: 'Oso', especie: 'perro', generoTexto: 'Perro', badgeClase: BADGE_PERRO,
    sexo: 'Macho', raza: 'Lanudo crema', tamano: 'Grande', edadTexto: '3.5 años', edadAnios: 3.5,
    tamanoTexto: 'Grande • 25 kg', distrito: 'San Agustín de Cajas', lugar: 'San Agustín de Cajas',
    foto: IMG + 'AB6AXuCCXeuQDIXn9Xn4-OdLJo-gkBEoQDGoLd7WghRTrA8J2RHvF9xWJ8zZMhy_E6RHPsYb_u1aagEEU78AD_euHSHIhXkPihnTbMtzwKk79mb3bjeoT15NRmCMr3ZMcQeGq5HURiSXOUO1L64a5SXy3MZAmW7faQT5lHoW_9nEvG3xbv5fPvjO21KWZA5BnqHCk0p0RpxogJFzbFcxnSNnzLDhOxfkB1imN_mgQGP_kpz1',
    alt: 'Oso, perro mestizo lanudo grande de color crema, sereno en un jardín',
    descripcion: 'Sereno, noble y protector. Un compañero leal para una casa con espacio exterior.',
    etiqueta: 'Guardián dócil', etiquetaIcono: 'verified', etiquetaClase: ETQ_SEC,
    salud: [{ texto: 'Esterilizado', ok: true }, { texto: 'Vacunas al día', ok: true }],
    esterilizado: true, vacunado: true, urgente: false, refugio: 'Albergue San Agustín', refugioId: 'san-agustin',
    energia: 'Medio', fichaId: 'LS-HYO-0492', actualizado: 'hace 4 días',
  },
  {
    id: 12, nombre: 'Killa', nombreCorto: 'Killa', especie: 'gato', generoTexto: 'Gata', badgeClase: BADGE_GATO,
    sexo: 'Hembra', raza: 'Siamés mestiza', tamano: 'Pequeño', edadTexto: '1.8 años', edadAnios: 1.8,
    tamanoTexto: 'Pequeña • 3.4 kg', distrito: 'El Tambo', lugar: 'El Tambo, Huancayo',
    foto: IMG + 'AB6AXuDO_azIjhe5hqII5j-lNzLF5e7f_iV2CmKKu4mGFu1t61CJ2BtPFo19kLKzO9SB7H7VlVbAYc_Lw2dI3Wx-KZLGTbnIqjh9vU6TrR1YPiRDPB0o-UHc4cQsPP_sb0Bzm3_nQwPMKcSh7YBtzvoT93X5ZXz6rND2DmNanPSiAyKiH7NAj65SZhuxRHLwenbTvn4aIXo28QEsnfX0SBfjk15G19mYVS7CugaRBZQXVgZi',
    alt: 'Killa, gatita siamesa mestiza de ojos celestes recostada al pie de una ventana',
    descripcion: 'Muy cariñosa y sociable. Le encanta dormir cerca de su persona favorita.',
    etiqueta: 'Muy cariñosa', etiquetaIcono: 'favorite', etiquetaClase: ETQ_SEC,
    salud: [{ texto: 'Esterilizada', ok: true }, { texto: 'Vacunas al día', ok: true }],
    esterilizado: true, vacunado: true, urgente: false, refugio: 'Albergue Huellitas Wanka', refugioId: 'huellitas-wanka',
    energia: 'Tranquila', fichaId: 'LS-HYO-0493', actualizado: 'hace 2 días',
  },
];
