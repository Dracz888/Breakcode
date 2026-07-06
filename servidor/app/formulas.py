"""Motor de fórmulas de la fábrica de sistemas.

Evalúa expresiones tipo Excel ("fuerza * 10 + nivel * 5") de forma segura
con simpleeval: el texto de la fórmula nunca puede ejecutar código arbitrario.
Todos los mensajes de error están en español claro, pensados para mostrarse
tal cual en el editor de sistemas.
"""

import ast
import math

from simpleeval import (
    FunctionNotDefined,
    NameNotDefined,
    SimpleEval,
)

# Funciones permitidas dentro de las fórmulas (con alias en español).
FUNCIONES = {
    "min": min,
    "max": max,
    "abs": abs,
    "redondear": round,
    "round": round,
    "piso": math.floor,
    "floor": math.floor,
    "techo": math.ceil,
    "ceil": math.ceil,
}


class ErrorDeFormula(Exception):
    """Error al evaluar una fórmula, con mensaje apto para el usuario."""

    def __init__(self, mensaje: str, nombre_faltante: str | None = None):
        super().__init__(mensaje)
        self.nombre_faltante = nombre_faltante


def nombres_usados(formula: str) -> set[str]:
    """Devuelve los nombres (atributos, estadísticas, funciones) que usa la fórmula."""
    try:
        arbol = ast.parse(formula, mode="eval")
    except SyntaxError:
        return set()
    return {nodo.id for nodo in ast.walk(arbol) if isinstance(nodo, ast.Name)}


def evaluar(formula: str, variables: dict) -> float:
    """Evalúa una fórmula con los valores dados. Lanza ErrorDeFormula si falla."""
    if not formula or not formula.strip():
        raise ErrorDeFormula("La fórmula está vacía")
    evaluador = SimpleEval(names=dict(variables), functions=dict(FUNCIONES))
    try:
        resultado = evaluador.eval(formula)
    except NameNotDefined as e:
        raise ErrorDeFormula(
            f"'{e.name}' no existe: no es un atributo ni una estadística de este sistema",
            nombre_faltante=e.name,
        )
    except FunctionNotDefined as e:
        disponibles = ", ".join(sorted(set(FUNCIONES)))
        raise ErrorDeFormula(
            f"La función '{e.func_name}' no existe. Funciones disponibles: {disponibles}"
        )
    except SyntaxError:
        raise ErrorDeFormula(
            "La fórmula tiene un error de escritura (revisa paréntesis, comas y símbolos)"
        )
    except ZeroDivisionError:
        raise ErrorDeFormula("La fórmula intenta dividir entre cero")
    except Exception:
        raise ErrorDeFormula("La fórmula no se pudo calcular (revisa que esté bien escrita)")
    if not isinstance(resultado, (int, float)) or isinstance(resultado, bool):
        raise ErrorDeFormula("La fórmula debe dar como resultado un número")
    return resultado


def evaluar_conjunto(
    formulas: dict[str, str], variables: dict
) -> tuple[dict[str, float], dict[str, str]]:
    """Evalúa todas las estadísticas derivadas de una ficha.

    Una fórmula puede usar el resultado de otra (ej. defensa = vida_maxima / 10),
    así que se resuelven en pasadas sucesivas hasta que ninguna avance.
    Devuelve (valores calculados, errores por estadística).
    """
    valores: dict[str, float] = {}
    errores: dict[str, str] = {}
    pendientes = dict(formulas)

    while pendientes:
        hubo_progreso = False
        fallos: dict[str, ErrorDeFormula] = {}
        for clave, formula in list(pendientes.items()):
            try:
                valores[clave] = evaluar(formula, {**variables, **valores})
                del pendientes[clave]
                hubo_progreso = True
            except ErrorDeFormula as e:
                fallos[clave] = e
        if not hubo_progreso:
            for clave, error in fallos.items():
                faltante = error.nombre_faltante
                if faltante is not None and faltante in pendientes:
                    errores[clave] = (
                        f"Referencia circular: '{clave}' y '{faltante}' dependen una de la otra"
                    )
                else:
                    errores[clave] = str(error)
            break

    return valores, errores
