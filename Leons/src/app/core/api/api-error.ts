/** Contrato de error del backend: `{ code, message, details }`. */
export interface ErrorOut {
  code: string;
  message: string;
  details: unknown | null;
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: unknown | null;

  constructor(status: number, code: string, message: string, details: unknown | null = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}
