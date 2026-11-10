import { Component, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { REQUISITOS } from '../../data/detalle.data';
import { FAQS, PASOS_ADOPCION, PASOS_REFUGIO } from '../../data/contenido.data';

@Component({
  selector: 'app-como-funciona',
  imports: [RouterLink],
  templateUrl: './como-funciona.html',
  styleUrl: './como-funciona.css',
})
export class ComoFunciona {
  readonly fill1 = "'FILL' 1";

  readonly pasos = PASOS_ADOPCION;
  readonly pasosRefugio = PASOS_REFUGIO;
  readonly requisitos = REQUISITOS;
  readonly faqs = FAQS;

  faqAbierta = signal<number | null>(0);

  alternarFaq(i: number) {
    this.faqAbierta.update((actual) => (actual === i ? null : i));
  }
}
