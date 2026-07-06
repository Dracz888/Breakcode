"""Conexión a la base de datos.

En desarrollo se usa SQLite (un archivo local, cero configuración).
Al publicar en internet se cambiará a PostgreSQL con solo ajustar la URL.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

URL_BASE_DE_DATOS = os.environ.get("DATABASE_URL", "sqlite:///./breakcode.db")

engine = create_engine(
    URL_BASE_DE_DATOS,
    connect_args={"check_same_thread": False} if URL_BASE_DE_DATOS.startswith("sqlite") else {},
)

SesionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def obtener_db():
    """Entrega una sesión de base de datos por petición y la cierra al terminar."""
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()
