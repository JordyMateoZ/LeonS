from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import token_demo


def test_health(client: TestClient) -> None:
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["ok"] is True


def test_mascotas_paginacion_y_estado(client: TestClient) -> None:
    respuesta = client.get("/api/v1/mascotas?limit=5&page=2")
    assert respuesta.status_code == 200
    assert len(respuesta.json()["data"]) == 5
    assert respuesta.json()["meta"]["total"] == 12
    assert all(m["estado"] == "disponible" for m in respuesta.json()["data"])
    assert respuesta.json()["data"][0]["badgeClase"]


def test_mascotas_filtros(client: TestClient) -> None:
    gatos = client.get("/api/v1/mascotas?especie=gato&todos=true")
    assert gatos.status_code == 200
    assert len(gatos.json()["data"]) > 0
    assert all(m["especie"] == "gato" for m in gatos.json()["data"])

    todos = client.get("/api/v1/mascotas?todos=true&limit=100")
    assert todos.json()["meta"]["total"] == 16


def test_stats_detalle_y_similares(client: TestClient) -> None:
    stats = client.get("/api/v1/mascotas/stats")
    assert stats.json()["data"]["total"] == 16
    assert stats.json()["data"]["disponibles"] == 12

    detalle = client.get("/api/v1/mascotas/1/detalle")
    assert detalle.status_code == 200
    assert detalle.json()["data"]["fichaId"] == "LS-HYO-0482"
    assert len(detalle.json()["data"]["historia"]) == 3

    similares = client.get("/api/v1/mascotas/1/similares")
    assert similares.status_code == 200
    assert len(similares.json()["data"]) > 0
    assert all(m["id"] != 1 for m in similares.json()["data"])


def test_refugios(client: TestClient) -> None:
    respuesta = client.get("/api/v1/refugios")
    assert respuesta.status_code == 200
    assert len(respuesta.json()["data"]) == 9
    assert respuesta.json()["data"][0]["resumen"]["total"] > 0


def test_contenido_e_impacto(client: TestClient) -> None:
    contenido = client.get("/api/v1/contenido")
    assert len(contenido.json()["data"]["faqs"]) == 6
    assert len(contenido.json()["data"]["pasosAdopcion"]) == 4

    impacto = client.get("/api/v1/estadisticas/impacto")
    assert impacto.json()["data"]["kpis"] == {
        "adoptadas": 702,
        "refugios": 9,
        "enAcogida": 96,
        "distritos": 6,
        "mascotasEnCatalogo": 16,
        "solicitudesActivas": 2,
    }


def test_registro_y_perfil(client: TestClient) -> None:
    registro = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Rosa",
            "apellido": "Pérez",
            "email": "rosa@example.com",
            "dni": "12345678",
            "password": "claveSegura123",
            "terminos": True,
            "distrito": "Chilca",
        },
    )
    assert registro.status_code == 201, registro.text
    token = registro.json()["data"]["token"]

    perfil = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert perfil.status_code == 200
    assert perfil.json()["data"]["email"] == "rosa@example.com"
    assert "passwordHash" not in perfil.json()["data"]


def test_registro_rechaza_datos_invalidos(client: TestClient) -> None:
    respuesta = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Ana",
            "email": "ana@example.com",
            "dni": "87654321",
            "password": "123",
            "terminos": False,
        },
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "BAD_REQUEST"


def test_login_por_correo_y_dni(client: TestClient) -> None:
    assert token_demo(client)
    por_dni = client.post(
        "/api/v1/auth/login",
        json={"identificador": "00000001", "password": "demo1234"},
    )
    assert por_dni.status_code == 200


def test_listar_solicitudes_demo(client: TestClient) -> None:
    token = token_demo(client)
    respuesta = client.get(
        "/api/v1/solicitudes", headers={"Authorization": f"Bearer {token}"}
    )
    assert respuesta.status_code == 200
    assert len(respuesta.json()["data"]) == 3
    assert len(respuesta.json()["data"][0]["etapas"]) > 0


NUEVA_SOLICITUD = {
    "mascotaId": 4,
    "solicitante": {
        "nombre": "Carlos Quispe",
        "telefono": "51999111222",
        "distrito": "El Tambo",
        "vivienda": "Casa con cerco perimétrico y jardín",
        "aceptaCompromiso": True,
        "dni": "11223344",
    },
}


