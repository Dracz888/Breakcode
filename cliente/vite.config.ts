import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo, las llamadas a la API se reenvían al servidor Python (puerto 8000).
// En producción no hace falta: el servidor Python sirve también esta aplicación.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/sistemas": "http://localhost:8000",
      "/personajes": "http://localhost:8000",
      "/mapas": "http://localhost:8000",
      "/tokens": "http://localhost:8000",
      "/terrenos": "http://localhost:8000",
      // La sala en tiempo real viaja por WebSocket.
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
