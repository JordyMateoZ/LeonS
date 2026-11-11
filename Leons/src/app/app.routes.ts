import { Routes } from '@angular/router';
import { Inicio } from './pages/inicio/inicio';

export const routes: Routes = [
  { path: '', component: Inicio },
  {
    path: 'mascotas',
    loadComponent: () => import('./pages/catalogo/catalogo').then((m) => m.Catalogo),
  },
  {
    path: 'mascotas/:id',
    loadComponent: () =>
      import('./pages/detalle-mascota/detalle-mascota').then((m) => m.DetalleMascota),
  },
  {
    path: 'refugios',
    loadComponent: () => import('./pages/refugios/refugios').then((m) => m.Refugios),
  },
  {
    path: 'refugios/:id',
    loadComponent: () =>
      import('./pages/detalle-refugio/detalle-refugio').then((m) => m.DetalleRefugio),
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login').then((m) => m.Login),
  },
  {
    path: 'mis-solicitudes',
    loadComponent: () =>
      import('./pages/mis-solicitudes/mis-solicitudes').then((m) => m.MisSolicitudes),
  },
  {
    path: 'impacto',
    loadComponent: () => import('./pages/impacto/impacto').then((m) => m.Impacto),
  },
  {
    path: 'sobre-nosotros',
    loadComponent: () => import('./pages/nosotros/nosotros').then((m) => m.Nosotros),
  },
  { path: 'nosotros', redirectTo: 'sobre-nosotros', pathMatch: 'full' },
  {
    path: 'como-funciona',
    loadComponent: () => import('./pages/como-funciona/como-funciona').then((m) => m.ComoFunciona),
  },
];
