"""Rutas del editor de sistemas: sistemas, atributos y estadísticas con fórmulas."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import formulas, models, schemas
from ..database import obtener_db

router = APIRouter(tags=["Editor de sistemas"])


def _obtener_sistema(db: Session, sistema_id: int) -> models.Sistema:
    sistema = db.get(models.Sistema, sistema_id)
    if sistema is None:
        raise HTTPException(404, "Ese sistema no existe")
    return sistema


def _claves_disponibles(sistema: models.Sistema, excluir_estadistica: str | None = None) -> set[str]:
    """Nombres que una fórmula puede usar: atributos, otras estadísticas y 'nivel'."""
    claves = {a.clave for a in sistema.atributos}
    claves |= {e.clave for e in sistema.estadisticas if e.clave != excluir_estadistica}
    claves.add("nivel")
    return claves


def _validar_formula(formula: str, disponibles: set[str]) -> None:
    """Rechaza fórmulas con nombres desconocidos o mal escritas, con error en español."""
    usados = formulas.nombres_usados(formula)
    desconocidos = usados - disponibles - set(formulas.FUNCIONES)
    if desconocidos:
        lista = ", ".join(f"'{n}'" for n in sorted(desconocidos))
        raise HTTPException(
            422,
            f"La fórmula usa nombres que no existen en este sistema: {lista}. "
            f"Disponibles: {', '.join(sorted(disponibles))}",
        )
    valores_de_prueba = {clave: 1 for clave in disponibles}
    try:
        formulas.evaluar(formula, valores_de_prueba)
    except formulas.ErrorDeFormula as e:
        raise HTTPException(422, str(e))


# ---------- Sistemas ----------

@router.post("/sistemas", response_model=schemas.SistemaSalida, status_code=201)
def crear_sistema(datos: schemas.SistemaCrear, db: Session = Depends(obtener_db)):
    sistema = models.Sistema(nombre=datos.nombre, descripcion=datos.descripcion)
    db.add(sistema)
    db.commit()
    db.refresh(sistema)
    return sistema


@router.get("/sistemas", response_model=list[schemas.SistemaSalida])
def listar_sistemas(db: Session = Depends(obtener_db)):
    return db.query(models.Sistema).order_by(models.Sistema.id).all()


@router.get("/sistemas/{sistema_id}", response_model=schemas.SistemaDetalle)
def ver_sistema(sistema_id: int, db: Session = Depends(obtener_db)):
    return _obtener_sistema(db, sistema_id)


@router.put("/sistemas/{sistema_id}", response_model=schemas.SistemaDetalle)
def editar_sistema(
    sistema_id: int, datos: schemas.SistemaEditar, db: Session = Depends(obtener_db)
):
    """Editar los datos del sistema, incluidas las notas privadas del DJ."""
    sistema = _obtener_sistema(db, sistema_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(sistema, campo, valor)
    db.commit()
    db.refresh(sistema)
    return sistema


@router.delete("/sistemas/{sistema_id}", status_code=204)
def borrar_sistema(sistema_id: int, db: Session = Depends(obtener_db)):
    db.delete(_obtener_sistema(db, sistema_id))
    db.commit()


# ---------- Exportar / importar (fase 9 — respaldo y compartir) ----------

@router.get("/sistemas/{sistema_id}/exportar", response_model=schemas.SistemaExportado)
def exportar_sistema(sistema_id: int, db: Session = Depends(obtener_db)):
    """Descarga el sistema entero (reglas, fichas y mapas) como un archivo."""
    sistema = _obtener_sistema(db, sistema_id)
    return schemas.SistemaExportado(
        nombre=sistema.nombre,
        descripcion=sistema.descripcion,
        notas=sistema.notas or "",
        atributos=[schemas.AtributoSalida.model_validate(a) for a in sistema.atributos],
        estadisticas=[
            schemas.EstadisticaSalida.model_validate(e) for e in sistema.estadisticas
        ],
        personajes=[
            schemas.PersonajeExportado(
                nombre=p.nombre,
                nivel=p.nivel,
                es_monstruo=p.es_monstruo,
                atributos=p.atributos,
            )
            for p in sistema.personajes
        ],
        mapas=[
            schemas.MapaExportado(
                nombre=m.nombre,
                ancho=m.ancho,
                alto=m.alto,
                celdas=m.celdas,
                niebla=m.niebla or [],
            )
            for m in sistema.mapas
        ],
    )


@router.post("/sistemas/importar", response_model=schemas.SistemaSalida, status_code=201)
def importar_sistema(datos: schemas.SistemaExportado, db: Session = Depends(obtener_db)):
    """Crea un sistema nuevo a partir de un archivo exportado.

    Siempre nace como un sistema aparte (nunca sobrescribe uno existente), así
    importar un respaldo no borra lo que ya tenías.
    """
    if datos.formato != "breakcode/sistema":
        raise HTTPException(422, "Este archivo no parece un sistema de Breakcode.")

    sistema = models.Sistema(
        nombre=datos.nombre, descripcion=datos.descripcion, notas=datos.notas
    )
    for a in datos.atributos:
        sistema.atributos.append(models.DefinicionAtributo(**a.model_dump()))
    for e in datos.estadisticas:
        sistema.estadisticas.append(models.DefinicionEstadistica(**e.model_dump()))
    for p in datos.personajes:
        sistema.personajes.append(
            models.Personaje(
                nombre=p.nombre,
                nivel=p.nivel,
                es_monstruo=p.es_monstruo,
                atributos=p.atributos,
            )
        )
    for m in datos.mapas:
        sistema.mapas.append(
            models.Mapa(
                nombre=m.nombre,
                ancho=m.ancho,
                alto=m.alto,
                celdas=m.celdas,
                niebla=m.niebla,
            )
        )
    db.add(sistema)
    db.commit()
    db.refresh(sistema)
    return sistema


# ---------- Atributos ----------

@router.post(
    "/sistemas/{sistema_id}/atributos",
    response_model=schemas.AtributoSalida,
    status_code=201,
)
def crear_atributo(
    sistema_id: int, datos: schemas.AtributoCrear, db: Session = Depends(obtener_db)
):
    sistema = _obtener_sistema(db, sistema_id)
    if datos.clave in _claves_disponibles(sistema):
        raise HTTPException(409, f"Ya existe un atributo o estadística con la clave '{datos.clave}'")
    atributo = models.DefinicionAtributo(sistema_id=sistema.id, **datos.model_dump())
    db.add(atributo)
    db.commit()
    db.refresh(atributo)
    return atributo


@router.put(
    "/sistemas/{sistema_id}/atributos/{clave}", response_model=schemas.AtributoSalida
)
def editar_atributo(
    sistema_id: int,
    clave: str,
    datos: schemas.AtributoEditar,
    db: Session = Depends(obtener_db),
):
    sistema = _obtener_sistema(db, sistema_id)
    atributo = next((a for a in sistema.atributos if a.clave == clave), None)
    if atributo is None:
        raise HTTPException(404, f"No existe el atributo '{clave}' en este sistema")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(atributo, campo, valor)
    db.commit()
    db.refresh(atributo)
    return atributo


@router.delete("/sistemas/{sistema_id}/atributos/{clave}", status_code=204)
def borrar_atributo(sistema_id: int, clave: str, db: Session = Depends(obtener_db)):
    """Red de seguridad: no se puede borrar un atributo que alguna fórmula usa."""
    sistema = _obtener_sistema(db, sistema_id)
    atributo = next((a for a in sistema.atributos if a.clave == clave), None)
    if atributo is None:
        raise HTTPException(404, f"No existe el atributo '{clave}' en este sistema")

    afectadas = [
        e.nombre for e in sistema.estadisticas if clave in formulas.nombres_usados(e.formula)
    ]
    if afectadas:
        raise HTTPException(
            409,
            f"No se puede borrar '{clave}' porque lo usan estas fórmulas: "
            f"{', '.join(afectadas)}. Edita o borra esas fórmulas primero.",
        )

    for personaje in sistema.personajes:
        if clave in personaje.atributos:
            valores = dict(personaje.atributos)
            del valores[clave]
            personaje.atributos = valores
    db.delete(atributo)
    db.commit()


# ---------- Estadísticas derivadas (fórmulas) ----------

@router.post(
    "/sistemas/{sistema_id}/estadisticas",
    response_model=schemas.EstadisticaSalida,
    status_code=201,
)
def crear_estadistica(
    sistema_id: int, datos: schemas.EstadisticaCrear, db: Session = Depends(obtener_db)
):
    sistema = _obtener_sistema(db, sistema_id)
    if datos.clave in _claves_disponibles(sistema):
        raise HTTPException(409, f"Ya existe un atributo o estadística con la clave '{datos.clave}'")
    _validar_formula(datos.formula, _claves_disponibles(sistema))
    estadistica = models.DefinicionEstadistica(sistema_id=sistema.id, **datos.model_dump())
    db.add(estadistica)
    db.commit()
    db.refresh(estadistica)
    return estadistica


@router.put(
    "/sistemas/{sistema_id}/estadisticas/{clave}",
    response_model=schemas.EstadisticaSalida,
)
def editar_estadistica(
    sistema_id: int,
    clave: str,
    datos: schemas.EstadisticaEditar,
    db: Session = Depends(obtener_db),
):
    """Al editar una fórmula, todas las fichas se recalculan solas al consultarlas."""
    sistema = _obtener_sistema(db, sistema_id)
    estadistica = next((e for e in sistema.estadisticas if e.clave == clave), None)
    if estadistica is None:
        raise HTTPException(404, f"No existe la estadística '{clave}' en este sistema")
    cambios = datos.model_dump(exclude_unset=True)
    if "formula" in cambios:
        _validar_formula(cambios["formula"], _claves_disponibles(sistema, excluir_estadistica=clave) | {clave})
    for campo, valor in cambios.items():
        setattr(estadistica, campo, valor)
    db.commit()
    db.refresh(estadistica)
    return estadistica


@router.delete("/sistemas/{sistema_id}/estadisticas/{clave}", status_code=204)
def borrar_estadistica(sistema_id: int, clave: str, db: Session = Depends(obtener_db)):
    sistema = _obtener_sistema(db, sistema_id)
    estadistica = next((e for e in sistema.estadisticas if e.clave == clave), None)
    if estadistica is None:
        raise HTTPException(404, f"No existe la estadística '{clave}' en este sistema")

    afectadas = [
        e.nombre
        for e in sistema.estadisticas
        if e.clave != clave and clave in formulas.nombres_usados(e.formula)
    ]
    if afectadas:
        raise HTTPException(
            409,
            f"No se puede borrar '{clave}' porque lo usan estas fórmulas: "
            f"{', '.join(afectadas)}. Edita o borra esas fórmulas primero.",
        )
    db.delete(estadistica)
    db.commit()


# ---------- Vista previa en vivo (para el editor de fórmulas) ----------

@router.post(
    "/sistemas/{sistema_id}/probar-formula", response_model=schemas.FormulaResultado
)
def probar_formula(
    sistema_id: int, datos: schemas.FormulaPrueba, db: Session = Depends(obtener_db)
):
    """Calcula una fórmula al instante contra valores de prueba, sin guardar nada.

    Es el respaldo de la vista previa en vivo del editor: si no se envían
    valores de prueba, cada atributo usa su valor inicial y el nivel es 1.
    """
    sistema = _obtener_sistema(db, sistema_id)
    valores: dict[str, float] = {a.clave: a.valor_inicial for a in sistema.atributos}
    valores["nivel"] = 1
    formulas_del_sistema = {e.clave: e.formula for e in sistema.estadisticas}
    calculadas, _ = formulas.evaluar_conjunto(formulas_del_sistema, valores)
    valores.update(calculadas)
    valores.update(datos.valores_de_prueba)

    try:
        valor = formulas.evaluar(datos.formula, valores)
    except formulas.ErrorDeFormula as e:
        return schemas.FormulaResultado(ok=False, error=str(e), valores_usados=valores)
    return schemas.FormulaResultado(ok=True, valor=valor, valores_usados=valores)
