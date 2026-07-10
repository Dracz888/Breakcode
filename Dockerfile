# Imagen de Breakcode: construye las pantallas (React) y las sirve junto con la
# API (FastAPI) en un solo servicio. Funciona en Render, Railway, Fly.io, etc.

# --- Etapa 1: construir la aplicación web ---
FROM node:22-alpine AS cliente
WORKDIR /cliente
COPY cliente/package.json cliente/package-lock.json ./
RUN npm ci
COPY cliente/ ./
RUN npm run build

# --- Etapa 2: el servidor, que además entrega lo construido arriba ---
FROM python:3.12-slim
WORKDIR /app

COPY servidor/requirements.txt ./servidor/requirements.txt
RUN pip install --no-cache-dir -r servidor/requirements.txt

COPY servidor/ ./servidor/
COPY --from=cliente /cliente/dist ./cliente/dist

WORKDIR /app/servidor
# El hosting indica el puerto en la variable PORT; localmente cae en 8000.
ENV PORT=8000
EXPOSE 8000
# Un solo proceso a propósito: el tiempo real (salas por WebSocket) vive en la
# memoria del servidor, apropiado para un grupo de amigos. Escalar a varios
# procesos requeriría un bus de mensajes (p. ej. Redis), innecesario aquí.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
