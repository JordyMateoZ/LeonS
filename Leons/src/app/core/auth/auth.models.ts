export type RolUsuario = 'adoptante' | 'refugio' | 'admin';

export interface Usuario {
  id: number;
  nombre: string;
  email: string;
  dni: string | null;
  telefono: string | null;
  distrito: string | null;
  rol: RolUsuario;
  refugioId: string | null;
  creadoEn: string;
}

export interface AuthResponse {
  usuario: Usuario;
  token: string;
  tokenType: string;
}

export interface LoginRequest {
  identificador?: string;
  email?: string;
  dni?: string;
  password: string;
}

export interface RegistroRequest {
  nombre: string;
  email: string;
  dni: string;
  password: string;
  telefono?: string | null;
  distrito?: string | null;
  rol?: 'adoptante' | 'refugio';
  refugioId?: string | null;
}
