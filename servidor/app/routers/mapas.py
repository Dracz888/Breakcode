"""Rutas del mapa de batalla: pintar terreno, colocar y mover fichas."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import obtener_db
from ..terrenos import TERRENO_INICIAL, TERRENOS, bloquea

router = APIRouter(tags=["Mapas de batalla"])


def _obtener_mapa(db: Session, mapa_id: int) -> models.Mapa:
    mapa = db.get(models.Mapa, mapa_id)
    if mapa is None:
        raise HTTPException(404, "Ese mapa no existe")
    return mapa


def _token_a_salida(token: models.Token) -> schemas.TokenSalida:
    return schemas.TokenSalida(
        id=token.id,
        mapa_id=token.mapa_id,
        personaje_id=token.personaje_id,
        nombre=token.personaje.nombre,
        es_monstruo=token.personaje.es_monstruo,
        x=token.x,
        y=token.y,
    )


def _mapa_a_detalle(mapa: models.Mapa) -> schemas.MapaDetalle:
    return schemas.MapaDetalle(
        id=mapa.id,
        sistema_id=mapa.sistema_id,
        nombre=mapa.nombre,
        ancho=mapa.ancho,
        alto=mapa.alto,
        celdas=mapa.celdas,
        tokens=[_token_a_salida(t) for t in mapa.tokens],
    )


def _validar_destino(mapa: models.Mapa, x: int, y: int, ignorar_token: int | None = None):
    """Reglas de ocupación: dentro del mapa, terreno transitable y celda libre."""
    if not (0 <= x < mapa.ancho and 0 <= y < mapa.alto):
        raise HTTPException(422, "Esa celda está fuera del mapa")
    terreno = mapa.celdas[y][x]
    if bloquea(terreno):
        nombre = TERRENOS.get(terreno, {}).get("nombre", terreno)
        raise HTTPException(422, f"No se puede pasar por ahí: hay {nombre.lower()}")
    for token in mapa.tokens:
        if token.id != ignorar_token and token.x == x and token.y == y:
            raise HTTPException(422, f"Esa celda ya está ocupada por {token.personaje.nombre}")


# ---------- Catálogo de terrenos ----------

@router.get("/terrenos")
def listar_terrenos() -> dict[str, dict]:
    return TERRENOS


# ---------- Mapas ----------

@router.post(
    "/sistemas/{sistema_id}/mapas", response_model=schemas.MapaSalida, status_code=201
)
def crear_mapa(sistema_id: int, datos: schemas.MapaCrear, db: Session = Depends(obtener_db)):
    if db.get(models.Sistema, sistema_id) is None:
        raise HTTPException(404, "Ese sistema no existe")
    mapa = models.Mapa(
        sistema_id=sistema_id,
        nombre=datos.nombre,
        ancho=datos.ancho,
        alto=datos.alto,
        celdas=[[TERRENO_INICIAL] * datos.ancho for _ in range(datos.alto)],
    )
    db.add(mapa)
    db.commit()
    db.refresh(mapa)
    return mapa


@router.get("/sistemas/{sistema_id}/mapas", response_model=list[schemas.MapaSalida])
def listar_mapas(sistema_id: int, db: Session = Depends(obtener_db)):
    sistema = db.get(models.Sistema, sistema_id)
    if sistema is None:
        raise HTTPException(404, "Ese sistema no existe")
    return sistema.mapas


@router.get("/mapas/{mapa_id}", response_model=schemas.MapaDetalle)
def ver_mapa(mapa_id: int, db: Session = Depends(obtener_db)):
    return _mapa_a_detalle(_obtener_mapa(db, mapa_id))


@router.delete("/mapas/{mapa_id}", status_code=204)
def borrar_mapa(mapa_id: int, db: Session = Depends(obtener_db)):
    db.delete(_obtener_mapa(db, mapa_id))
    db.commit()


@router.put("/mapas/{mapa_id}/celdas", response_model=schemas.MapaDetalle)
def pintar_celdas(
    mapa_id: int, datos: schemas.PintarCeldas, db: Session = Depends(obtener_db)
):
    """Pinta un lote de celdas (el pincel del editor envía varias de una vez)."""
    mapa = _obtener_mapa(db, mapa_id)
    celdas = [fila[:] for fila in mapa.celdas]
    for cambio in datos.cambios:
        if cambio.terreno not in TERRENOS:
            raise HTTPException(
                422,
                f"El terreno '{cambio.terreno}' no existe. "
                f"Disponibles: {', '.join(TERRENOS)}",
            )
        if not (0 <= cambio.x < mapa.ancho and 0 <= cambio.y < mapa.alto):
            raise HTTPException(422, "Hay una celda fuera del mapa en los cambios")
        celdas[cambio.y][cambio.x] = cambio.terreno
    mapa.celdas = celdas
    db.commit()
    db.refresh(mapa)
    return _mapa_a_detalle(mapa)


# ---------- Fichas sobre el mapa (tokens) ----------

@router.post("/mapas/{mapa_id}/tokens", response_model=schemas.TokenSalida, status_code=201)
def colocar_token(
    mapa_id: int, datos: schemas.TokenColocar, db: Session = Depends(obtener_db)
):
    mapa = _obtener_mapa(db, mapa_id)
    personaje = db.get(models.Personaje, datos.personaje_id)
    if personaje is None:
        raise HTTPException(404, "Esa ficha no existe")
    if personaje.sistema_id != mapa.sistema_id:
        raise HTTPException(422, "Esa ficha pertenece a otro sistema")
    if any(t.personaje_id == personaje.id for t in mapa.tokens):
        raise HTTPException(409, f"{personaje.nombre} ya está en este mapa")
    _validar_destino(mapa, datos.x, datos.y)

    token = models.Token(mapa_id=mapa.id, personaje_id=personaje.id, x=datos.x, y=datos.y)
    db.add(token)
    db.commit()
    db.refresh(token)
    return _token_a_salida(token)


@router.put("/tokens/{token_id}", response_model=schemas.TokenSalida)
def mover_token(token_id: int, datos: schemas.TokenMover, db: Session = Depends(obtener_db)):
    token = db.get(models.Token, token_id)
    if token is None:
        raise HTTPException(404, "Esa ficha no está en el mapa")
    _validar_destino(token.mapa, datos.x, datos.y, ignorar_token=token.id)
    token.x = datos.x
    token.y = datos.y
    db.commit()
    db.refresh(token)
    return _token_a_salida(token)


@router.delete("/tokens/{token_id}", status_code=204)
def quitar_token(token_id: int, db: Session = Depends(obtener_db)):
    token = db.get(models.Token, token_id)
    if token is None:
        raise HTTPException(404, "Esa ficha no está en el mapa")
    db.delete(token)
    db.commit()
