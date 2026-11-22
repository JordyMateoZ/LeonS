import { defineConfig, devices } from '@playwright/test';

/**
 * Configuración exclusiva de E2E (5.6.3.2A).
 * Usa el Chrome instalado en el sistema (`channel: 'chrome'`): no descarga
 * navegadores. Los servidores (FastAPI :8010 y Angular :4300) se inician
 * manualmente y se reutilizan; esta configuración no levanta ni detiene nada.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  forbidOnly: true,
  retries: 0,
  reporter: [['list']],
  timeout: 45_000,
  expect: { timeout: 10_000 },
  use: {
    ...devices['Desktop Chrome'],
    baseURL: 'http://localhost:4300',
    channel: 'chrome',
    headless: true,
    trace: 'on',
    screenshot: 'on',
  },
  projects: [
    {
      name: 'chrome-e2e',
    },
  ],
});
