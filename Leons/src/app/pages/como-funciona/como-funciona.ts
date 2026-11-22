import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ContenidoService } from '../../services/contenido.service';

@Component({
  selector: 'app-como-funciona',
  imports: [RouterLink],
  templateUrl: './como-funciona.html',
  styleUrl: './como-funciona.css',
})
export class ComoFunciona {
  private readonly contenido = inject(ContenidoService);

  readonly fill1 = "'FILL' 1";

  readonly pasos = this.contenido.pasosAdopcion;
  readonly pasosRefugio = this.contenido.pasosRefugio;
  readonly requisitos = this.contenido.requisitos;
  readonly faqs = this.contenido.faqs;

  faqAbierta = signal<number | null>(0);

  alternarFaq(i: number) {
    this.faqAbierta.update((actual) => (actual === i ? null : i));
  }
}
