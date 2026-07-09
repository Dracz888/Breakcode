"""Rutas del módulo de voces: catálogo por sistema y narración compartida.

El flujo que promete el diseño: el DJ crea voces (con su descripción y su voz de
ElevenLabs), se las asigna a personajes, escribe una línea y genera el audio.
Cada audio queda en el historial del sistema para que todos en la mesa puedan
reproducirlo. Sin clave de ElevenLabs todo funciona en modo demostración.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import models, schemas, voces
from ..database import obtener_db

router = APIRouter(tags=["Voces"])


def _obtener_sistema(db: Session, sistema_id: int) -> models.Sistema:
    sistema = db.get(models.Sistema, sistema_id)
    if sistema is None:
        raise HTTPException(404, "Ese sistema no existe")
    return sistema


def _obtener_voz(db: Session, voz_id: int) -> models.Voz:
    voz = db.get(models.Voz, voz_id)
    if voz is None:
        raise HTTPException(404, "Esa voz no existe")
    return voz


# ---------- Estado y catálogo sugerido ----------

@router.get("/voces/estado", response_model=schemas.EstadoVoces)
def estado_de_voces():
    """Indica si hay ElevenLabs configurado y las voces sugeridas para empezar."""
    return schemas.EstadoVoces(
        hay_api=voces.hay_api(),
        sugeridas=[schemas.VozSugerida(**v) for v in voces.VOCES_SUGERIDAS],
        max_caracteres=voces.MAX_CARACTERES,
    )


# ---------- Catálogo de voces del sistema ----------

@router.post(
    "/sistemas/{sistema_id}/voces", response_model=schemas.VozSalida, status_code=201
)
def crear_voz(sistema_id: int, datos: schemas.VozCrear, db: Session = Depends(obtener_db)):
    sistema = _obtener_sistema(db, sistema_id)
    voz = models.Voz(sistema_id=sistema.id, **datos.model_dump())
    db.add(voz)
    db.commit()
    db.refresh(voz)
    return voz


@router.get("/sistemas/{sistema_id}/voces", response_model=list[schemas.VozSalida])
def listar_voces(sistema_id: int, db: Session = Depends(obtener_db)):
    return _obtener_sistema(db, sistema_id).voces


@router.put("/voces/{voz_id}", response_model=schemas.VozSalida)
def editar_voz(voz_id: int, datos: schemas.VozEditar, db: Session = Depends(obtener_db)):
    voz = _obtener_voz(db, voz_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(voz, campo, valor)
    db.commit()
    db.refresh(voz)
    return voz


@router.delete("/voces/{voz_id}", status_code=204)
def borrar_voz(voz_id: int, db: Session = Depends(obtener_db)):
    """Al borrar una voz, los personajes que la usaban se quedan sin voz asignada."""
    voz = _obtener_voz(db, voz_id)
    for personaje in voz.personajes:
        personaje.voz_id = None
    db.delete(voz)
    db.commit()


# ---------- Narración (generar audio y guardarlo en el historial) ----------

@router.post(
    "/sistemas/{sistema_id}/narrar",
    response_model=schemas.NarracionSalida,
    status_code=201,
)
def narrar(sistema_id: int, datos: schemas.NarracionCrear, db: Session = Depends(obtener_db)):
    """Genera el audio de una línea y lo registra para toda la mesa."""
    sistema = _obtener_sistema(db, sistema_id)

    voz: models.Voz | None = None
    personaje: models.Personaje | None = None
    nombre_locutor = ""

    if datos.personaje_id is not None:
        personaje = db.get(models.Personaje, datos.personaje_id)
        if personaje is None or personaje.sistema_id != sistema.id:
            raise HTTPException(404, "Esa ficha no existe en este sistema")
        nombre_locutor = personaje.nombre
        voz = personaje.voz

    if datos.voz_id is not None:
        voz = _obtener_voz(db, datos.voz_id)
        if voz.sistema_id != sistema.id:
            raise HTTPException(422, "Esa voz pertenece a otro sistema")

    if voz is None:
        if personaje is not None:
            raise HTTPException(
                422,
                f"{personaje.nombre} no tiene una voz asignada. "
                f"Asígnale una voz del catálogo o elige una para narrar.",
            )
        raise HTTPException(422, "Elige una voz o un personaje con voz para narrar")

    if not nombre_locutor:
        nombre_locutor = voz.nombre

    try:
        audio, tipo_mime, es_demostracion = voces.generar_audio(
            datos.texto, voz.voz_externa_id, voz.ajustes
        )
    except voces.ErrorDeVoz as e:
        raise HTTPException(422, str(e))

    narracion = models.Narracion(
        sistema_id=sistema.id,
        personaje_id=personaje.id if personaje else None,
        voz_id=voz.id,
        nombre_locutor=nombre_locutor,
        texto=datos.texto.strip(),
        audio=audio,
        tipo_mime=tipo_mime,
        es_demostracion=es_demostracion,
    )
    db.add(narracion)
    db.commit()
    db.refresh(narracion)
    return narracion


@router.get(
    "/sistemas/{sistema_id}/narraciones", response_model=list[schemas.NarracionSalida]
)
def listar_narraciones(sistema_id: int, db: Session = Depends(obtener_db)):
    """El historial compartido de audio, del más reciente al más antiguo."""
    sistema = _obtener_sistema(db, sistema_id)
    return sorted(sistema.narraciones, key=lambda n: n.id, reverse=True)


@router.get("/narraciones/{narracion_id}/audio")
def audio_de_narracion(narracion_id: int, db: Session = Depends(obtener_db)):
    """Entrega el audio en bruto para reproducirlo en cualquier dispositivo."""
    narracion = db.get(models.Narracion, narracion_id)
    if narracion is None:
        raise HTTPException(404, "Esa narración no existe")
    return Response(content=narracion.audio, media_type=narracion.tipo_mime)


@router.delete("/narraciones/{narracion_id}", status_code=204)
def borrar_narracion(narracion_id: int, db: Session = Depends(obtener_db)):
    narracion = db.get(models.Narracion, narracion_id)
    if narracion is None:
        raise HTTPException(404, "Esa narración no existe")
    db.delete(narracion)
    db.commit()
