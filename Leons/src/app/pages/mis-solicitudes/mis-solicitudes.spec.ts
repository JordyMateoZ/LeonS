import { WritableSignal, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';

import { AuthService } from '../../core/auth/auth.service';
import { SolicitudesService } from '../../services/solicitudes.service';
import { MisSolicitudes } from './mis-solicitudes';

describe('MisSolicitudes', () => {
  let component: MisSolicitudes;
  let fixture: ComponentFixture<MisSolicitudes>;
  let cancelar: ReturnType<typeof vi.fn>;
  let error: WritableSignal<string | null>;
  let solicitudes: WritableSignal<any[]>;
  let autenticada: WritableSignal<boolean>;
  let cargar: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    cancelar = vi.fn(async () => true);
    error = signal<string | null>(null);
    solicitudes = signal<any[]>([]);
    autenticada = signal(false);
    cargar = vi.fn(async () => {});

    await TestBed.configureTestingModule({
      imports: [MisSolicitudes],
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: {
            isAuthenticated: () => autenticada(),
            sesionPendiente: () => false,
            errorSesion: () => null,
            revalidar: () => Promise.resolve(),
          },
        },
        {
          provide: SolicitudesService,
          useValue: {
            solicitudes,
            total: signal(0),
            activas: signal(0),
            finalizadas: signal(0),
            canceladas: signal(0),
            error,
            cargar,
            restaurarCanceladas: () => {},
            cancelar,
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MisSolicitudes);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start with an empty list when there is no authenticated session', () => {
    expect(component.total()).toBe(0);
    expect(component.visibles().length).toBe(0);
  });

  it('no carga datos privados mientras la sesión no está confirmada', async () => {
    fixture.detectChanges();
    await fixture.whenStable();

    expect(cargar).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('No se mostrarán datos privados');
  });

  it('carga los datos una sola vez cuando /auth/me confirma la sesión', async () => {
    autenticada.set(true);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(cargar).toHaveBeenCalledTimes(1);
    expect(fixture.nativeElement.textContent).not.toContain('No se mostrarán datos privados');
  });

  it('should filter without errors on an empty list', () => {
    component.cambiarFiltro('active');
    expect(component.visibles().length).toBe(0);

    component.cambiarFiltro('completed');
    expect(component.visibles().length).toBe(0);

    component.cambiarFiltro('cancelled');
    expect(component.visibles().length).toBe(0);
    expect(component.pestanas().some((p) => p.valor === 'cancelled')).toBe(true);
  });

  it('should toggle the empty state', () => {
    component.alternarVacio();
    expect(component.vacio()).toBe(true);

    component.alternarVacio();
    expect(component.vacio()).toBe(false);
  });

  it('sends the selected reason and only confirms a successful cancellation', async () => {
    component.abrirCancelar({ id: 7, nombre: 'Sumaq', exp: 'LS-0490' } as any);
    component.motivoSeleccionado.set('Mudanza fuera de Huancayo');

    await component.confirmarCancelacion();

    expect(cancelar).toHaveBeenCalledWith(7, 'Mudanza fuera de Huancayo');
    expect(component.aCancelar()).toBeNull();
    expect(component.mensaje()).toContain('fue cancelada');
  });

  it('keeps the dialog open and shows the error when cancellation fails', async () => {
    cancelar.mockResolvedValue(false);
    error.set('No se pudo cancelar la solicitud.');
    component.abrirCancelar({ id: 8, nombre: 'Inti', exp: 'LS-0491' } as any);

    await component.confirmarCancelacion();

    expect(component.aCancelar()).not.toBeNull();
    expect(component.mensaje()).toBe('No se pudo cancelar la solicitud.');
    expect(component.mensaje()).not.toContain('fue cancelada');
  });
});
