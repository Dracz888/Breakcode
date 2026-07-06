"""Pruebas del mapa de batalla: pintar, colocar fichas y las reglas de paso."""

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
def entorno(cliente):
    """Un sistema con dos fichas y un mapa de 8x6, listo para jugar."""
    sistema = cliente.post("/sistemas", json={"nombre": "Prueba"}).json()["id"]
    heroe = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "Kaelith", "atributos": {}}
    ).json()["id"]
    ogro = cliente.post(
        f"/sistemas/{sistema}/personajes",
        json={"nombre": "Ogro", "es_monstruo": True, "atributos": {}},
    ).json()["id"]
    mapa = cliente.post(
        f"/sistemas/{sistema}/mapas", json={"nombre": "Claro del bosque", "ancho": 8, "alto": 6}
    ).json()["id"]
    return {"sistema": sistema, "heroe": heroe, "ogro": ogro, "mapa": mapa}


def test_mapa_nace_lleno_de_pasto(cliente, entorno):
    mapa = cliente.get(f"/mapas/{entorno['mapa']}").json()
    assert mapa["ancho"] == 8 and mapa["alto"] == 6
    assert len(mapa["celdas"]) == 6 and len(mapa["celdas"][0]) == 8
    assert all(celda == "pasto" for fila in mapa["celdas"] for celda in fila)
    assert mapa["tokens"] == []


def test_pintar_celdas(cliente, entorno):
    r = cliente.put(
        f"/mapas/{entorno['mapa']}/celdas",
        json={"cambios": [
            {"x": 0, "y": 0, "terreno": "agua"},
            {"x": 1, "y": 0, "terreno": "muro"},
            {"x": 2, "y": 3, "terreno": "camino"},
        ]},
    )
    assert r.status_code == 200
    celdas = r.json()["celdas"]
    assert celdas[0][0] == "agua" and celdas[0][1] == "muro" and celdas[3][2] == "camino"


def test_pintar_terreno_inexistente_se_rechaza(cliente, entorno):
    r = cliente.put(
        f"/mapas/{entorno['mapa']}/celdas",
        json={"cambios": [{"x": 0, "y": 0, "terreno": "lava"}]},
    )
    assert r.status_code == 422
    assert "'lava' no existe" in r.json()["detail"]


def test_colocar_y_mover_ficha(cliente, entorno):
    r = cliente.post(
        f"/mapas/{entorno['mapa']}/tokens",
        json={"personaje_id": entorno["heroe"], "x": 2, "y": 2},
    )
    assert r.status_code == 201
    token = r.json()
    assert token["nombre"] == "Kaelith" and token["es_monstruo"] is False

    r = cliente.put(f"/tokens/{token['id']}", json={"x": 5, "y": 3})
    assert r.status_code == 200
    assert (r.json()["x"], r.json()["y"]) == (5, 3)


def test_no_se_puede_pisar_terreno_que_bloquea(cliente, entorno):
    cliente.put(
        f"/mapas/{entorno['mapa']}/celdas",
        json={"cambios": [{"x": 4, "y": 4, "terreno": "muro"}]},
    )
    r = cliente.post(
        f"/mapas/{entorno['mapa']}/tokens",
        json={"personaje_id": entorno["heroe"], "x": 4, "y": 4},
    )
    assert r.status_code == 422
    assert "muro" in r.json()["detail"].lower()


def test_no_se_puede_salir_del_mapa(cliente, entorno):
    r = cliente.post(
        f"/mapas/{entorno['mapa']}/tokens",
        json={"personaje_id": entorno["heroe"], "x": 99, "y": 0},
    )
    assert r.status_code == 422
    assert "fuera del mapa" in r.json()["detail"]


def test_celda_ocupada_avisa_quien_esta(cliente, entorno):
    cliente.post(
        f"/mapas/{entorno['mapa']}/tokens",
        json={"personaje_id": entorno["heroe"], "x": 1, "y": 1},
    )
    r = cliente.post(
        f"/mapas/{entorno['mapa']}/tokens",
        json={"personaje_id": entorno["ogro"], "x": 1, "y": 1},
    )
    assert r.status_code == 422
    assert "Kaelith" in r.json()["detail"]


def test_una_ficha_no_puede_estar_dos_veces(cliente, entorno):
    cliente.post(
        f"/mapas/{entorno['mapa']}/tokens",
        json={"personaje_id": entorno["heroe"], "x": 1, "y": 1},
    )
    r = cliente.post(
        f"/mapas/{entorno['mapa']}/tokens",
        json={"personaje_id": entorno["heroe"], "x": 2, "y": 2},
    )
    assert r.status_code == 409
    assert "ya está en este mapa" in r.json()["detail"]


def test_quitar_token(cliente, entorno):
    token = cliente.post(
        f"/mapas/{entorno['mapa']}/tokens",
        json={"personaje_id": entorno["ogro"], "x": 0, "y": 0},
    ).json()
    assert cliente.delete(f"/tokens/{token['id']}").status_code == 204
    assert cliente.get(f"/mapas/{entorno['mapa']}").json()["tokens"] == []


def test_borrar_personaje_quita_su_token(cliente, entorno):
    cliente.post(
        f"/mapas/{entorno['mapa']}/tokens",
        json={"personaje_id": entorno["heroe"], "x": 1, "y": 1},
    )
    assert cliente.delete(f"/personajes/{entorno['heroe']}").status_code == 204
    assert cliente.get(f"/mapas/{entorno['mapa']}").json()["tokens"] == []


def test_ficha_de_otro_sistema_se_rechaza(cliente, entorno):
    otro = cliente.post("/sistemas", json={"nombre": "Otro mundo"}).json()["id"]
    forastero = cliente.post(
        f"/sistemas/{otro}/personajes", json={"nombre": "Forastero", "atributos": {}}
    ).json()["id"]
    r = cliente.post(
        f"/mapas/{entorno['mapa']}/tokens", json={"personaje_id": forastero, "x": 0, "y": 0}
    )
    assert r.status_code == 422
    assert "otro sistema" in r.json()["detail"]


def test_catalogo_de_terrenos(cliente):
    terrenos = cliente.get("/terrenos").json()
    assert "pasto" in terrenos and terrenos["muro"]["bloquea"] is True
