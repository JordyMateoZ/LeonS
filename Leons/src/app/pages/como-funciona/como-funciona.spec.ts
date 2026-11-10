import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ComoFunciona } from './como-funciona';

describe('ComoFunciona', () => {
  let component: ComoFunciona;
  let fixture: ComponentFixture<ComoFunciona>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComoFunciona],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ComoFunciona);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render the adoption steps', () => {
    expect(fixture.nativeElement.textContent).toContain('Tu adopción, paso a paso');
    expect(fixture.nativeElement.textContent).toContain('Explora y elige con el corazón');
  });

  it('should toggle the FAQ accordion', () => {
    component.alternarFaq(1);
    expect(component.faqAbierta()).toBe(1);

    component.alternarFaq(1);
    expect(component.faqAbierta()).toBeNull();
  });
});
