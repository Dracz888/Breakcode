"""Formatos de entrada y salida de la API (validación con Pydantic).

Las 'claves' (los nombres que se usan dentro de las fórmulas) deben ser
identificadores simples: minúsculas, sin espacios ni acentos, ej. 'voluntad_arcana'.
"""

import re
from datetime import datetime

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
    # Se envía null para quitarle la voz; un id para asignársela. Si no se
    # incluye el campo, la voz queda como estaba.
    voz_id: int | None = None


class PersonajeSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sistema_id: int
    nombre: str
    nivel: int
    es_monstruo: bool
    atributos: dict[str, float]
    voz_id: int | None = None


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


# ---------- Voces (Módulo 5) ----------

class VozCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = ""
    voz_externa_id: str = Field(min_length=1, max_length=120)
    ajustes: dict = {}


class VozEditar(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    voz_externa_id: str | None = None
    ajustes: dict | None = None


class VozSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sistema_id: int
    nombre: str
    descripcion: str
    voz_externa_id: str
    ajustes: dict


class VozSugerida(BaseModel):
    voz_externa_id: str
    nombre: str
    descripcion: str
    genero: str


class EstadoVoces(BaseModel):
    """Cómo está el módulo de voces: con ElevenLabs real o en demostración."""

    hay_api: bool
    sugeridas: list[VozSugerida]
    max_caracteres: int


# ---------- Narración (audio compartido) ----------

class NarracionCrear(BaseModel):
    texto: str = Field(min_length=1)
    # Se narra con la voz de un personaje o con una voz del catálogo directamente.
    personaje_id: int | None = None
    voz_id: int | None = None


class NarracionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sistema_id: int
    personaje_id: int | None
    voz_id: int | None
    nombre_locutor: str
    texto: str
    tipo_mime: str
    es_demostracion: bool
    creada_en: datetime
