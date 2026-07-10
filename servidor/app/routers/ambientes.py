"""Rutas de la mesa de sonido: ambientes integrados y subidos por el DJ.

Los integrados se sintetizan en el servidor (no ocupan base de datos); los
subidos son grabaciones propias del DJ que se guardan por sistema. Ambos se
sirven como audio para reproducirse en bucle desde el cliente.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from .. import ambientes, models, schemas
from ..database import obtener_db

router = APIRouter(tags=["Ambientes de sonido"])

# Tope prudente para las subidas (una pista de música cabe de sobra).
MAX_BYTES = 15 * 1024 * 1024


def _obtener_sistema(db: Session, sistema_id: int) -> models.Sistema:
    sistema = db.get(models.Sistema, sistema_id)
    if sistema is None:
        raise HTTPException(404, "Ese sistema no existe")
    return sistema


# ---------- Ambientes integrados (sintetizados) ----------

@router.get("/ambientes/integrados", response_model=list[schemas.AmbienteIntegrado])
def listar_integrados():
    """El catálogo de atmósferas que trae el programa, listas para usar."""
    return ambientes.AMBIENTES_INTEGRADOS


@router.get("/ambientes/integrados/{clave}/audio")
def audio_integrado(clave: str):
    if not ambientes.existe(clave):
        raise HTTPException(404, "Ese ambiente integrado no existe")
    return Response(content=ambientes.audio_integrado(clave), media_type="audio/wav")


# ---------- Ambientes subidos por el DJ ----------

@router.post(
    "/sistemas/{sistema_id}/ambientes",
    response_model=schemas.AmbienteSalida,
    status_code=201,
)
async def subir_ambiente(
    sistema_id: int,
    nombre: str = Form(..., min_length=1, max_length=120),
    categoria: str = Form("Propios"),
    icono: str = Form("🎵"),
    bucle: bool = Form(True),
    archivo: UploadFile = File(...),
    db: Session = Depends(obtener_db),
):
    """Guarda una grabación propia del DJ para usarla como ambiente."""
    sistema = _obtener_sistema(db, sistema_id)

    if not (archivo.content_type or "").startswith("audio/"):
        raise HTTPException(422, "El archivo debe ser de audio (MP3, OGG, WAV…).")
    datos = await archivo.read()
    if not datos:
        raise HTTPException(422, "El archivo de audio está vacío.")
    if len(datos) > MAX_BYTES:
        raise HTTPException(
            422, f"El audio es muy pesado (máximo {MAX_BYTES // (1024 * 1024)} MB)."
        )

    ambiente = models.Ambiente(
        sistema_id=sistema.id,
        nombre=nombre,
        categoria=categoria or "Propios",
        icono=icono or "🎵",
        audio=datos,
        tipo_mime=archivo.content_type,
        bucle=bucle,
    )
    db.add(ambiente)
    db.commit()
    db.refresh(ambiente)
    return ambiente


@router.get("/sistemas/{sistema_id}/ambientes", response_model=list[schemas.AmbienteSalida])
def listar_ambientes(sistema_id: int, db: Session = Depends(obtener_db)):
    return _obtener_sistema(db, sistema_id).ambientes


@router.get("/ambientes/{ambiente_id}/audio")
def audio_de_ambiente(ambiente_id: int, db: Session = Depends(obtener_db)):
    ambiente = db.get(models.Ambiente, ambiente_id)
    if ambiente is None:
        raise HTTPException(404, "Ese ambiente no existe")
    return Response(content=ambiente.audio, media_type=ambiente.tipo_mime)


@router.delete("/ambientes/{ambiente_id}", status_code=204)
def borrar_ambiente(ambiente_id: int, db: Session = Depends(obtener_db)):
    ambiente = db.get(models.Ambiente, ambiente_id)
    if ambiente is None:
        raise HTTPException(404, "Ese ambiente no existe")
    db.delete(ambiente)
    db.commit()
