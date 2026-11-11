import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { map } from 'rxjs';
import { ESTADOS_MASCOTA, Mascota } from '../../data/mascotas.data';
import { Refugio } from '../../data/refugios.data';
import { MascotasService } from '../../services/mascotas.service';

@Component({
  selector: 'app-detalle-refugio',
  imports: [RouterLink],
  templateUrl: './detalle-refugio.html',
  styleUrl: './detalle-refugio.css',
})
export class DetalleRefugio {
  private readonly route = inject(ActivatedRoute);
  private readonly mascotasService = inject(MascotasService);

  readonly id = toSignal(this.route.paramMap.pipe(map((params) => params.get('id') ?? '')), {
    initialValue: this.route.snapshot.paramMap.get('id') ?? '',
  });

  readonly refugio = computed(() => this.mascotasService.refugioPorId(this.id()));
  readonly mascotas = computed(() => this.mascotasService.mascotasDeRefugio(this.id()));
  readonly resumen = computed(() => this.mascotasService.resumenDeRefugio(this.id()));

  readonly fotoPrincipal = computed(() => this.mascotas()[0]?.foto ?? this.refugio()?.logo ?? '');

  readonly whatsappUrl = computed(() => {
    const refugio = this.refugio();
    if (!refugio) {
      return '#';
    }
    const texto = encodeURIComponent(
      `Hola ${refugio.contacto}, quisiera información sobre ${refugio.nombre} en LeonS.`,
    );
    return `https://wa.me/${refugio.whatsapp}?text=${texto}`;
  });

  estadoDe(mascota: Mascota) {
    return ESTADOS_MASCOTA[mascota.estado];
  }

  etiquetaEspecies(refugio: Refugio): string {
    if (refugio.especies.length === 2) {
      return 'Caninos y Felinos';
    }
    return refugio.especies[0] === 'perro' ? 'Caninos' : 'Felinos';
  }
}
