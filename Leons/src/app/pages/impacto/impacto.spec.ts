import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Impacto } from './impacto';

describe('Impacto', () => {
  let component: Impacto;
  let fixture: ComponentFixture<Impacto>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Impacto],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Impacto);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render the real network metrics', () => {
    const texto = fixture.nativeElement.textContent;

    expect(texto).toContain('Cada adopción cambia una vida');
    expect(component.totalAdoptadas()).toBe(702);
    expect(component.totalRefugios()).toBe(9);
    expect(component.totalEnAcogida()).toBe(96);
    expect(component.totalDistritos()).toBe(6);
    expect(component.totalMascotas()).toBe(12);
  });

  it('should compute the species distribution from the catalogue', () => {
    expect(component.totalPerros()).toBe(7);
    expect(component.totalGatos()).toBe(5);
    expect(component.species()[0].pct).toBe(58);
    expect(component.species()[1].pct).toBe(42);
    expect(component.donutSegments().length).toBe(2);
  });

  it('should compute the adoption totals by district', () => {
    const distritos = component.districts();

    expect(distritos.find((d) => d.name === 'El Tambo')?.count).toBe(231);
    expect(distritos.find((d) => d.name === 'Huancayo Centro')?.count).toBe(157);
    expect(distritos.find((d) => d.name === 'Chilca')?.count).toBe(72);
    expect(distritos.reduce((total, d) => total + d.count, 0)).toBe(702);
  });

  it('should toggle the volunteer notice', () => {
    expect(component.volunteerNotice()).toBe(false);

    component.toggleVolunteerNotice();
    expect(component.volunteerNotice()).toBe(true);

    component.toggleVolunteerNotice();
    expect(component.volunteerNotice()).toBe(false);
  });
});
