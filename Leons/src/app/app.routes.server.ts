import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  { path: 'mascotas', renderMode: RenderMode.Server },
  { path: 'mascotas/:id', renderMode: RenderMode.Server },
  { path: 'refugios', renderMode: RenderMode.Server },
  { path: 'refugios/:id', renderMode: RenderMode.Server },
  // Ruta privada: nunca prerenderizar; el servidor emite solo un shell neutro
  // y la autorización se resuelve en el navegador tras `/auth/me`.
  { path: 'mis-solicitudes', renderMode: RenderMode.Server },
  { path: '**', renderMode: RenderMode.Prerender },
];
