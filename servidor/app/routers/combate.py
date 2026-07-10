"""Combate por turnos (Fase 5): dados con historial, iniciativa, turnos y vida.

Todo lo que cambia el estado de la mesa (una tirada, aplicar daño, iniciar el
combate o pasar el turno) se valida aquí y luego se anuncia a la sala del mapa,
para que todos los conectados lo vean al instante.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import dados, formulas, models, motor, schemas
from ..database import obtener_db
from ..tiempo_real import gestor

router = APIRouter(tags=["Combate por turnos"])


# ---------- Ajustes de combate del sistema ----------

def _config(sistema: models.Sistema) -> schemas.ConfigCombate:
    """Los ajustes guardados, completados con los valores por defecto."""
    return schemas.ConfigCombate(**(sistema.config_combate or {}))


def _obtener_sistema(db: Session, sistema_id: int) -> models.Sistema:
    sistema = db.get(models.Sistema, sistema_id)
    if sistema is None:
        raise HTTPException(404, "Ese sistema no existe")
    return sistema


def _obtener_mapa(db: Session, mapa_id: int) -> models.Mapa:
    mapa = db.get(models.Mapa, mapa_id)
    if mapa is None:
        raise HTTPException(404, "Ese mapa no existe")
    return mapa


@router.get("/sistemas/{sistema_id}/config-combate", response_model=schemas.ConfigCombate)
def ver_config_combate(sistema_id: int, db: Session = Depends(obtener_db)):
    return _config(_obtener_sistema(db, sistema_id))


@router.put("/sistemas/{sistema_id}/config-combate", response_model=schemas.ConfigCombate)
def guardar_config_combate(
    sistema_id: int, datos: schemas.ConfigCombate, db: Session = Depends(obtener_db)
):
    sistema = _obtener_sistema(db, sistema_id)

    # El dado de iniciativa debe entenderse.
    try:
        dados.tirar(datos.dado_iniciativa)
    except dados.ErrorDeTirada as e:
        raise HTTPException(422, f"Dado de iniciativa inválido: {e}")

    disponibles = (
        {a.clave for a in sistema.atributos}
        | {e.clave for e in sistema.estadisticas}
        | {"nivel"}
    )
    # La fórmula de iniciativa solo puede nombrar cosas que existan.
    if datos.formula_iniciativa.strip():
        desconocidos = (
            formulas.nombres_usados(datos.formula_iniciativa)
            - disponibles
            - set(formulas.FUNCIONES)
        )
        if desconocidos:
            lista = ", ".join(f"'{n}'" for n in sorted(desconocidos))
            raise HTTPException(
                422,
                f"La fórmula de iniciativa usa nombres que no existen: {lista}. "
                f"Disponibles: {', '.join(sorted(disponibles))}",
            )
    # La estadística de vida, si se indica, debe existir.
    if datos.estadistica_vida.strip():
        claves_estadisticas = {e.clave for e in sistema.estadisticas}
        if datos.estadistica_vida not in claves_estadisticas:
            raise HTTPException(
                422,
                f"La estadística de vida '{datos.estadistica_vida}' no existe. "
                f"Estadísticas: {', '.join(sorted(claves_estadisticas)) or '(ninguna)'}",
            )

    sistema.config_combate = datos.model_dump()
    db.commit()
    return datos


# ---------- Dados con historial compartido ----------

def _tirada_a_salida(t: models.TiradaDado) -> schemas.TiradaSalida:
    return schemas.TiradaSalida(
        id=t.id,
        mapa_id=t.mapa_id,
        autor=t.autor,
        motivo=t.motivo,
        expresion=t.expresion,
        grupos=t.grupos,
        modificador=t.modificador,
        total=t.total,
        creada_en=t.creada_en.isoformat(),
    )


@router.get("/mapas/{mapa_id}/tiradas", response_model=list[schemas.TiradaSalida])
def historial_de_tiradas(
    mapa_id: int, limite: int = 50, db: Session = Depends(obtener_db)
):
    _obtener_mapa(db, mapa_id)
    limite = max(1, min(limite, 200))
    tiradas = (
        db.query(models.TiradaDado)
        .filter_by(mapa_id=mapa_id)
        .order_by(models.TiradaDado.id.desc())
        .limit(limite)
        .all()
    )
    return [_tirada_a_salida(t) for t in reversed(tiradas)]


@router.post("/mapas/{mapa_id}/tiradas", response_model=schemas.TiradaSalida, status_code=201)
def tirar_dados(mapa_id: int, datos: schemas.TiradaCrear, db: Session = Depends(obtener_db)):
    _obtener_mapa(db, mapa_id)
    try:
        resultado = dados.tirar(datos.expresion)
    except dados.ErrorDeTirada as e:
        raise HTTPException(422, str(e))

    tirada = models.TiradaDado(
        mapa_id=mapa_id,
        autor=datos.autor,
        motivo=datos.motivo,
        expresion=resultado.expresion,
        grupos=[{"cantidad": g.cantidad, "caras": g.caras, "valores": g.valores} for g in resultado.grupos],
        modificador=resultado.modificador,
        total=resultado.total,
    )
    db.add(tirada)
    db.commit()
    db.refresh(tirada)
    salida = _tirada_a_salida(tirada)
    gestor.anunciar(mapa_id, "tirada", salida.model_dump())
    return salida


# ---------- Vida de las fichas (daño y curación) ----------

@router.put("/tokens/{token_id}/vida", response_model=schemas.TokenSalida)
def cambiar_vida(token_id: int, datos: schemas.VidaCambio, db: Session = Depends(obtener_db)):
    token = db.get(models.Token, token_id)
    if token is None:
        raise HTTPException(404, "Esa ficha no está en el mapa")
    maxima = motor.vida_maxima_de(token.personaje)
    if maxima is None:
        raise HTTPException(422, "Este sistema no define una estadística de vida")
    actual = token.vida_actual if token.vida_actual is not None else maxima
    token.vida_actual = max(0, min(maxima, actual + datos.delta))
    db.commit()
    db.refresh(token)
    salida = schemas.TokenSalida(
        id=token.id,
        mapa_id=token.mapa_id,
        personaje_id=token.personaje_id,
        nombre=token.personaje.nombre,
        es_monstruo=token.personaje.es_monstruo,
        x=token.x,
        y=token.y,
        vida_actual=token.vida_actual,
        vida_maxima=maxima,
    )
    gestor.anunciar(token.mapa_id, "token_actualizado", salida.model_dump())
    return salida


# ---------- Seguimiento del combate por turnos ----------

def _combate_a_salida(combate: models.Combate) -> schemas.CombateSalida:
    orden = combate.orden or []
    en_turno = None
    if orden and 0 <= combate.indice_turno < len(orden):
        en_turno = orden[combate.indice_turno]["token_id"]
    return schemas.CombateSalida(
        mapa_id=combate.mapa_id,
        ronda=combate.ronda,
        indice_turno=combate.indice_turno,
        orden=[schemas.Participante(**p) for p in orden],
        token_en_turno=en_turno,
    )


def _iniciativa_de(personaje: models.Personaje, config: schemas.ConfigCombate) -> int:
    """Tira el dado de iniciativa y le suma la fórmula del sistema (0 si falla)."""
    modificador = 0
    if config.formula_iniciativa.strip():
        try:
            modificador = int(formulas.evaluar(config.formula_iniciativa, motor.variables_de(personaje)))
        except formulas.ErrorDeFormula:
            modificador = 0
    return dados.tirar(config.dado_iniciativa).total + modificador


@router.get("/mapas/{mapa_id}/combate", response_model=schemas.CombateSalida | None)
def ver_combate(mapa_id: int, db: Session = Depends(obtener_db)):
    mapa = _obtener_mapa(db, mapa_id)
    if mapa.combate is None:
        return None
    return _combate_a_salida(mapa.combate)


@router.post("/mapas/{mapa_id}/combate/iniciar", response_model=schemas.CombateSalida)
def iniciar_combate(mapa_id: int, db: Session = Depends(obtener_db)):
    mapa = _obtener_mapa(db, mapa_id)
    if not mapa.tokens:
        raise HTTPException(422, "No hay fichas en el mapa para iniciar el combate")
    config = _config(mapa.sistema)

    participantes = [
        {
            "token_id": token.id,
            "nombre": token.personaje.nombre,
            "iniciativa": _iniciativa_de(token.personaje, config),
        }
        for token in mapa.tokens
    ]
    # Mayor iniciativa juega primero; a igualdad, orden estable por nombre.
    participantes.sort(key=lambda p: (-p["iniciativa"], p["nombre"]))

    if mapa.combate is None:
        mapa.combate = models.Combate(mapa_id=mapa.id)
    mapa.combate.ronda = 1
    mapa.combate.indice_turno = 0
    mapa.combate.orden = participantes
    db.commit()
    db.refresh(mapa.combate)
    salida = _combate_a_salida(mapa.combate)
    gestor.anunciar(mapa_id, "combate", salida.model_dump())
    return salida


@router.post("/mapas/{mapa_id}/combate/siguiente", response_model=schemas.CombateSalida)
def siguiente_turno(mapa_id: int, db: Session = Depends(obtener_db)):
    mapa = _obtener_mapa(db, mapa_id)
    if mapa.combate is None or not mapa.combate.orden:
        raise HTTPException(422, "No hay un combate en curso en este mapa")
    combate = mapa.combate
    combate.indice_turno += 1
    if combate.indice_turno >= len(combate.orden):  # se completó la vuelta
        combate.indice_turno = 0
        combate.ronda += 1
    db.commit()
    db.refresh(combate)
    salida = _combate_a_salida(combate)
    gestor.anunciar(mapa_id, "combate", salida.model_dump())
    return salida


@router.delete("/mapas/{mapa_id}/combate", status_code=204)
def terminar_combate(mapa_id: int, db: Session = Depends(obtener_db)):
    mapa = _obtener_mapa(db, mapa_id)
    if mapa.combate is not None:
        db.delete(mapa.combate)
        db.commit()
    gestor.anunciar(mapa_id, "combate_terminado", {"mapa_id": mapa_id})
