import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { map } from 'rxjs';
import { MascotasService } from '../../services/mascotas.service';

type Orden = 'recent' | 'urgent' | 'youngest' | 'oldest';

interface Opcion {
  etiqueta: string;
  valor: string;
  icono?: string;
}

@Component({
  selector: 'app-catalogo',
  imports: [RouterLink],
  templateUrl: './catalogo.html',
  styleUrl: './catalogo.css',
})
export class Catalogo {
  private readonly mascotasService = inject(MascotasService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  /** Refugio recibido por query param al llegar desde «Ver mascotas». */
  readonly refugioId = toSignal(
    this.route.queryParamMap.pipe(map((params) => params.get('refugio') ?? '')),
    { initialValue: this.route.snapshot.queryParamMap.get('refugio') ?? '' },
  );

  readonly refugioFiltro = computed(() => {
    const id = this.refugioId();
    return id ? this.mascotasService.refugioPorId(id) : undefined;
  });

  // Valores constantes para el icono de favorito
  readonly fill0 = "'FILL' 0";
  readonly fill1 = "'FILL' 1";

  // Paginación en cliente
  readonly porPagina = 8;

  // Opciones de los filtros
  readonly especies: Opcion[] = [
    { etiqueta: 'Todos', valor: 'todos' },
    { etiqueta: 'Perros', valor: 'perro', icono: 'cruelty_free' },
    { etiqueta: 'Gatos', valor: 'gato', icono: 'sound_detection_dog_barking' },
    { etiqueta: 'Otros', valor: 'otro' },
  ];
  readonly distritos = [
    'Todos',
    'Huancayo Centro',
    'El Tambo',
    'Chilca',
    'Pilcomayo',
    'San Agustín de Cajas',
    'Sapallanga',
  ];
  readonly tamanos = ['Todos', 'Pequeño', 'Mediano', 'Grande'];
  readonly edades: Opcion[] = [
    { etiqueta: 'Todos', valor: 'todos' },
    { etiqueta: 'Cachorro (<1a)', valor: 'cachorro' },
    { etiqueta: 'Joven (1-3a)', valor: 'joven' },
    { etiqueta: 'Adulto (3-7a)', valor: 'adulto' },
    { etiqueta: 'Senior (>7a)', valor: 'senior' },
  ];
  readonly sexos = ['Todos', 'Macho', 'Hembra'];

  // Estado de los filtros
  busqueda = signal('');
  especie = signal('todos');
  distrito = signal('Todos');
  tamano = signal('Todos');
  edad = signal('todos');
  sexo = signal('Todos');
  soloEsterilizados = signal(false);
  soloVacunados = signal(false);
  soloUrgentes = signal(false);
  orden = signal<Orden>('recent');

  // Otros estados interactivos
  favoritos = signal<ReadonlySet<number>>(new Set<number>());
  paginaActual = signal(1);
  alertaMensaje = signal('');

  // Datos compartidos con Inicio y la ficha de detalle
  readonly mascotas = this.mascotasService.mascotas;

  // Total real de mascotas registradas
  get totalMascotas(): number {
    return this.mascotasService.total;
  }

  // Lista filtrada y ordenada según el estado de los signals
  readonly filtradas = computed(() => {
    const q = this.busqueda().trim().toLowerCase();
    const lista = this.mascotas.filter(
      (m) =>
        (!q ||
          [m.nombre, m.refugio, m.etiqueta, m.lugar].some((t) => t.toLowerCase().includes(q))) &&
        (!this.refugioId() || m.refugioId === this.refugioId()) &&
        (this.especie() === 'todos' || m.especie === this.especie()) &&
        (this.distrito() === 'Todos' || m.distrito === this.distrito()) &&
        (this.tamano() === 'Todos' || m.tamano === this.tamano()) &&
        (this.sexo() === 'Todos' || m.sexo === this.sexo()) &&
        this.coincideEdad(m.edadAnios, this.edad()) &&
        (!this.soloEsterilizados() || m.esterilizado) &&
        (!this.soloVacunados() || m.vacunado) &&
        (!this.soloUrgentes() || m.urgente),
    );
    switch (this.orden()) {
      case 'urgent':
        return [...lista].sort((a, b) => Number(b.urgente) - Number(a.urgente));
      case 'youngest':
        return [...lista].sort((a, b) => a.edadAnios - b.edadAnios);
      case 'oldest':
        return [...lista].sort((a, b) => b.edadAnios - a.edadAnios);
      default:
        return lista;
    }
  });

  // Paginación calculada sobre el resultado filtrado
  readonly totalPaginas = computed(() =>
    Math.max(1, Math.ceil(this.filtradas().length / this.porPagina)),
  );
  readonly paginas = computed(() => Array.from({ length: this.totalPaginas() }, (_, i) => i + 1));
  readonly paginaSegura = computed(() => Math.min(this.paginaActual(), this.totalPaginas()));
  readonly visibles = computed(() => {
    const inicio = (this.paginaSegura() - 1) * this.porPagina;
    return this.filtradas().slice(inicio, inicio + this.porPagina);
  });

  private coincideEdad(anios: number, grupo: string): boolean {
    switch (grupo) {
      case 'cachorro':
        return anios < 1;
      case 'joven':
        return anios >= 1 && anios < 3;
      case 'adulto':
        return anios >= 3 && anios <= 7;
      case 'senior':
        return anios > 7;
      default:
        return true;
    }
  }

  buscar(texto: string) {
    this.busqueda.set(texto);
  }

  limpiarFiltros() {
    this.busqueda.set('');
    this.especie.set('todos');
    this.distrito.set('Todos');
    this.tamano.set('Todos');
    this.edad.set('todos');
    this.sexo.set('Todos');
    this.soloEsterilizados.set(false);
    this.soloVacunados.set(false);
    this.soloUrgentes.set(false);
    this.orden.set('recent');
    this.paginaActual.set(1);
    if (this.refugioId()) {
      this.router.navigate(['/mascotas']);
    }
  }

  quitarFiltroRefugio() {
    this.router.navigate(['/mascotas']);
  }

  cambiarOrden(valor: string) {
    this.orden.set(valor as Orden);
  }

  alternarEsterilizados() {
    this.soloEsterilizados.update((v) => !v);
  }
  alternarVacunados() {
    this.soloVacunados.update((v) => !v);
  }
  alternarUrgentes() {
    this.soloUrgentes.update((v) => !v);
  }

  esFavorito(id: number): boolean {
    return this.favoritos().has(id);
  }

  alternarFavorito(id: number) {
    const nuevo = new Set(this.favoritos());
    if (nuevo.has(id)) nuevo.delete(id);
    else nuevo.add(id);
    this.favoritos.set(nuevo);
  }

  irAPagina(n: number) {
    if (n >= 1 && n <= this.totalPaginas()) {
      this.paginaActual.set(n);
    }
  }

  registrarAlerta(contacto: string) {
    this.alertaMensaje.set(
      contacto.trim()
        ? 'Listo, te avisaremos cuando llegue una mascota para ti.'
        : 'Escribe tu correo o WhatsApp para avisarte.',
    );
  }
}
