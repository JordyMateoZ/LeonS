import { RenderMode, ServerRoute } from '@angular/ssr';
import { MASCOTAS } from './data/mascotas.data';

export const serverRoutes: ServerRoute[] = [
  {
    path: 'mascotas/:id',
    renderMode: RenderMode.Prerender,
    getPrerenderParams: async () => MASCOTAS.map((m) => ({ id: String(m.id) })),
  },
  {
    path: '**',
    renderMode: RenderMode.Prerender
  }
];
