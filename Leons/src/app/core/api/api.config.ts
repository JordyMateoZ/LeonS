import { InjectionToken } from '@angular/core';
import { environment } from '../../../environments/environment';

/**
 * URL base completa de la API (incluye `/api/v1`). Centraliza la configuración
 * para que ningún servicio hardcodee la dirección del backend.
 */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => environment.apiUrl,
});

export const API_ORIGIN = new InjectionToken<string>('API_ORIGIN', {
  providedIn: 'root',
  factory: () => environment.apiOrigin,
});

/** Construye una URL absoluta a partir de un path relativo de la API. */
export function apiUrl(path: string): string {
  const base = environment.apiUrl.replace(/\/+$/, '');
  const suffix = path.startsWith('/') ? path : `/${path}`;
  return `${base}${suffix}`;
}
