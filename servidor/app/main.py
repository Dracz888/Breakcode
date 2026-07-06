"""Punto de arranque del servidor Breakcode.

Para iniciarlo:  uvicorn app.main:app --reload  (desde la carpeta servidor/)
La pantalla de pruebas interactiva queda en:  http://localhost:8000/docs
"""

from fastapi import FastAPI

from .database import Base, engine
from .routers import personajes, sistemas

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Breakcode — Fábrica de sistemas de rol",
    description=(
        "El cerebro de la plataforma: aquí se crean sistemas de rol completos "
        "(atributos, fórmulas, fichas) sin escribir código. "
        "Esta pantalla (/docs) permite probar todo antes de que exista la interfaz."
    ),
    version="0.1.0",
)

app.include_router(sistemas.router)
app.include_router(personajes.router)


@app.get("/", include_in_schema=False)
def raiz():
    return {
        "mensaje": "Servidor Breakcode funcionando",
        "pantalla_de_pruebas": "/docs",
    }
