import { execFileSync } from 'node:child_process';
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

/**
 * Soporte para 5.6.3.2B: invoca el helper Python (SQL controlado), centraliza
 * las peticiones a :8010 y registra evidencias. Sin dependencias nuevas.
 */

export const API_ORIGIN = 'http://localhost:8010';
export const API_BASE = `${API_ORIGIN}/api/v1`;
export const FRONTEND_ORIGIN = 'http://localhost:4300';

export async function healthApi(): Promise<RespuestaApi> {
  const respuesta = await fetch(`${API_ORIGIN}/health`);
  const texto = await respuesta.text();
  let cuerpo: any = null;
  if (texto) {
    try {
      cuerpo = JSON.parse(texto);
    } catch {
      cuerpo = texto;
    }
  }
  return { status: respuesta.status, body: cuerpo, headers: respuesta.headers };
}

const ROOT = path.resolve(__dirname, '../..');
const BACKEND = path.join(ROOT, 'Backend');
const MANIFEST_DIR = path.join(__dirname, 'manifests');
const EVIDENCE_DIR = path.join(__dirname, 'evidence');

let runIdActual = 'sin-run';

export function nuevoRunId(): string {
  const fecha = new Date();
  const sello = [
    fecha.getFullYear(),
    String(fecha.getMonth() + 1).padStart(2, '0'),
    String(fecha.getDate()).padStart(2, '0'),
    String(fecha.getHours()).padStart(2, '0'),
    String(fecha.getMinutes()).padStart(2, '0'),
    String(fecha.getSeconds()).padStart(2, '0'),
  ].join('');
  return `e2e${sello}${Math.random().toString(36).slice(2, 6)}`;
}

export function usarRunId(id: string): void {
  runIdActual = id;
  mkdirSync(MANIFEST_DIR, { recursive: true });
  mkdirSync(EVIDENCE_DIR, { recursive: true });
}

export function rutaManifiesto(): string {
  return path.join(MANIFEST_DIR, `${runIdActual}.json`);
}

export function rutaEvidencias(): string {
  return path.join(EVIDENCE_DIR, `${runIdActual}.jsonl`);
}

export interface RespuestaApi {
  status: number;
  body: any;
  headers: any;
}

export async function api(
  method: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE',
  ruta: string,
  opciones: { body?: unknown; token?: string } = {},
): Promise<RespuestaApi> {
  const headers: Record<string, string> = {};
  if (opciones.body !== undefined) headers['content-type'] = 'application/json';
  if (opciones.token) headers.authorization = `Bearer ${opciones.token}`;
  // Reintento solo ante errores de red (socket cerrado), nunca ante un
  // código HTTP: los 4xx/5xx son evidencia y deben llegar intactos al spec.
  let respuesta: Awaited<ReturnType<typeof fetch>> | undefined;
  for (let intento = 0; intento < 3; intento += 1) {
    try {
      respuesta = await fetch(`${API_BASE}${ruta}`, {
        method,
        headers,
        body: opciones.body === undefined ? undefined : JSON.stringify(opciones.body),
      });
      break;
    } catch (error) {
      if (intento === 2) throw error;
      await new Promise((resolver) => setTimeout(resolver, 250 * (intento + 1)));
    }
  }
  if (!respuesta) throw new Error(`Sin respuesta de ${API_BASE}${ruta}`);
  const texto = await respuesta.text();
  let cuerpo: any = null;
  if (texto) {
    try {
      cuerpo = JSON.parse(texto);
    } catch {
      cuerpo = texto;
    }
  }
  return { status: respuesta.status, body: cuerpo, headers: respuesta.headers };
}

export function support(args: string[]): any {
  const salida = execFileSync(
    'uv',
    ['run', 'python', 'scripts/e2e_support.py', ...args],
    {
      cwd: BACKEND,
      encoding: 'utf8',
      maxBuffer: 20 * 1024 * 1024,
      env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' },
    },
  );
  return JSON.parse(salida);
}

/** Bloquea la corrida si hay un pytest que pueda escribir en LeonsDB_Test. */
export function assertNoSqlPytest(): void {
  const comando =
    "$ErrorActionPreference='SilentlyContinue'; " +
    "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -match 'pytest' } | " +
    "Where-Object { $_.CommandLine -notmatch '--ignore=tests/test_sqlserver.py' } | " +
    'Select-Object -ExpandProperty ProcessId';
  const salida = execFileSync('powershell', ['-NoProfile', '-Command', comando], {
    encoding: 'utf8',
  }).trim();
  if (salida) {
    throw new Error(`Fail-closed: hay pytest activo que podría escribir SQL (PID ${salida}).`);
  }
}

