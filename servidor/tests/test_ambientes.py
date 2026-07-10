"""Pruebas de la mesa de sonido (ambientes de fondo).

Comprueba que los ambientes integrados se sintetizan y sirven como audio real, y
que el DJ puede subir, listar, reproducir y borrar sus propias grabaciones.
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import ambientes
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
    return cliente.post("/sistemas", json={"nombre": "Mesa de prueba"}).json()["id"]


def test_catalogo_integrado_cubre_las_categorias(cliente):
    r = cliente.get("/ambientes/integrados")
    assert r.status_code == 200
    claves = {a["clave"] for a in r.json()}
    # Lo que pidió la mesa: taberna, fiesta, guerra, choque de armas, naturaleza, agua…
    for esperado in {"taberna", "fiesta", "guerra", "choque_armas", "bosque", "rio", "mar"}:
        assert esperado in claves


@pytest.mark.parametrize("clave", [a["clave"] for a in ambientes.AMBIENTES_INTEGRADOS])
def test_cada_ambiente_integrado_suena(cliente, clave):
    r = cliente.get(f"/ambientes/integrados/{clave}/audio")
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"
    assert r.content[:4] == b"RIFF"  # es un WAV válido
    assert len(r.content) > 1000


def test_ambiente_inexistente_da_404(cliente):
    assert cliente.get("/ambientes/integrados/inventado/audio").status_code == 404


def test_subir_listar_reproducir_y_borrar(cliente, sistema):
    audio_falso = b"ID3fake-mp3-bytes" * 10
    r = cliente.post(
        f"/sistemas/{sistema}/ambientes",
        data={"nombre": "Taberna del puerto", "categoria": "Social", "icono": "🍺"},
        files={"archivo": ("taberna.mp3", io.BytesIO(audio_falso), "audio/mpeg")},
    )
    assert r.status_code == 201, r.text
    ambiente = r.json()
    assert ambiente["nombre"] == "Taberna del puerto"
    assert ambiente["bucle"] is True

    lista = cliente.get(f"/sistemas/{sistema}/ambientes").json()
    assert len(lista) == 1

    audio = cliente.get(f"/ambientes/{ambiente['id']}/audio")
    assert audio.status_code == 200
    assert audio.content == audio_falso

    assert cliente.delete(f"/ambientes/{ambiente['id']}").status_code == 204
    assert cliente.get(f"/sistemas/{sistema}/ambientes").json() == []


def test_subir_archivo_no_audio_se_rechaza(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/ambientes",
        data={"nombre": "Trampa"},
        files={"archivo": ("virus.txt", io.BytesIO(b"no soy audio"), "text/plain")},
    )
    assert r.status_code == 422
    assert "audio" in r.json()["detail"].lower()
