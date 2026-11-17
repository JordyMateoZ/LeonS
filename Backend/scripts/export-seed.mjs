import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import ts from 'typescript';

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const frontendData = path.resolve(root, '..', 'Frontend', 'src', 'app', 'data');

function loadDataModule(fileName, exportName) {
  const source = readFileSync(path.join(frontendData, fileName), 'utf8');
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      esModuleInterop: true,
    },
  });
  const module = { exports: {} };
  // Los archivos de datos son constantes puras; no necesitan un loader real.
  new Function('exports', 'require', 'module', outputText)(module.exports, require, module);
  return module.exports[exportName];
}

/** Elimina cualquier clase CSS: el backend guarda semántica, no presentación. */
function sinClases(valor) {
  if (Array.isArray(valor)) return valor.map(sinClases);
  if (valor && typeof valor === 'object') {
    return Object.fromEntries(
      Object.entries(valor)
        .filter(([clave]) => clave !== 'clase' && !clave.endsWith('Clase'))
        .map(([clave, v]) => [clave, sinClases(v)]),
    );
  }
  return valor;
}

const mascotasFuente = loadDataModule('mascotas.data.ts', 'MASCOTAS');
const refugiosFuente = loadDataModule('refugios.data.ts', 'REFUGIOS');
const solicitudesFuente = loadDataModule('solicitudes.data.ts', 'SOLICITUDES_DEMO');
const pasosAdopcion = loadDataModule('contenido.data.ts', 'PASOS_ADOPCION');
const pasosRefugio = loadDataModule('contenido.data.ts', 'PASOS_REFUGIO');
const faqs = loadDataModule('contenido.data.ts', 'FAQS');

const mascotas = mascotasFuente.map((m) =>
  sinClases({
    ...m,
    galeria: m.galeria ?? [],
    rasgos: m.rasgos ?? [],
  }),
);

const refugios = refugiosFuente.map((r) => sinClases(r));

const fechasDemo = {
  1: '2025-05-18T09:00:00.000Z',
  2: '2025-05-19T11:30:00.000Z',
  3: '2025-02-12T15:00:00.000Z',
};

const solicitudes = solicitudesFuente.map((s) =>
  sinClases({
    id: s.id,
    estado: s.estado,
    paso: s.paso,
    mascotaId: s.fichaId,
    fichaId: s.fichaId,
    nombre: s.nombre,
    refugio: s.refugio,
    lugar: s.lugar,
    exp: s.exp,
    usuarioId: 'demo-user',
    creadaEn: fechasDemo[s.id] ?? '2025-05-18T09:00:00.000Z',
    actualizadaEn: fechasDemo[s.id] ?? '2025-05-18T09:00:00.000Z',
    tiempoRespuesta: s.tiempoRespuesta,
    whatsapp: s.whatsapp,
    cita: s.cita,
    mensaje: s.mensaje,
    cierre: s.cierre,
    solicitante: {
      nombre: 'Familia adoptiva (demo)',
      telefono: s.whatsapp?.replace('https://wa.me/', '+') ?? '+51 900 000 000',
      distrito: s.lugar.split(',')[0]?.trim() ?? 'Huancayo',
      vivienda: 'Casa con cerco perimétrico',
      aceptaCompromiso: true,
    },
    fotosSeguimiento: [],
  }),
);

const seed = {
  mascotas,
  refugios,
  solicitudes,
  contenido: sinClases({ pasosAdopcion, pasosRefugio, faqs }),
};

const destino = path.join(root, 'src', 'data', 'seed.json');
writeFileSync(destino, `${JSON.stringify(seed, null, 2)}\n`, 'utf8');

console.log(
  `Seed exportado: ${mascotas.length} mascotas, ${refugios.length} refugios, ${solicitudes.length} solicitudes -> ${destino}`,
);
