"""Pruebas del combate por turnos (Fase 5): config, dados, vida y turnos."""

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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def entorno(cliente):
    """Un sistema con vida e iniciativa configuradas, dos fichas y un mapa con
    ambas colocadas."""
    sistema = cliente.post("/sistemas", json={"nombre": "Combate"}).json()["id"]
    for clave, nombre, inicial in [("fuerza", "Fuerza", 5), ("destreza", "Destreza", 3)]:
        cliente.post(
            f"/sistemas/{sistema}/atributos",
            json={"clave": clave, "nombre": nombre, "valor_inicial": inicial},
        )
    cliente.post(
        f"/sistemas/{sistema}/estadisticas",
        json={"clave": "vida_maxima", "nombre": "Vida", "formula": "fuerza * 10"},
    )
    cliente.post(
        f"/sistemas/{sistema}/estadisticas",
        json={"clave": "iniciativa", "nombre": "Iniciativa", "formula": "destreza"},
    )
    cliente.put(
        f"/sistemas/{sistema}/config-combate",
        json={
            "formula_iniciativa": "iniciativa",
            "dado_iniciativa": "1d20",
            "estadistica_vida": "vida_maxima",
        },
    )
    heroe = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "Kaelith", "atributos": {}}
    ).json()["id"]
    ogro = cliente.post(
        f"/sistemas/{sistema}/personajes",
        json={"nombre": "Ogro", "es_monstruo": True, "atributos": {"fuerza": 8}},
    ).json()["id"]
    mapa = cliente.post(
        f"/sistemas/{sistema}/mapas", json={"nombre": "Arena", "ancho": 8, "alto": 6}
    ).json()["id"]
    tok_heroe = cliente.post(
        f"/mapas/{mapa}/tokens", json={"personaje_id": heroe, "x": 1, "y": 1}
    ).json()
    tok_ogro = cliente.post(
        f"/mapas/{mapa}/tokens", json={"personaje_id": ogro, "x": 5, "y": 3}
    ).json()
    return {"sistema": sistema, "mapa": mapa, "heroe": tok_heroe, "ogro": tok_ogro}


# ---------- Config ----------

def test_config_por_defecto(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()["id"]
    config = cliente.get(f"/sistemas/{sistema}/config-combate").json()
    assert config == {
        "formula_iniciativa": "",
        "dado_iniciativa": "1d20",
        "estadistica_vida": "",
    }


def test_config_rechaza_estadistica_de_vida_inexistente(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()["id"]
    r = cliente.put(
        f"/sistemas/{sistema}/config-combate",
        json={"estadistica_vida": "no_existe"},
    )
    assert r.status_code == 422
    assert "no existe" in r.json()["detail"]


def test_config_rechaza_dado_invalido(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "X"}).json()["id"]
    r = cliente.put(
        f"/sistemas/{sistema}/config-combate", json={"dado_iniciativa": "abc"}
    )
    assert r.status_code == 422


# ---------- Dados con historial ----------

def test_tirar_dados_guarda_en_historial(cliente, entorno):
    r = cliente.post(
        f"/mapas/{entorno['mapa']}/tiradas",
        json={"expresion": "2d6+3", "autor": "Kaelith", "motivo": "ataque"},
    )
    assert r.status_code == 201
    tirada = r.json()
    assert tirada["expresion"] == "2d6+3" and tirada["modificador"] == 3
    suma_dados = sum(v for g in tirada["grupos"] for v in g["valores"])
    assert tirada["total"] == suma_dados + 3

    historial = cliente.get(f"/mapas/{entorno['mapa']}/tiradas").json()
    assert len(historial) == 1 and historial[0]["autor"] == "Kaelith"


def test_tirada_invalida_se_rechaza(cliente, entorno):
    r = cliente.post(f"/mapas/{entorno['mapa']}/tiradas", json={"expresion": "hola"})
    assert r.status_code == 422


# ---------- Vida (daño y curación) ----------

def test_ficha_nace_con_la_vida_llena(cliente, entorno):
    # Kaelith: fuerza 5 -> vida_maxima 50.
    assert entorno["heroe"]["vida_maxima"] == 50
    assert entorno["heroe"]["vida_actual"] == 50
    # Ogro: fuerza 8 -> vida_maxima 80.
    assert entorno["ogro"]["vida_maxima"] == 80


def test_aplicar_dano_y_curar_respeta_los_limites(cliente, entorno):
    tok = entorno["heroe"]["id"]
    r = cliente.put(f"/tokens/{tok}/vida", json={"delta": -12})
    assert r.json()["vida_actual"] == 38

    # No baja de 0 aunque el daño sea enorme.
    r = cliente.put(f"/tokens/{tok}/vida", json={"delta": -999})
    assert r.json()["vida_actual"] == 0

    # No sube por encima del máximo.
    r = cliente.put(f"/tokens/{tok}/vida", json={"delta": 999})
    assert r.json()["vida_actual"] == 50


def test_dano_sin_estadistica_de_vida_se_rechaza(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "SinVida"}).json()["id"]
    p = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "P", "atributos": {}}
    ).json()["id"]
    mapa = cliente.post(
        f"/sistemas/{sistema}/mapas", json={"nombre": "M", "ancho": 6, "alto": 6}
    ).json()["id"]
    tok = cliente.post(f"/mapas/{mapa}/tokens", json={"personaje_id": p, "x": 0, "y": 0}).json()
    assert tok["vida_maxima"] is None
    r = cliente.put(f"/tokens/{tok['id']}/vida", json={"delta": -5})
    assert r.status_code == 422


