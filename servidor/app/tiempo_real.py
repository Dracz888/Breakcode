"""Multijugador en tiempo real (Fase 4).

Cada mapa de batalla tiene una "sala": todos los que lo tienen abierto quedan
conectados por un WebSocket (una línea que queda descolgada). Cuando alguien
pinta terreno, coloca, mueve o quita una ficha, el servidor —la única fuente de
verdad— reparte la novedad a todos los demás de esa sala al instante.

Los endpoints REST corren en un hilo de trabajo aparte del bucle de eventos, así
que para emitir desde ellos se programa el envío en el bucle con
`run_coroutine_threadsafe`. El bucle se aprende solo: queda registrado en cuanto
alguien se conecta, que es justo cuando emitir tiene sentido.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class GestorDeSalas:
    def __init__(self) -> None:
        self._salas: dict[int, set[WebSocket]] = {}
        self._bucle: asyncio.AbstractEventLoop | None = None

    async def conectar(self, mapa_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._bucle = asyncio.get_running_loop()
        self._salas.setdefault(mapa_id, set()).add(ws)
        await self._emitir(mapa_id, "presencia", {"conectados": len(self._salas[mapa_id])})

    def desconectar(self, mapa_id: int, ws: WebSocket) -> None:
        sala = self._salas.get(mapa_id)
        if not sala:
            return
        sala.discard(ws)
        if sala:
            self.anunciar(mapa_id, "presencia", {"conectados": len(sala)})
        else:
            self._salas.pop(mapa_id, None)

    def conectados(self, mapa_id: int) -> int:
        return len(self._salas.get(mapa_id, ()))

    async def _emitir(self, mapa_id: int, tipo: str, datos: Any) -> None:
        mensaje = {"tipo": tipo, "datos": datos}
        for ws in list(self._salas.get(mapa_id, ())):
            try:
                await ws.send_json(mensaje)
            except Exception:  # conexión ya rota: la sacamos de la sala
                self._salas.get(mapa_id, set()).discard(ws)

    def anunciar(self, mapa_id: int, tipo: str, datos: Any) -> None:
        """Emite una novedad a la sala desde código sincrónico (endpoints REST)."""
        if self._bucle is None or not self._salas.get(mapa_id):
            return
        asyncio.run_coroutine_threadsafe(self._emitir(mapa_id, tipo, datos), self._bucle)


gestor = GestorDeSalas()
