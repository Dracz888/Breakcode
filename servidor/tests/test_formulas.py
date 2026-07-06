"""Pruebas del motor de fórmulas: la pieza más delicada se prueba sola."""

import pytest

from app import formulas
from app.formulas import ErrorDeFormula, evaluar, evaluar_conjunto, nombres_usados


def test_aritmetica_basica():
    assert evaluar("2 + 3 * 4", {}) == 14


def test_usa_atributos_y_nivel():
    valores = {"fuerza": 5, "nivel": 3}
    assert evaluar("fuerza * 10 + nivel * 5", valores) == 65


def test_funciones_en_espanol():
    assert evaluar("piso(7 / 2)", {}) == 3
    assert evaluar("techo(7 / 2)", {}) == 4
    assert evaluar("max(fuerza, destreza)", {"fuerza": 2, "destreza": 9}) == 9


def test_atributo_inexistente_da_error_claro():
    with pytest.raises(ErrorDeFormula) as excinfo:
        evaluar("fuersa * 2", {"fuerza": 5})
    assert "'fuersa' no existe" in str(excinfo.value)
    assert excinfo.value.nombre_faltante == "fuersa"


def test_error_de_escritura():
    with pytest.raises(ErrorDeFormula) as excinfo:
        evaluar("fuerza * (2 +", {"fuerza": 5})
    assert "error de escritura" in str(excinfo.value)


def test_division_entre_cero():
    with pytest.raises(ErrorDeFormula) as excinfo:
        evaluar("10 / defensa", {"defensa": 0})
    assert "dividir entre cero" in str(excinfo.value)


def test_formula_vacia():
    with pytest.raises(ErrorDeFormula):
        evaluar("   ", {})


def test_conjunto_con_dependencias_entre_estadisticas():
    # 'defensa' usa 'vida_maxima', que a su vez usa atributos: deben
    # resolverse en el orden correcto sin importar cómo se declaren.
    conjunto = {
        "defensa": "vida_maxima / 10 + armadura",
        "vida_maxima": "fuerza * 10",
    }
    valores, errores = evaluar_conjunto(conjunto, {"fuerza": 5, "armadura": 2})
    assert errores == {}
    assert valores["vida_maxima"] == 50
    assert valores["defensa"] == 7


def test_referencia_circular_detectada():
    conjunto = {"a": "b + 1", "b": "a + 1"}
    valores, errores = evaluar_conjunto(conjunto, {})
    assert valores == {}
    assert "circular" in errores["a"].lower()
    assert "circular" in errores["b"].lower()


def test_un_error_no_bloquea_al_resto():
    conjunto = {"vida": "fuerza * 10", "rota": "no_existe + 1"}
    valores, errores = evaluar_conjunto(conjunto, {"fuerza": 3})
    assert valores == {"vida": 30}
    assert "no_existe" in errores["rota"]


def test_nombres_usados():
    assert nombres_usados("fuerza * 2 + max(destreza, nivel)") == {
        "fuerza",
        "destreza",
        "nivel",
        "max",
    }
    assert nombres_usados("2 +") == set()  # sintaxis rota: sin nombres


def test_no_ejecuta_codigo_peligroso():
    # simpleeval no expone import ni funciones del sistema.
    with pytest.raises(ErrorDeFormula):
        evaluar("__import__('os').system('echo hola')", {})
