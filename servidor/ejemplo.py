"""Carga un sistema de ejemplo en la base de datos, para tener algo que ver.

Uso:  python ejemplo.py   (desde la carpeta servidor/)

Crea el sistema "Fantasía básica" con atributos en las tres categorías,
cinco fórmulas y dos fichas (una heroína y un monstruo). Todo esto es
borrable y editable — es solo material de demostración.
"""

from app.database import Base, SesionLocal, engine
from app.models import (
    DefinicionAtributo,
    DefinicionEstadistica,
    Mapa,
    Personaje,
    Sistema,
    Token,
)
from app.terrenos import TERRENO_INICIAL

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

kaelith = Personaje(
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
ogro = Personaje(
    sistema_id=sistema.id,
    nombre="Ogro de las ciénagas",
    nivel=2,
    es_monstruo=True,
    atributos={"fuerza": 8, "destreza": 1, "intelecto": 1, "voluntad": 2},
)
db.add_all([kaelith, ogro])
db.flush()

# Un mapa de batalla de muestra: un claro con río, camino y arboleda.
ancho, alto = 16, 12
celdas = [[TERRENO_INICIAL] * ancho for _ in range(alto)]
for y in range(alto):  # río vertical con un vado de arena
    celdas[y][10] = "agua"
    celdas[y][11] = "agua"
celdas[5][10], celdas[5][11] = "arena", "arena"
for x in range(ancho):  # camino horizontal
    if celdas[5][x] == TERRENO_INICIAL:
        celdas[5][x] = "camino"
for x, y in [(2, 1), (3, 2), (1, 8), (2, 9), (6, 10), (13, 2), (14, 8)]:  # arboleda
    celdas[y][x] = "arbol"
for x in range(4, 9):  # ruina de muro
    celdas[8][x] = "muro"
celdas[8][6] = "camino"  # con una brecha

mapa = Mapa(
    sistema_id=sistema.id, nombre="Claro del bosque", ancho=ancho, alto=alto, celdas=celdas
)
db.add(mapa)
db.flush()
db.add_all(
    [
        Token(mapa_id=mapa.id, personaje_id=kaelith.id, x=3, y=5),
        Token(mapa_id=mapa.id, personaje_id=ogro.id, x=13, y=5),
    ]
)

db.commit()
print(
    f"Sistema de ejemplo creado (id {sistema.id}) con 6 atributos, 5 fórmulas, "
    "2 fichas y 1 mapa de batalla."
)
db.close()
