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
    dados.py       Tirador de dados ("2d6+3") — Fase 5
    motor.py       Cálculo de estadísticas de una ficha (vida, iniciativa…)
    models.py      Tablas: sistemas, atributos, estadísticas, personajes
    schemas.py     Validación de datos de entrada/salida
    tiempo_real.py Salas multijugador por WebSocket — Fase 4
    routers/       Las operaciones de la API (incl. combate — Fase 5)
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

### El combate por turnos (Fase 5)

En la pestaña **⚔ Combate** del mapa:

- **Dados con historial compartido**: escribe una tirada (`1d20+5`, `2d6`) y
  todos en la sala ven el resultado y el desglose de cada dado. El servidor es
  quien tira, así el azar es justo e igual para todos.
- **Iniciativa y turnos**: "Iniciar combate" tira la iniciativa de cada ficha
  (dado + fórmula, configurables por sistema) y las ordena; la ficha en turno se
  resalta en el mapa. "Siguiente turno" avanza y cuenta las rondas.
- **Vida y daño**: selecciona una ficha y aplícale daño o curación; su barra de
  vida se actualiza para todos. Qué estadística marca la vida máxima se
  configura por sistema (`config_combate`).

## Cómo correr las pruebas

```bash
cd servidor
python -m pytest
```

## Publicar en internet (Fase 6)

La app se empaqueta en una sola imagen (Dockerfile) que construye las pantallas
y las sirve junto con la API. Sirve en Render, Railway o Fly.io.

### Camino recomendado: Render (con `render.yaml`)

1. Sube este repositorio a GitHub.
2. En [Render](https://render.com): **New + → Blueprint** y elige el repo.
   Render lee `render.yaml`, construye la imagen, crea una base de datos
   PostgreSQL y las conecta sola.
3. Cuando termine, Render te da un enlace `https://…onrender.com`. Ese es el
   enlace que compartes con tus amigos.

### Probar la imagen en tu máquina (opcional)

```bash
docker build -t breakcode .
docker run -p 8000:8000 breakcode      # luego abre http://localhost:8000
```

### Base de datos

- **En desarrollo**: SQLite (un archivo, cero configuración).
- **En producción**: PostgreSQL. Basta con poner su dirección en la variable de
  entorno `DATABASE_URL`; el servidor la traduce sola. En Render, `render.yaml`
  ya lo hace por ti.

### App instalable (PWA)

Al abrir el enlace en el celular, el navegador ofrece **"Agregar a pantalla de
inicio"**: la app queda con su propio ícono y a pantalla completa, como una app
nativa. Su interfaz también carga aunque la red parpadee un momento.

> Nota: el tiempo real (las salas por WebSocket) vive en la memoria del
> servidor, así que se ejecuta en **un solo proceso** — lo apropiado para un
> grupo de amigos. Escalar a muchos procesos requeriría un bus de mensajes
> (como Redis), innecesario a esta escala.
