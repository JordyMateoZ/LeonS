import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { MASCOTAS } from '../../data/mascotas.data';
import { REFUGIOS } from '../../data/refugios.data';
import { SolicitudesService } from '../../services/solicitudes.service';
import { DetalleMascota } from './detalle-mascota';

const STORAGE_KEY = 'leons.solicitudes.v1';

describe('DetalleMascota', () => {
  let component: DetalleMascota;
  let fixture: ComponentFixture<DetalleMascota>;

  beforeEach(async () => {
    localStorage.removeItem(STORAGE_KEY);

    await TestBed.configureTestingModule({
      imports: [DetalleMascota],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(DetalleMascota);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  afterEach(() => {
    localStorage.removeItem(STORAGE_KEY);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show the not-found state when there is no id', () => {
    expect(fixture.nativeElement.textContent).toContain('No encontramos esta mascota');
  });
});

describe('DetalleMascota con una mascota válida', () => {
  let component: DetalleMascota;
  let fixture: ComponentFixture<DetalleMascota>;
  let solicitudes: SolicitudesService;

  beforeEach(async () => {
    localStorage.removeItem(STORAGE_KEY);
    const paramMap = convertToParamMap({ id: '4' });

    await TestBed.configureTestingModule({
      imports: [DetalleMascota],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(paramMap),
            snapshot: { paramMap, queryParamMap: convertToParamMap({}) },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DetalleMascota);
    component = fixture.componentInstance;
    solicitudes = TestBed.inject(SolicitudesService);
    await fixture.whenStable();
    fixture.detectChanges();
  });

  afterEach(() => {
    localStorage.removeItem(STORAGE_KEY);
  });

  it('should register the adoption request and link to Mis Solicitudes', () => {
    expect(component.mascota()?.nombre).toBe('Sumaq');
    expect(component.refugio()?.id).toBe('red-animalista-wanka');

    component.enviarSolicitud(new Event('submit'));

    expect(solicitudes.total()).toBe(4);
    expect(solicitudes.activas()).toBe(3);
    expect(solicitudes.solicitudes()[0].nombre).toBe('Sumaq');

    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Solicitud enviada');
    expect(texto).toContain('Ver mis solicitudes');
  });

  it('should not duplicate an active request for the same pet', () => {
    component.enviarSolicitud(new Event('submit'));
    component.enviarSolicitud(new Event('submit'));

    expect(solicitudes.total()).toBe(4);
    expect(solicitudes.activas()).toBe(3);

    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Ya tienes una solicitud activa');
  });

  it('should use real pets and refugios from the existing catalogue', () => {
    const sumaq = MASCOTAS.find((m) => m.id === 4)!;
    const refugio = REFUGIOS.find((r) => r.id === sumaq.refugioId)!;

    expect(component.mascota()).toBe(sumaq);
    expect(component.refugio()?.nombre).toBe(refugio.nombre);
  });
});
