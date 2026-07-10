"""Tablas de la base de datos (fase 1: la fábrica de sistemas).

Un Sistema es un juego de reglas completo diseñado por el usuario.
Sus atributos y estadísticas derivadas son definiciones que el usuario
crea desde el editor — el programa no trae ninguna regla fija.

Desde la fase 7 un Sistema también contiene el mundo donde se juega:
mapas geográficos con marcadores (ciudades, mazmorras…) y campañas con
sus arcos y eventos, que juntos reconstruyen la línea de tiempo de la trama.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
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
    # Notas privadas del DJ: no las ve el jugador. (fase 9 — refinamiento)
    notas: Mapped[str] = mapped_column(Text, default="")

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
    # La voz con la que habla este personaje (opcional; se elige del catálogo).
    voz_id: Mapped[int | None] = mapped_column(
        ForeignKey("voces.id", ondelete="SET NULL"), nullable=True
    )

    sistema: Mapped[Sistema] = relationship(back_populates="personajes")
    voz: Mapped["Voz | None"] = relationship(back_populates="personajes")
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
    # Niebla de guerra: niebla[y][x] = True si esa celda está oculta al jugador.
    # (fase 9 — refinamiento). Nace vacía: el DJ decide qué esconde.
    niebla: Mapped[list] = mapped_column(JSON, default=list)

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
