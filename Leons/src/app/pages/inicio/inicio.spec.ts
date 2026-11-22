import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Inicio } from './inicio';

describe('Inicio', () => {
  let component: Inicio;
  let fixture: ComponentFixture<Inicio>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Inicio],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Inicio);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('etiqueta por separado los contadores reportados por los refugios', () => {
    const textos = component.metricas().map((m) => m.texto);

    expect(textos).toContain('Adopciones acumuladas reportadas por los refugios');
    expect(textos).toContain('Mascotas en acogida reportadas por los refugios');
    expect(textos).not.toContain('Mascotas con hogar definitivo');
  });
});
