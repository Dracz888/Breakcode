"""Pruebas de la fase 9 (refinamiento): notas del DJ, niebla de guerra y
exportar/importar sistemas."""

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
def sistema_poblado(cliente):
    """Un sistema con un atributo, una fórmula, una ficha y un mapa."""
    sistema = cliente.post("/sistemas", json={"nombre": "Reino Roto"}).json()["id"]
    cliente.post(
        f"/sistemas/{sistema}/atributos",
        json={"clave": "fuerza", "nombre": "Fuerza", "valor_inicial": 5},
    )
    cliente.post(
        f"/sistemas/{sistema}/estadisticas",
        json={"clave": "vida", "nombre": "Vida", "formula": "fuerza * 10 + nivel * 5"},
    )
    cliente.post(
        f"/sistemas/{sistema}/personajes",
        json={"nombre": "Kaelith", "atributos": {"fuerza": 8}},
    )
    cliente.post(
        f"/sistemas/{sistema}/mapas",
        json={"nombre": "Claro", "ancho": 6, "alto": 5},
    )
    return sistema


# ---------- Notas del DJ ----------

def test_sistema_nace_sin_notas(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()
    assert sistema["notas"] == ""


def test_editar_notas_del_dj(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()["id"]
    r = cliente.put(
        f"/sistemas/{sistema}",
        json={"notas": "El posadero miente sobre el sótano."},
    )
    assert r.status_code == 200
    assert r.json()["notas"] == "El posadero miente sobre el sótano."
    # Persiste al volver a consultarlo
    assert cliente.get(f"/sistemas/{sistema}").json()["notas"].startswith("El posadero")


def test_editar_nombre_no_borra_notas(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()["id"]
    cliente.put(f"/sistemas/{sistema}", json={"notas": "secreto"})
    cliente.put(f"/sistemas/{sistema}", json={"nombre": "Nuevo nombre"})
    detalle = cliente.get(f"/sistemas/{sistema}").json()
    assert detalle["nombre"] == "Nuevo nombre" and detalle["notas"] == "secreto"


# ---------- Niebla de guerra ----------

def test_mapa_nace_sin_niebla(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()["id"]
    mapa = cliente.post(
        f"/sistemas/{sistema}/mapas", json={"nombre": "M", "ancho": 4, "alto": 4}
    ).json()["id"]
    detalle = cliente.get(f"/mapas/{mapa}").json()
    assert len(detalle["niebla"]) == 4 and len(detalle["niebla"][0]) == 4
    assert all(not celda for fila in detalle["niebla"] for celda in fila)


def test_pintar_y_revelar_niebla(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()["id"]
    mapa = cliente.post(
        f"/sistemas/{sistema}/mapas", json={"nombre": "M", "ancho": 4, "alto": 4}
    ).json()["id"]

    r = cliente.put(
        f"/mapas/{mapa}/niebla",
        json={"cambios": [
            {"x": 0, "y": 0, "oculta": True},
            {"x": 3, "y": 2, "oculta": True},
        ]},
    )
    assert r.status_code == 200
    niebla = r.json()["niebla"]
    assert niebla[0][0] is True and niebla[2][3] is True and niebla[1][1] is False

    # Revelar de nuevo la primera celda
    r = cliente.put(
        f"/mapas/{mapa}/niebla", json={"cambios": [{"x": 0, "y": 0, "oculta": False}]}
    )
    assert r.json()["niebla"][0][0] is False


def test_niebla_fuera_del_mapa_se_rechaza(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()["id"]
    mapa = cliente.post(
        f"/sistemas/{sistema}/mapas", json={"nombre": "M", "ancho": 4, "alto": 4}
    ).json()["id"]
    r = cliente.put(
        f"/mapas/{mapa}/niebla", json={"cambios": [{"x": 9, "y": 0, "oculta": True}]}
    )
    assert r.status_code == 422
    assert "fuera del mapa" in r.json()["detail"]


# ---------- Exportar / importar ----------

def test_exportar_trae_todo_el_sistema(cliente, sistema_poblado):
    exp = cliente.get(f"/sistemas/{sistema_poblado}/exportar").json()
    assert exp["formato"] == "breakcode/sistema"
    assert exp["nombre"] == "Reino Roto"
    assert [a["clave"] for a in exp["atributos"]] == ["fuerza"]
    assert [e["clave"] for e in exp["estadisticas"]] == ["vida"]
    assert [p["nombre"] for p in exp["personajes"]] == ["Kaelith"]
    assert [m["nombre"] for m in exp["mapas"]] == ["Claro"]


def test_importar_crea_un_sistema_equivalente(cliente, sistema_poblado):
    exp = cliente.get(f"/sistemas/{sistema_poblado}/exportar").json()

    nuevo = cliente.post("/sistemas/importar", json=exp)
    assert nuevo.status_code == 201
    nuevo_id = nuevo.json()["id"]
    assert nuevo_id != sistema_poblado  # nunca sobrescribe el original

    detalle = cliente.get(f"/sistemas/{nuevo_id}").json()
    assert [a["clave"] for a in detalle["atributos"]] == ["fuerza"]
    assert [e["formula"] for e in detalle["estadisticas"]] == ["fuerza * 10 + nivel * 5"]

    # La ficha importada recalcula su estadística: fuerza 8 * 10 + nivel 1 * 5 = 85
    personajes = cliente.get(f"/sistemas/{nuevo_id}/personajes").json()
    assert personajes[0]["nombre"] == "Kaelith"
    assert personajes[0]["estadisticas"]["vida"] == 85

    mapas = cliente.get(f"/sistemas/{nuevo_id}/mapas").json()
    assert mapas[0]["nombre"] == "Claro"


def test_importar_archivo_ajeno_se_rechaza(cliente):
    r = cliente.post(
        "/sistemas/importar",
        json={"formato": "otro/cosa", "nombre": "X"},
    )
    assert r.status_code == 422
    assert "Breakcode" in r.json()["detail"]


def test_exportar_conserva_la_niebla(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()["id"]
    mapa = cliente.post(
        f"/sistemas/{sistema}/mapas", json={"nombre": "M", "ancho": 4, "alto": 4}
    ).json()["id"]
    cliente.put(f"/mapas/{mapa}/niebla", json={"cambios": [{"x": 1, "y": 1, "oculta": True}]})

    exp = cliente.get(f"/sistemas/{sistema}/exportar").json()
    nuevo = cliente.post("/sistemas/importar", json=exp).json()["id"]
    mapa_nuevo = cliente.get(f"/sistemas/{nuevo}/mapas").json()[0]["id"]
    assert cliente.get(f"/mapas/{mapa_nuevo}").json()["niebla"][1][1] is True
