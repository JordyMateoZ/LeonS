import { HttpClient } from '@angular/common/http';
import { Injectable, PLATFORM_ID, computed, effect, inject, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { firstValueFrom } from 'rxjs';

import { AuthService } from '../core/auth/auth.service';
import { API_BASE_URL } from '../core/api/api.config';
import { ApiError } from '../core/api/api-error';

interface FavoritosResponse {
  ids: number[];
  mascotas?: unknown[];
}

@Injectable({ providedIn: 'root' })
export class FavoritosService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly platformId = inject(PLATFORM_ID);
  private readonly baseUrl = inject(API_BASE_URL);

  private readonly _ids = signal<ReadonlySet<number>>(new Set<number>());
  private readonly _cargando = signal(false);
  private readonly _error = signal<string | null>(null);
  private readonly _enCurso = new Set<number>();

  readonly ids = this._ids.asReadonly();
  readonly cargando = this._cargando.asReadonly();
  readonly error = this._error.asReadonly();
  readonly total = computed(() => this._ids().size);

  constructor() {
    // Al cerrar sesión se descarta de inmediato cualquier estado privado.
    this.auth.registrarLimpieza?.(() => this.limpiar());
    if (isPlatformBrowser(this.platformId)) {
      // Carga y limpia según el estado de autenticación, sin compartir estado entre usuarios.
      effect(() => {
        if (this.auth.isAuthenticated()) {
          void this.cargar();
        } else {
          this.limpiar();
        }
      });
    }
  }

  limpiar(): void {
    this._ids.set(new Set<number>());
    this._enCurso.clear();
    this._cargando.set(false);
    this._error.set(null);
  }

  esFavorito(id: number): boolean {
    return this._ids().has(id);
  }

  async cargar(): Promise<void> {
    if (!this.auth.isAuthenticated()) {
      this._ids.set(new Set<number>());
      return;
    }
    this._cargando.set(true);
    this._error.set(null);
    try {
      const respuesta = await firstValueFrom(
        this.http.get<FavoritosResponse>(`${this.baseUrl}/favoritos`),
      );
      this._ids.set(new Set<number>(respuesta?.ids ?? []));
    } catch (error) {
      this._error.set(error instanceof ApiError ? error.message : 'No se pudieron cargar los favoritos.');
    } finally {
      this._cargando.set(false);
    }
  }

  async agregar(id: number): Promise<void> {
    if (!this.auth.isAuthenticated()) {
      this._error.set('Inicia sesión para guardar favoritos.');
      return;
    }
    if (this._ids().has(id) || this._enCurso.has(id)) {
      return;
    }
    const anterior = new Set(this._ids());
    this._enCurso.add(id);
    this._cargando.set(true);
    this._error.set(null);
    try {
      const respuesta = await firstValueFrom(
        this.http.post<FavoritosResponse>(`${this.baseUrl}/favoritos`, { mascotaId: id }),
      );
      this._ids.set(new Set<number>(respuesta?.ids ?? [...anterior, id]));
    } catch (error) {
      this._ids.set(anterior);
      this._error.set(error instanceof ApiError ? error.message : 'No se pudo agregar a favoritos.');
    } finally {
      this._enCurso.delete(id);
      this._cargando.set(false);
    }
  }

  async quitar(id: number): Promise<void> {
    if (!this._ids().has(id) || this._enCurso.has(id)) {
      return;
    }
    const anterior = new Set(this._ids());
    this._enCurso.add(id);
    this._cargando.set(true);
    this._error.set(null);
    try {
      await firstValueFrom(this.http.delete(`${this.baseUrl}/favoritos/${id}`));
      const nuevo = new Set(anterior);
      nuevo.delete(id);
      this._ids.set(nuevo);
    } catch (error) {
      this._ids.set(anterior);
      this._error.set(error instanceof ApiError ? error.message : 'No se pudo quitar de favoritos.');
    } finally {
      this._enCurso.delete(id);
      this._cargando.set(false);
    }
  }

  async alternar(id: number): Promise<void> {
    if (this._ids().has(id)) {
      await this.quitar(id);
    } else {
      await this.agregar(id);
    }
  }
}
