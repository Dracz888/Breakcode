import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo, las llamadas a la API se reenvían al servidor Python (puerto 8000).
// En producción no hace falta: el servidor Python sirve también esta aplicación.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      [
        "/sistemas",
        "/personajes",
        "/terrenos",
        "/mapas",
        "/tokens",
        "/voces",
        "/narraciones",
        "/ambientes",
      ].map((ruta) => [ruta, "http://localhost:8000"]),
    ),
  },
});
