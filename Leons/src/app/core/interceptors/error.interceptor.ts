import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { ApiError } from '../api/api-error';
import { AuthService } from '../auth/auth.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  return next(req).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse) {
        const cuerpo = (error.error ?? {}) as { code?: string; message?: string; details?: unknown };
        const codigo = cuerpo.code ?? httpStatusToCode(error.status);
        const mensaje = cuerpo.message ?? error.message ?? 'Error HTTP';
        // Un 401 en una petición con Bearer significa credencial vencida o
        // inválida; se unifica con el cierre de sesión local (A-08).
        if (error.status === 401 && req.headers.has('Authorization')) {
          auth.invalidarPor401();
        }
        return throwError(() => new ApiError(error.status, codigo, mensaje, cuerpo.details ?? null));
      }
      return throwError(() => error);
    }),
  );
};

function httpStatusToCode(status: number): string {
  switch (status) {
    case 400:
      return 'BAD_REQUEST';
    case 401:
      return 'UNAUTHORIZED';
    case 403:
      return 'FORBIDDEN';
    case 404:
      return 'NOT_FOUND';
    case 409:
      return 'CONFLICT';
    case 422:
      return 'VALIDATION_ERROR';
    case 429:
      return 'RATE_LIMIT';
    case 500:
      return 'INTERNAL_ERROR';
    case 501:
      return 'NOT_IMPLEMENTED';
    default:
      return 'HTTP_ERROR';
  }
}
