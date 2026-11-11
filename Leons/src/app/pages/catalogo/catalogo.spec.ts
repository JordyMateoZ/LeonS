import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { Catalogo } from './catalogo';

describe('Catalogo', () => {
  let component: Catalogo;
  let fixture: ComponentFixture<Catalogo>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Catalogo],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Catalogo);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

describe('Catalogo con filtro por refugio', () => {
  let component: Catalogo;
  let fixture: ComponentFixture<Catalogo>;

  beforeEach(async () => {
    const queryParamMap = convertToParamMap({ refugio: 'amigos-4-patas' });

    await TestBed.configureTestingModule({
      imports: [Catalogo],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            queryParamMap: of(queryParamMap),
            snapshot: { queryParamMap, paramMap: convertToParamMap({}) },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Catalogo);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should preserve the shelter id from the query params', () => {
    expect(component.refugioId()).toBe('amigos-4-patas');
    expect(component.refugioFiltro()?.nombre).toBe('Amigos de 4 Patas El Tambo');
  });

  it('should only list the available pets of that shelter', () => {
    const mascotas = component.filtradas();
    expect(mascotas.length).toBe(1);
    expect(mascotas[0].nombre).toBe('Negrito');
    expect(mascotas.every((m) => m.refugioId === 'amigos-4-patas')).toBe(true);
    expect(mascotas.every((m) => m.estado === 'disponible')).toBe(true);
  });

  it('should render the shelter filter banner', () => {
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Filtrando por refugio');
    expect(texto).toContain('Amigos de 4 Patas El Tambo');
    expect(texto).toContain('Ver todas las mascotas');
  });
});