/** Fail-closed reforzado antes de cada operación con escritura. */
export function guard(operacion: string): { db: string } {
  assertNoSqlPytest();
  const resultado = support(['guard', '--manifest', rutaManifiesto(), '--operation', operacion]);
  if (resultado.db !== 'LeonsDB_Test') {
    throw new Error(`Fail-closed: base efectiva inesperada ${resultado.db}.`);
  }
  return resultado;
}

export function init(runId: string): any {
  usarRunId(runId);
  assertNoSqlPytest();
  return support(['init', '--manifest', rutaManifiesto(), '--run-id', runId]);
}

export function verificarMarcador(email: string): any {
  return support(['verify-marker', '--manifest', rutaManifiesto(), '--email', email]);
}

export function identifiers(seed: string, count: number): Array<{ email: string; dni: string }> {
  return support([
    'identifiers',
    '--manifest',
    rutaManifiesto(),
    '--seed',
    seed,
    '--count',
    String(count),
  ]);
}

export function chooseSource(): { id: number; nombre: string; refugio_id: string } {
  return support(['choose-source']);
}

export function createRoleUsers(datos: {
  runId: string;
  refugioId: string;
  emailRefugio: string;
  dniRefugio: string;
  emailAdmin: string;
  dniAdmin: string;
  password: string;
}): Record<'refugio' | 'admin', { id: number; email: string; rol: string }> {
  guard('create-role-users');
  return support([
    'create-role-users',
    '--manifest',
    rutaManifiesto(),
    '--run-id',
    datos.runId,
    '--refugio-id',
    datos.refugioId,
    '--email-refugio',
    datos.emailRefugio,
    '--dni-refugio',
    datos.dniRefugio,
    '--email-admin',
    datos.emailAdmin,
    '--dni-admin',
    datos.dniAdmin,
    '--password',
    datos.password,
  ]);
}

export function createMascota(datos: {
  runId: string;
  sourceId: number;
  nombre: string;
  fotoPrincipal?: string;
}): { id: number; nombre: string; refugio_id: string } {
  guard('create-mascota');
  const args = [
    'create-mascota',
    '--manifest',
    rutaManifiesto(),
    '--run-id',
    datos.runId,
    '--source-id',
    String(datos.sourceId),
    '--nombre',
    datos.nombre,
  ];
  if (datos.fotoPrincipal) args.push('--foto-principal', datos.fotoPrincipal);
  return support(args);
}

export function trackSolicitudes(): { registradas: number; añadidas: number } {
  guard('track-solicitudes');
  return support(['track-solicitudes', '--manifest', rutaManifiesto()]);
}

export function trackDistritos(): { nuevos: number; referidos: number; añadidos: number } {
  guard('track-distritos');
  return support(['track-distritos', '--manifest', rutaManifiesto()]);
}

export function createAdoptantes(datos: {
  runId: string;
  correos: string[];
  dnis: string[];
  password: string;
}): Array<{ id: number; email: string; rol: string }> {
  guard('create-adoptantes');
  return support([
    'create-adoptantes',
    '--manifest',
    rutaManifiesto(),
    '--run-id',
    datos.runId,
    '--correos',
    JSON.stringify(datos.correos),
    '--dnis',
    JSON.stringify(datos.dnis),
    '--password',
    datos.password,
  ]);
}

export function anadirRegistro(kind: string, value: Record<string, unknown>): void {
  const datos = JSON.parse(readFileSync(rutaManifiesto(), 'utf8'));
  datos.records ??= {};
  datos.records[kind] ??= [];
  datos.records[kind].push(value);
  writeFileSync(rutaManifiesto(), JSON.stringify(datos, null, 2), 'utf8');
}

export function inspeccionar(): any {
  return support(['inspect', '--manifest', rutaManifiesto()]);
}

export function rollbackFixture(solicitudId: number, autorId: number): any {
  guard('rollback-fixture');
  return support([
    'rollback-fixture',
    '--manifest',
    rutaManifiesto(),
    '--run-id',
    runIdActual,
    '--solicitud-id',
    String(solicitudId),
    '--autor-id',
    String(autorId),
  ]);
}

export function limpiar(): any {
  assertNoSqlPytest();
  return support(['cleanup', '--manifest', rutaManifiesto()]);
}

export interface Evidencia {
  id: string;
  resultado: 'PASS' | 'FAIL' | 'BLOCKED';
  tipo: 'navegador' | 'api' | 'sql';
  base: string;
  http?: number | null;
  persistencia?: string;
  captura?: string;
  error?: string;
  detalle?: string;
}

export function evidencia(entry: Evidencia): void {
  mkdirSync(EVIDENCE_DIR, { recursive: true });
  appendFileSync(
    rutaEvidencias(),
    `${JSON.stringify({ run_id: runIdActual, en: new Date().toISOString(), ...entry })}\n`,
    'utf8',
  );
}

export function codigoError(cuerpo: any): string | undefined {
  return cuerpo && typeof cuerpo === 'object' ? cuerpo.code ?? cuerpo.error?.code : undefined;
}
