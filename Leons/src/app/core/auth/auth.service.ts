import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, PLATFORM_ID, computed, inject, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Observable, firstValueFrom, tap, timeout } from 'rxjs';

import { API_BASE_URL } from '../api/api.config';
import { ApiError } from '../api/api-error';
import { AuthResponse, LoginRequest, RegistroRequest, Usuario } from './auth.models';

const TOKEN_KEY = 'leons.token.v1';
const TIEMPO_ESPERA_ME_MS = 3000;

/**
 * A-07/A-08/A-09: la sesión tiene tres estados observables.
 * - `no-autenticada`: no hay credenciales utilizables.
 * - `pendiente`: hay un token local todavía no verificado contra FastAPI.
 * - `confirmada`: `/auth/me` validó el token y se conoce el usuario.
 */
export type EstadoSesion = 'no-autenticada' | 'pendiente' | 'confirmada';

/** Lee solo `exp` del JWT; la firma la valida FastAPI. Sin librerías nuevas. */
function expiracionJwt(token: string): number | null {
  try {
    const partes = token.split('.');
    if (partes.length !== 3) {
      return null;
    }
    const payload = partes[1].replace(/-/g, '+').replace(/_/g, '/');
    const relleno = '='.repeat((4 - (payload.length % 4)) % 4);
    const decodificado = atob(payload + relleno);
    const exp = JSON.parse(decodificado)['exp'];
    return typeof exp === 'number' && Number.isFinite(exp) ? exp : null;
  } catch {
    return null;
  }
}

