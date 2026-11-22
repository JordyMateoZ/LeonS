import { CanActivateFn, Router } from '@angular/router';
import { inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

import { AuthService } from '../auth/auth.service';

/**
 * 5.6.3.2D: la decisión definitiva se toma en el navegador, después de que
 * `/auth/me` confirme la sesión. En SSR se renderiza un shell neutro: no hay
 * `localStorage`, por lo que redirigir aquí congelaría la ruta en `/login`
 * durante la hidratación. Nunca se autoriza solo por existir un token.
 */
export const authGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const platformId = inject(PLATFORM_ID);

  if (!isPlatformBrowser(platformId)) {
    return true;
  }

  if (auth.isAuthenticated()) {
    return true;
  }

  if (auth.estado() === 'no-autenticada') {
    return router.createUrlTree(['/login']);
  }

  // `pendiente`: hay un token local cuya firma aún no fue validada.
  await auth.inicializar();

  if (auth.isAuthenticated()) {
    return true;
  }
  if (auth.estado() === 'no-autenticada') {
    return router.createUrlTree(['/login']);
  }

  // 401/403 o fallo transitorio: no se autoriza ningún dato privado, pero se
  // conserva la navegación para mostrar el estado recuperable del componente.
  return true;
};
