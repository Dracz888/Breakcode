"""Tablas de la base de datos (fase 1: la fábrica de sistemas).

Un Sistema es un juego de reglas completo diseñado por el usuario.
Sus atributos y estadísticas derivadas son definiciones que el usuario
crea desde el editor — el programa no trae ninguna regla fija.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class Sistema(Base):
    __tablename__ = "sistemas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    # Ajustes del combate por turnos, editables por sistema (ver schemas.ConfigCombate):
    # de qué atributo/fórmula sale la iniciativa, qué dado la acompaña y qué
    # estadística marca la vida máxima. Vacío = valores por defecto sensatos.
    config_combate: Mapped[dict] = mapped_column(JSON, default=dict)

    atributos: Mapped[list["DefinicionAtributo"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )
    estadisticas: Mapped[list["DefinicionEstadistica"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )
    personajes: Mapped[list["Personaje"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )
    mapas: Mapped[list["Mapa"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )


class DefinicionAtributo(Base):
    """Un atributo base del sistema (ej. fuerza, destreza, voluntad_arcana)."""

    __tablename__ = "definiciones_atributo"
    __table_args__ = (UniqueConstraint("sistema_id", "clave"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema_id: Mapped[int] = mapped_column(ForeignKey("sistemas.id"))
    clave: Mapped[str] = mapped_column(String(60))  # nombre usable en fórmulas
    nombre: Mapped[str] = mapped_column(String(120))
    categoria: Mapped[str] = mapped_column(String(60), default="")
    descripcion: Mapped[str] = mapped_column(Text, default="")
    valor_inicial: Mapped[int] = mapped_column(Integer, default=0)

    sistema: Mapped[Sistema] = relationship(back_populates="atributos")


class DefinicionEstadistica(Base):
    """Una estadística derivada con su fórmula (ej. vida_maxima = fuerza*10+nivel*5)."""

    __tablename__ = "definiciones_estadistica"
    __table_args__ = (UniqueConstraint("sistema_id", "clave"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema_id: Mapped[int] = mapped_column(ForeignKey("sistemas.id"))
    clave: Mapped[str] = mapped_column(String(60))
    nombre: Mapped[str] = mapped_column(String(120))
    formula: Mapped[str] = mapped_column(Text)
    descripcion: Mapped[str] = mapped_column(Text, default="")

    sistema: Mapped[Sistema] = relationship(back_populates="estadisticas")


class Personaje(Base):
    """Una ficha (personaje o monstruo) que vive dentro de un sistema."""

    __tablename__ = "personajes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema_id: Mapped[int] = mapped_column(ForeignKey("sistemas.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    nivel: Mapped[int] = mapped_column(Integer, default=1)
    es_monstruo: Mapped[bool] = mapped_column(Boolean, default=False)
    atributos: Mapped[dict] = mapped_column(JSON, default=dict)  # {clave: valor}

    sistema: Mapped[Sistema] = relationship(back_populates="personajes")
    tokens: Mapped[list["Token"]] = relationship(
        back_populates="personaje", cascade="all, delete-orphan"
    )


class Mapa(Base):
    """Un mapa de batalla: una cuadrícula de terrenos pintada por el usuario."""

    __tablename__ = "mapas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema_id: Mapped[int] = mapped_column(ForeignKey("sistemas.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    ancho: Mapped[int] = mapped_column(Integer)
    alto: Mapped[int] = mapped_column(Integer)
    celdas: Mapped[list] = mapped_column(JSON)  # celdas[y][x] = clave de terreno

    sistema: Mapped[Sistema] = relationship(back_populates="mapas")
    tokens: Mapped[list["Token"]] = relationship(
        back_populates="mapa", cascade="all, delete-orphan"
    )
    tiradas: Mapped[list["TiradaDado"]] = relationship(
        back_populates="mapa", cascade="all, delete-orphan"
    )
    combate: Mapped["Combate | None"] = relationship(
        back_populates="mapa", cascade="all, delete-orphan", uselist=False
    )


class Token(Base):
    """La presencia de una ficha sobre una celda del mapa.

    La vida es del token, no de la ficha: las heridas pertenecen a esta batalla
    (un mismo monstruo puede aparecer sano en otro mapa). 'vida_actual' es None
    cuando el sistema no define una estadística de vida.
    """

    __tablename__ = "tokens"
    __table_args__ = (UniqueConstraint("mapa_id", "personaje_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mapa_id: Mapped[int] = mapped_column(ForeignKey("mapas.id"))
    personaje_id: Mapped[int] = mapped_column(ForeignKey("personajes.id"))
    x: Mapped[int] = mapped_column(Integer)
    y: Mapped[int] = mapped_column(Integer)
    vida_actual: Mapped[int | None] = mapped_column(Integer, nullable=True)

    mapa: Mapped[Mapa] = relationship(back_populates="tokens")
    personaje: Mapped[Personaje] = relationship(back_populates="tokens")


class TiradaDado(Base):
    """Una tirada de dados registrada en el historial compartido de un mapa."""

    __tablename__ = "tiradas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mapa_id: Mapped[int] = mapped_column(ForeignKey("mapas.id"))
    autor: Mapped[str] = mapped_column(String(120), default="")
    motivo: Mapped[str] = mapped_column(String(200), default="")
    expresion: Mapped[str] = mapped_column(String(120))
    grupos: Mapped[list] = mapped_column(JSON)  # [{cantidad, caras, valores:[...]}]
    modificador: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer)
    creada_en: Mapped[datetime] = mapped_column(DateTime, default=_ahora)

    mapa: Mapped[Mapa] = relationship(back_populates="tiradas")


class Combate(Base):
    """El seguimiento de un combate por turnos sobre un mapa (uno por mapa).

    'orden' es la lista de participantes ya ordenada por iniciativa:
    [{token_id, nombre, iniciativa}]. El turno actual es orden[indice_turno].
    """

    __tablename__ = "combates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mapa_id: Mapped[int] = mapped_column(ForeignKey("mapas.id"), unique=True)
    ronda: Mapped[int] = mapped_column(Integer, default=1)
    indice_turno: Mapped[int] = mapped_column(Integer, default=0)
    orden: Mapped[list] = mapped_column(JSON, default=list)

    mapa: Mapped[Mapa] = relationship(back_populates="combate")
