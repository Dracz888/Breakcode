import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api";

interface Props {
  sistemaId: number;
  voces: api.Voz[];
  hayApi: boolean;
  maxCaracteres: number;
}

/** El taller de narración: escribe una línea, elige la voz y genera el audio,
 *  que queda en el historial compartido de la mesa para volver a reproducirlo. */
export default function Narrador({ sistemaId, voces, hayApi, maxCaracteres }: Props) {
  const [historial, setHistorial] = useState<api.Narracion[]>([]);
  const [texto, setTexto] = useState("");
  const [vozId, setVozId] = useState<number | "">("");
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState("");
  const audioRef = useRef<HTMLAudioElement>(null);

  const recargar = useCallback(
    () =>
      api
        .listarNarraciones(sistemaId)
        .then(setHistorial)
        .catch((e) => setError(e.message)),
    [sistemaId],
  );

  useEffect(() => {
    recargar();
  }, [recargar]);

  // Selecciona la primera voz por defecto cuando llega el catálogo.
  useEffect(() => {
    if (vozId === "" && voces.length > 0) setVozId(voces[0].id);
  }, [voces, vozId]);

  function reproducir(narracionId: number) {
    const audio = audioRef.current;
    if (!audio) return;
    audio.src = api.audioDeNarracion(narracionId);
    audio.play().catch(() => {
      /* algunos navegadores exigen un toque previo: no es un error grave */
    });
  }

  async function narrar(evento: FormEvent) {
    evento.preventDefault();
    if (vozId === "") return;
    setError("");
    setGenerando(true);
    try {
      const narracion = await api.narrar(sistemaId, { texto, voz_id: vozId });
      setTexto("");
      await recargar();
      reproducir(narracion.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerando(false);
    }
  }

  async function borrar(narracion: api.Narracion) {
    setError("");
    try {
      await api.borrarNarracion(narracion.id);
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="dos-columnas">
      <div>
        <div className="tarjeta">
          <h3>Narrar una línea</h3>
          {voces.length === 0 ? (
            <p className="nota">
              Primero crea al menos una voz en el catálogo de al lado para poder narrar.
            </p>
          ) : (
            <form onSubmit={narrar}>
              <label className="campo">
                <span>Voz</span>
                <select
                  value={vozId}
                  onChange={(e) => setVozId(Number(e.target.value))}
                >
                  {voces.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.nombre}
                    </option>
                  ))}
                </select>
              </label>
              <label className="campo">
                <span>Texto ({texto.length}/{maxCaracteres})</span>
                <textarea
                  value={texto}
                  onChange={(e) => setTexto(e.target.value.slice(0, maxCaracteres))}
                  placeholder="Ej. Nadie sale vivo de mi mazmorra, insensatos…"
                  rows={4}
                  required
                />
              </label>
              <button className="boton" type="submit" disabled={generando || !texto.trim()}>
                {generando ? "Generando audio…" : "Narrar y reproducir"}
              </button>
            </form>
          )}
          {error && <div className="error" style={{ marginTop: 10 }}>{error}</div>}
        </div>

        <div className="tarjeta">
          <h3>Historial de la mesa</h3>
          {historial.length === 0 && (
            <p className="nota">
              Aún no se ha narrado nada. Lo que generes aquí quedará guardado para que
              todos puedan volver a escucharlo.
            </p>
          )}
          {historial.map((n) => (
            <div key={n.id} className="narracion">
              <div className="espacio">
                <div className="fila" style={{ gap: 8, alignItems: "baseline" }}>
                  <strong>{n.nombre_locutor || "Voz"}</strong>
                  {n.es_demostracion && <span className="chip">demostración</span>}
                </div>
                <span className="nota">«{n.texto}»</span>
              </div>
              <button className="boton boton-secundario" onClick={() => reproducir(n.id)}>
                ▶ Reproducir
              </button>
              <button className="boton boton-peligro" onClick={() => borrar(n)}>
                Borrar
              </button>
            </div>
          ))}
        </div>
        {/* Un solo reproductor para toda la pantalla. */}
        <audio ref={audioRef} />
      </div>

      <div className="tarjeta">
        <h3>Cómo funcionan las voces</h3>
        {hayApi ? (
          <p className="nota">
            ElevenLabs está configurado: las voces que generes serán reales, con el
            timbre que describa cada voz del catálogo.
          </p>
        ) : (
          <p className="nota">
            <strong>Modo demostración.</strong> Todavía no hay una clave de ElevenLabs
            configurada, así que cada narración suena como un tono de relleno (distinto por
            voz). Toda la función se puede probar así; al añadir la clave{" "}
            <code>ELEVENLABS_API_KEY</code> en el servidor, estas mismas pantallas
            producirán voces reales sin cambiar nada.
          </p>
        )}
        <p className="nota" style={{ marginTop: 10 }}>
          Cada línea narrada se guarda en el historial compartido: es la base para que,
          con el multijugador, el audio suene a la vez para todos los conectados.
        </p>
      </div>
    </div>
  );
}
