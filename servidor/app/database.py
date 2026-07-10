"""Conexión a la base de datos.

En desarrollo se usa SQLite (un archivo local, cero configuración).
Al publicar en internet se cambiará a PostgreSQL con solo ajustar la URL.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def _normalizar_url(url: str) -> str:
    """Deja la URL lista para SQLAlchemy.

    Los servicios de hosting (Render, Railway, Heroku) entregan la dirección de
    PostgreSQL como 'postgres://...'; SQLAlchemy necesita el prefijo del driver
    ('postgresql+psycopg://'). Aquí se traduce sola, así en producción basta con
    pegar la URL que da el hosting en la variable DATABASE_URL.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


URL_BASE_DE_DATOS = _normalizar_url(os.environ.get("DATABASE_URL", "sqlite:///./breakcode.db"))

engine = create_engine(
    URL_BASE_DE_DATOS,
    connect_args={"check_same_thread": False} if URL_BASE_DE_DATOS.startswith("sqlite") else {},
    pool_pre_ping=not URL_BASE_DE_DATOS.startswith("sqlite"),  # reconecta si la BD cerró la conexión
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
