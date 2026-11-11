import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Refugios } from './refugios';

describe('Refugios', () => {
  let component: Refugios;
  let fixture: ComponentFixture<Refugios>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Refugios],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Refugios);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should list the 9 real refugios with their string ids', () => {
    expect(component.refugios().length).toBe(9);
    expect(component.refugios().every((r) => typeof r.id === 'string')).toBe(true);
    expect(component.refugios().map((r) => r.id)).toContain('huellitas-wanka');
    expect(component.filtrados().length).toBe(9);
  });

  it('should calculate the statistics from the service data', () => {
    expect(component.estadisticas().map((e) => e.valor)).toEqual(['9', '702', '96', '6']);
  });

  it('should group the coverage by the 6 real districts', () => {
    expect(component.cobertura().length).toBe(6);
    const aliados = component
      .cobertura()
      .reduce((total, c) => total + Number(c.aliados.split(' ')[0]), 0);
    expect(aliados).toBe(9);
  });

  it('should filter by district and type', () => {
    component.distrito.set('Chilca');
    expect(component.filtrados().map((r) => r.nombre)).toEqual(['Hogar San Roque Chilca']);

    component.distrito.set('Todos');
    component.tipo.set('independiente');
    expect(component.filtrados().length).toBe(4);
  });

  it('should filter by species', () => {
    component.especie.set('gato');
    expect(component.filtrados().length).toBe(8);

    component.especie.set('perro');
    expect(component.filtrados().length).toBe(7);
  });

  it('should sort by rescues and available pets', () => {
    component.cambiarOrden('rescues');
    expect(component.filtrados()[0].adopciones).toBe(140);

    component.cambiarOrden('available');
    expect(component.filtrados()[0].disponibles).toBe(2);
  });

  it('should search by name and show an empty state message', () => {
    component.buscar('Esperanza');
    expect(component.filtrados().length).toBe(1);

    component.buscar('inexistente');
    fixture.detectChanges();
    expect(component.filtrados().length).toBe(0);
    expect(fixture.nativeElement.textContent).toContain('No encontramos refugios con esos filtros');
  });
});
