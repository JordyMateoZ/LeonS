import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { SolicitudesService } from '../../services/solicitudes.service';

@Component({
  imports: [RouterLink, RouterLinkActive],
  selector: 'app-header',
  styleUrl: './header.css',
  templateUrl: './header.html',
})
export class Header {
  private readonly solicitudes = inject(SolicitudesService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly activas = this.solicitudes.activas;
  readonly autenticado = this.auth.isAuthenticated;
  readonly sesionPendiente = this.auth.sesionPendiente;
  readonly nombreUsuario = this.auth.usuario;

  async cerrarSesion(): Promise<void> {
    this.auth.cerrarSesion();
    await this.router.navigateByUrl('/');
  }
}
