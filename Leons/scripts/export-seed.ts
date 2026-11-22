/**
 * Exporta los datos demo de Angular a Backend/app/data/seed.json.
 *
 * Uso (desde Leons/):
 *   node_modules/.bin/esbuild scripts/export-seed.ts --bundle --platform=node --format=esm --outfile=scripts/.tmp/export-seed.mjs
 *   node scripts/.tmp/export-seed.mjs ../Backend/app/data/seed.json
 *
 * Si cambias las constantes de src/app/data/*, vuelve a ejecutar este script.
 * No edites seed.json a mano.
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

import { ESTADOS_MASCOTA, MASCOTAS } from '../src/app/data/mascotas.data';
import { REFUGIOS } from '../src/app/data/refugios.data';
import { SOLICITUDES_DEMO } from '../src/app/data/solicitudes.data';
import { FAQS, PASOS_ADOPCION, PASOS_REFUGIO } from '../src/app/data/contenido.data';
import {
  REQUISITOS,
  citaDe,
  cuidadosDe,
  historiaDe,
  rasgosDe,
} from '../src/app/data/detalle.data';

const destino = process.argv[2];
if (!destino) {
  console.error('Falta la ruta de salida: node export-seed.mjs <seed.json>');
  process.exit(1);
}

const salida = resolve(process.cwd(), destino);

/** Fechas de envío de las solicitudes demo (el dato de Angular solo trae el texto). */
const FECHAS_DEMO: Record<number, string> = {
  1: '2025-05-18T09:00:00',
  2: '2025-05-19T09:00:00',
  3: '2025-02-12T09:00:00',
};

const detalles: Record<string, unknown> = {};
for (const mascota of MASCOTAS) {
  detalles[String(mascota.id)] = {
    historia: historiaDe(mascota),
    cuidados: cuidadosDe(mascota),
    rasgos: rasgosDe(mascota),
    cita: citaDe(mascota) ?? null,
  };
}

const seed = {
  generadoPor: 'Leons/scripts/export-seed.ts',
  mascotas: MASCOTAS,
  refugios: REFUGIOS,
  solicitudesDemo: SOLICITUDES_DEMO.map((solicitud) => ({
    ...solicitud,
    creadaEn: FECHAS_DEMO[solicitud.id] ?? '2025-01-01T09:00:00',
  })),
  contenido: {
    pasosAdopcion: PASOS_ADOPCION,
    pasosRefugio: PASOS_REFUGIO,
    faqs: FAQS,
    requisitos: REQUISITOS,
  },
  detalles,
  estadosMascota: ESTADOS_MASCOTA,
};

mkdirSync(dirname(salida), { recursive: true });
writeFileSync(salida, `${JSON.stringify(seed, null, 2)}\n`, 'utf8');
console.log(`Seed generado: ${salida}`);
console.log(
  `Mascotas: ${MASCOTAS.length} | Refugios: ${REFUGIOS.length} | Solicitudes demo: ${SOLICITUDES_DEMO.length}`,
);
