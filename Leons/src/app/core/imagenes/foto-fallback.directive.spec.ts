import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { FOTO_PLACEHOLDER, FotoFallbackDirective } from './foto-fallback.directive';

@Component({
  imports: [FotoFallbackDirective],
  template: `<img [src]="src" [alt]="alt" appFotoFallback />`,
})
class Host {
  src = 'https://example.invalid/michi-rota.jpg';
  alt = 'Michi Mantaro';
}

describe('FotoFallbackDirective', () => {
  let fixture: ComponentFixture<Host>;
  let imagen: HTMLImageElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [Host] }).compileComponents();
    fixture = TestBed.createComponent(Host);
    fixture.detectChanges();
    imagen = fixture.nativeElement.querySelector('img') as HTMLImageElement;
  });

  it('sustituye una foto rota por el placeholder local conservando el alt', () => {
    imagen.dispatchEvent(new Event('error'));

    expect(imagen.getAttribute('src')).toBe(FOTO_PLACEHOLDER);
    expect(imagen.getAttribute('alt')).toBe('Michi Mantaro');
  });

  it('no reasigna el src cuando ya está el placeholder: sin ciclo de error', () => {
    imagen.setAttribute('src', FOTO_PLACEHOLDER);
    const setter = vi.spyOn(imagen, 'setAttribute');

    imagen.dispatchEvent(new Event('error'));
    imagen.dispatchEvent(new Event('error'));

    expect(setter).not.toHaveBeenCalled();
    expect(imagen.getAttribute('src')).toBe(FOTO_PLACEHOLDER);
  });

  it('usa un alt identificable cuando la imagen no tiene texto alternativo', () => {
    imagen.removeAttribute('alt');

    imagen.dispatchEvent(new Event('error'));

    expect(imagen.getAttribute('alt')).toBe('Imagen no disponible');
  });
});
