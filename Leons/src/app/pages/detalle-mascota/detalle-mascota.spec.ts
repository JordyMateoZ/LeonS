import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { DetalleMascota } from './detalle-mascota';

describe('DetalleMascota', () => {
  let component: DetalleMascota;
  let fixture: ComponentFixture<DetalleMascota>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DetalleMascota],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(DetalleMascota);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show the not-found state when there is no id', () => {
    expect(fixture.nativeElement.textContent).toContain('No encontramos esta mascota');
  });
});
