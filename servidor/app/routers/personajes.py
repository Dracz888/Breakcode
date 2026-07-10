"""Rutas de fichas: personajes y monstruos usan el mismo motor."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, motor, schemas
from ..database import obtener_db

router = APIRouter(tags=["Fichas"])


def _con_estadisticas(personaje: models.Personaje) -> schemas.PersonajeConEstadisticas:
    """Arma la ficha completa: las estadísticas se calculan siempre al momento,
    así cualquier cambio en las fórmulas del sistema se refleja de inmediato."""
    valores, errores = motor.estadisticas_de(personaje)
    return schemas.PersonajeConEstadisticas(
        id=personaje.id,
        sistema_id=personaje.sistema_id,
        nombre=personaje.nombre,
        nivel=personaje.nivel,
        es_monstruo=personaje.es_monstruo,
        atributos=personaje.atributos,
        voz_id=personaje.voz_id,
        estadisticas=valores,
        errores_de_formulas=errores,
    )


def _validar_atributos(sistema: models.Sistema, atributos: dict[str, float]) -> None:
    claves_del_sistema = {a.clave for a in sistema.atributos}
    desconocidos = set(atributos) - claves_del_sistema
    if desconocidos:
        lista = ", ".join(f"'{c}'" for c in sorted(desconocidos))
        raise HTTPException(
            422,
            f"Estos atributos no existen en el sistema: {lista}. "
            f"Atributos del sistema: {', '.join(sorted(claves_del_sistema))}",
        )


@router.post(
    "/sistemas/{sistema_id}/personajes",
    response_model=schemas.PersonajeConEstadisticas,
    status_code=201,
)
def crear_personaje(
    sistema_id: int, datos: schemas.PersonajeCrear, db: Session = Depends(obtener_db)
):
    sistema = db.get(models.Sistema, sistema_id)
    if sistema is None:
        raise HTTPException(404, "Ese sistema no existe")
    _validar_atributos(sistema, datos.atributos)

    # Los atributos no indicados arrancan con el valor inicial que define el sistema.
    valores = {a.clave: a.valor_inicial for a in sistema.atributos}
    valores.update(datos.atributos)

    personaje = models.Personaje(
        sistema_id=sistema.id,
        nombre=datos.nombre,
        nivel=datos.nivel,
        es_monstruo=datos.es_monstruo,
        atributos=valores,
    )
    db.add(personaje)
    db.commit()
    db.refresh(personaje)
    return _con_estadisticas(personaje)


@router.get(
    "/sistemas/{sistema_id}/personajes",
    response_model=list[schemas.PersonajeConEstadisticas],
)
def listar_personajes(sistema_id: int, db: Session = Depends(obtener_db)):
    sistema = db.get(models.Sistema, sistema_id)
    if sistema is None:
        raise HTTPException(404, "Ese sistema no existe")
    return [_con_estadisticas(p) for p in sistema.personajes]


@router.get("/personajes/{personaje_id}", response_model=schemas.PersonajeConEstadisticas)
def ver_personaje(personaje_id: int, db: Session = Depends(obtener_db)):
    personaje = db.get(models.Personaje, personaje_id)
    if personaje is None:
        raise HTTPException(404, "Esa ficha no existe")
    return _con_estadisticas(personaje)


@router.put("/personajes/{personaje_id}", response_model=schemas.PersonajeConEstadisticas)
def editar_personaje(
    personaje_id: int, datos: schemas.PersonajeEditar, db: Session = Depends(obtener_db)
):
    personaje = db.get(models.Personaje, personaje_id)
    if personaje is None:
        raise HTTPException(404, "Esa ficha no existe")
    cambios = datos.model_dump(exclude_unset=True)
    if "atributos" in cambios:
        _validar_atributos(personaje.sistema, cambios["atributos"])
        cambios["atributos"] = {**personaje.atributos, **cambios["atributos"]}
    if cambios.get("voz_id") is not None:
        voz = db.get(models.Voz, cambios["voz_id"])
        if voz is None or voz.sistema_id != personaje.sistema_id:
            raise HTTPException(422, "Esa voz no existe en el sistema de la ficha")
    for campo, valor in cambios.items():
        setattr(personaje, campo, valor)
    db.commit()
    db.refresh(personaje)
    return _con_estadisticas(personaje)


@router.delete("/personajes/{personaje_id}", status_code=204)
def borrar_personaje(personaje_id: int, db: Session = Depends(obtener_db)):
    personaje = db.get(models.Personaje, personaje_id)
    if personaje is None:
        raise HTTPException(404, "Esa ficha no existe")
    db.delete(personaje)
    db.commit()
