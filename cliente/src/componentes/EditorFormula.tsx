import { FormEvent, useEffect, useRef, useState } from "react";
import * as api from "../api";

// Convierte un nombre visible en una clave usable en fórmulas:
// "Voluntad Arcana" -> "voluntad_arcana"
export function aClave(nombre: string): string {
  return nombre
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ñ/g, "n")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

interface Props {
  sistemaId: number;
  clavesDisponibles: string[];
  inicial?: { clave: string; nombre: string; formula: string };
  onGuardar: (datos: { clave: string; nombre: string; formula: string }) => Promise<void>;
  onCancelar?: () => void;
}

/** Editor de una estadística derivada, con vista previa calculada en vivo:
 *  mientras se escribe la fórmula, el servidor la evalúa contra valores de
 *  prueba y muestra el resultado o el error, antes de guardar nada. */
export default function EditorFormula({
  sistemaId,
  clavesDisponibles,
  inicial,
  onGuardar,
  onCancelar,
}: Props) {
  const [nombre, setNombre] = useState(inicial?.nombre ?? "");
  const [formula, setFormula] = useState(inicial?.formula ?? "");
  const [previa, setPrevia] = useState<api.FormulaResultado | null>(null);
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const campoFormula = useRef<HTMLInputElement>(null);
  const esEdicion = Boolean(inicial);

  // Vista previa en vivo, con una pequeña espera para no llamar en cada tecla.
  useEffect(() => {
    if (!formula.trim()) {
      setPrevia(null);
      return;
    }
    const temporizador = setTimeout(() => {
      api
        .probarFormula(sistemaId, formula)
        .then(setPrevia)
        .catch(() => setPrevia(null));
    }, 350);
    return () => clearTimeout(temporizador);
  }, [formula, sistemaId]);

  function insertarClave(clave: string) {
    const campo = campoFormula.current;
    if (!campo) return;
    const inicio = campo.selectionStart ?? formula.length;
    const fin = campo.selectionEnd ?? formula.length;
    const nueva = formula.slice(0, inicio) + clave + formula.slice(fin);
    setFormula(nueva);
    requestAnimationFrame(() => {
      campo.focus();
      campo.setSelectionRange(inicio + clave.length, inicio + clave.length);
    });
  }

  async function guardar(evento: FormEvent) {
    evento.preventDefault();
    setError("");
    setGuardando(true);
    try {
      await onGuardar({ clave: inicial?.clave ?? aClave(nombre), nombre, formula });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <form onSubmit={guardar}>
      <label className="campo">
        <span>Nombre de la estadística</span>
        <input
          type="text"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder="Ej. Vida máxima"
          required
        />
        {!esEdicion && nombre && (
          <span className="nota">En las fórmulas se usará como: {aClave(nombre)}</span>
        )}
      </label>

      <label className="campo">
        <span>Fórmula (como en Excel)</span>
        <input
          ref={campoFormula}
          type="text"
          className="formula"
          value={formula}
          onChange={(e) => setFormula(e.target.value)}
          placeholder="Ej. fuerza * 10 + nivel * 5"
          autoComplete="off"
          required
        />
      </label>

      <div className="nota">Toca un nombre para insertarlo en la fórmula:</div>
      <div className="paleta-claves">
        {clavesDisponibles
          .filter((c) => c !== inicial?.clave)
          .map((clave) => (
            <button
              key={clave}
              type="button"
              className="chip-clave"
              onClick={() => insertarClave(clave)}
            >
              {clave}
            </button>
          ))}
      </div>

      {previa && (
        <div className={`vista-previa ${previa.ok ? "ok" : "mal"}`}>
          {previa.ok ? (
            <>
              Vista previa con valores de prueba:{" "}
              <span className="valor">{previa.valor}</span>
            </>
          ) : (
            previa.error
          )}
        </div>
      )}

      {error && <div className="error">{error}</div>}

      <div className="fila" style={{ marginTop: 14 }}>
        <button className="boton" type="submit" disabled={guardando || !previa?.ok}>
          {esEdicion ? "Guardar cambios" : "Crear estadística"}
        </button>
        {onCancelar && (
          <button className="boton boton-secundario" type="button" onClick={onCancelar}>
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}
