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
    routers/       Las operaciones de la API
  tests/           Pruebas automáticas
  ejemplo.py       Carga un sistema de demostración
```

## Cómo arrancar el servidor (Fase 1)

```bash
cd servidor
pip install -r requirements.txt
python ejemplo.py                 # opcional: carga el sistema de demostración
uvicorn app.main:app --reload
```

Luego abre `http://localhost:8000/docs` — una pantalla de pruebas interactiva
(generada automáticamente) donde se puede crear sistemas, atributos, fórmulas
y fichas sin necesidad de interfaz propia todavía.

## Cómo correr las pruebas

```bash
cd servidor
python -m pytest
```
