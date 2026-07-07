# Breakcode — Fábrica de sistemas de rol

Plataforma de rol digital para celular y PC donde las reglas no vienen fijas:
cada quien diseña su propio sistema (atributos, fórmulas, mecánicas) desde la
propia aplicación, sin escribir código.

📄 **El diseño completo está en [DISEÑO.md](DISEÑO.md).**

## Estructura del proyecto

```
DISEÑO.md        El documento de diseño (empieza por aquí)
servidor/        El cerebro: API en Python (FastAPI) — Fase 1
  app/
    formulas.py    Motor de fórmulas tipo Excel (simpleeval)
    models.py      Tablas: sistemas, atributos, estadísticas, personajes
    schemas.py     Validación de datos de entrada/salida
    tiempo_real.py Salas multijugador por WebSocket — Fase 4
    routers/       Las operaciones de la API
  tests/           Pruebas automáticas
  ejemplo.py       Carga un sistema de demostración
cliente/         Las pantallas: aplicación web (React) — Fase 2
  src/
    vistas/        Inicio, editor de sistema, ficha de personaje
    componentes/   Editor de fórmulas con vista previa en vivo
```

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

### Probar el multijugador (Fase 4)

Abre el mismo mapa de batalla en dos ventanas (o en tu PC y tu celular en la
misma red). Al pintar terreno o mover una ficha en una, la otra lo ve al
instante: el servidor reparte cada cambio a todos los conectados por WebSocket.
La cabecera del mapa muestra cuántas personas están mirándolo.

## Cómo correr las pruebas

```bash
cd servidor
python -m pytest
```
