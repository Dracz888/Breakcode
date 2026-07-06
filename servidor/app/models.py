"""Tablas de la base de datos (fase 1: la fábrica de sistemas).

Un Sistema es un juego de reglas completo diseñado por el usuario.
Sus atributos y estadísticas derivadas son definiciones que el usuario
crea desde el editor — el programa no trae ninguna regla fija.
"""

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Sistema(Base):
    __tablename__ = "sistemas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text, default="")

    atributos: Mapped[list["DefinicionAtributo"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )
    estadisticas: Mapped[list["DefinicionEstadistica"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )
    personajes: Mapped[list["Personaje"]] = relationship(
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
