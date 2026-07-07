"""Tirador de dados de la mesa.

Entiende expresiones como las que se dicen en voz alta en una partida:
"1d20+5", "2d6+1d4+3", "d20-1". El servidor es quien tira —así el azar es
justo e igual para todos— y devuelve el desglose de cada dado, no solo el total,
para que la mesa pueda ver exactamente qué salió (transparencia).
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

# Un término es un dado (2d6) o un número suelto (+3). Se admite espacio en blanco.
_TERMINO = re.compile(r"\s*([+-])?\s*(?:(\d*)d(\d+)|(\d+))\s*", re.IGNORECASE)

MAX_DADOS = 100  # topes para evitar tiradas absurdas ("9999d9999")
MAX_CARAS = 1000


class ErrorDeTirada(Exception):
    """Expresión de dados mal escrita, con mensaje apto para el usuario."""


@dataclass
class GrupoDeDados:
    """Un grupo de dados iguales dentro de la tirada (ej. los '2d6')."""

    cantidad: int
    caras: int
    valores: list[int] = field(default_factory=list)

    @property
    def subtotal(self) -> int:
        return sum(self.valores)


@dataclass
class Tirada:
    expresion: str
    grupos: list[GrupoDeDados]
    modificador: int
    total: int


def _parsear(expresion: str) -> list[tuple[str, str]]:
    """Corta la expresión en términos con su signo, validando que no sobre nada."""
    if not expresion or not expresion.strip():
        raise ErrorDeTirada("Escribe una tirada, por ejemplo 1d20+5")
    terminos: list[tuple[str, str]] = []
    pos = 0
    for m in _TERMINO.finditer(expresion):
        if m.start() != pos:
            break  # hay algo que no encaja entre términos
        pos = m.end()
        signo = m.group(1) or "+"
        if m.group(3):  # es un dado NdM
            terminos.append((signo, f"{m.group(2) or '1'}d{m.group(3)}"))
        else:  # es un número suelto
            terminos.append((signo, m.group(4)))
    if pos != len(expresion) or not terminos:
        raise ErrorDeTirada(
            f"No entiendo '{expresion}'. Usa el formato 1d20+5 (dados y números "
            "separados por + o -)."
        )
    return terminos


def tirar(expresion: str, aleatorio: random.Random | None = None) -> Tirada:
    """Tira la expresión y devuelve el desglose completo. Lanza ErrorDeTirada."""
    rng = aleatorio or random
    terminos = _parsear(expresion)
    grupos: list[GrupoDeDados] = []
    modificador = 0
    total = 0
    for signo, cuerpo in terminos:
        factor = 1 if signo == "+" else -1
        if "d" in cuerpo.lower():
            cantidad_txt, caras_txt = cuerpo.lower().split("d")
            cantidad = int(cantidad_txt)
            caras = int(caras_txt)
            if cantidad < 1 or cantidad > MAX_DADOS:
                raise ErrorDeTirada(f"El número de dados debe estar entre 1 y {MAX_DADOS}")
            if caras < 2 or caras > MAX_CARAS:
                raise ErrorDeTirada(f"Un dado debe tener entre 2 y {MAX_CARAS} caras")
            valores = [rng.randint(1, caras) for _ in range(cantidad)]
            grupos.append(GrupoDeDados(cantidad=cantidad, caras=caras, valores=valores))
            total += factor * sum(valores)
        else:
            numero = int(cuerpo)
            modificador += factor * numero
            total += factor * numero
    return Tirada(expresion=expresion.strip(), grupos=grupos, modificador=modificador, total=total)
