"""Pruebas del tirador de dados (motor puro, sin servidor)."""

import random

import pytest

from app.dados import ErrorDeTirada, tirar


def _rng():
    # Semilla fija para que las tiradas sean reproducibles en las pruebas.
    return random.Random(1234)


def test_dado_suelto_con_modificador():
    t = tirar("1d20+5", _rng())
    assert len(t.grupos) == 1
    assert t.grupos[0].cantidad == 1 and t.grupos[0].caras == 20
    assert t.modificador == 5
    assert t.total == t.grupos[0].subtotal + 5
    assert 6 <= t.total <= 25


def test_d20_sin_cantidad_es_un_dado():
    t = tirar("d20", _rng())
    assert t.grupos[0].cantidad == 1 and t.grupos[0].caras == 20
    assert 1 <= t.total <= 20


def test_varios_grupos_y_numeros():
    t = tirar("2d6+1d4+3", _rng())
    assert [g.caras for g in t.grupos] == [6, 4]
    assert t.grupos[0].cantidad == 2
    assert t.modificador == 3
    esperado = sum(t.grupos[0].valores) + sum(t.grupos[1].valores) + 3
    assert t.total == esperado


def test_resta():
    t = tirar("1d6-2", _rng())
    assert t.modificador == -2
    assert t.total == t.grupos[0].subtotal - 2


def test_numero_solo():
    t = tirar("7", _rng())
    assert t.grupos == [] and t.modificador == 7 and t.total == 7


def test_cada_valor_esta_en_rango():
    t = tirar("5d8", _rng())
    assert len(t.grupos[0].valores) == 5
    assert all(1 <= v <= 8 for v in t.grupos[0].valores)


@pytest.mark.parametrize("mala", ["", "   ", "hola", "1d20+", "2x6", "1d", "d", "1d1", "0d6"])
def test_expresiones_invalidas(mala):
    with pytest.raises(ErrorDeTirada):
        tirar(mala, _rng())


def test_topes_de_seguridad():
    with pytest.raises(ErrorDeTirada):
        tirar("101d6", _rng())
    with pytest.raises(ErrorDeTirada):
        tirar("1d5000", _rng())
