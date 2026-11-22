import { Directive, ElementRef, Renderer2, inject } from '@angular/core';

/** Placeholder local e identificable cuando no hay una foto válida (INC-001). */
export const FOTO_PLACEHOLDER = '/images/placeholder-mascota.svg';

/**
 * Sustituye una imagen de mascota que falla por el placeholder local.
 * La guarda evita reasignar el mismo `src` y, por tanto, ciclos de error.
 */
@Directive({
  selector: 'img[appFotoFallback]',
  standalone: true,
  host: { '(error)': 'onError()' },
})
export class FotoFallbackDirective {
  private readonly elemento = inject<ElementRef<HTMLImageElement>>(ElementRef);
  private readonly renderer = inject(Renderer2);

  onError(): void {
    const imagen = this.elemento.nativeElement;
    const actual = imagen.getAttribute('src') ?? '';

    if (!actual || actual === FOTO_PLACEHOLDER) {
      return;
    }

    this.renderer.setAttribute(imagen, 'src', FOTO_PLACEHOLDER);
    if (!imagen.getAttribute('alt')) {
      this.renderer.setAttribute(imagen, 'alt', 'Imagen no disponible');
    }
  }
}
