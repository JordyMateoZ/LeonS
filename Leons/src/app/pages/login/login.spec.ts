import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Login } from './login';

describe('Login', () => {
  let component: Login;
  let fixture: ComponentFixture<Login>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start on the register tab', () => {
    expect(fixture.nativeElement.textContent).toContain('Crea tu cuenta en LeonS');
  });

  it('should switch to the login tab', async () => {
    component.cambiarModo('login');
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('¡Bienvenido de vuelta a LeonS!');
  });

  it('should show a message when Google OAuth is not configured', () => {
    component.google();
    expect(component.mensaje()).toContain('Google');
  });

  it('should block registration without accepting the terms', () => {
    component.aceptaTerminos.set(false);
    component.clave.set('Password123');
    component.registrar(new Event('submit'));

    expect(component.mensaje()).toContain('Compromiso de Bienestar Animal');
  });
});
