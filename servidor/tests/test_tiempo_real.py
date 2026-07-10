"""Pruebas del multijugador en tiempo real (Fase 4).

Comprueba que la sala del mapa (WebSocket) reparte a todos los conectados los
cambios que ocurren por las rutas REST: presencia, pintar terreno, y colocar,
mover o quitar una ficha.
"""

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
    # Usar TestClient como contexto arranca el bucle de eventos de la app, que es
    # el que reparte los mensajes de las salas en tiempo real.
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def entorno(cliente):
    sistema = cliente.post("/sistemas", json={"nombre": "Prueba"}).json()["id"]
    heroe = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "Kaelith", "atributos": {}}
    ).json()["id"]
    mapa = cliente.post(
        f"/sistemas/{sistema}/mapas", json={"nombre": "Claro", "ancho": 8, "alto": 6}
    ).json()["id"]
    return {"sistema": sistema, "heroe": heroe, "mapa": mapa}


def test_al_conectarse_recibe_la_presencia(cliente, entorno):
    with cliente.websocket_connect(f"/ws/mapas/{entorno['mapa']}") as ws:
        mensaje = ws.receive_json()
        assert mensaje == {"tipo": "presencia", "datos": {"conectados": 1}}


def test_dos_conectados_ven_la_misma_presencia(cliente, entorno):
    ruta = f"/ws/mapas/{entorno['mapa']}"
    with cliente.websocket_connect(ruta) as ws1:
        assert ws1.receive_json()["datos"]["conectados"] == 1
        with cliente.websocket_connect(ruta) as ws2:
            # Al entrar el segundo, ambos reciben la presencia actualizada.
            assert ws2.receive_json()["datos"]["conectados"] == 2
            assert ws1.receive_json()["datos"]["conectados"] == 2


def test_pintar_terreno_se_reparte(cliente, entorno):
    with cliente.websocket_connect(f"/ws/mapas/{entorno['mapa']}") as ws:
        ws.receive_json()  # presencia inicial
        cliente.put(
            f"/mapas/{entorno['mapa']}/celdas",
            json={"cambios": [{"x": 1, "y": 2, "terreno": "agua"}]},
        )
        evento = ws.receive_json()
        assert evento["tipo"] == "terreno"
        assert evento["datos"]["cambios"] == [{"x": 1, "y": 2, "terreno": "agua"}]


def test_colocar_mover_y_quitar_ficha_se_reparten(cliente, entorno):
    with cliente.websocket_connect(f"/ws/mapas/{entorno['mapa']}") as ws:
        ws.receive_json()  # presencia inicial

        token = cliente.post(
            f"/mapas/{entorno['mapa']}/tokens",
            json={"personaje_id": entorno["heroe"], "x": 2, "y": 2},
        ).json()
        colocado = ws.receive_json()
        assert colocado["tipo"] == "token_colocado"
        assert colocado["datos"]["nombre"] == "Kaelith"
        assert (colocado["datos"]["x"], colocado["datos"]["y"]) == (2, 2)

        cliente.put(f"/tokens/{token['id']}", json={"x": 5, "y": 3})
        movido = ws.receive_json()
        assert movido["tipo"] == "token_movido"
        assert (movido["datos"]["x"], movido["datos"]["y"]) == (5, 3)

        cliente.delete(f"/tokens/{token['id']}")
        quitado = ws.receive_json()
        assert quitado == {"tipo": "token_quitado", "datos": {"id": token["id"]}}
