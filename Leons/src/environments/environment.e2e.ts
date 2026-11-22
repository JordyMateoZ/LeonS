// Configuración exclusiva de las pruebas E2E (5.6.3.2A).
// Apunta únicamente al FastAPI E2E aislado, nunca al backend principal :8000.
// No se incluyen secretos en este archivo.
export const environment = {
  production: false,
  apiOrigin: 'http://localhost:8010',
  apiUrl: 'http://localhost:8010/api/v1',
} as const;