function tokenUtil(token: string | null): string | null {
  if (!token) {
    return null;
  }
  const exp = expiracionJwt(token);
  // Sin `exp` o con `exp` vencido no se considera utilizable. Se aplica un
  // margen de 5 s para compensar relojes locales desincronizados.
  if (exp === null || exp * 1000 <= Date.now() + 5000) {
    return null;
  }
  return token;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly platformId = inject(PLATFORM_ID);
  private readonly baseUrl = inject(API_BASE_URL);

  private readonly _token = signal<string | null>(null);
  private readonly _usuario = signal<Usuario | null>(null);
  private readonly _estado = signal<EstadoSesion>('no-autenticada');
  private readonly _errorSesion = signal<string | null>(null);

  /** Última verificación en curso; varias llamadas comparten la misma promesa. */
  private verificacion: Promise<void> | null = null;
  /** Último token que se intentó verificar; permite reintentar tras recuperarse. */
  private ultimoTokenVerificado: string | null = null;
  /** Servicios privados registran aquí su limpieza al cerrar sesión. */
  private readonly limpiezas = new Set<() => void>();

  readonly token = this._token.asReadonly();
  readonly usuario = this._usuario.asReadonly();
  readonly estado = this._estado.asReadonly();
  readonly errorSesion = this._errorSesion.asReadonly();
  /** Solo una sesión confirmada autoriza operaciones privadas. */
  readonly isAuthenticated = computed(() => this._estado() === 'confirmada');
  readonly sesionPendiente = computed(() => this._estado() === 'pendiente');

  constructor() {
    const almacenado = this.leerToken();
    const util = tokenUtil(almacenado);
    if (util !== almacenado) {
      // Token vencido o ilegible: no se queda en localStorage ni en memoria.
      this.guardarToken(null);
    }
    if (util) {
      this._token.set(util);
      this._estado.set('pendiente');
    }
  }

  private leerToken(): string | null {
    if (!isPlatformBrowser(this.platformId)) {
      return null;
    }
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }

  private guardarToken(token: string | null): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    try {
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    } catch {
      // Sin almacenamiento disponible (modo privado o cuota llena).
    }
  }

  login(datos: LoginRequest): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.baseUrl}/auth/login`, datos)
      .pipe(tap((respuesta) => this.establecerSesion(respuesta)));
  }

  registrar(datos: RegistroRequest): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.baseUrl}/auth/registro`, datos)
      .pipe(tap((respuesta) => this.establecerSesion(respuesta)));
  }

  /** Consulta el perfil del usuario autenticado; no modifica el token por sí sola. */
  me(): Observable<Usuario> {
    return this.http
      .get<Usuario>(`${this.baseUrl}/auth/me`)
      .pipe(timeout(TIEMPO_ESPERA_ME_MS), tap((usuario) => this._usuario.set(usuario)));
  }

  /**
   * Verifica la sesión almacenada contra `/auth/me`.
   * A-09: un fallo de red/timeout/5xx conserva el token y deja el estado en
   * `pendiente`; un 401 lo invalida; un 403 solo informa falta de permisos.
   */
  async inicializar(): Promise<void> {
    const token = this._token();
    if (!token) {
      return;
    }
    if (this.verificacion) {
      return this.verificacion;
    }
    // Un token ya confirmado en esta misma sesión no necesita otra llamada.
    if (this._estado() === 'confirmada' && this.ultimoTokenVerificado === token) {
      return;
    }

    this.verificacion = this.verificarToken(token).finally(() => {
      this.verificacion = null;
    });
    return this.verificacion;
  }

  /**
   * Registra la limpieza de un servicio privado. Devuelve la función para
   * cancelar el registro; evita que AuthService importe servicios que a su vez
   * lo importan (dependencia circular).
   */
  registrarLimpieza(limpieza: () => void): () => void {
    this.limpiezas.add(limpieza);
    return () => this.limpiezas.delete(limpieza);
  }

  /** Reintento manual tras una caída transitoria del backend. */
  async revalidar(): Promise<void> {
    if (!this._token()) {
      return;
    }
    this.ultimoTokenVerificado = null;
    return this.inicializar();
  }

  private async verificarToken(token: string): Promise<void> {
    this._errorSesion.set(null);
    try {
      await firstValueFrom(this.me());
      this.ultimoTokenVerificado = token;
      this._estado.set('confirmada');
    } catch (error: unknown) {
      const estado = this.clasificarError(error);
      if (estado === 'invalida') {
        this.cerrarSesion('Tu sesión venció o no es válida. Inicia sesión de nuevo.');
        return;
      }
      if (estado === 'sin-permisos') {
        this._estado.set('pendiente');
        this._errorSesion.set('Tu cuenta no tiene permisos para esta consulta.');
        return;
      }
      // Red, timeout o 5xx: se conserva el token, sin afirmar autenticación.
      this._estado.set('pendiente');
      this._errorSesion.set(
        'No se pudo verificar tu sesión. Se conservarán tus credenciales y se reintentará al recuperar la conexión.',
      );
    }
  }

  private clasificarError(error: unknown): 'invalida' | 'sin-permisos' | 'transitorio' {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        return 'invalida';
      }
      if (error.status === 403) {
        return 'sin-permisos';
      }
    }
    if (error instanceof HttpErrorResponse) {
      if (error.status === 401) {
        return 'invalida';
      }
      if (error.status === 403) {
        return 'sin-permisos';
      }
    }
    return 'transitorio';
  }

  /** Un 401 en cualquier endpoint privado invalida la sesión de forma consistente. */
  invalidarPor401(): void {
    if (this._token()) {
      this.cerrarSesion('Tu sesión venció o no es válida. Inicia sesión de nuevo.');
    }
  }

  cerrarSesion(motivo: string | null = null): void {
    this._token.set(null);
    this._usuario.set(null);
    this._estado.set('no-autenticada');
    this._errorSesion.set(motivo);
    this.ultimoTokenVerificado = null;
    this.verificacion = null;
    this.guardarToken(null);
    for (const limpieza of this.limpiezas) {
      limpieza();
    }
  }

  private establecerSesion(respuesta: AuthResponse): void {
    const util = tokenUtil(respuesta.token);
    if (!util) {
      this.cerrarSesion('El servidor devolvió una credencial no válida.');
      return;
    }
    this._token.set(util);
    this._usuario.set(respuesta.usuario);
    this._estado.set('confirmada');
    this.ultimoTokenVerificado = util;
    this._errorSesion.set(null);
    this.guardarToken(util);
  }
}
