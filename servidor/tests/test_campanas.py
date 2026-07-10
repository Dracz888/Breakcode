"""Pruebas de campañas: campaña → arcos → eventos y su línea de tiempo."""

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
    """Un sistema con dos fichas, un mundo con un marcador y una campaña."""
    sistema = cliente.post("/sistemas", json={"nombre": "Reino Roto"}).json()["id"]
    heroe = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "Kaelith", "atributos": {}}
    ).json()["id"]
    aliada = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "Mira", "atributos": {}}
    ).json()["id"]
    mundo = cliente.post(
        f"/sistemas/{sistema}/mapas-geograficos", json={"nombre": "Aletheia"}
    ).json()["id"]
    lugar = cliente.post(
        f"/mapas-geograficos/{mundo}/marcadores",
        json={"nombre": "Puerto Gris", "tipo": "ciudad", "x": 0.3, "y": 0.4},
    ).json()["id"]
    campana = cliente.post(
        f"/sistemas/{sistema}/campanas", json={"nombre": "La caída del faro"}
    ).json()["id"]
    return {
        "sistema": sistema,
        "heroe": heroe,
        "aliada": aliada,
        "mundo": mundo,
        "lugar": lugar,
        "campana": campana,
    }


def test_campana_nace_vacia(cliente, entorno):
    detalle = cliente.get(f"/campanas/{entorno['campana']}").json()
    assert detalle["nombre"] == "La caída del faro"
    assert detalle["arcos"] == []


def test_arcos_conservan_su_orden(cliente, entorno):
    campana = entorno["campana"]
    cliente.post(f"/campanas/{campana}/arcos", json={"titulo": "Primer arco"})
    cliente.post(f"/campanas/{campana}/arcos", json={"titulo": "Segundo arco"})
    cliente.post(f"/campanas/{campana}/arcos", json={"titulo": "Tercer arco"})
    arcos = cliente.get(f"/campanas/{campana}").json()["arcos"]
    assert [a["titulo"] for a in arcos] == ["Primer arco", "Segundo arco", "Tercer arco"]
    assert [a["orden"] for a in arcos] == [0, 1, 2]


def test_registrar_evento_con_personajes_y_lugar(cliente, entorno):
    arco = cliente.post(
        f"/campanas/{entorno['campana']}/arcos", json={"titulo": "El zarpazo"}
    ).json()["id"]
    r = cliente.post(
        f"/arcos/{arco}/eventos",
        json={
            "titulo": "Emboscada en el muelle",
            "fecha": "Día 3 del Ocaso",
            "descripcion": "El grupo cae en una trampa.",
            "marcador_id": entorno["lugar"],
            "personajes": [entorno["heroe"], entorno["aliada"]],
        },
    )
    assert r.status_code == 201
    evento = r.json()
    assert evento["fecha"] == "Día 3 del Ocaso"
    assert evento["marcador"]["nombre"] == "Puerto Gris"
    assert {p["nombre"] for p in evento["personajes"]} == {"Kaelith", "Mira"}


def test_linea_de_tiempo_completa(cliente, entorno):
    arco = cliente.post(
        f"/campanas/{entorno['campana']}/arcos", json={"titulo": "El zarpazo"}
    ).json()["id"]
    cliente.post(f"/arcos/{arco}/eventos", json={"titulo": "Uno"})
    cliente.post(f"/arcos/{arco}/eventos", json={"titulo": "Dos"})
    detalle = cliente.get(f"/campanas/{entorno['campana']}").json()
    eventos = detalle["arcos"][0]["eventos"]
    assert [e["titulo"] for e in eventos] == ["Uno", "Dos"]
    assert [e["orden"] for e in eventos] == [0, 1]


def test_evento_con_ficha_de_otro_sistema_se_rechaza(cliente, entorno):
    otro = cliente.post("/sistemas", json={"nombre": "Otro"}).json()["id"]
    forastero = cliente.post(
        f"/sistemas/{otro}/personajes", json={"nombre": "Forastero", "atributos": {}}
    ).json()["id"]
    arco = cliente.post(
        f"/campanas/{entorno['campana']}/arcos", json={"titulo": "Arco"}
    ).json()["id"]
    r = cliente.post(
        f"/arcos/{arco}/eventos",
        json={"titulo": "Cruce", "personajes": [forastero]},
    )
    assert r.status_code == 422
    assert "otro sistema" in r.json()["detail"]


def test_editar_evento_cambia_involucrados(cliente, entorno):
    arco = cliente.post(
        f"/campanas/{entorno['campana']}/arcos", json={"titulo": "Arco"}
    ).json()["id"]
    evento = cliente.post(
        f"/arcos/{arco}/eventos",
        json={"titulo": "Reunión", "personajes": [entorno["heroe"]]},
    ).json()["id"]
    r = cliente.put(
        f"/eventos/{evento}", json={"personajes": [entorno["aliada"]], "fecha": "Más tarde"}
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert [p["nombre"] for p in cuerpo["personajes"]] == ["Mira"]
    assert cuerpo["fecha"] == "Más tarde"


def test_borrar_lugar_no_borra_el_evento(cliente, entorno):
    arco = cliente.post(
        f"/campanas/{entorno['campana']}/arcos", json={"titulo": "Arco"}
    ).json()["id"]
    evento = cliente.post(
        f"/arcos/{arco}/eventos",
        json={"titulo": "Suceso", "marcador_id": entorno["lugar"]},
    ).json()["id"]
    assert cliente.delete(f"/marcadores/{entorno['lugar']}").status_code == 204
    detalle = cliente.get(f"/campanas/{entorno['campana']}").json()
    evento_actual = detalle["arcos"][0]["eventos"][0]
    assert evento_actual["id"] == evento
    assert evento_actual["marcador"] is None


def test_borrar_arco_borra_sus_eventos(cliente, entorno):
    arco = cliente.post(
        f"/campanas/{entorno['campana']}/arcos", json={"titulo": "Arco"}
    ).json()["id"]
    cliente.post(f"/arcos/{arco}/eventos", json={"titulo": "Suceso"})
    assert cliente.delete(f"/arcos/{arco}").status_code == 204
    detalle = cliente.get(f"/campanas/{entorno['campana']}").json()
    assert detalle["arcos"] == []


def test_borrar_ficha_la_quita_de_los_eventos(cliente, entorno):
    arco = cliente.post(
        f"/campanas/{entorno['campana']}/arcos", json={"titulo": "Arco"}
    ).json()["id"]
    evento = cliente.post(
        f"/arcos/{arco}/eventos",
        json={"titulo": "Suceso", "personajes": [entorno["heroe"], entorno["aliada"]]},
    ).json()["id"]
    assert cliente.delete(f"/personajes/{entorno['heroe']}").status_code == 204
    detalle = cliente.get(f"/campanas/{entorno['campana']}").json()
    involucrados = detalle["arcos"][0]["eventos"][0]["personajes"]
    assert [p["nombre"] for p in involucrados] == ["Mira"]


def test_borrar_sistema_borra_sus_campanas(cliente, entorno):
    assert cliente.delete(f"/sistemas/{entorno['sistema']}").status_code == 204
    assert cliente.get(f"/campanas/{entorno['campana']}").status_code == 404
