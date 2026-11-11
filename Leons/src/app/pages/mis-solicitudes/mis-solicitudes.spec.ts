import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { MASCOTAS } from '../../data/mascotas.data';
import { REFUGIOS } from '../../data/refugios.data';
import { SolicitudesService } from '../../services/solicitudes.service';
import { MisSolicitudes } from './mis-solicitudes';

const STORAGE_KEY = 'leons.solicitudes.v1';

describe('MisSolicitudes', () => {
  let component: MisSolicitudes;
  let fixture: ComponentFixture<MisSolicitudes>;

  beforeEach(async () => {
    localStorage.removeItem(STORAGE_KEY);

    await TestBed.configureTestingModule({
      imports: [MisSolicitudes],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(MisSolicitudes);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  afterEach(() => {
    localStorage.removeItem(STORAGE_KEY);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show the three sample requests', () => {
    expect(component.total()).toBe(3);
    expect(component.enProceso()).toBe(2);
    expect(component.finalizadas()).toBe(1);

    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('Chaska');
    expect(texto).toContain('Inti');
    expect(texto).toContain('Wanka');
  });

  it('should filter the active requests', () => {
    component.cambiarFiltro('active');

    expect(component.visibles().length).toBe(2);
    expect(component.visibles().every((s) => s.estado === 'active')).toBe(true);
  });

  it('should filter the completed requests', () => {
    component.cambiarFiltro('completed');

    expect(component.visibles().length).toBe(1);
    expect(component.visibles()[0].nombre).toBe('Wanka');
  });

  it('should cancel a request and update the counters', () => {
    component.abrirCancelar(component.visibles()[0]);
    component.confirmarCancelacion();

    expect(component.total()).toBe(2);
    expect(component.mensaje()).toContain('cancelada');
  });

  it('should toggle the empty state', () => {
    component.alternarVacio();
    expect(component.mostrarVacio()).toBe(true);

    component.alternarVacio();
    expect(component.mostrarVacio()).toBe(false);
    expect(component.total()).toBe(3);
  });

  it('should show a request sent from a pet detail', () => {
    const servicio = TestBed.inject(SolicitudesService);
    const sumaq = MASCOTAS.find((m) => m.id === 4)!;
    const refugio = REFUGIOS.find((r) => r.id === 'red-animalista-wanka')!;

    servicio.crearDesdeMascota(sumaq, refugio);
    fixture.detectChanges();

    expect(component.total()).toBe(4);
    expect(component.enProceso()).toBe(3);
    expect(fixture.nativeElement.textContent).toContain('Sumaq');
  });
});
