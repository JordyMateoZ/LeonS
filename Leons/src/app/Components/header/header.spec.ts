import { WritableSignal, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';

import { AuthService, EstadoSesion } from '../../core/auth/auth.service';
import { SolicitudesService } from '../../services/solicitudes.service';
import { Header } from './header';

describe('Header', () => {
  let component: Header;
  let fixture: ComponentFixture<Header>;
  let estado: WritableSignal<EstadoSesion>;
  let cerrarSesion: ReturnType<typeof vi.fn>;

  async function configurar(estadoInicial: EstadoSesion) {
    estado = signal<EstadoSesion>(estadoInicial);
    cerrarSesion = vi.fn(() => estado.set('no-autenticada'));
    await TestBed.configureTestingModule({
      imports: [Header],
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: {
            isAuthenticated: () => estado() === 'confirmada',
            sesionPendiente: () => estado() === 'pendiente',
            usuario: signal(null).asReadonly(),
            cerrarSesion,
          },
        },
        {
          provide: SolicitudesService,
          useValue: {
            activas: signal(0).asReadonly(),
            limpiarPrivados: vi.fn(),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Header);
    component = fixture.componentInstance;
    await fixture.whenStable();
  }

  afterEach(() => {
    localStorage.removeItem('leons.token.v1');
  });

  it('should create', async () => {
    await configurar('no-autenticada');
    expect(component).toBeTruthy();
  });

  it('muestra acceso público y oculta datos privados sin sesión', async () => {
    await configurar('no-autenticada');
    const html = fixture.nativeElement as HTMLElement;

    expect(html.textContent).toContain('Iniciar sesión');
    expect(html.querySelector('a[href="/mis-solicitudes"]')).toBeNull();
    expect(html.querySelector('[data-accion="cerrar-sesion"]')).toBeNull();
  });

  it('muestra Mis solicitudes y un cierre de sesión visible con sesión confirmada', async () => {
    await configurar('confirmada');
    const html = fixture.nativeElement as HTMLElement;

    expect(html.querySelector('a[href="/mis-solicitudes"]')).toBeTruthy();
    expect(html.textContent).toContain('Cerrar sesión');
    expect(html.querySelector('[data-accion="cerrar-sesion"]')).toBeTruthy();
    expect(html.textContent).not.toContain('Iniciar sesión');
  });

  it('cierra la sesión al pulsar el botón', async () => {
    await configurar('confirmada');
    const boton = fixture.nativeElement.querySelector(
      '[data-accion="cerrar-sesion"]',
    ) as HTMLButtonElement;

    boton.click();
    await fixture.whenStable();

    expect(cerrarSesion).toHaveBeenCalledTimes(1);
  });

  it('no muestra datos privados mientras la sesión está pendiente', async () => {
    await configurar('pendiente');
    const html = fixture.nativeElement as HTMLElement;

    expect(html.querySelector('a[href="/mis-solicitudes"]')).toBeNull();
    expect(html.querySelector('[data-accion="cerrar-sesion"]')).toBeNull();
    expect(html.textContent).toContain('Verificando sesión');
  });
});
