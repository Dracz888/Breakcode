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
