import { useState } from "react";
import Inicio from "./vistas/Inicio";
import VistaSistema from "./vistas/Sistema";
import VistaFicha from "./vistas/Ficha";
import VistaMapa from "./vistas/Mapa";
import VistaMundo from "./vistas/Mundo";
import VistaCampana from "./vistas/Campana";

// Navegación simple entre las pantallas de la aplicación.
export type Pantalla =
  | { nombre: "inicio" }
  | { nombre: "sistema"; sistemaId: number }
  | { nombre: "ficha"; personajeId: number; sistemaId: number }
  | { nombre: "mapa"; mapaId: number; sistemaId: number }
  | { nombre: "mundo"; mundoId: number; sistemaId: number }
  | { nombre: "campana"; campanaId: number; sistemaId: number };

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
      {pantalla.nombre === "mapa" && (
        <VistaMapa
          mapaId={pantalla.mapaId}
          sistemaId={pantalla.sistemaId}
          navegar={setPantalla}
        />
      )}
      {pantalla.nombre === "mundo" && (
        <VistaMundo
          mundoId={pantalla.mundoId}
          sistemaId={pantalla.sistemaId}
          navegar={setPantalla}
        />
      )}
      {pantalla.nombre === "campana" && (
        <VistaCampana
          campanaId={pantalla.campanaId}
          sistemaId={pantalla.sistemaId}
          navegar={setPantalla}
        />
      )}
    </div>
  );
}
