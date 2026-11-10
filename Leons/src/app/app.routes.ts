import { Routes } from '@angular/router';
import { Inicio } from './pages/inicio/inicio';

export const routes: Routes = [
  { path: '', component: Inicio },
  { path: 'mascotas', loadComponent: () => import('./pages/catalogo/catalogo').then((m) => m.Catalogo) },
  {
    path: 'mascotas/:id',
    loadComponent: () => import('./pages/detalle-mascota/detalle-mascota').then((m) => m.DetalleMascota),
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login').then((m) => m.Login),
  },
  {
    path: 'como-funciona',
    loadComponent: () => import('./pages/como-funciona/como-funciona').then((m) => m.ComoFunciona),
  },
  // las demás páginas se agregan igual a medida que las creen
];