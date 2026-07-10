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


class SistemaEditar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = None
    notas: str | None = None


class SistemaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str
    notas: str = ""


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
    vida_actual: int | None = None
    vida_maxima: int | None = None


class MapaDetalle(MapaSalida):
    celdas: list[list[str]]
    niebla: list[list[bool]]
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


# ---------- Mapa geográfico (el mundo) ----------

class MapaGeograficoCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    imagen_url: str = ""


class MapaGeograficoEditar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    imagen_url: str | None = None


class MapaGeograficoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sistema_id: int
    nombre: str
    imagen_url: str


class MarcadorCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    tipo: str = "punto"
    descripcion: str = ""
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class MarcadorEditar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    tipo: str | None = None
    descripcion: str | None = None
    x: float | None = Field(default=None, ge=0, le=1)
    y: float | None = Field(default=None, ge=0, le=1)


class MarcadorSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mapa_id: int
    nombre: str
    tipo: str
    descripcion: str
    x: float
    y: float


class MapaGeograficoDetalle(MapaGeograficoSalida):
    marcadores: list[MarcadorSalida]


# ---------- Campañas: arcos y eventos ----------

class CampanaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = ""


class CampanaEditar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = None


class CampanaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sistema_id: int
    nombre: str
    descripcion: str


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


# ---------- Ambientes de sonido (Módulo 5.7) ----------

class AmbienteIntegrado(BaseModel):
    clave: str
    nombre: str
    categoria: str
    icono: str
    descripcion: str
    bucle: bool


class AmbienteSalida(BaseModel):
    """Un ambiente subido por el DJ (sin los bytes de audio, que van aparte)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sistema_id: int
    nombre: str
    categoria: str
    icono: str
    tipo_mime: str
    bucle: bool


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


class ArcoCrear(BaseModel):
    titulo: str = Field(min_length=1, max_length=160)
    descripcion: str = ""


class ArcoEditar(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=160)
    descripcion: str | None = None
    orden: int | None = None


class EventoCrear(BaseModel):
    titulo: str = Field(min_length=1, max_length=160)
    fecha: str = ""
    descripcion: str = ""
    marcador_id: int | None = None
    personajes: list[int] = []


class EventoEditar(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=160)
    fecha: str | None = None
    descripcion: str | None = None
    orden: int | None = None
    marcador_id: int | None = None
    personajes: list[int] | None = None


class PersonajeBreve(BaseModel):
    """Ficha resumida para listar los involucrados en un evento."""

    id: int
    nombre: str
    es_monstruo: bool


class MarcadorBreve(BaseModel):
    id: int
    nombre: str
    tipo: str


class EventoSalida(BaseModel):
    id: int
    arco_id: int
    titulo: str
    fecha: str
    descripcion: str
    orden: int
    marcador: MarcadorBreve | None
    personajes: list[PersonajeBreve]


class ArcoSalida(BaseModel):
    id: int
    campana_id: int
    titulo: str
    descripcion: str
    orden: int
    eventos: list[EventoSalida]


class CampanaDetalle(CampanaSalida):
    """La campaña completa: sus arcos y eventos en orden (la línea de tiempo)."""

    arcos: list[ArcoSalida]


# ---------- Niebla de guerra (fase 9) ----------

class CambioDeNiebla(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    oculta: bool  # True = tapar la celda; False = revelarla al jugador


class PintarNiebla(BaseModel):
    cambios: list[CambioDeNiebla] = Field(min_length=1, max_length=6400)


# ---------- Exportar / importar sistemas (fase 9) ----------

class MapaExportado(BaseModel):
    nombre: str
    ancho: int
    alto: int
    celdas: list[list[str]]
    niebla: list[list[bool]] = []


class PersonajeExportado(BaseModel):
    nombre: str
    nivel: int = 1
    es_monstruo: bool = False
    atributos: dict[str, float] = {}


class SistemaExportado(BaseModel):
    """El sistema completo en un archivo: reglas, fichas y mapas.

    Sirve de respaldo y para compartir un sistema con otra mesa. Los tokens
    (la posición de una ficha sobre un mapa) no se exportan a propósito: son
    estado de partida, no parte del diseño del sistema.
    """

    formato: str = "breakcode/sistema"
    version: int = 1
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = ""
    notas: str = ""
    atributos: list[AtributoSalida] = []
    estadisticas: list[EstadisticaSalida] = []
    personajes: list[PersonajeExportado] = []
    mapas: list[MapaExportado] = []
