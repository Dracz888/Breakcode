"""Rutas del mapa geográfico: el mundo con sus marcadores de lugares."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import obtener_db
from ..marcadores import TIPOS_MARCADOR

router = APIRouter(tags=["Mapa geográfico"])


def _obtener_mapa(db: Session, mapa_id: int) -> models.MapaGeografico:
    mapa = db.get(models.MapaGeografico, mapa_id)
    if mapa is None:
        raise HTTPException(404, "Ese mapa del mundo no existe")
    return mapa


def _obtener_marcador(db: Session, marcador_id: int) -> models.Marcador:
    marcador = db.get(models.Marcador, marcador_id)
    if marcador is None:
        raise HTTPException(404, "Ese marcador no existe")
    return marcador


# ---------- Catálogo de tipos de marcador ----------

@router.get("/tipos-marcador")
def listar_tipos_marcador() -> dict[str, dict]:
    return TIPOS_MARCADOR


# ---------- Mapas geográficos ----------

@router.post(
    "/sistemas/{sistema_id}/mapas-geograficos",
    response_model=schemas.MapaGeograficoSalida,
    status_code=201,
)
def crear_mapa_geografico(
    sistema_id: int,
    datos: schemas.MapaGeograficoCrear,
    db: Session = Depends(obtener_db),
):
    if db.get(models.Sistema, sistema_id) is None:
        raise HTTPException(404, "Ese sistema no existe")
    mapa = models.MapaGeografico(sistema_id=sistema_id, **datos.model_dump())
    db.add(mapa)
    db.commit()
    db.refresh(mapa)
    return mapa


@router.get(
    "/sistemas/{sistema_id}/mapas-geograficos",
    response_model=list[schemas.MapaGeograficoSalida],
)
def listar_mapas_geograficos(sistema_id: int, db: Session = Depends(obtener_db)):
    sistema = db.get(models.Sistema, sistema_id)
    if sistema is None:
        raise HTTPException(404, "Ese sistema no existe")
    return sistema.mapas_geograficos


@router.get(
    "/mapas-geograficos/{mapa_id}", response_model=schemas.MapaGeograficoDetalle
)
def ver_mapa_geografico(mapa_id: int, db: Session = Depends(obtener_db)):
    return _obtener_mapa(db, mapa_id)


@router.put(
    "/mapas-geograficos/{mapa_id}", response_model=schemas.MapaGeograficoSalida
)
def editar_mapa_geografico(
    mapa_id: int,
    datos: schemas.MapaGeograficoEditar,
    db: Session = Depends(obtener_db),
):
    mapa = _obtener_mapa(db, mapa_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(mapa, campo, valor)
    db.commit()
    db.refresh(mapa)
    return mapa


@router.delete("/mapas-geograficos/{mapa_id}", status_code=204)
def borrar_mapa_geografico(mapa_id: int, db: Session = Depends(obtener_db)):
    db.delete(_obtener_mapa(db, mapa_id))
    db.commit()


# ---------- Marcadores (lugares sobre el mapa) ----------

@router.post(
    "/mapas-geograficos/{mapa_id}/marcadores",
    response_model=schemas.MarcadorSalida,
    status_code=201,
)
def crear_marcador(
    mapa_id: int, datos: schemas.MarcadorCrear, db: Session = Depends(obtener_db)
):
    mapa = _obtener_mapa(db, mapa_id)
    if datos.tipo not in TIPOS_MARCADOR:
        raise HTTPException(
            422,
            f"El tipo de marcador '{datos.tipo}' no existe. "
            f"Disponibles: {', '.join(TIPOS_MARCADOR)}",
        )
    marcador = models.Marcador(mapa_id=mapa.id, **datos.model_dump())
    db.add(marcador)
    db.commit()
    db.refresh(marcador)
    return marcador


@router.put("/marcadores/{marcador_id}", response_model=schemas.MarcadorSalida)
def editar_marcador(
    marcador_id: int,
    datos: schemas.MarcadorEditar,
    db: Session = Depends(obtener_db),
):
    marcador = _obtener_marcador(db, marcador_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "tipo" in cambios and cambios["tipo"] not in TIPOS_MARCADOR:
        raise HTTPException(
            422,
            f"El tipo de marcador '{cambios['tipo']}' no existe. "
            f"Disponibles: {', '.join(TIPOS_MARCADOR)}",
        )
    for campo, valor in cambios.items():
        setattr(marcador, campo, valor)
    db.commit()
    db.refresh(marcador)
    return marcador


@router.delete("/marcadores/{marcador_id}", status_code=204)
def borrar_marcador(marcador_id: int, db: Session = Depends(obtener_db)):
    """Al borrar un lugar, los eventos que ocurrían ahí quedan sin lugar (no se borran)."""
    marcador = _obtener_marcador(db, marcador_id)
    for evento in marcador.eventos:
        evento.marcador_id = None
    db.delete(marcador)
    db.commit()
