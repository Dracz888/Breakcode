"""Carga un sistema de ejemplo en la base de datos, para tener algo que ver.

Uso:  python ejemplo.py   (desde la carpeta servidor/)

Crea el sistema "Fantasía básica" con atributos en las tres categorías,
cinco fórmulas y dos fichas (una heroína y un monstruo). Todo esto es
borrable y editable — es solo material de demostración.
"""

from app.database import Base, SesionLocal, engine
from app.models import DefinicionAtributo, DefinicionEstadistica, Personaje, Sistema

Base.metadata.create_all(bind=engine)
db = SesionLocal()

if db.query(Sistema).filter_by(nombre="Fantasía básica").first():
    print("El sistema de ejemplo ya existe; no se crea de nuevo.")
    raise SystemExit

sistema = Sistema(
    nombre="Fantasía básica",
    descripcion="Sistema de demostración con las tres categorías clásicas.",
)
db.add(sistema)
db.flush()

atributos = [
    ("fuerza", "Fuerza", "fisica", "Potencia muscular", 1),
    ("destreza", "Destreza", "fisica", "Agilidad y reflejos", 1),
    ("intelecto", "Intelecto", "mental", "Razonamiento y memoria", 1),
    ("voluntad", "Voluntad", "mental", "Determinación y aguante mental", 1),
    ("voluntad_arcana", "Voluntad Arcana", "magica", "Canalización de poder mágico", 0),
    ("sintonia", "Sintonía", "magica", "Conexión con las fuerzas del mundo", 0),
]
for clave, nombre, categoria, descripcion, inicial in atributos:
    db.add(
        DefinicionAtributo(
            sistema_id=sistema.id,
            clave=clave,
            nombre=nombre,
            categoria=categoria,
            descripcion=descripcion,
            valor_inicial=inicial,
        )
    )

estadisticas = [
    ("vida_maxima", "Vida máxima", "fuerza * 10 + nivel * 5"),
    ("mana_maximo", "Maná máximo", "voluntad_arcana * 8 + sintonia * 4"),
    ("defensa", "Defensa", "piso(vida_maxima / 10) + destreza"),
    ("velocidad", "Velocidad", "3 + piso(destreza / 2)"),
    ("iniciativa", "Iniciativa", "destreza + piso(intelecto / 2)"),
]
for clave, nombre, formula in estadisticas:
    db.add(
        DefinicionEstadistica(
            sistema_id=sistema.id, clave=clave, nombre=nombre, formula=formula
        )
    )

db.add(
    Personaje(
        sistema_id=sistema.id,
        nombre="Kaelith",
        nivel=3,
        atributos={
            "fuerza": 5,
            "destreza": 3,
            "intelecto": 2,
            "voluntad": 3,
            "voluntad_arcana": 4,
            "sintonia": 2,
        },
    )
)
db.add(
    Personaje(
        sistema_id=sistema.id,
        nombre="Ogro de las ciénagas",
        nivel=2,
        es_monstruo=True,
        atributos={"fuerza": 8, "destreza": 1, "intelecto": 1, "voluntad": 2},
    )
)

db.commit()
print(f"Sistema de ejemplo creado (id {sistema.id}) con 6 atributos, 5 fórmulas y 2 fichas.")
db.close()
