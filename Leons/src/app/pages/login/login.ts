import { Component, OnDestroy, PLATFORM_ID, computed, inject, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';
import { ApiError } from '../../core/api/api-error';

type Modo = 'register' | 'login';
type Rol = 'adopter' | 'shelter';

interface Distrito {
  valor: string;
  nombre: string;
}

interface Prueba {
  icono: string;
  fondo: string;
  iconoClase: string;
  relleno: boolean;
  titulo: string;
  texto: string;
}

interface Beneficio {
  icono: string;
  fondo: string;
  iconoClase: string;
  titulo: string;
  texto: string;
}

@Component({
  selector: 'app-login',
  imports: [RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login implements OnDestroy {
  readonly fill0 = "'FILL' 0";
  readonly fill1 = "'FILL' 1";

  private readonly platformId = inject(PLATFORM_ID);
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);
  private mensajeTimer?: ReturnType<typeof setTimeout>;

  // Estado interactivo
  modo = signal<Modo>('register');
  rol = signal<Rol>('adopter');
  clave = signal('');
  verClaveRegistro = signal(false);
  verClaveLogin = signal(false);
  aceptaTerminos = signal(false);
  mensaje = signal('');
  cargando = signal(false);

  // Fortaleza de la contraseña (misma lógica del script de Stitch)
  readonly fortaleza = computed(() => {
    const v = this.clave();
    if (!v) return { barra: 'w-1/4 bg-primary', texto: 'Básica' };
    if (v.length < 5) return { barra: 'w-1/4 bg-error', texto: 'Débil' };
    if (v.length < 9) return { barra: 'w-2/4 bg-primary', texto: 'Moderada' };
    if (/[A-Z]/.test(v) && /[0-9]/.test(v)) return { barra: 'w-full bg-secondary', texto: 'Excelente' };
    return { barra: 'w-3/4 bg-primary-container', texto: 'Buena' };
  });

  readonly distritos: Distrito[] = [
    { valor: 'el-tambo', nombre: 'El Tambo' },
    { valor: 'huancayo-centro', nombre: 'Huancayo Centro' },
    { valor: 'chilca', nombre: 'Chilca' },
    { valor: 'pilcomayo', nombre: 'Pilcomayo' },
    { valor: 'san-agustin', nombre: 'San Agustín de Cajas' },
    { valor: 'sapallanga', nombre: 'Sapallanga' },
    { valor: 'san-jeronimo', nombre: 'San Jerónimo de Tunán' },
    { valor: 'huancan', nombre: 'Huancán' },
    { valor: 'concepcion', nombre: 'Concepción (Valle)' },
    { valor: 'chupaca', nombre: 'Chupaca (Valle)' },
  ];

  // Datos de ejemplo (más adelante pueden venir de la API)
  readonly pruebas: Prueba[] = [
    {
      icono: 'diversity_3',
      fondo: 'bg-secondary-container',
      iconoClase: 'text-on-secondary-container',
      relleno: true,
      titulo: '+1,200 Familias y Rescatistas',
      texto: 'Comunidad activa en Huancayo, San Jerónimo y El Tambo.',
    },
    {
      icono: 'verified',
      fondo: 'bg-primary-fixed',
      iconoClase: 'text-primary',
      relleno: true,
      titulo: '100% Sin Fines de Lucro',
      texto: 'Prohibida la venta de animales. Todo proceso es gratuito.',
    },
    {
      icono: 'medical_services',
      fondo: 'bg-surface-variant',
      iconoClase: 'text-secondary',
      relleno: false,
      titulo: 'Apoyo Veterinario Solidario',
      texto: 'Campañas de esterilización y vacunación en Junín.',
    },
  ];

  readonly beneficios: Beneficio[] = [
    {
      icono: 'home_pin',
      fondo: 'bg-primary-fixed',
      iconoClase: 'text-primary',
      titulo: 'Cercanía y Validación',
      texto:
        'Priorizamos visitas domiciliarias y adopciones responsables dentro de la provincia de Huancayo y el Valle del Mantaro.',
    },
    {
      icono: 'receipt_long',
      fondo: 'bg-secondary-container',
      iconoClase: 'text-on-secondary-container',
      titulo: 'Compromiso Notarial Solidario',
      texto:
        'Firma un acta simple de tenencia responsable con compromiso de esterilización y vacunas anuales.',
    },
    {
      icono: 'volunteer_activism',
      fondo: 'bg-surface-container-high',
      iconoClase: 'text-secondary',
      titulo: 'Red de Rescate Colectivo',
      texto:
        'Si eres albergue o rescatista independiente de Junín, LeonS te brinda visibilidad gratuita y filtros de candidatos.',
    },
  ];

  cambiarModo(m: Modo) {
    this.modo.set(m);
  }

  elegirRol(r: Rol) {
    if (r === 'shelter') {
      this.avisar(
        'El registro de refugios o rescatistas está temporalmente no disponible. Por ahora puedes registrarte como adoptante.',
      );
      return;
    }
    this.rol.set(r);
  }

  alternarVerClaveRegistro() {
    this.verClaveRegistro.update((v) => !v);
  }

  alternarVerClaveLogin() {
    this.verClaveLogin.update((v) => !v);
  }

  registrar(e: Event) {
    e.preventDefault();
    if (this.cargando()) {
      return;
    }
    if (this.rol() === 'shelter') {
      this.avisar(
        'El registro de refugios o rescatistas está temporalmente no disponible. Por ahora puedes registrarte como adoptante.',
      );
      return;
    }
    if (!this.aceptaTerminos()) {
      this.avisar('Debes aceptar el Compromiso de Bienestar Animal para crear tu cuenta.');
      return;
    }
    if (this.clave().length < 8) {
      this.avisar('La contraseña debe tener al menos 8 caracteres.');
      return;
    }

    const form = e.target as HTMLFormElement;
    const data = new FormData(form);
    const nombre = String(data.get('name') ?? '').trim();
    const email = String(data.get('email') ?? '').trim();
    const dni = String(data.get('dni') ?? '').trim();
    const telefono = String(data.get('phone') ?? '').trim();
    const password = this.clave();
    const distritoSlug = String(data.get('district') ?? '');
    const distrito = this.distritos.find((d) => d.valor === distritoSlug)?.nombre ?? null;
    const rol = 'adoptante';

    if (!nombre || !email) {
      this.avisar('Completa tu nombre y correo para crear la cuenta.');
      return;
    }
    if (!/^\d{8}$/.test(dni)) {
      this.avisar('Ingresa un DNI válido de 8 dígitos.');
      return;
    }

    this.cargando.set(true);
    this.authService
      .registrar({
        nombre,
        email,
        dni,
        password,
        telefono: telefono || null,
        distrito,
        rol,
        refugioId: null,
      })
      .subscribe({
        next: () => {
          this.cargando.set(false);
          this.avisar('¡Cuenta creada! Bienvenido a LeonS.');
          void this.router.navigateByUrl('/mis-solicitudes');
        },
        error: (error: unknown) => {
          this.cargando.set(false);
          this.avisar(this.mensajeDeError(error));
        },
      });
  }

  ingresar(e: Event) {
    e.preventDefault();
    if (this.cargando()) {
      return;
    }
    const form = e.target as HTMLFormElement;
    const data = new FormData(form);
    const identificador = String(data.get('username') ?? '').trim();
    const password = String(data.get('password') ?? '');

    if (!identificador || !password) {
      this.avisar('Ingresa tu correo/DNI y contraseña.');
      return;
    }

    this.cargando.set(true);
    this.authService
      .login({ identificador, password })
      .subscribe({
        next: () => {
          this.cargando.set(false);
          this.avisar('¡Bienvenido a LeonS!');
          void this.router.navigateByUrl('/mis-solicitudes');
        },
        error: (error: unknown) => {
          this.cargando.set(false);
          this.avisar(this.mensajeDeError(error));
        },
      });
  }

  recuperarClave() {
    this.avisar('La recuperación de contraseña se habilitará cuando conectemos la API de LeonS.');
  }

  contactarSoporte() {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    const texto = encodeURIComponent('Hola, necesito ayuda para acceder a mi cuenta de LeonS.');
    window.open(`https://wa.me/51964123456?text=${texto}`, '_blank', 'noopener,noreferrer');
  }

  ngOnDestroy() {
    if (this.mensajeTimer) {
      clearTimeout(this.mensajeTimer);
    }
  }

  private mensajeDeError(error: unknown): string {
    if (error instanceof ApiError) {
      return error.message || 'No se pudo completar la operación.';
    }
    return 'No se pudo conectar con el servidor. Intenta de nuevo.';
  }

  private avisar(texto: string) {
    this.mensaje.set(texto);
    if (this.mensajeTimer) {
      clearTimeout(this.mensajeTimer);
    }
    this.mensajeTimer = setTimeout(() => this.mensaje.set(''), 4000);
  }
}
