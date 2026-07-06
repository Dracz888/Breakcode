import { useState } from "react";
import Inicio from "./vistas/Inicio";
import VistaSistema from "./vistas/Sistema";
import VistaFicha from "./vistas/Ficha";

// Navegación simple entre las tres pantallas de esta fase.
export type Pantalla =
  | { nombre: "inicio" }
  | { nombre: "sistema"; sistemaId: number }
  | { nombre: "ficha"; personajeId: number; sistemaId: number };

export default function App() {
  const [pantalla, setPantalla] = useState<Pantalla>({ nombre: "inicio" });

  return (
    <div className="app">
      {pantalla.nombre === "inicio" && <Inicio navegar={setPantalla} />}
      {pantalla.nombre === "sistema" && (
        <VistaSistema sistemaId={pantalla.sistemaId} navegar={setPantalla} />
      )}
      {pantalla.nombre === "ficha" && (
        <VistaFicha
          personajeId={pantalla.personajeId}
          sistemaId={pantalla.sistemaId}
          navegar={setPantalla}
        />
      )}
    </div>
  );
}
