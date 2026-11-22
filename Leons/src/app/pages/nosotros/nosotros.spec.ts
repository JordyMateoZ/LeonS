import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Nosotros } from './nosotros';

describe('Nosotros', () => {
  let component: Nosotros;
  let fixture: ComponentFixture<Nosotros>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Nosotros],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Nosotros);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render the mission and the real network metrics', () => {
    const texto = fixture.nativeElement.textContent;

    expect(texto).toContain('Conectamos hogares responsables');
    expect(component.totalAdoptadas()).toBe(702);
    expect(component.totalRefugios()).toBe(9);
    expect(component.totalDistritos()).toBe(6);
  });

  it('should switch between adopter and shelter tabs', () => {
    expect(component.activeTab()).toBe('adopters');

    component.setTab('shelters');
    expect(component.activeTab()).toBe('shelters');

    component.setTab('adopters');
    expect(component.activeTab()).toBe('adopters');
  });

  it('should toggle the FAQ accordion', () => {
    component.toggleFaq(1);
    expect(component.openFaq()).toBe(1);

    component.toggleFaq(1);
    expect(component.openFaq()).toBeNull();
  });
});
