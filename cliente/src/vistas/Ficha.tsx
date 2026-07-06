import { useCallback, useEffect, useState } from "react";
import * as api from "../api";
import type { Pantalla } from "../App";

interface Props {
  personajeId: number;
  sistemaId: number;
  navegar: (p: Pantalla) => void;
}

/** La hoja del personaje. Cada vez que cambias un atributo o el nivel,
 *  el servidor recalcula todas las estadísticas derivadas al instante. */
export default function VistaFicha({ personajeId, sistemaId, navegar }: Props) {
  const [personaje, setPersonaje] = useState<api.Personaje | null>(null);
  const [sistema, setSistema] = useState<api.SistemaDetalle | null>(null);
  const [error, setError] = useState("");

  const recargar = useCallback(() => {
    api
      .verPersonaje(personajeId)
      .then(setPersonaje)
      .catch((e) => setError(e.message));
    api
      .verSistema(sistemaId)
      .then(setSistema)
      .catch((e) => setError(e.message));
  }, [personajeId, sistemaId]);

  useEffect(() => {
    recargar();
  }, [recargar]);

  if (!personaje || !sistema) {
    return error ? <div className="error">{error}</div> : <p className="nota">Cargando…</p>;
  }

  async function guardar(datos: {
    nivel?: number;
    atributos?: Record<string, number>;
  }) {
    setError("");
    try {
      setPersonaje(await api.editarPersonaje(personajeId, datos));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function borrar() {
    if (!confirm(`¿Borrar la ficha de "${personaje!.nombre}"?`)) return;
    try {
      await api.borrarPersonaje(personajeId);
      navegar({ nombre: "sistema", sistemaId });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const nombreDeEstadistica = (clave: string) =>
    sistema.estadisticas.find((e) => e.clave === clave)?.nombre ?? clave;

  return (
    <>
      <header className="cabecera">
        <button
          className="boton-volver"
          onClick={() => navegar({ nombre: "sistema", sistemaId })}
        >
          ← {sistema.nombre}
        </button>
        <h1>{personaje.nombre}</h1>
        {personaje.es_monstruo && <span className="insignia-monstruo">monstruo</span>}
      </header>

      {error && <div className="error">{error}</div>}

      <div className="ficha">
        <div className="tarjeta">
          <h3>Atributos</h3>
          <div className="atributo-editable">
            <span className="nombre">Nivel</span>
            <input
              type="number"
              min={1}
              value={personaje.nivel}
              onChange={(e) => guardar({ nivel: Math.max(1, Number(e.target.value)) })}
            />
          </div>
          {sistema.atributos.map((a) => (
            <div key={a.clave} className="atributo-editable">
              <span className="nombre">
                {a.nombre}{" "}
                {a.categoria && <span className={`chip ${a.categoria}`}>{a.categoria}</span>}
              </span>
              <input
                type="number"
                value={personaje.atributos[a.clave] ?? a.valor_inicial}
                onChange={(e) =>
                  guardar({ atributos: { [a.clave]: Number(e.target.value) } })
                }
              />
            </div>
          ))}
          <p className="nota" style={{ marginTop: 12 }}>
            Cambia un valor y mira cómo las estadísticas se recalculan solas.
          </p>
        </div>

        <div className="tarjeta">
          <h3>Estadísticas (calculadas por tus fórmulas)</h3>
          {Object.keys(personaje.estadisticas).length === 0 && (
            <p className="nota">
              Este sistema aún no tiene fórmulas. Créalas en la pestaña "Fórmulas" del
              sistema.
            </p>
          )}
          <div className="bloque-stats">
            {Object.entries(personaje.estadisticas).map(([clave, valor]) => (
              <div key={clave} className="stat">
                <div className="numero">{Math.round(valor * 100) / 100}</div>
                <div className="nombre">{nombreDeEstadistica(clave)}</div>
              </div>
            ))}
          </div>
          {Object.entries(personaje.errores_de_formulas).map(([clave, mensaje]) => (
            <div key={clave} className="error">
              {nombreDeEstadistica(clave)}: {mensaje}
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 20 }}>
        <button className="boton boton-peligro" onClick={borrar}>
          Borrar esta ficha
        </button>
      </div>
    </>
  );
}
