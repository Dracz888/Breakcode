"""Pruebas de la API completa: el flujo real de la fábrica de sistemas.

Recorre lo mismo que hará una persona desde el editor: crear un sistema,
definir atributos y fórmulas, crear una ficha y ver que todo se calcula
y se protege como promete el diseño.
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
    # Base de datos en memoria, limpia para cada prueba.
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
    """Un sistema de ejemplo con atributos y fórmulas ya definidos."""
    r = cliente.post("/sistemas", json={"nombre": "Fantasía de prueba"})
    assert r.status_code == 201
    sistema_id = r.json()["id"]

    for atributo in [
        {"clave": "fuerza", "nombre": "Fuerza", "categoria": "fisica", "valor_inicial": 1},
        {"clave": "destreza", "nombre": "Destreza", "categoria": "fisica", "valor_inicial": 1},
        {"clave": "voluntad_arcana", "nombre": "Voluntad Arcana", "categoria": "magica"},
    ]:
        assert cliente.post(f"/sistemas/{sistema_id}/atributos", json=atributo).status_code == 201

    for estadistica in [
        {"clave": "vida_maxima", "nombre": "Vida máxima", "formula": "fuerza * 10 + nivel * 5"},
        {"clave": "mana_maximo", "nombre": "Maná máximo", "formula": "voluntad_arcana * 8"},
        {"clave": "defensa", "nombre": "Defensa", "formula": "piso(vida_maxima / 10) + destreza"},
    ]:
        r = cliente.post(f"/sistemas/{sistema_id}/estadisticas", json=estadistica)
        assert r.status_code == 201, r.text

    return sistema_id


def test_flujo_completo_de_ficha(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/personajes",
        json={"nombre": "Kaelith", "nivel": 3, "atributos": {"fuerza": 5, "voluntad_arcana": 4}},
    )
    assert r.status_code == 201
    ficha = r.json()

    # Atributo no indicado (destreza) toma su valor inicial.
    assert ficha["atributos"]["destreza"] == 1
    # Estadísticas calculadas por las fórmulas del sistema:
    assert ficha["estadisticas"]["vida_maxima"] == 65  # 5*10 + 3*5
    assert ficha["estadisticas"]["mana_maximo"] == 32  # 4*8
    assert ficha["estadisticas"]["defensa"] == 7       # piso(65/10) + 1
    assert ficha["errores_de_formulas"] == {}


def test_editar_formula_recalcula_fichas(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/personajes",
        json={"nombre": "Kaelith", "atributos": {"fuerza": 5}},
    )
    ficha_id = r.json()["id"]
    assert r.json()["estadisticas"]["vida_maxima"] == 55  # 5*10 + 1*5

    # El DJ decide que la vida ahora vale el doble:
    r = cliente.put(
        f"/sistemas/{sistema}/estadisticas/vida_maxima",
        json={"formula": "fuerza * 20 + nivel * 5"},
    )
    assert r.status_code == 200

    # La ficha existente se recalcula sola:
    r = cliente.get(f"/personajes/{ficha_id}")
    assert r.json()["estadisticas"]["vida_maxima"] == 105


def test_formula_con_nombre_inexistente_se_rechaza(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/estadisticas",
        json={"clave": "rota", "nombre": "Rota", "formula": "inteligencia * 2"},
    )
    assert r.status_code == 422
    assert "'inteligencia'" in r.json()["detail"]
    assert "no existen en este sistema" in r.json()["detail"]


def test_no_se_puede_borrar_atributo_usado(cliente, sistema):
    r = cliente.delete(f"/sistemas/{sistema}/atributos/fuerza")
    assert r.status_code == 409
    assert "Vida máxima" in r.json()["detail"]

    # Un atributo que ninguna fórmula usa sí se puede borrar... pero primero
    # borramos la fórmula que usa a destreza para comprobarlo.
    assert cliente.delete(f"/sistemas/{sistema}/estadisticas/defensa").status_code == 204
    assert cliente.delete(f"/sistemas/{sistema}/atributos/destreza").status_code == 204


def test_no_se_puede_borrar_estadistica_usada_por_otra(cliente, sistema):
    # 'defensa' depende de 'vida_maxima'
    r = cliente.delete(f"/sistemas/{sistema}/estadisticas/vida_maxima")
    assert r.status_code == 409
    assert "Defensa" in r.json()["detail"]


def test_vista_previa_de_formula(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/probar-formula",
        json={"formula": "fuerza * 2 + destreza", "valores_de_prueba": {"fuerza": 4, "destreza": 3}},
    )
    assert r.status_code == 200
    assert r.json() == {
        "ok": True,
        "valor": 11,
        "error": None,
        "valores_usados": r.json()["valores_usados"],
    }

    r = cliente.post(
        f"/sistemas/{sistema}/probar-formula",
        json={"formula": "fuersa * 2"},
    )
    assert r.json()["ok"] is False
    assert "'fuersa' no existe" in r.json()["error"]


def test_clave_invalida_da_mensaje_claro(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/atributos",
        json={"clave": "Voluntad Arcana", "nombre": "Voluntad Arcana"},
    )
    assert r.status_code == 422
    assert "guion_bajo" in r.text


def test_clave_duplicada_se_rechaza(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/atributos",
        json={"clave": "fuerza", "nombre": "Fuerza otra vez"},
    )
    assert r.status_code == 409


def test_personaje_con_atributo_desconocido_se_rechaza(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/personajes",
        json={"nombre": "Bugbear", "atributos": {"suerte": 3}},
    )
    assert r.status_code == 422
    assert "'suerte'" in r.json()["detail"]


def test_monstruos_usan_el_mismo_motor(cliente, sistema):
    r = cliente.post(
        f"/sistemas/{sistema}/personajes",
        json={"nombre": "Ogro", "es_monstruo": True, "atributos": {"fuerza": 8}},
    )
    assert r.status_code == 201
    assert r.json()["es_monstruo"] is True
    assert r.json()["estadisticas"]["vida_maxima"] == 85


def test_sistemas_independientes(cliente, sistema):
    # Un segundo sistema con reglas distintas no se mezcla con el primero.
    r = cliente.post("/sistemas", json={"nombre": "Ciencia ficción"})
    otro = r.json()["id"]
    cliente.post(
        f"/sistemas/{otro}/atributos", json={"clave": "punteria", "nombre": "Puntería"}
    )
    r = cliente.post(
        f"/sistemas/{otro}/estadisticas",
        json={"clave": "impacto", "nombre": "Impacto", "formula": "fuerza * 2"},
    )
    assert r.status_code == 422  # 'fuerza' pertenece al otro sistema, aquí no existe
