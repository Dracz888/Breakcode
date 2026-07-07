"""Formatos de entrada y salida de la API (validación con Pydantic).

Las 'claves' (los nombres que se usan dentro de las fórmulas) deben ser
identificadores simples: minúsculas, sin espacios ni acentos, ej. 'voluntad_arcana'.
"""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

PATRON_CLAVE = re.compile(r"^[a-z_][a-z0-9_]*$")

MENSAJE_CLAVE = (
    "La clave debe ir en minúsculas, sin espacios, acentos ni ñ; "
    "usa guion_bajo para separar palabras (ej. 'voluntad_arcana')"
)


def _validar_clave(clave: str) -> str:
    if not PATRON_CLAVE.match(clave):
        raise ValueError(MENSAJE_CLAVE)
    return clave


# ---------- Sistemas ----------

class SistemaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = ""


class SistemaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str


# ---------- Atributos ----------

class AtributoCrear(BaseModel):
    clave: str = Field(min_length=1, max_length=60)
    nombre: str = Field(min_length=1, max_length=120)
    categoria: str = ""
    descripcion: str = ""
    valor_inicial: int = 0

    @field_validator("clave")
    @classmethod
    def clave_valida(cls, v: str) -> str:
        return _validar_clave(v)


class AtributoEditar(BaseModel):
    nombre: str | None = None
    categoria: str | None = None
    descripcion: str | None = None
    valor_inicial: int | None = None


class AtributoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clave: str
    nombre: str
    categoria: str
    descripcion: str
    valor_inicial: int


# ---------- Estadísticas derivadas ----------

class EstadisticaCrear(BaseModel):
    clave: str = Field(min_length=1, max_length=60)
    nombre: str = Field(min_length=1, max_length=120)
    formula: str = Field(min_length=1)
    descripcion: str = ""

    @field_validator("clave")
    @classmethod
    def clave_valida(cls, v: str) -> str:
        return _validar_clave(v)


class EstadisticaEditar(BaseModel):
    nombre: str | None = None
    formula: str | None = None
    descripcion: str | None = None


class EstadisticaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clave: str
    nombre: str
    formula: str
    descripcion: str


class SistemaDetalle(SistemaSalida):
    atributos: list[AtributoSalida]
    estadisticas: list[EstadisticaSalida]


# ---------- Vista previa de fórmulas (para el editor) ----------

class FormulaPrueba(BaseModel):
    formula: str
    valores_de_prueba: dict[str, float] = {}


class FormulaResultado(BaseModel):
    ok: bool
    valor: float | None = None
    error: str | None = None
    valores_usados: dict[str, float] = {}


# ---------- Personajes ----------

class PersonajeCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    nivel: int = Field(default=1, ge=1)
    es_monstruo: bool = False
    atributos: dict[str, float] = {}


class PersonajeEditar(BaseModel):
    nombre: str | None = None
    nivel: int | None = Field(default=None, ge=1)
    atributos: dict[str, float] | None = None


class PersonajeSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sistema_id: int
    nombre: str
    nivel: int
    es_monstruo: bool
    atributos: dict[str, float]


class PersonajeConEstadisticas(PersonajeSalida):
    """La ficha completa: atributos + estadísticas derivadas ya calculadas."""

    estadisticas: dict[str, float]
    errores_de_formulas: dict[str, str]


# ---------- Mapas de batalla ----------

class MapaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    ancho: int = Field(default=16, ge=4, le=80)
    alto: int = Field(default=12, ge=4, le=80)


class MapaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sistema_id: int
    nombre: str
    ancho: int
    alto: int


class TokenSalida(BaseModel):
    id: int
    mapa_id: int
    personaje_id: int
    nombre: str
    es_monstruo: bool
    x: int
    y: int
    vida_actual: int | None = None
    vida_maxima: int | None = None


class MapaDetalle(MapaSalida):
    celdas: list[list[str]]
    tokens: list[TokenSalida]


class CambioDeCelda(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    terreno: str


class PintarCeldas(BaseModel):
    cambios: list[CambioDeCelda] = Field(min_length=1, max_length=6400)


class TokenColocar(BaseModel):
    personaje_id: int
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class TokenMover(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class VidaCambio(BaseModel):
    """Aplica daño (delta negativo) o curación (delta positivo) a un token."""

    delta: int


# ---------- Combate por turnos ----------

class ConfigCombate(BaseModel):
    """Ajustes del combate, editables por sistema. Vacío = por defecto."""

    # Expresión (tipo fórmula) que da el modificador de iniciativa de cada ficha,
    # ej. 'destreza' o 'iniciativa'. Vacío = sin modificador (solo el dado).
    formula_iniciativa: str = ""
    # Dado que se suma a la iniciativa al empezar el combate.
    dado_iniciativa: str = "1d20"
    # Clave de la estadística que marca la vida máxima, ej. 'vida_maxima'.
    # Vacío = las fichas no llevan vida en el mapa.
    estadistica_vida: str = ""


class TiradaCrear(BaseModel):
    expresion: str = Field(min_length=1, max_length=120)
    autor: str = Field(default="", max_length=120)
    motivo: str = Field(default="", max_length=200)


class GrupoSalida(BaseModel):
    cantidad: int
    caras: int
    valores: list[int]


class TiradaSalida(BaseModel):
    id: int
    mapa_id: int
    autor: str
    motivo: str
    expresion: str
    grupos: list[GrupoSalida]
    modificador: int
    total: int
    creada_en: str


class Participante(BaseModel):
    token_id: int
    nombre: str
    iniciativa: int


class CombateSalida(BaseModel):
    mapa_id: int
    ronda: int
    indice_turno: int
    orden: list[Participante]
    token_en_turno: int | None = None
