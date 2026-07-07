# Breakcode — Fábrica de sistemas de rol

Plataforma de rol digital para celular y PC donde las reglas no vienen fijas:
cada quien diseña su propio sistema (atributos, fórmulas, mecánicas) desde la
propia aplicación, sin escribir código.

📄 **El diseño completo está en [DISEÑO.md](DISEÑO.md).**

## Estructura del proyecto

```
DISEÑO.md        El documento de diseño (empieza por aquí)
servidor/        El cerebro: API en Python (FastAPI)
  app/
    formulas.py    Motor de fórmulas tipo Excel (simpleeval)
    models.py      Tablas: sistemas, atributos, estadísticas, personajes,
                   mapas, mundos y marcadores, campañas/arcos/eventos
    schemas.py     Validación de datos de entrada/salida
    terrenos.py    Catálogo de terrenos del mapa de batalla
    marcadores.py  Catálogo de tipos de marcador del mapa geográfico
    routers/       Las operaciones de la API (sistemas, personajes, mapas,
                   geografia, campanas)
  tests/           Pruebas automáticas
  ejemplo.py       Carga un sistema de demostración
cliente/         Las pantallas: aplicación web (React)
  src/
    vistas/        Inicio, editor de sistema, ficha, mapa de batalla,
                   mapa del mundo (Mundo) y campañas (Campana)
    componentes/   Editor de fórmulas con vista previa en vivo
```

## Estado por fases

Fases 1–3 y 7 construidas: la fábrica de sistemas (atributos, fórmulas,
fichas), el mapa de batalla, y —desde la fase 7— el **mapa geográfico** del
mundo con marcadores de lugares y las **campañas** con sus arcos y eventos
(la línea de tiempo de la trama). Ver la hoja de ruta completa en
[DISEÑO.md](DISEÑO.md).

## Cómo arrancar la aplicación

```bash
# 1. Construir las pantallas (solo la primera vez o tras cambiarlas)
cd cliente
npm install
npm run build

# 2. Arrancar el servidor (sirve la API y también las pantallas)
cd ../servidor
pip install -r requirements.txt
python ejemplo.py                 # opcional: carga el sistema de demostración
uvicorn app.main:app --reload
```

Luego abre `http://localhost:8000` — la aplicación completa, usable desde
PC o celular. En `http://localhost:8000/docs` sigue estando la pantalla
técnica de pruebas de la API.

## Cómo correr las pruebas

```bash
cd servidor
python -m pytest
```
