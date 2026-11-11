import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { SolicitudesService } from '../../services/solicitudes.service';

@Component({
  imports: [RouterLink, RouterLinkActive],
  selector: 'app-header',
  styleUrl: './header.css',
  templateUrl: './header.html',
})
export class Header {
  private readonly solicitudes = inject(SolicitudesService);

  readonly activas = this.solicitudes.activas;
}