# ---------- Turnos e iniciativa ----------

def test_iniciar_combate_ordena_por_iniciativa(cliente, entorno):
    combate = cliente.post(f"/mapas/{entorno['mapa']}/combate/iniciar").json()
    assert combate["ronda"] == 1 and combate["indice_turno"] == 0
    assert len(combate["orden"]) == 2
    # La iniciativa no crece hacia abajo en la lista.
    inis = [p["iniciativa"] for p in combate["orden"]]
    assert inis == sorted(inis, reverse=True)
    assert combate["token_en_turno"] == combate["orden"][0]["token_id"]


def test_pasar_turnos_avanza_y_cuenta_rondas(cliente, entorno):
    cliente.post(f"/mapas/{entorno['mapa']}/combate/iniciar")
    c1 = cliente.post(f"/mapas/{entorno['mapa']}/combate/siguiente").json()
    assert c1["indice_turno"] == 1 and c1["ronda"] == 1
    # Con dos participantes, el siguiente cierra la vuelta y empieza la ronda 2.
    c2 = cliente.post(f"/mapas/{entorno['mapa']}/combate/siguiente").json()
    assert c2["indice_turno"] == 0 and c2["ronda"] == 2


def test_terminar_combate(cliente, entorno):
    cliente.post(f"/mapas/{entorno['mapa']}/combate/iniciar")
    assert cliente.delete(f"/mapas/{entorno['mapa']}/combate").status_code == 204
    assert cliente.get(f"/mapas/{entorno['mapa']}/combate").json() is None


def test_siguiente_sin_combate_se_rechaza(cliente, entorno):
    r = cliente.post(f"/mapas/{entorno['mapa']}/combate/siguiente")
    assert r.status_code == 422


# ---------- Tiempo real ----------

def test_tirada_y_combate_se_reparten_en_la_sala(cliente, entorno):
    with cliente.websocket_connect(f"/ws/mapas/{entorno['mapa']}") as ws:
        ws.receive_json()  # presencia inicial

        cliente.post(f"/mapas/{entorno['mapa']}/tiradas", json={"expresion": "1d20"})
        evento = ws.receive_json()
        assert evento["tipo"] == "tirada"
        assert 1 <= evento["datos"]["total"] <= 20

        cliente.post(f"/mapas/{entorno['mapa']}/combate/iniciar")
        evento = ws.receive_json()
        assert evento["tipo"] == "combate"
        assert evento["datos"]["ronda"] == 1

        cliente.put(f"/tokens/{entorno['heroe']['id']}/vida", json={"delta": -5})
        evento = ws.receive_json()
        assert evento["tipo"] == "token_actualizado"
        assert evento["datos"]["vida_actual"] == 45
