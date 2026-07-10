"""Rutas de campañas: la historia como campaña → arcos → eventos.

Con solo registrar eventos (qué pasó, cuándo, con quién y dónde), la campaña
reconstruye su línea de tiempo: los arcos en orden, y dentro de cada uno sus
eventos en orden. De ahí salen el historial de cada personaje y el recorrido
del grupo por el mapa.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import obtener_db

router = APIRouter(tags=["Campañas"])


# ---------- Serialización ----------

def _evento_a_salida(evento: models.Evento) -> schemas.EventoSalida:
    return schemas.EventoSalida(
        id=evento.id,
        arco_id=evento.arco_id,
        titulo=evento.titulo,
        fecha=evento.fecha,
        descripcion=evento.descripcion,
        orden=evento.orden,
        marcador=(
            schemas.MarcadorBreve(
                id=evento.marcador.id,
                nombre=evento.marcador.nombre,
                tipo=evento.marcador.tipo,
            )
            if evento.marcador
            else None
        ),
        personajes=[
            schemas.PersonajeBreve(id=p.id, nombre=p.nombre, es_monstruo=p.es_monstruo)
            for p in evento.personajes
        ],
    )


def _arco_a_salida(arco: models.Arco) -> schemas.ArcoSalida:
    return schemas.ArcoSalida(
        id=arco.id,
        campana_id=arco.campana_id,
        titulo=arco.titulo,
        descripcion=arco.descripcion,
        orden=arco.orden,
        eventos=[_evento_a_salida(e) for e in arco.eventos],
    )


def _campana_a_detalle(campana: models.Campana) -> schemas.CampanaDetalle:
    return schemas.CampanaDetalle(
        id=campana.id,
        sistema_id=campana.sistema_id,
        nombre=campana.nombre,
        descripcion=campana.descripcion,
        arcos=[_arco_a_salida(a) for a in campana.arcos],
    )


# ---------- Ayudas ----------

def _obtener_campana(db: Session, campana_id: int) -> models.Campana:
    campana = db.get(models.Campana, campana_id)
    if campana is None:
        raise HTTPException(404, "Esa campaña no existe")
    return campana


def _obtener_arco(db: Session, arco_id: int) -> models.Arco:
    arco = db.get(models.Arco, arco_id)
    if arco is None:
        raise HTTPException(404, "Ese arco no existe")
    return arco


def _obtener_evento(db: Session, evento_id: int) -> models.Evento:
    evento = db.get(models.Evento, evento_id)
    if evento is None:
        raise HTTPException(404, "Ese evento no existe")
    return evento


def _resolver_personajes(
    db: Session, sistema_id: int, ids: list[int]
) -> list[models.Personaje]:
    """Carga las fichas indicadas y comprueba que pertenezcan al mismo sistema."""
    personajes: list[models.Personaje] = []
    for pid in dict.fromkeys(ids):  # sin duplicados, conservando el orden
        personaje = db.get(models.Personaje, pid)
        if personaje is None:
            raise HTTPException(422, f"La ficha con id {pid} no existe")
        if personaje.sistema_id != sistema_id:
            raise HTTPException(
                422, f"La ficha '{personaje.nombre}' pertenece a otro sistema"
            )
        personajes.append(personaje)
    return personajes


def _validar_marcador(db: Session, sistema_id: int, marcador_id: int | None) -> None:
    if marcador_id is None:
        return
    marcador = db.get(models.Marcador, marcador_id)
    if marcador is None:
        raise HTTPException(422, "Ese lugar (marcador) no existe")
    if marcador.mapa.sistema_id != sistema_id:
        raise HTTPException(422, "Ese lugar pertenece a otro sistema")


# ---------- Campañas ----------

@router.post(
    "/sistemas/{sistema_id}/campanas",
    response_model=schemas.CampanaSalida,
    status_code=201,
)
def crear_campana(
    sistema_id: int, datos: schemas.CampanaCrear, db: Session = Depends(obtener_db)
):
    if db.get(models.Sistema, sistema_id) is None:
        raise HTTPException(404, "Ese sistema no existe")
    campana = models.Campana(sistema_id=sistema_id, **datos.model_dump())
    db.add(campana)
    db.commit()
    db.refresh(campana)
    return campana


@router.get(
    "/sistemas/{sistema_id}/campanas", response_model=list[schemas.CampanaSalida]
)
def listar_campanas(sistema_id: int, db: Session = Depends(obtener_db)):
    sistema = db.get(models.Sistema, sistema_id)
    if sistema is None:
        raise HTTPException(404, "Ese sistema no existe")
    return sistema.campanas


@router.get("/campanas/{campana_id}", response_model=schemas.CampanaDetalle)
def ver_campana(campana_id: int, db: Session = Depends(obtener_db)):
    return _campana_a_detalle(_obtener_campana(db, campana_id))


@router.put("/campanas/{campana_id}", response_model=schemas.CampanaSalida)
def editar_campana(
    campana_id: int, datos: schemas.CampanaEditar, db: Session = Depends(obtener_db)
):
    campana = _obtener_campana(db, campana_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(campana, campo, valor)
    db.commit()
    db.refresh(campana)
    return campana


@router.delete("/campanas/{campana_id}", status_code=204)
def borrar_campana(campana_id: int, db: Session = Depends(obtener_db)):
    db.delete(_obtener_campana(db, campana_id))
    db.commit()


# ---------- Arcos ----------

@router.post(
    "/campanas/{campana_id}/arcos", response_model=schemas.ArcoSalida, status_code=201
)
def crear_arco(
    campana_id: int, datos: schemas.ArcoCrear, db: Session = Depends(obtener_db)
):
    campana = _obtener_campana(db, campana_id)
    orden = max((a.orden for a in campana.arcos), default=-1) + 1
    arco = models.Arco(campana_id=campana.id, orden=orden, **datos.model_dump())
    db.add(arco)
    db.commit()
    db.refresh(arco)
    return _arco_a_salida(arco)


@router.put("/arcos/{arco_id}", response_model=schemas.ArcoSalida)
def editar_arco(
    arco_id: int, datos: schemas.ArcoEditar, db: Session = Depends(obtener_db)
):
    arco = _obtener_arco(db, arco_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(arco, campo, valor)
    db.commit()
    db.refresh(arco)
    return _arco_a_salida(arco)


@router.delete("/arcos/{arco_id}", status_code=204)
def borrar_arco(arco_id: int, db: Session = Depends(obtener_db)):
    db.delete(_obtener_arco(db, arco_id))
    db.commit()


# ---------- Eventos ----------

@router.post(
    "/arcos/{arco_id}/eventos", response_model=schemas.EventoSalida, status_code=201
)
def crear_evento(
    arco_id: int, datos: schemas.EventoCrear, db: Session = Depends(obtener_db)
):
    arco = _obtener_arco(db, arco_id)
    sistema_id = arco.campana.sistema_id
    _validar_marcador(db, sistema_id, datos.marcador_id)
    personajes = _resolver_personajes(db, sistema_id, datos.personajes)

    orden = max((e.orden for e in arco.eventos), default=-1) + 1
    evento = models.Evento(
        arco_id=arco.id,
        titulo=datos.titulo,
        fecha=datos.fecha,
        descripcion=datos.descripcion,
        marcador_id=datos.marcador_id,
        orden=orden,
        personajes=personajes,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return _evento_a_salida(evento)


@router.put("/eventos/{evento_id}", response_model=schemas.EventoSalida)
def editar_evento(
    evento_id: int, datos: schemas.EventoEditar, db: Session = Depends(obtener_db)
):
    evento = _obtener_evento(db, evento_id)
    sistema_id = evento.arco.campana.sistema_id
    cambios = datos.model_dump(exclude_unset=True)

    if "marcador_id" in cambios:
        _validar_marcador(db, sistema_id, cambios["marcador_id"])
    if "personajes" in cambios:
        evento.personajes = _resolver_personajes(db, sistema_id, cambios.pop("personajes"))
    for campo, valor in cambios.items():
        setattr(evento, campo, valor)
    db.commit()
    db.refresh(evento)
    return _evento_a_salida(evento)


@router.delete("/eventos/{evento_id}", status_code=204)
def borrar_evento(evento_id: int, db: Session = Depends(obtener_db)):
    db.delete(_obtener_evento(db, evento_id))
    db.commit()
