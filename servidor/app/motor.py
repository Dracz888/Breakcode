"""Cálculo de las estadísticas de una ficha, en un solo lugar.

Tanto la hoja de personaje como el combate necesitan saber, por ejemplo, la
vida máxima o la iniciativa de una ficha. Ese cálculo vive aquí para que el
motor sea uno solo y no se repita.
"""

from __future__ import annotations

from . import formulas, models


def estadisticas_de(personaje: "models.Personaje") -> tuple[dict[str, float], dict[str, str]]:
    """Calcula las estadísticas derivadas de una ficha (valores, errores)."""
    variables: dict[str, float] = dict(personaje.atributos)
    variables["nivel"] = personaje.nivel
    formulas_del_sistema = {e.clave: e.formula for e in personaje.sistema.estadisticas}
    return formulas.evaluar_conjunto(formulas_del_sistema, variables)


def variables_de(personaje: "models.Personaje") -> dict[str, float]:
    """Todo lo que una fórmula de combate puede nombrar: atributos, nivel y
    estadísticas derivadas ya calculadas."""
    valores, _ = estadisticas_de(personaje)
    variables: dict[str, float] = dict(personaje.atributos)
    variables["nivel"] = personaje.nivel
    variables.update(valores)
    return variables


def vida_maxima_de(personaje: "models.Personaje") -> int | None:
    """La vida máxima de la ficha según la estadística que su sistema señale.

    Devuelve None si el sistema no configuró una estadística de vida o si esa
    estadística no se pudo calcular (una fórmula con error, por ejemplo).
    """
    clave = (personaje.sistema.config_combate or {}).get("estadistica_vida", "")
    if not clave:
        return None
    valores, _ = estadisticas_de(personaje)
    if clave not in valores:
        return None
    return int(valores[clave])