def test_crear_solicitud_duplicados_y_no_disponible(client: TestClient) -> None:
    token = token_demo(client)
    headers = {"Authorization": f"Bearer {token}"}

    creada = client.post("/api/v1/solicitudes", json=NUEVA_SOLICITUD, headers=headers)
    assert creada.status_code == 201, creada.text
    assert creada.json()["data"]["estado"] == "active"
    assert creada.json()["data"]["paso"] == 2
    assert creada.json()["data"]["exp"].startswith("#SOL-HYO-")
    assert creada.json()["data"]["exp"].endswith("-004")

    duplicada = client.post("/api/v1/solicitudes", json=NUEVA_SOLICITUD, headers=headers)
    assert duplicada.status_code == 409
    assert duplicada.json()["error"]["code"] == "CONFLICT"

    no_disponible = client.post(
        "/api/v1/solicitudes",
        json={**NUEVA_SOLICITUD, "mascotaId": 13},
        headers=headers,
    )
    assert no_disponible.status_code == 409


def test_cancelar_y_documentos_pdf(client: TestClient) -> None:
    token = token_demo(client)
    headers = {"Authorization": f"Bearer {token}"}

    cancelada = client.post(
        "/api/v1/solicitudes/2/cancelar",
        json={"motivo": "Ya no puedo coordinar la visita"},
        headers=headers,
    )
    assert cancelada.status_code == 200
    assert cancelada.json()["data"]["estado"] == "cancelled"
    assert cancelada.json()["data"]["motivoCancelacion"]

    carnet = client.get(
        "/api/v1/solicitudes/1/documentos/carnet", headers=headers
    )
    assert carnet.status_code == 200
    assert "application/pdf" in carnet.headers["content-type"]
    assert carnet.content.startswith(b"%PDF")


def test_fotos_seguimiento(client: TestClient) -> None:
    token = token_demo(client)
    headers = {"Authorization": f"Bearer {token}"}

    respuesta = client.post(
        "/api/v1/solicitudes/1/seguimiento/fotos",
        headers=headers,
        files={"fotos": ("adaptacion.png", b"contenido-imagen", "image/png")},
    )
    assert respuesta.status_code == 201, respuesta.text
    assert len(respuesta.json()["data"]) == 1

    listado = client.get("/api/v1/solicitudes/1/seguimiento", headers=headers)
    assert len(listado.json()["data"]) == 1


def test_favoritos(client: TestClient) -> None:
    token = token_demo(client)
    headers = {"Authorization": f"Bearer {token}"}

    agregado = client.post(
        "/api/v1/favoritos", json={"mascotaId": 7}, headers=headers
    )
    assert agregado.status_code == 201

    duplicado = client.post(
        "/api/v1/favoritos", json={"mascotaId": 7}, headers=headers
    )
    assert duplicado.status_code == 409

    listado = client.get("/api/v1/favoritos", headers=headers)
    assert len(listado.json()["data"]) == 1
    assert listado.json()["data"][0]["id"] == 7

    eliminado = client.delete("/api/v1/favoritos/7", headers=headers)
    assert eliminado.status_code == 204


def test_alertas_rescate(client: TestClient) -> None:
    alerta = {
        "nombre": "María Torres",
        "email": "maria@example.com",
        "telefono": "51999888777",
        "distrito": "Chilca",
        "direccion": "Jr. Los Pinos 123",
        "descripcion": "Encontré tres cachorros abandonados cerca de la cancha.",
        "especie": "perro",
        "cantidad": 3,
        "urgente": True,
    }
    creada = client.post("/api/v1/alertas-rescate", json=alerta)
    assert creada.status_code == 201, creada.text
    assert creada.json()["data"]["atendida"] is False

    sin_auth = client.get("/api/v1/alertas-rescate")
    assert sin_auth.status_code == 401

    admin = token_demo(client, "admin@leons.pe", "admin1234")
    listado = client.get(
        "/api/v1/alertas-rescate", headers={"Authorization": f"Bearer {admin}"}
    )
    assert listado.status_code == 200
    assert len(listado.json()["data"]) == 1
