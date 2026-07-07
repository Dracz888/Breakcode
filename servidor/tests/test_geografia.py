"""Pruebas del mapa geográfico: crear el mundo y colocar marcadores."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, obtener_db
from app.main import app


@pytest.fixture()
def cliente():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Sesion = sessionmaker(bind=engine)

    def db_de_prueba():
        db = Sesion()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[obtener_db] = db_de_prueba
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def sistema(cliente):
    return cliente.post("/sistemas", json={"nombre": "Reino Roto"}).json()["id"]


def test_crear_mundo_y_listarlo(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/mapas-geograficos", json={"nombre": "Aletheia"}
    )
    assert r.status_code == 201
    assert r.json()["nombre"] == "Aletheia"

    lista = cliente.get(f"/sistemas/{sistema}/mapas-geograficos").json()
    assert len(lista) == 1 and lista[0]["nombre"] == "Aletheia"


def test_colocar_marcadores(cliente, sistema):
    mundo = cliente.post(
        f"/sistemas/{sistema}/mapas-geograficos", json={"nombre": "Aletheia"}
    ).json()["id"]

    r = cliente.post(
        f"/mapas-geograficos/{mundo}/marcadores",
        json={"nombre": "Puerto Gris", "tipo": "ciudad", "x": 0.3, "y": 0.4},
    )
    assert r.status_code == 201
    assert r.json()["tipo"] == "ciudad"

    cliente.post(
        f"/mapas-geograficos/{mundo}/marcadores",
        json={"nombre": "Cripta del Eco", "tipo": "mazmorra", "x": 0.7, "y": 0.6},
    )
    detalle = cliente.get(f"/mapas-geograficos/{mundo}").json()
    assert len(detalle["marcadores"]) == 2
    nombres = {m["nombre"] for m in detalle["marcadores"]}
    assert nombres == {"Puerto Gris", "Cripta del Eco"}


def test_tipo_de_marcador_invalido_se_rechaza(cliente, sistema):
    mundo = cliente.post(
        f"/sistemas/{sistema}/mapas-geograficos", json={"nombre": "Aletheia"}
    ).json()["id"]
    r = cliente.post(
        f"/mapas-geograficos/{mundo}/marcadores",
        json={"nombre": "Volcán", "tipo": "volcan", "x": 0.5, "y": 0.5},
    )
    assert r.status_code == 422
    assert "'volcan' no existe" in r.json()["detail"]


def test_coordenadas_fuera_de_rango_se_rechazan(cliente, sistema):
    mundo = cliente.post(
        f"/sistemas/{sistema}/mapas-geograficos", json={"nombre": "Aletheia"}
    ).json()["id"]
    r = cliente.post(
        f"/mapas-geograficos/{mundo}/marcadores",
        json={"nombre": "Fuera", "tipo": "punto", "x": 1.5, "y": 0.5},
    )
    assert r.status_code == 422


def test_mover_y_editar_marcador(cliente, sistema):
    mundo = cliente.post(
        f"/sistemas/{sistema}/mapas-geograficos", json={"nombre": "Aletheia"}
    ).json()["id"]
    marcador = cliente.post(
        f"/mapas-geograficos/{mundo}/marcadores",
        json={"nombre": "Aldea", "tipo": "pueblo", "x": 0.1, "y": 0.1},
    ).json()["id"]

    r = cliente.put(
        f"/marcadores/{marcador}",
        json={"x": 0.8, "y": 0.9, "tipo": "ciudad", "nombre": "Gran Ciudad"},
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["x"] == 0.8 and cuerpo["tipo"] == "ciudad" and cuerpo["nombre"] == "Gran Ciudad"


def test_borrar_marcador(cliente, sistema):
    mundo = cliente.post(
        f"/sistemas/{sistema}/mapas-geograficos", json={"nombre": "Aletheia"}
    ).json()["id"]
    marcador = cliente.post(
        f"/mapas-geograficos/{mundo}/marcadores",
        json={"nombre": "Aldea", "tipo": "pueblo", "x": 0.1, "y": 0.1},
    ).json()["id"]
    assert cliente.delete(f"/marcadores/{marcador}").status_code == 204
    assert cliente.get(f"/mapas-geograficos/{mundo}").json()["marcadores"] == []


def test_borrar_mundo_borra_sus_marcadores(cliente, sistema):
    mundo = cliente.post(
        f"/sistemas/{sistema}/mapas-geograficos", json={"nombre": "Aletheia"}
    ).json()["id"]
    cliente.post(
        f"/mapas-geograficos/{mundo}/marcadores",
        json={"nombre": "Aldea", "tipo": "pueblo", "x": 0.1, "y": 0.1},
    )
    assert cliente.delete(f"/mapas-geograficos/{mundo}").status_code == 204
    assert cliente.get(f"/mapas-geograficos/{mundo}").status_code == 404


def test_catalogo_de_tipos(cliente):
    tipos = cliente.get("/tipos-marcador").json()
    assert "ciudad" in tipos and "mazmorra" in tipos
    assert tipos["ciudad"]["simbolo"]


def test_borrar_sistema_borra_su_mundo(cliente, sistema):
    mundo = cliente.post(
        f"/sistemas/{sistema}/mapas-geograficos", json={"nombre": "Aletheia"}
    ).json()["id"]
    assert cliente.delete(f"/sistemas/{sistema}").status_code == 204
    assert cliente.get(f"/mapas-geograficos/{mundo}").status_code == 404
