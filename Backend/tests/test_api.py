"""Pruebas del contrato `/api/v1` (Fases 0–3, repositorio en memoria)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from .conftest import autenticar

API = "/api/v1"


# 1 -------------------------------------------------------------------------
def test_health(client: TestClient) -> None:
    salud = client.get("/health")
    assert salud.status_code == 200
    assert salud.json()["status"] == "ok"
    assert salud.json()["backend"] == "memory"

    docs = client.get("/docs")
    assert docs.status_code == 200

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    rutas = openapi.json()["paths"]
    assert "/api/v1/mascotas" in rutas
    assert "/api/v1/solicitudes" in rutas


# 2 -------------------------------------------------------------------------
def test_mascotas_paginacion_y_estado(client: TestClient) -> None:
    primera = client.get(f"{API}/mascotas", params={"page": 1, "limit": 8})
    assert primera.status_code == 200
    cuerpo = primera.json()
    assert cuerpo["page"] == 1
    assert cuerpo["limit"] == 8
    assert cuerpo["total"] == 16
    assert cuerpo["totalPages"] == 2
    assert len(cuerpo["items"]) == 8
    assert [m["id"] for m in cuerpo["items"]] == [16, 15, 14, 13, 12, 11, 10, 9]

    segunda = client.get(f"{API}/mascotas", params={"page": 2, "limit": 8}).json()
    assert [m["id"] for m in segunda["items"]] == [8, 7, 6, 5, 4, 3, 2, 1]

    disponibles = client.get(f"{API}/mascotas", params={"estado": "disponible"}).json()
    assert disponibles["total"] == 12

    adoptadas = client.get(f"{API}/mascotas", params={"estado": "adoptada"}).json()
    assert adoptadas["total"] == 2
    assert {m["id"] for m in adoptadas["items"]} == {13, 15}

    acogida = client.get(f"{API}/mascotas", params={"estado": "en_acogida"}).json()
    assert acogida["total"] == 2
    assert {m["id"] for m in acogida["items"]} == {14, 16}

    ficha = client.get(f"{API}/mascotas/13")
    assert ficha.status_code == 200
    assert ficha.json()["estado"] == "adoptada"
    assert ficha.json()["refugioId"] == "amigos-4-patas"

    inexistente = client.get(f"{API}/mascotas/999")
    assert inexistente.status_code == 404
    assert inexistente.json()["code"] == "NOT_FOUND"


# 3 -------------------------------------------------------------------------
def test_mascotas_filtros(client: TestClient) -> None:
    def total(**params: object) -> int:
        respuesta = client.get(f"{API}/mascotas", params=params)
        assert respuesta.status_code == 200, respuesta.text
        return respuesta.json()["total"]

    assert total(especie="gato") == 7
    assert total(especie="perro") == 9
    assert total(distrito="El Tambo") == 6
    assert total(tamano="Grande") == 2
    assert total(sexo="Hembra") == 9
    assert total(edad="cachorro") == 3
    assert total(q="chaska") == 1
    assert total(soloUrgentes="true") == 2
    assert total(soloVacunados="true") == 13
    assert total(refugioId="huellitas-wanka") == 2

    jovenes = client.get(f"{API}/mascotas", params={"orden": "youngest", "limit": 5}).json()
    assert jovenes["items"][0]["id"] == 4

    mayores = client.get(f"{API}/mascotas", params={"orden": "oldest", "limit": 3}).json()
    assert mayores["items"][0]["id"] == 13

    urgentes = client.get(f"{API}/mascotas", params={"orden": "urgent", "limit": 3}).json()
    assert {m["id"] for m in urgentes["items"][:2]} == {1, 7}

    busqueda = client.get(f"{API}/mascotas", params={"q": "chaska"}).json()
    mascota = busqueda["items"][0]
    assert mascota["nombre"] == "Chaska"
    assert mascota["generoTexto"] == "Perra"
    assert mascota["edadTexto"] == "1.5 años"
    assert mascota["tamanoTexto"] == "Mediana • 14 kg"
    assert mascota["badgeClase"] == "text-primary bg-primary-fixed"
    assert mascota["actualizado"] == "hace 2 días"


# 4 -------------------------------------------------------------------------
def test_stats_detalle_y_similares(client: TestClient) -> None:
    stats = client.get(f"{API}/mascotas/stats")
    assert stats.status_code == 200
    cuerpo = stats.json()
    assert cuerpo["total"] == 12
    assert cuerpo["totalRegistradas"] == 16
    assert cuerpo["disponibles"] == 12
    assert cuerpo["adoptadas"] == 2
    assert cuerpo["enAcogida"] == 2
    assert cuerpo["urgentes"] == 2
    assert cuerpo["totalRefugios"] == 9
    assert cuerpo["porEspecie"] == {"gato": 7, "perro": 9}
    assert cuerpo["porDistrito"]["El Tambo"] == 6

    detalle = client.get(f"{API}/mascotas/1/detalle")
    assert detalle.status_code == 200
    datos = detalle.json()
    assert datos["mascota"]["id"] == 1
    assert datos["refugio"]["id"] == "huellitas-wanka"
    assert len(datos["historia"]) == 3
    assert len(datos["cuidados"]) == 4
    assert len(datos["requisitos"]) == 4
    assert len(datos["preguntas"]) == 3
    assert len(datos["galeria"]) == 5
    assert datos["cita"]["autor"].startswith("Lic. Silvia Mallqui")
    assert len(datos["similares"]) == 3

    similares = client.get(f"{API}/mascotas/1/similares", params={"limite": 3})
    assert similares.status_code == 200
    assert [m["id"] for m in similares.json()] == [6, 3, 4]

    assert client.get(f"{API}/mascotas/999/detalle").status_code == 404
    assert client.get(f"{API}/mascotas/999/similares").status_code == 404


def test_rasgos_solo_registrados(client: TestClient) -> None:
    """Los rasgos son individuales: sin registro no se inventan (INC-003)."""
    chaska = client.get(f"{API}/mascotas/1").json()
    assert [rasgo["texto"] for rasgo in chaska["rasgos"]] == [
        "Juguetona y cariñosa",
        "Tranquila en interiores",
        "Excelente con niños",
        "Sociable con otros perros",
        "Acostumbrada a paseos con correa",
        "Tolerante con gatos (prueba básica OK)",
    ]

    killa = client.get(f"{API}/mascotas/12").json()
    assert killa["nombre"] == "Killa"
    assert killa["rasgos"] == []

    detalle = client.get(f"{API}/mascotas/12/detalle")
    assert detalle.status_code == 200
    datos = detalle.json()
    assert datos["mascota"]["id"] == 12
    assert datos["mascota"]["rasgos"] == []
    # El resto del contrato no se toca.
    assert len(datos["historia"]) == 3
    assert len(datos["cuidados"]) == 3  # 2 de salud + condición física (sin override)
    assert len(datos["requisitos"]) == 4
    assert len(datos["preguntas"]) == 3
    assert len(datos["galeria"]) > 0
    assert isinstance(datos["mascota"]["salud"], list)
    assert len(datos["similares"]) == 3

    listado = client.get(f"{API}/mascotas", params={"limit": 50}).json()
    assert listado["total"] == 16
    assert sum(len(item["rasgos"]) for item in listado["items"]) == 6


# 5 -------------------------------------------------------------------------
def test_refugios(client: TestClient) -> None:
    listado = client.get(f"{API}/refugios")
    assert listado.status_code == 200
    assert len(listado.json()) == 9

    detalle = client.get(f"{API}/refugios/huellitas-wanka")
    assert detalle.status_code == 200
    datos = detalle.json()
    assert datos["refugio"]["nombre"] == "Albergue Huellitas Wanka"
    assert datos["refugio"]["adoptadas"] == 86
    assert datos["resumen"] == {
        "total": 2,
        "disponibles": 2,
        "adoptadas": 0,
        "enAcogida": 0,
    }
    assert {m["id"] for m in datos["mascotas"]} == {1, 12}

    mascotas = client.get(f"{API}/refugios/huellitas-wanka/mascotas")
    assert mascotas.status_code == 200
    assert len(mascotas.json()) == 2

    felinos = client.get(f"{API}/refugios", params={"especie": "gato"}).json()
    assert len(felinos) == 8
    assert "amigos-4-patas" not in {r["id"] for r in felinos}

    tambo = client.get(f"{API}/refugios", params={"distrito": "El Tambo"}).json()
    assert {r["id"] for r in tambo} == {
        "huellitas-wanka",
        "hogar-felino-wanka",
        "amigos-4-patas",
    }

    assert client.get(f"{API}/refugios/no-existe").status_code == 404
    assert client.get(f"{API}/refugios/no-existe/mascotas").status_code == 404


# 6 -------------------------------------------------------------------------
def test_contenido_e_impacto(client: TestClient) -> None:
    contenido = client.get(f"{API}/contenido")
    assert contenido.status_code == 200
    datos = contenido.json()
    assert len(datos["pasosAdopcion"]) == 4
    assert len(datos["pasosRefugio"]) == 3
    assert len(datos["faqs"]) == 6
    assert len(datos["requisitos"]) == 4

    pasos = client.get(f"{API}/contenido/pasos", params={"tipo": "refugio"})
    assert pasos.status_code == 200
    assert len(pasos.json()) == 3

    faqs = client.get(f"{API}/contenido/faqs")
    assert faqs.status_code == 200
    assert len(faqs.json()) == 6

    impacto = client.get(f"{API}/estadisticas/impacto")
    assert impacto.status_code == 200
    cifras = impacto.json()
    assert cifras["totalAdoptadas"] == 702
    assert cifras["totalRefugios"] == 9
    assert cifras["totalEnAcogida"] == 96
    assert cifras["totalDistritos"] == 6
    assert cifras["totalMascotas"] == 12
    assert cifras["totalPerros"] == 7
    assert cifras["totalGatos"] == 5
    assert cifras["adoptadasPorDistrito"]["El Tambo"] == 231
    assert cifras["adoptadasPorDistrito"]["Huancayo Centro"] == 157


# 7 -------------------------------------------------------------------------
def test_registro_y_perfil(client: TestClient) -> None:
    registro = client.post(
        f"{API}/auth/registro",
        json={
            "nombre": "Ana Torres",
            "email": "ana@example.com",
            "dni": "71234567",
            "password": "claveSegura1",
            "telefono": "+51 999 888 777",
            "distrito": "Chilca",
        },
    )
    assert registro.status_code == 201, registro.text
    datos = registro.json()
    assert datos["usuario"]["email"] == "ana@example.com"
    assert datos["usuario"]["rol"] == "adoptante"
    assert datos["token"]
    assert datos["tokenType"] == "Bearer"
    assert "passwordHash" not in datos["usuario"]
    assert "password_hash" not in datos["usuario"]

    perfil = client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {datos['token']}"}
    )
    assert perfil.status_code == 200
    # A-01: el token debe nacer del usuario ya persistido, con id real.
    assert datos["usuario"]["id"] > 0
    assert perfil.json()["id"] == datos["usuario"]["id"]
    assert perfil.json()["dni"] == "71234567"
    assert perfil.json()["telefono"] == "+51 999 888 777"

    login = client.post(
        f"{API}/auth/login",
        json={"email": "ana@example.com", "password": "claveSegura1"},
    )
    assert login.status_code == 200
    assert login.json()["usuario"]["id"] == datos["usuario"]["id"]


# 8 -------------------------------------------------------------------------
def test_registro_rechaza_datos_invalidos(client: TestClient) -> None:
    base = {
        "nombre": "Persona Prueba",
        "email": "persona@example.com",
        "dni": "76543210",
        "password": "claveSegura1",
    }

    mal_correo = client.post(f"{API}/auth/registro", json={**base, "email": "no-es-correo"})
    assert mal_correo.status_code == 422
    assert mal_correo.json()["code"] == "VALIDATION_ERROR"

    clave_corta = client.post(f"{API}/auth/registro", json={**base, "password": "corta"})
    assert clave_corta.status_code == 422

    dni_corto = client.post(f"{API}/auth/registro", json={**base, "dni": "1234567"})
    assert dni_corto.status_code == 422

    correo_repetido = client.post(
        f"{API}/auth/registro", json={**base, "email": "demo@leons.pe"}
    )
    assert correo_repetido.status_code == 409
    assert correo_repetido.json()["code"] == "EMAIL_YA_REGISTRADO"

    dni_repetido = client.post(f"{API}/auth/registro", json={**base, "dni": "70000002"})
    assert dni_repetido.status_code == 409
    assert dni_repetido.json()["code"] == "DNI_YA_REGISTRADO"


# 7b ------------------------------------------------------------------------
# AUD-01: el registro público nunca debe crear roles privilegiados.


def _cuerpo_registro(**sobrescritos) -> dict:
    cuerpo = {
        "nombre": "Registro Seguro",
        "email": "registro-seguro@example.com",
        "dni": "71456789",
        "password": "claveSegura1",
    }
    cuerpo.update(sobrescritos)
    return cuerpo


def _cuerpo_mascota() -> dict:
    return {
        "nombre": "Mascota Prueba AUD01",
        "especie": "perro",
        "sexo": "Macho",
        "raza": "Mestizo",
        "edadAnios": 2,
        "tamano": "Mediano",
        "pesoKg": 12.5,
        "distrito": "El Tambo",
        "lugar": "Huancayo",
        "foto": "/assets/prueba.jpg",
        "alt": "Mascota de prueba",
        "descripcion": "Mascota usada solo para verificar permisos.",
        "etiqueta": "Amigable",
        "refugioId": "huellitas-wanka",
    }


def test_registro_publico_rechaza_roles_privilegiados(client: TestClient, app) -> None:
    repo = app.state.container.repo
    total_inicial = len(repo.listar_usuarios())

    refugio = client.post(
        f"{API}/auth/registro",
        json=_cuerpo_registro(
            email="intento-refugio@example.com",
            dni="71456780",
            rol="refugio",
            refugioId="huellitas-wanka",
        ),
    )
    assert refugio.status_code == 403, refugio.text
    assert refugio.json()["code"] == "FORBIDDEN"

    administrador = client.post(
        f"{API}/auth/registro",
        json=_cuerpo_registro(
            email="intento-admin@example.com",
            dni="71456781",
            rol="admin",
        ),
    )
    assert administrador.status_code == 422, administrador.text
    assert administrador.json()["code"] == "VALIDATION_ERROR"

    assert len(repo.listar_usuarios()) == total_inicial


def test_registro_adoptante_ignora_refugio_id_y_no_eleva(client: TestClient, app) -> None:
    repo = app.state.container.repo
    respuesta = client.post(
        f"{API}/auth/registro",
        json=_cuerpo_registro(rol="adoptante", refugioId="huellitas-wanka"),
    )
    assert respuesta.status_code == 201, respuesta.text
    datos = respuesta.json()
    assert datos["usuario"]["rol"] == "adoptante"
    assert datos["usuario"]["refugioId"] is None

    persistido = repo.buscar_usuario_por_email("registro-seguro@example.com")
    assert persistido is not None
    assert persistido.rol == "adoptante"
    assert persistido.refugio_id is None

    headers = {"Authorization": f"Bearer {datos['token']}"}
    alertas = client.get(f"{API}/alertas-rescate", headers=headers)
    assert alertas.status_code == 403, alertas.text
    assert alertas.json()["code"] == "FORBIDDEN"

    mascotas = client.post(f"{API}/mascotas", json=_cuerpo_mascota(), headers=headers)
    assert mascotas.status_code == 403, mascotas.text
    assert mascotas.json()["code"] == "FORBIDDEN"


# 9 -------------------------------------------------------------------------
def test_login_por_correo_y_dni(client: TestClient) -> None:
    por_correo = client.post(
        f"{API}/auth/login",
        json={"identificador": "demo@leons.pe", "password": "demo12345"},
    )
    assert por_correo.status_code == 200
    assert por_correo.json()["usuario"]["rol"] == "adoptante"

    por_dni = client.post(
        f"{API}/auth/login",
        json={"identificador": "70000001", "password": "demo12345"},
    )
    assert por_dni.status_code == 200
    assert por_dni.json()["usuario"]["email"] == "demo@leons.pe"

    clave_mala = client.post(
        f"{API}/auth/login",
        json={"identificador": "demo@leons.pe", "password": "incorrecta"},
    )
    assert clave_mala.status_code == 401
    assert clave_mala.json()["code"] == "UNAUTHORIZED"

    inexistente = client.post(
        f"{API}/auth/login",
        json={"identificador": "90000000", "password": "demo12345"},
    )
    assert inexistente.status_code == 401

    sin_identificador = client.post(f"{API}/auth/login", json={"password": "demo12345"})
    assert sin_identificador.status_code == 422
    assert sin_identificador.json()["code"] == "CREDENCIALES_REQUERIDAS"

    sin_token = client.get(f"{API}/auth/me")
    assert sin_token.status_code == 401

    token_invalido = client.get(
        f"{API}/auth/me", headers={"Authorization": "Bearer token-falso"}
    )
    assert token_invalido.status_code == 401


# 10 ------------------------------------------------------------------------
def test_listar_solicitudes_demo(client: TestClient) -> None:
    assert client.get(f"{API}/solicitudes").status_code == 401

    headers = autenticar(client)
    listado = client.get(f"{API}/solicitudes", headers=headers)
    assert listado.status_code == 200
    datos = listado.json()
    assert datos["total"] == 3
    assert {s["exp"] for s in datos["items"]} == {
        "#SOL-HYO-2025-084",
        "#SOL-HYO-2025-091",
        "#SOL-HYO-2025-012",
    }

    detalle = client.get(f"{API}/solicitudes/1", headers=headers)
    assert detalle.status_code == 200
    solicitud = detalle.json()
    assert solicitud["nombre"] == "Chaska"
    assert solicitud["paso"] == 3
    assert solicitud["pasoTexto"] == "Paso 3 de 5"
    assert solicitud["estado"] == "active"
    assert len(solicitud["etapas"]) == 5
    assert solicitud["cita"]["coordinadora"] == "Silvia Mallqui"
    assert solicitud["whatsapp"] == "https://wa.me/51964123456"

    completada = client.get(f"{API}/solicitudes/3", headers=headers).json()
    assert completada["estado"] == "completed"
    assert completada["cierre"]["controlTitulo"] == "Control Veterinario Trimestral"
    assert completada["etapas"] == []

    refugio = autenticar(client, "refugio@leons.pe", "refugio12345")
    propias = client.get(f"{API}/solicitudes", headers=refugio).json()
    assert propias["total"] == 1
    assert propias["items"][0]["fichaId"] == 1

    admin = autenticar(client, "admin@leons.pe", "admin12345")
    todas = client.get(f"{API}/solicitudes", headers=admin).json()
    assert todas["total"] == 3

    ajeno = client.get(f"{API}/solicitudes/2", headers=refugio)
    assert ajeno.status_code == 403


# 11 ------------------------------------------------------------------------
def test_crear_solicitud_duplicados_y_no_disponible(client: TestClient) -> None:
    headers = autenticar(client)

    creada = client.post(f"{API}/solicitudes", json={"mascotaId": 4}, headers=headers)
    assert creada.status_code == 201, creada.text
    solicitud = creada.json()
    assert solicitud["fichaId"] == 4
    assert solicitud["estado"] == "active"
    assert solicitud["paso"] == 2
    assert solicitud["exp"].endswith("-004")
    assert solicitud["tiempoRespuesta"] == "24 a 48 horas"

    # A-12: el contrato sigue aceptando los campos del formulario sin cambiar
    # las claves del JSON; `telefono` se ignora (no se persiste) y `mensaje`
    # se guarda como mensaje de adopción.
    con_datos = client.post(
        f"{API}/solicitudes",
        json={
            "mascotaId": 4,
            "mensaje": "Vivo en El Tambo y tengo un patio seguro.",
            "telefono": "987654321",
        },
        headers=headers,
    )
    assert con_datos.status_code == 409
    assert con_datos.json()["code"] == "SOLICITUD_DUPLICADA"

    duplicada = client.post(f"{API}/solicitudes", json={"mascotaId": 4}, headers=headers)
    assert duplicada.status_code == 409
    assert duplicada.json()["code"] == "SOLICITUD_DUPLICADA"
    assert duplicada.json()["details"]["solicitudId"] == solicitud["id"]

    # A-17: el permiso de creación pertenece al rol `adoptante` (§9 AGENTS.md).
    for identificador, password in (
        ("refugio@leons.pe", "refugio12345"),
        ("admin@leons.pe", "admin12345"),
    ):
        otro_rol = autenticar(client, identificador, password)
        rechazada = client.post(
            f"{API}/solicitudes", json={"mascotaId": 4}, headers=otro_rol
        )
        assert rechazada.status_code == 403
        assert rechazada.json()["code"] == "FORBIDDEN"

    adoptada = client.post(f"{API}/solicitudes", json={"mascotaId": 13}, headers=headers)
    assert adoptada.status_code == 409
    assert adoptada.json()["code"] == "MASCOTA_NO_DISPONIBLE"

    acogida = client.post(f"{API}/solicitudes", json={"mascotaId": 14}, headers=headers)
    assert acogida.status_code == 409
    assert acogida.json()["code"] == "MASCOTA_NO_DISPONIBLE"

    inexistente = client.post(f"{API}/solicitudes", json={"mascotaId": 999}, headers=headers)
    assert inexistente.status_code == 404

    sin_auth = client.post(f"{API}/solicitudes", json={"mascotaId": 5})
    assert sin_auth.status_code == 401


# 12 ------------------------------------------------------------------------
def test_cancelar_y_documentos_pdf(client: TestClient) -> None:
    headers = autenticar(client)
    creada = client.post(f"{API}/solicitudes", json={"mascotaId": 5}, headers=headers).json()

    cancelada = client.patch(
        f"{API}/solicitudes/{creada['id']}/cancelar",
        json={"motivo": "Cambio de planes familiares"},
        headers=headers,
    )
    assert cancelada.status_code == 200
    assert cancelada.json()["estado"] == "cancelled"
    assert cancelada.json()["motivoCancelacion"] == "Cambio de planes familiares"

    listado = client.get(f"{API}/solicitudes", headers=headers).json()
    assert listado["total"] == 3
    assert all(s["id"] != creada["id"] for s in listado["items"])

    con_canceladas = client.get(
        f"{API}/solicitudes", params={"incluirCanceladas": "true"}, headers=headers
    ).json()
    assert con_canceladas["total"] == 4

    repetida = client.patch(
        f"{API}/solicitudes/{creada['id']}/cancelar",
        json={"motivo": "Otra vez"},
        headers=headers,
    )
    assert repetida.status_code == 409
    assert repetida.json()["code"] == "SOLICITUD_NO_ACTIVA"

    pdf = client.get(f"{API}/solicitudes/{creada['id']}/documentos", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF-1.4")
    assert "constancia" in pdf.headers["content-disposition"]

    assert (
        client.get(f"{API}/solicitudes/999/documentos", headers=headers).status_code == 404
    )


# 13 ------------------------------------------------------------------------
def test_favoritos(client: TestClient) -> None:
    assert client.get(f"{API}/favoritos").status_code == 401

    headers = autenticar(client)
    agregado = client.post(f"{API}/favoritos", json={"mascotaId": 2}, headers=headers)
    assert agregado.status_code == 201
    assert agregado.json()["ids"] == [2]
    assert agregado.json()["mascotas"][0]["nombre"] == "Inti"

    listado = client.get(f"{API}/favoritos", headers=headers).json()
    assert listado["ids"] == [2]
    assert len(listado["mascotas"]) == 1

    duplicado = client.post(f"{API}/favoritos", json={"mascotaId": 2}, headers=headers)
    assert duplicado.status_code == 409
    assert duplicado.json()["code"] == "FAVORITO_DUPLICADO"

    assert client.post(
        f"{API}/favoritos", json={"mascotaId": 999}, headers=headers
    ).status_code == 404

    eliminado = client.delete(f"{API}/favoritos/2", headers=headers)
    assert eliminado.status_code == 204
    assert client.get(f"{API}/favoritos", headers=headers).json()["ids"] == []

    assert client.delete(f"{API}/favoritos/2", headers=headers).status_code == 404

    otro = client.post(
        f"{API}/auth/registro",
        json={
            "nombre": "Otro Usuario",
            "email": "otro@example.com",
            "dni": "70111222",
            "password": "claveSegura1",
        },
    ).json()
    otro_headers = {"Authorization": f"Bearer {otro['token']}"}
    assert client.get(f"{API}/favoritos", headers=otro_headers).json()["ids"] == []


# 14 ------------------------------------------------------------------------
def test_fotos_seguimiento(client: TestClient) -> None:
    headers = autenticar(client)
    creada = client.post(f"{API}/solicitudes", json={"mascotaId": 6}, headers=headers).json()

    archivo = ("seguimiento.png", b"\x89PNG\r\n\x1a\ncontenido-falso", "image/png")
    subida = client.post(
        f"{API}/solicitudes/{creada['id']}/seguimiento",
        files={"archivo": archivo},
        data={"nota": "Primer control mensual"},
        headers=headers,
    )
    assert subida.status_code == 201, subida.text
    fotos = subida.json()["fotosSeguimiento"]
    assert len(fotos) == 1
    assert fotos[0]["src"].startswith("/uploads/")
    assert fotos[0]["alt"] == "Primer control mensual"

    estatico = client.get(fotos[0]["src"])
    assert estatico.status_code == 200
    assert estatico.content.startswith(b"\x89PNG")

    detalle = client.get(f"{API}/solicitudes/{creada['id']}", headers=headers).json()
    assert len(detalle["fotosSeguimiento"]) == 1

    invalido = client.post(
        f"{API}/solicitudes/{creada['id']}/seguimiento",
        files={"archivo": ("nota.txt", b"texto plano", "text/plain")},
        headers=headers,
    )
    assert invalido.status_code == 422
    assert invalido.json()["code"] == "MIME_NO_SOPORTADO"

    inexistente = client.post(
        f"{API}/solicitudes/999/seguimiento",
        files={"archivo": archivo},
        headers=headers,
    )
    assert inexistente.status_code == 404

    sin_auth = client.post(
        f"{API}/solicitudes/{creada['id']}/seguimiento",
        files={"archivo": archivo},
    )
    assert sin_auth.status_code == 401


# 15 ------------------------------------------------------------------------
def test_alertas_rescate(client: TestClient) -> None:
    invalida = client.post(f"{API}/alertas-rescate", json={"nombre": "X", "contacto": "1"})
    assert invalida.status_code == 422

    for indice in range(5):
        respuesta = client.post(
            f"{API}/alertas-rescate",
            json={
                "nombre": f"Vecino {indice}",
                "contacto": f"vecino{indice}@example.com",
                "distrito": "El Tambo",
                "especie": "perro",
                "mensaje": "Perrito herido cerca del parque.",
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["id"] == indice + 1
        assert respuesta.json()["atendida"] is False

    bloqueada = client.post(
        f"{API}/alertas-rescate",
        json={"nombre": "Vecino 6", "contacto": "vecino6@example.com"},
    )
    assert bloqueada.status_code == 429
    assert bloqueada.json()["code"] == "RATE_LIMIT"

    assert client.get(f"{API}/alertas-rescate").status_code == 401

    adoptante = autenticar(client)
    assert client.get(f"{API}/alertas-rescate", headers=adoptante).status_code == 403

    admin = autenticar(client, "admin@leons.pe", "admin12345")
    listado = client.get(f"{API}/alertas-rescate", headers=admin)
    assert listado.status_code == 200
    assert listado.json()["total"] == 5



# 16 ------------------------------------------------------------------------
def test_jwt_secret_debil_rechazado_en_produccion() -> None:
    from app.config import Settings

    try:
        Settings(app_env="production", jwt_secret="dev-secret-change-me-en-produccion-32-bytes")
    except Exception as exc:
        assert ("producción" in str(exc).lower() or "default" in str(exc).lower()
                or "débil" in str(exc).lower() or "32" in str(exc))
    else:
        raise AssertionError("Se esperaba un error de configuración en producción con secreto débil.")

    try:
        Settings(app_env="production", jwt_secret="")
    except Exception:
        pass
    else:
        raise AssertionError("Se esperaba un error con secreto vacío.")

    dev = Settings(app_env="development")
    assert dev.jwt_secret


# 17 ------------------------------------------------------------------------
def test_rate_limit_login(client: TestClient) -> None:
    from app.app import create_app
    from app.config import Settings
    from fastapi.testclient import TestClient as TC

    settings = Settings(
        app_env="test",
        jwt_secret="test-secret-con-mas-de-32-bytes-para-hs256",
        repos_backend="memory",
        rate_limit_auth_max=2,
        rate_limit_auth_window_seconds=60,
    )
    app = create_app(settings)
    with TC(app) as c:
        for _ in range(2):
            c.post("/api/v1/auth/login", json={"identificador": "demo@leons.pe", "password": "mala"})
        respuesta = c.post("/api/v1/auth/login", json={"identificador": "demo@leons.pe", "password": "mala"})
        assert respuesta.status_code == 429
        cuerpo = respuesta.json()
        assert cuerpo["code"] == "RATE_LIMIT"
        assert "message" in cuerpo


# 18 ------------------------------------------------------------------------
def test_rate_limit_registro(client: TestClient) -> None:
    from app.app import create_app
    from app.config import Settings
    from fastapi.testclient import TestClient as TC

    settings = Settings(
        app_env="test",
        jwt_secret="test-secret-con-mas-de-32-bytes-para-hs256",
        repos_backend="memory",
        rate_limit_register_max=1,
        rate_limit_register_window_seconds=60,
    )
    app = create_app(settings)
    with TC(app) as c:
        payload = {
            "nombre": "Rate Test",
            "email": "ratetest@example.com",
            "dni": "79999999",
            "password": "claveSegura1",
        }
        primera = c.post("/api/v1/auth/registro", json=payload)
        assert primera.status_code in (201, 409)
        segunda = c.post("/api/v1/auth/registro", json={**payload, "email": "ratetest2@example.com", "dni": "79999998"})
        assert segunda.status_code == 429
        assert segunda.json()["code"] == "RATE_LIMIT"


# 19 ------------------------------------------------------------------------
def test_usuario_desactivado_no_puede_iniciar_sesion(client: TestClient) -> None:
    repo = client.app.state.container.repo
    usuario = repo.buscar_usuario_por_email("demo@leons.pe")
    assert usuario is not None
    usuario.activo = False

    respuesta = client.post(
        f"{API}/auth/login",
        json={"identificador": "demo@leons.pe", "password": "demo12345"},
    )
    assert respuesta.status_code == 401

    usuario.activo = True


# 20 ------------------------------------------------------------------------
def test_token_de_usuario_desactivado_es_rechazado(client: TestClient) -> None:
    login = client.post(
        f"{API}/auth/login",
        json={"identificador": "demo@leons.pe", "password": "demo12345"},
    )
    assert login.status_code == 200
    token = login.json()["token"]

    repo = client.app.state.container.repo
    usuario = repo.buscar_usuario_por_email("demo@leons.pe")
    assert usuario is not None
    usuario.activo = False

    perfil = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert perfil.status_code == 401

    usuario.activo = True


# 21 ------------------------------------------------------------------------
def test_resumen_impacto_memoria(client: TestClient) -> None:
    repo = client.app.state.container.repo
    resumen = repo.resumen_impacto()
    disponibles = [m for m in repo.listar_mascotas() if m.estado == "disponible"]
    refugios = repo.listar_refugios()
    por_distrito: dict[str, int] = {}
    for r in refugios:
        por_distrito[r.distrito] = por_distrito.get(r.distrito, 0) + r.adoptadas

    assert resumen["total_mascotas"] == len(disponibles)
    assert resumen["total_perros"] == sum(1 for m in disponibles if m.especie == "perro")
    assert resumen["total_gatos"] == sum(1 for m in disponibles if m.especie == "gato")
    assert resumen["total_refugios"] == len(refugios)
    assert resumen["total_adoptadas"] == sum(r.adoptadas for r in refugios)
    assert resumen["total_en_acogida"] == sum(r.en_acogida for r in refugios)
    assert resumen["total_distritos"] == len({r.distrito for r in refugios})
    assert resumen["adoptadas_por_distrito"] == dict(sorted(por_distrito.items()))

    # El endpoint debe consumir el mismo resumen.
    impacto = client.get(f"{API}/estadisticas/impacto")
    assert impacto.status_code == 200
    cuerpo = impacto.json()
    assert cuerpo["totalMascotas"] == resumen["total_mascotas"]
    assert cuerpo["totalRefugios"] == resumen["total_refugios"]
    assert cuerpo["adoptadasPorDistrito"] == resumen["adoptadas_por_distrito"]


def test_contadores_y_galerias_con_significados_distintos(client: TestClient) -> None:
    """INC-002 e INC-004: registros actuales ≠ contadores reportados."""
    stats = client.get(f"{API}/mascotas/stats").json()
    impacto = client.get(f"{API}/estadisticas/impacto").json()
    refugios = client.get(f"{API}/refugios").json()

    # A) Registros actuales de la plataforma (cuentalos sobre `mascotas`).
    assert stats["totalRegistradas"] == 16
    assert stats["disponibles"] == 12
    assert stats["adoptadas"] == 2
    assert stats["enAcogida"] == 2
    assert impacto["totalMascotas"] == 12

    # B/C) Contadores acumulados reportados por los refugios (D-036 / §4.1).
    assert sum(r["adoptadas"] for r in refugios) == impacto["totalAdoptadas"] == 702
    assert sum(r["enAcogida"] for r in refugios) == impacto["totalEnAcogida"] == 96
    assert impacto["totalAdoptadas"] != stats["adoptadas"]
    assert impacto["totalEnAcogida"] != stats["enAcogida"]

    # INC-004: solo Chaska tiene fotos secundarias; el resto usa la principal.
    mascotas = client.get(f"{API}/mascotas", params={"limit": 50}).json()["items"]
    assert len(mascotas) == 16
    assert sum(len(m["galeria"]) for m in mascotas) == 20
    chaska = next(m for m in mascotas if m["id"] == 1)
    assert len(chaska["galeria"]) == 5
    for mascota in mascotas:
        if mascota["id"] != 1:
            assert len(mascota["galeria"]) == 1
            assert mascota["galeria"][0] == {
                "src": mascota["foto"],
                "alt": mascota["alt"],
            }


# 23 ------------------------------------------------------------------------
def test_catalogo_filtros_combinados_y_paginacion(client: TestClient) -> None:
    """P1: filtros, orden y paginación del catálogo conservan sus resultados."""

    def pagina(**params: object) -> dict:
        respuesta = client.get(f"{API}/mascotas", params=params)
        assert respuesta.status_code == 200, respuesta.text
        return respuesta.json()

    combinado = pagina(especie="perro", estado="disponible", limit=50)
    assert combinado["total"] == len(combinado["items"]) == 7
    assert all(
        m["especie"] == "perro" and m["estado"] == "disponible"
        for m in combinado["items"]
    )

    por_refugio = pagina(refugioId="huellitas-wanka", limit=50)
    assert por_refugio["total"] == 2
    assert all(m["refugioId"] == "huellitas-wanka" for m in por_refugio["items"])

    # La búsqueda mira nombre, raza, etiqueta y lugar.
    assert pagina(q="wanka")["total"] >= 1
    assert pagina(q="mestiza")["total"] >= 1
    assert pagina(q="no-existe-esta-mascota")["total"] == 0

    # Ordenamientos vigentes.
    oldest = [m["edadAnios"] for m in pagina(orden="oldest", limit=50)["items"]]
    assert oldest == sorted(oldest, reverse=True)
    youngest = [m["edadAnios"] for m in pagina(orden="youngest", limit=50)["items"]]
    assert youngest == sorted(youngest)
    recientes = [m["id"] for m in pagina(limit=50)["items"]]
    assert recientes == sorted(recientes, reverse=True)
    urgentes = [m["urgente"] for m in pagina(orden="urgent", limit=50)["items"]]
    assert urgentes == sorted(urgentes, reverse=True)

    # Paginación: sin solapes y cubre todo el catálogo.
    ids: list[int] = []
    for numero in (1, 2, 3, 4):
        ids.extend(m["id"] for m in pagina(page=numero, limit=5)["items"])
    assert len(ids) == len(set(ids)) == 16

    fuera_de_rango = pagina(page=99, limit=5)
    assert fuera_de_rango["items"] == []
    assert fuera_de_rango["total"] == 16


# 24 ------------------------------------------------------------------------
def test_solicitudes_visibilidad_filtros_y_paginacion(client: TestClient) -> None:
    """P6: la visibilidad por rol, el estado y la paginación no cambiaron."""
    adoptante = autenticar(client)
    refugio = autenticar(client, "refugio@leons.pe", "refugio12345")
    admin = autenticar(client, "admin@leons.pe", "admin12345")

    todas = client.get(f"{API}/solicitudes", params={"limit": 50}, headers=adoptante)
    assert todas.status_code == 200
    assert todas.json()["total"] == 3

    activas = client.get(
        f"{API}/solicitudes", params={"estado": "activa", "limit": 50}, headers=adoptante
    ).json()
    assert all(s["estado"] == "active" for s in activas["items"])
    completadas = client.get(
        f"{API}/solicitudes",
        params={"estado": "completada", "limit": 50},
        headers=adoptante,
    ).json()
    assert all(s["estado"] == "completed" for s in completadas["items"])

    # El refugio solo ve las solicitudes de sus mascotas; el admin, todas.
    propias = client.get(
        f"{API}/solicitudes", params={"limit": 50}, headers=refugio
    ).json()
    assert propias["total"] == 1
    assert {s["fichaId"] for s in propias["items"]} == {1}
    todas_admin = client.get(
        f"{API}/solicitudes", params={"limit": 50}, headers=admin
    ).json()
    assert todas_admin["total"] == 3

    # Paginación: dos páginas sin solapes que suman el total.
    primera = client.get(
        f"{API}/solicitudes", params={"page": 1, "limit": 2}, headers=adoptante
    ).json()
    segunda = client.get(
        f"{API}/solicitudes", params={"page": 2, "limit": 2}, headers=adoptante
    ).json()
    ids = [s["id"] for s in primera["items"]] + [s["id"] for s in segunda["items"]]
    assert primera["total"] == 3
    assert primera["totalPages"] == 2
    assert len(ids) == len(set(ids)) == 3


# 25 ------------------------------------------------------------------------
def test_a15_paridad_memoria_finalizacion_atomica(client: TestClient) -> None:
    """La rama en memoria respeta permisos, bloqueo por activas e idempotencia."""
    adoptante = autenticar(client)
    refugio = autenticar(client, "refugio@leons.pe", "refugio12345")
    admin = autenticar(client, "admin@leons.pe", "admin12345")

    creada = client.post(f"{API}/solicitudes", json={"mascotaId": 12}, headers=adoptante)
    assert creada.status_code == 201, creada.text
    solicitud_id = creada.json()["id"]
    ruta = f"{API}/solicitudes/{solicitud_id}/etapa"

    sin_permiso = client.patch(
        ruta, json={"etapa": 5, "nota": "No autorizado"}, headers=adoptante
    )
    assert sin_permiso.status_code == 403
    assert sin_permiso.json()["code"] == "FORBIDDEN"

    sufijo = uuid.uuid4().hex[:8]
    registro = client.post(
        f"{API}/auth/registro",
        json={
            "nombre": "Otro Adoptante A15",
            "email": f"a15-{sufijo}@example.com",
            "dni": str(uuid.uuid4().int % 90_000_000 + 10_000_000),
            "password": "claveSegura1",
        },
    )
    assert registro.status_code == 201, registro.text
    otro_headers = {"Authorization": f"Bearer {registro.json()['token']}"}
    otra = client.post(f"{API}/solicitudes", json={"mascotaId": 12}, headers=otro_headers)
    assert otra.status_code == 201, otra.text

    bloqueada = client.patch(
        ruta, json={"etapa": 5, "nota": "Debe esperar"}, headers=refugio
    )
    assert bloqueada.status_code == 409
    assert bloqueada.json()["code"] == "ADOPCION_EN_CURSO"

    # Mecanismo autorizado existente: el admin resuelve la otra postulación.
    resuelta = client.patch(
        f"{API}/solicitudes/{otra.json()['id']}/cancelar",
        json={"motivo": "Resuelta por el refugio"},
        headers=admin,
    )
    assert resuelta.status_code == 200

    nota = f"Nota final única {sufijo}"
    finalizada = client.patch(ruta, json={"etapa": 5, "nota": nota}, headers=refugio)
    assert finalizada.status_code == 200, finalizada.text
    cuerpo = finalizada.json()
    assert cuerpo["estado"] == "completed"
    assert cuerpo["etapas"] == []
    assert cuerpo["mensaje"]["texto"] == nota
    assert cuerpo["mensaje"]["nombre"] == "Silvia Mallqui"
    assert cuerpo["mensaje"]["rol"] == "Coordinación del refugio"

    mascota = client.get(f"{API}/mascotas/12").json()
    assert mascota["estado"] == "adoptada"

    repeticion = client.patch(
        ruta, json={"etapa": 5, "nota": f"{nota}-distinta"}, headers=refugio
    )
    assert repeticion.status_code == 200
    repetido = repeticion.json()
    assert repetido["estado"] == "completed"
    assert repetido["mensaje"]["texto"] == nota
    assert repetido["etapas"] == []

    sin_permiso_despues = client.patch(
        ruta, json={"etapa": 5, "nota": "Sigue sin permiso"}, headers=adoptante
    )
    assert sin_permiso_despues.status_code == 403


# 26 ------------------------------------------------------------------------
def test_a14_paridad_memoria_autoria_real(client: TestClient) -> None:
    """El repositorio en memoria conserva al autor autenticado de cada mensaje."""
    adoptante = autenticar(client)
    refugio = autenticar(client, "refugio@leons.pe", "refugio12345")
    admin = autenticar(client, "admin@leons.pe", "admin12345")
    sufijo = uuid.uuid4().hex[:8]

    creada = client.post(
        f"{API}/solicitudes",
        json={"mascotaId": 12, "mensaje": f"Postulación {sufijo}"},
        headers=adoptante,
    )
    assert creada.status_code == 201, creada.text
    solicitud_id = creada.json()["id"]
    mensaje = creada.json()["mensaje"]
    assert mensaje["nombre"] == "Valeria Quispe"
    assert mensaje["rol"] == "Adoptante"

    por_refugio = client.post(
        f"{API}/solicitudes/{solicitud_id}/mensajes",
        json={"texto": f"Refugio {sufijo}"},
        headers=refugio,
    )
    assert por_refugio.status_code == 200
    mensaje = por_refugio.json()["mensaje"]
    assert mensaje["nombre"] == "Silvia Mallqui"
    assert mensaje["rol"] == "Coordinación del refugio"

    por_admin = client.post(
        f"{API}/solicitudes/{solicitud_id}/mensajes",
        json={"texto": f"Admin {sufijo}"},
        headers=admin,
    )
    assert por_admin.status_code == 200
    mensaje = por_admin.json()["mensaje"]
    assert mensaje["nombre"] == "Administrador LeonS"
    assert mensaje["rol"] == "Coordinación del refugio"

    registro = client.post(
        f"{API}/auth/registro",
        json={
            "nombre": "Sin Permiso A14",
            "email": f"a14-{sufijo}@example.com",
            "dni": str(uuid.uuid4().int % 90_000_000 + 10_000_000),
            "password": "claveSegura1",
        },
    )
    assert registro.status_code == 201, registro.text
    otro = {"Authorization": f"Bearer {registro.json()['token']}"}
    rechazado = client.post(
        f"{API}/solicitudes/{solicitud_id}/mensajes",
        json={"texto": "No debería guardarse"},
        headers=otro,
    )
    assert rechazado.status_code == 403
    assert rechazado.json()["code"] == "FORBIDDEN"


# 27 ------------------------------------------------------------------------
def test_a16_contrato_publico_de_fecha_no_cambia(client: TestClient) -> None:
    """A-16 conserva `fecha` como texto con los mismos límites del contrato."""
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    esquema = openapi.json()["components"]["schemas"]["AgendarCitaRequest"]
    fecha = esquema["properties"]["fecha"]
    assert fecha["type"] == "string"
    assert fecha["minLength"] == 4
    assert fecha["maxLength"] == 120
    assert "fecha" in esquema["required"]
