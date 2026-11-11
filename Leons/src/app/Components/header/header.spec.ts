import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Header } from './header';

const STORAGE_KEY = 'leons.solicitudes.v1';

describe('Header', () => {
  let component: Header;
  let fixture: ComponentFixture<Header>;

  beforeEach(async () => {
    localStorage.removeItem(STORAGE_KEY);

    await TestBed.configureTestingModule({
      imports: [Header],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Header);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  afterEach(() => {
    localStorage.removeItem(STORAGE_KEY);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show a labelled access to Mis Solicitudes', () => {
    const enlace = fixture.nativeElement.querySelector(
      'a[href="/mis-solicitudes"]',
    ) as HTMLAnchorElement;

    expect(enlace).toBeTruthy();
    expect(enlace.textContent).toContain('Mis solicitudes');
    expect(enlace.getAttribute('aria-label')).toContain('2 activas');
  });

  it('should show the badge with the active requests count', () => {
    expect(component.activas()).toBe(2);
    const enlace = fixture.nativeElement.querySelector(
      'a[href="/mis-solicitudes"]',
    ) as HTMLAnchorElement;

    expect(enlace.textContent).toContain('2');
  });
});
