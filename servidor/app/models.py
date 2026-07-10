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
    LargeBinary,
    String,
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
    voces: Mapped[list["Voz"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )
    narraciones: Mapped[list["Narracion"]] = relationship(
        back_populates="sistema", cascade="all, delete-orphan"
    )
    ambientes: Mapped[list["Ambiente"]] = relationship(
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
    # La voz con la que habla este personaje (opcional; se elige del catálogo).
    voz_id: Mapped[int | None] = mapped_column(
        ForeignKey("voces.id", ondelete="SET NULL"), nullable=True
    )

    sistema: Mapped[Sistema] = relationship(back_populates="personajes")
    voz: Mapped["Voz | None"] = relationship(back_populates="personajes")
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


class Voz(Base):
    """Una voz del catálogo del sistema (Módulo 5).

    Guarda la descripción escrita ("ogro grave y monstruoso") y el identificador
    de la voz en ElevenLabs. Cada personaje puede tener asignada una de estas.
    """

    __tablename__ = "voces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema_id: Mapped[int] = mapped_column(ForeignKey("sistemas.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    voz_externa_id: Mapped[str] = mapped_column(String(120))  # id de voz en ElevenLabs
    ajustes: Mapped[dict] = mapped_column(JSON, default=dict)  # estabilidad, similitud…

    sistema: Mapped[Sistema] = relationship(back_populates="voces")
    personajes: Mapped[list["Personaje"]] = relationship(back_populates="voz")


class Narracion(Base):
    """Una línea narrada con su audio, guardada como historial compartido.

    Es la pieza "audio para todos": el audio queda registrado en el sistema para
    que cualquiera en la mesa pueda volver a reproducirlo. El audio se guarda en
    la propia base de datos (clips cortos), sin archivos sueltos que administrar.
    """

    __tablename__ = "narraciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema_id: Mapped[int] = mapped_column(ForeignKey("sistemas.id"))
    personaje_id: Mapped[int | None] = mapped_column(
        ForeignKey("personajes.id", ondelete="SET NULL"), nullable=True
    )
    voz_id: Mapped[int | None] = mapped_column(
        ForeignKey("voces.id", ondelete="SET NULL"), nullable=True
    )
    nombre_locutor: Mapped[str] = mapped_column(String(120), default="")
    texto: Mapped[str] = mapped_column(Text)
    audio: Mapped[bytes] = mapped_column(LargeBinary)
    tipo_mime: Mapped[str] = mapped_column(String(40), default="audio/mpeg")
    es_demostracion: Mapped[bool] = mapped_column(Boolean, default=False)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    sistema: Mapped[Sistema] = relationship(back_populates="narraciones")


class Ambiente(Base):
    """Un sonido de fondo subido por el DJ a la mesa de sonido (Módulo 5.7).

    Los ambientes integrados se sintetizan en el servidor y no viven aquí; esta
    tabla guarda solo las grabaciones propias que el DJ sube (una taberna real,
    una pista de música…). El audio se guarda en la base de datos.
    """

    __tablename__ = "ambientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sistema_id: Mapped[int] = mapped_column(ForeignKey("sistemas.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    categoria: Mapped[str] = mapped_column(String(60), default="Propios")
    icono: Mapped[str] = mapped_column(String(8), default="🎵")
    audio: Mapped[bytes] = mapped_column(LargeBinary)
    tipo_mime: Mapped[str] = mapped_column(String(40), default="audio/mpeg")
    bucle: Mapped[bool] = mapped_column(Boolean, default=True)

    sistema: Mapped[Sistema] = relationship(back_populates="ambientes")
