import { RenderMode, ServerRoute } from '@angular/ssr';
import { MASCOTAS } from './data/mascotas.data';
import { REFUGIOS } from './data/refugios.data';

export const serverRoutes: ServerRoute[] = [
  {
    path: 'mascotas/:id',
    renderMode: RenderMode.Prerender,
    getPrerenderParams: async () => MASCOTAS.map((m) => ({ id: String(m.id) })),
  },
  {
    path: 'refugios/:id',
    renderMode: RenderMode.Prerender,
    getPrerenderParams: async () => REFUGIOS.map((r) => ({ id: r.id })),
  },
  {
    path: '**',
    renderMode: RenderMode.Prerender,
  },
];
