"""Tablas de la base de datos (fase 1: la fábrica de sistemas).

Un Sistema es un juego de reglas completo diseñado por el usuario.
Sus atributos y estadísticas derivadas son definiciones que el usuario
crea desde el editor — el programa no trae ninguna regla fija.

Desde la fase 7 un Sistema también contiene el mundo donde se juega:
mapas geográficos con marcadores (ciudades, mazmorras…) y campañas con
sus arcos y eventos, que juntos reconstruyen la línea de tiempo de la trama.
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
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
    mapas: Mapped[list["Mapa"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )
    mapas_geograficos: Mapped[list["MapaGeografico"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )
    campanas: Mapped[list["Campana"]] = relationship(
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
    eventos: Mapped[list["Evento"]] = relationship(
        secondary="evento_personajes", back_populates="personajes"
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


class Token(Base):
    """La presencia de una ficha sobre una celda del mapa."""

    __tablename__ = "tokens"
    __table_args__ = (UniqueConstraint("mapa_id", "personaje_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mapa_id: Mapped[int] = mapped_column(ForeignKey("mapas.id"))
    personaje_id: Mapped[int] = mapped_column(ForeignKey("personajes.id"))
    x: Mapped[int] = mapped_column(Integer)
    y: Mapped[int] = mapped_column(Integer)

    mapa: Mapped[Mapa] = relationship(back_populates="tokens")
    personaje: Mapped[Personaje] = relationship(back_populates="tokens")


# ---------- Mapa geográfico (el mundo) ----------


class MapaGeografico(Base):
    """El mapa del mundo: una imagen de fondo con marcadores de lugares.

    A diferencia del mapa de batalla (una cuadrícula), aquí los marcadores se
    colocan en coordenadas relativas (x, y entre 0 y 1) para que funcionen sea
    cual sea el tamaño real de la imagen de fondo.
    """

    __tablename__ = "mapas_geograficos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema_id: Mapped[int] = mapped_column(ForeignKey("sistemas.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    imagen_url: Mapped[str] = mapped_column(Text, default="")

    sistema: Mapped[Sistema] = relationship(back_populates="mapas_geograficos")
    marcadores: Mapped[list["Marcador"]] = relationship(
        back_populates="mapa", cascade="all, delete-orphan"
    )


class Marcador(Base):
    """Un lugar señalado sobre el mapa del mundo (ciudad, mazmorra, punto…)."""

    __tablename__ = "marcadores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mapa_id: Mapped[int] = mapped_column(ForeignKey("mapas_geograficos.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(40), default="punto")
    descripcion: Mapped[str] = mapped_column(Text, default="")
    x: Mapped[float] = mapped_column(Float)  # 0..1 relativo al ancho de la imagen
    y: Mapped[float] = mapped_column(Float)  # 0..1 relativo al alto de la imagen

    mapa: Mapped[MapaGeografico] = relationship(back_populates="marcadores")
    eventos: Mapped[list["Evento"]] = relationship(back_populates="marcador")


# ---------- Campañas: arcos y eventos (la historia) ----------

# Un evento puede involucrar a varios personajes y un personaje aparece en
# varios eventos: relación de muchos-a-muchos entre eventos y fichas.
evento_personajes = Table(
    "evento_personajes",
    Base.metadata,
    Column("evento_id", ForeignKey("eventos.id"), primary_key=True),
    Column("personaje_id", ForeignKey("personajes.id"), primary_key=True),
)


class Campana(Base):
    """Una campaña: la historia que se juega dentro de un sistema."""

    __tablename__ = "campanas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema_id: Mapped[int] = mapped_column(ForeignKey("sistemas.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text, default="")

    sistema: Mapped[Sistema] = relationship(back_populates="campanas")
    arcos: Mapped[list["Arco"]] = relationship(
        back_populates="campana",
        cascade="all, delete-orphan",
        order_by="Arco.orden",
    )


class Arco(Base):
    """Un arco o capítulo dentro de una campaña; agrupa eventos."""

    __tablename__ = "arcos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campana_id: Mapped[int] = mapped_column(ForeignKey("campanas.id"))
    titulo: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    orden: Mapped[int] = mapped_column(Integer, default=0)

    campana: Mapped[Campana] = relationship(back_populates="arcos")
    eventos: Mapped[list["Evento"]] = relationship(
        back_populates="arco",
        cascade="all, delete-orphan",
        order_by="Evento.orden",
    )


class Evento(Base):
    """Un evento de la trama: qué pasó, cuándo, con quién y en qué lugar."""

    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    arco_id: Mapped[int] = mapped_column(ForeignKey("arcos.id"))
    titulo: Mapped[str] = mapped_column(String(160))
    fecha: Mapped[str] = mapped_column(String(120), default="")  # fecha del mundo, texto libre
    descripcion: Mapped[str] = mapped_column(Text, default="")
    orden: Mapped[int] = mapped_column(Integer, default=0)
    marcador_id: Mapped[int | None] = mapped_column(
        ForeignKey("marcadores.id"), nullable=True
    )

    arco: Mapped[Arco] = relationship(back_populates="eventos")
    marcador: Mapped[Marcador | None] = relationship(back_populates="eventos")
    personajes: Mapped[list["Personaje"]] = relationship(
        secondary=evento_personajes, back_populates="eventos"
    )
