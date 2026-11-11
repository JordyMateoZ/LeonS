import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { DetalleRefugio } from './detalle-refugio';

function crearComponente(id: string): {
  component: DetalleRefugio;
  fixture: ComponentFixture<DetalleRefugio>;
} {
  const paramMap = convertToParamMap({ id });
  TestBed.configureTestingModule({
    imports: [DetalleRefugio],
    providers: [
      provideRouter([]),
      {
        provide: ActivatedRoute,
        useValue: {
          paramMap: of(paramMap),
          snapshot: { paramMap },
        },
      },
    ],
  });

  const fixture = TestBed.createComponent(DetalleRefugio);
  return { component: fixture.componentInstance, fixture };
}

describe('DetalleRefugio', () => {
  it('should load a refugio by its string id', async () => {
    const { component, fixture } = crearComponente('huellitas-wanka');
    await fixture.whenStable();

    expect(component.refugio()?.nombre).toBe('Albergue Huellitas Wanka');
    expect(component.mascotas().length).toBe(2);
    expect(component.resumen().disponibles).toBe(2);
    expect(component.whatsappUrl()).toContain('wa.me/51964123456');
  });

  it('should list the pets of each refugio without mixing them', async () => {
    const { component, fixture } = crearComponente('hogar-san-roque');
    await fixture.whenStable();

    const ids = component.mascotas().map((m) => m.id);
    expect(ids).toEqual([2, 9]);
    expect(component.mascotas().every((m) => m.refugioId === 'hogar-san-roque')).toBe(true);
  });

  it('should show the different pet states of a refugio', async () => {
    const { component, fixture } = crearComponente('amigos-4-patas');
    await fixture.whenStable();

    const estados = component.mascotas().map((m) => m.estado);
    expect(estados).toContain('disponible');
    expect(estados).toContain('adoptada');
    expect(estados).toContain('en_acogida');
    expect(component.resumen().total).toBe(3);
  });

  it('should show a not-found state for an unknown refugio', async () => {
    const { fixture } = crearComponente('no-existe');
    await fixture.whenStable();
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('No encontramos este refugio');
    expect(texto).toContain('Volver al listado de refugios');
  });
});
