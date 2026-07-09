"""Pruebas del módulo de voces (Fase 8).

Recorre lo que hará el DJ: ver el catálogo sugerido, crear una voz, asignarla a
un personaje, narrar una línea y comprobar que el audio queda en el historial
compartido y se puede reproducir. Todo en modo demostración (sin ElevenLabs),
que es como se prueba sin contratar el servicio.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, obtener_db
from app.main import app


@pytest.fixture()
def cliente(monkeypatch):
    # Sin clave: el módulo trabaja en modo demostración durante las pruebas.
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
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
    return cliente.post("/sistemas", json={"nombre": "Mesa de prueba"}).json()["id"]


def test_estado_reporta_modo_demostracion_y_sugeridas(cliente):
    r = cliente.get("/voces/estado")
    assert r.status_code == 200
    estado = r.json()
    assert estado["hay_api"] is False  # sin clave configurada
    assert len(estado["sugeridas"]) > 0
    assert "voz_externa_id" in estado["sugeridas"][0]
    assert estado["max_caracteres"] > 0


def test_crear_listar_y_borrar_voz(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/voces",
        json={
            "nombre": "Ogro cavernario",
            "descripcion": "Voz grave y monstruosa que arrastra las palabras",
            "voz_externa_id": "VR6AewLTigWG4xSOukaG",
        },
    )
    assert r.status_code == 201
    voz = r.json()

    assert cliente.get(f"/sistemas/{sistema}/voces").json()[0]["nombre"] == "Ogro cavernario"

    assert cliente.delete(f"/voces/{voz['id']}").status_code == 204
    assert cliente.get(f"/sistemas/{sistema}/voces").json() == []


def test_asignar_voz_a_personaje(cliente, sistema):
    voz = cliente.post(
        f"/sistemas/{sistema}/voces",
        json={"nombre": "Anciana sabia", "voz_externa_id": "21m00Tcm4TlvDq8ikWAM"},
    ).json()
    personaje = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "Maga Elda"}
    ).json()

    r = cliente.put(f"/personajes/{personaje['id']}", json={"voz_id": voz["id"]})
    assert r.status_code == 200
    assert r.json()["voz_id"] == voz["id"]

    # Se le puede quitar la voz enviando null explícito.
    r = cliente.put(f"/personajes/{personaje['id']}", json={"voz_id": None})
    assert r.json()["voz_id"] is None


def test_borrar_voz_deja_al_personaje_sin_voz(cliente, sistema):
    voz = cliente.post(
        f"/sistemas/{sistema}/voces",
        json={"nombre": "Heraldo", "voz_externa_id": "pNInz6obpgDQGcFmaJgB"},
    ).json()
    personaje = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "Voz del rey"}
    ).json()
    cliente.put(f"/personajes/{personaje['id']}", json={"voz_id": voz["id"]})

    assert cliente.delete(f"/voces/{voz['id']}").status_code == 204
    assert cliente.get(f"/personajes/{personaje['id']}").json()["voz_id"] is None


def test_narrar_genera_audio_en_el_historial(cliente, sistema):
    voz = cliente.post(
        f"/sistemas/{sistema}/voces",
        json={"nombre": "Narrador", "voz_externa_id": "pNInz6obpgDQGcFmaJgB"},
    ).json()

    r = cliente.post(
        f"/sistemas/{sistema}/narrar",
        json={"texto": "Las puertas del castillo se abren con un crujido.", "voz_id": voz["id"]},
    )
    assert r.status_code == 201, r.text
    narracion = r.json()
    assert narracion["es_demostracion"] is True  # sin ElevenLabs
    assert narracion["nombre_locutor"] == "Narrador"

    # Queda en el historial compartido.
    historial = cliente.get(f"/sistemas/{sistema}/narraciones").json()
    assert len(historial) == 1

    # El audio se puede descargar y no está vacío.
    audio = cliente.get(f"/narraciones/{narracion['id']}/audio")
    assert audio.status_code == 200
    assert audio.headers["content-type"].startswith("audio/")
    assert len(audio.content) > 0


def test_narrar_con_personaje_usa_su_voz(cliente, sistema):
    voz = cliente.post(
        f"/sistemas/{sistema}/voces",
        json={"nombre": "Kaelith", "voz_externa_id": "EXAVITQu4vr4xnSDxMaL"},
    ).json()
    personaje = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "Kaelith"}
    ).json()
    cliente.put(f"/personajes/{personaje['id']}", json={"voz_id": voz["id"]})

    r = cliente.post(
        f"/sistemas/{sistema}/narrar",
        json={"texto": "No pasarán mientras yo respire.", "personaje_id": personaje["id"]},
    )
    assert r.status_code == 201
    assert r.json()["personaje_id"] == personaje["id"]
    assert r.json()["nombre_locutor"] == "Kaelith"


def test_narrar_personaje_sin_voz_avisa(cliente, sistema):
    personaje = cliente.post(
        f"/sistemas/{sistema}/personajes", json={"nombre": "Mudo"}
    ).json()
    r = cliente.post(
        f"/sistemas/{sistema}/narrar",
        json={"texto": "Hola", "personaje_id": personaje["id"]},
    )
    assert r.status_code == 422
    assert "no tiene una voz asignada" in r.json()["detail"]


def test_narrar_texto_muy_largo_se_rechaza(cliente, sistema):
    voz = cliente.post(
        f"/sistemas/{sistema}/voces",
        json={"nombre": "Voz", "voz_externa_id": "pNInz6obpgDQGcFmaJgB"},
    ).json()
    r = cliente.post(
        f"/sistemas/{sistema}/narrar",
        json={"texto": "a" * 5000, "voz_id": voz["id"]},
    )
    assert r.status_code == 422
    assert "muy larga" in r.json()["detail"]
