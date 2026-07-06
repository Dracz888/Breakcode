"""Catálogo de terrenos del mapa de batalla.

Cada terreno tiene un color, un símbolo opcional y si bloquea el paso.
Vive en el servidor para que cliente y reglas usen la misma fuente de verdad.
"""

TERRENOS: dict[str, dict] = {
    "pasto": {"nombre": "Pasto", "color": "#4a7c46", "simbolo": "", "bloquea": False},
    "camino": {"nombre": "Camino", "color": "#8a6f4d", "simbolo": "", "bloquea": False},
    "arena": {"nombre": "Arena", "color": "#c2a76c", "simbolo": "", "bloquea": False},
    "madera": {"nombre": "Piso de madera", "color": "#7a5a38", "simbolo": "", "bloquea": False},
    "agua": {"nombre": "Agua", "color": "#3d6e8f", "simbolo": "", "bloquea": True},
    "muro": {"nombre": "Muro", "color": "#55504b", "simbolo": "", "bloquea": True},
    "arbol": {"nombre": "Árbol", "color": "#2e5b2b", "simbolo": "🌲", "bloquea": True},
    "roca": {"nombre": "Roca", "color": "#6e6258", "simbolo": "🪨", "bloquea": True},
}

TERRENO_INICIAL = "pasto"


def bloquea(terreno: str) -> bool:
    return TERRENOS.get(terreno, {}).get("bloquea", False)
