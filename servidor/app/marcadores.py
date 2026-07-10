"""Catálogo de tipos de marcador del mapa geográfico.

Cada tipo tiene un nombre para mostrar, un color y un símbolo. Vive en el
servidor para que cliente y reglas usen la misma fuente de verdad, igual que
los terrenos del mapa de batalla.
"""

TIPOS_MARCADOR: dict[str, dict] = {
    "ciudad": {"nombre": "Ciudad", "color": "#c9a35c", "simbolo": "🏰"},
    "pueblo": {"nombre": "Pueblo", "color": "#b5895a", "simbolo": "🏘"},
    "mazmorra": {"nombre": "Mazmorra", "color": "#a33b2a", "simbolo": "⚔"},
    "fortaleza": {"nombre": "Fortaleza", "color": "#8a6f4d", "simbolo": "🛡"},
    "bosque": {"nombre": "Bosque", "color": "#4a7c46", "simbolo": "🌲"},
    "montana": {"nombre": "Montaña", "color": "#6e6258", "simbolo": "⛰"},
    "ruinas": {"nombre": "Ruinas", "color": "#7a746c", "simbolo": "🏛"},
    "punto": {"nombre": "Punto de interés", "color": "#7a9ec7", "simbolo": "📍"},
}

TIPO_INICIAL = "punto"


def existe(tipo: str) -> bool:
    return tipo in TIPOS_MARCADOR
