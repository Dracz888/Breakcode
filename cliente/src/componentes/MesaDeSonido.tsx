import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api";

interface Props {
  sistemaId: number;
  setError: (m: string) => void;
}

// Cada pista que suena se identifica con una clave única para poder mezclar
// varias a la vez (lluvia + taberna, por ejemplo) con su propio volumen.
const claveIntegrado = (clave: string) => `int:${clave}`;
const claveSubido = (id: number) => `sub:${id}`;

/** La mesa de sonido del DJ: pone atmósferas de fondo en bucle, varias a la vez,
 *  cada una con su volumen. Es la base de la música ambiental sincronizada. */
export default function MesaDeSonido({ sistemaId, setError }: Props) {
  const [integrados, setIntegrados] = useState<api.AmbienteIntegrado[]>([]);
  const [subidos, setSubidos] = useState<api.Ambiente[]>([]);
  const [volumenes, setVolumenes] = useState<Record<string, number>>({});
  const audiosRef = useRef<Record<string, HTMLAudioElement>>({});

  const recargarSubidos = useCallback(
    () =>
      api
        .listarAmbientes(sistemaId)
        .then(setSubidos)
        .catch((e) => setError(e.message)),
    [sistemaId, setError],
  );

  useEffect(() => {
    api.listarAmbientesIntegrados().then(setIntegrados).catch((e) => setError(e.message));
    recargarSubidos();
  }, [recargarSubidos, setError]);

  // Al salir de la pantalla, callar todo lo que esté sonando.
  useEffect(() => {
    const audios = audiosRef.current;
    return () => {
      Object.values(audios).forEach((a) => {
        a.pause();
        a.src = "";
      });
    };
  }, []);

  function detener(clave: string) {
    const audio = audiosRef.current[clave];
    if (audio) {
      audio.pause();
      audio.src = "";
      delete audiosRef.current[clave];
    }
    setVolumenes((v) => {
      const copia = { ...v };
      delete copia[clave];
      return copia;
    });
  }

  function iniciar(clave: string, url: string, bucle: boolean, volumen = 0.6) {
    const audio = new Audio(url);
    audio.loop = bucle;
    audio.volume = volumen;
    if (!bucle) audio.addEventListener("ended", () => detener(clave));
    audio.play().catch(() => {
      /* el navegador puede exigir un toque previo; no es un fallo grave */
    });
    audiosRef.current[clave] = audio;
    setVolumenes((v) => ({ ...v, [clave]: volumen }));
  }

  function alternar(clave: string, url: string, bucle: boolean) {
    if (audiosRef.current[clave]) detener(clave);
    else iniciar(clave, url, bucle);
  }

  // Efecto puntual (choque de armas): suena una vez, sin quedar "encendido".
  function reproducirUnaVez(url: string) {
    const audio = new Audio(url);
    audio.volume = 0.9;
    audio.play().catch(() => {});
  }

  function ajustarVolumen(clave: string, volumen: number) {
    const audio = audiosRef.current[clave];
    if (audio) audio.volume = volumen;
    setVolumenes((v) => ({ ...v, [clave]: volumen }));
  }

  function detenerTodo() {
    Object.keys(audiosRef.current).forEach(detener);
  }

  const sonando = Object.keys(volumenes).length;

  // Pista reutilizable para integrados y subidos.
  function Pista({
    clave,
    url,
    icono,
    nombre,
    descripcion,
    bucle,
    onBorrar,
  }: {
    clave: string;
    url: string;
    icono: string;
    nombre: string;
    descripcion?: string;
    bucle: boolean;
    onBorrar?: () => void;
  }) {
    const activa = clave in volumenes;
    return (
      <div className={`pista ${activa ? "activa" : ""}`}>
        <div className="fila" style={{ gap: 8, alignItems: "flex-start" }}>
          <span className="pista-icono">{icono}</span>
          <div className="espacio">
            <strong>{nombre}</strong>
            {descripcion && <div className="nota">{descripcion}</div>}
          </div>
          {onBorrar && (
            <button
              className="boton boton-peligro"
              title="Borrar"
              onClick={onBorrar}
              style={{ padding: "4px 8px" }}
            >
              ✕
            </button>
          )}
        </div>

        {bucle ? (
          <>
            <button
              className={`boton ${activa ? "" : "boton-secundario"}`}
              onClick={() => alternar(clave, url, true)}
            >
              {activa ? "⏸ Detener" : "▶ Reproducir en bucle"}
            </button>
            {activa && (
              <label className="pista-volumen">
                <span className="nota">Volumen</span>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={Math.round((volumenes[clave] ?? 0) * 100)}
                  onChange={(e) => ajustarVolumen(clave, Number(e.target.value) / 100)}
                />
              </label>
            )}
          </>
        ) : (
          <button className="boton boton-secundario" onClick={() => reproducirUnaVez(url)}>
            🔊 Reproducir
          </button>
        )}
      </div>
    );
  }

  // Agrupa los integrados por categoría para presentarlos ordenados.
  const categorias: string[] = [];
  for (const a of integrados) if (!categorias.includes(a.categoria)) categorias.push(a.categoria);

  return (
    <div>
      <div className="fila" style={{ marginBottom: 12 }}>
        <p className="nota espacio" style={{ margin: 0 }}>
          Pon una o varias atmósferas de fondo a la vez. Suenan solo en tu dispositivo por
          ahora; con el multijugador sonarán sincronizadas para toda la mesa.
        </p>
        {sonando > 0 && (
          <button className="boton boton-peligro" onClick={detenerTodo}>
            Silenciar todo ({sonando})
          </button>
        )}
      </div>

      {categorias.map((categoria) => (
        <section key={categoria} style={{ marginBottom: 18 }}>
          <h3 className="titulo-categoria">{categoria}</h3>
          <div className="mezclador">
            {integrados
              .filter((a) => a.categoria === categoria)
              .map((a) => (
                <Pista
                  key={a.clave}
                  clave={claveIntegrado(a.clave)}
                  url={api.audioAmbienteIntegrado(a.clave)}
                  icono={a.icono}
                  nombre={a.nombre}
                  descripcion={a.descripcion}
                  bucle={a.bucle}
                />
              ))}
          </div>
        </section>
      ))}

      <section>
        <h3 className="titulo-categoria">Mis audios</h3>
        <div className="mezclador">
          {subidos.map((a) => (
            <Pista
              key={a.id}
              clave={claveSubido(a.id)}
              url={api.audioAmbiente(a.id)}
              icono={a.icono}
              nombre={a.nombre}
              descripcion={a.categoria}
              bucle={a.bucle}
              onBorrar={async () => {
                if (!confirm(`¿Borrar el ambiente "${a.nombre}"?`)) return;
                detener(claveSubido(a.id));
                try {
                  await api.borrarAmbiente(a.id);
                  await recargarSubidos();
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            />
          ))}
        </div>
        <FormularioSubida
          sistemaId={sistemaId}
          onSubido={recargarSubidos}
          setError={setError}
        />
      </section>
    </div>
  );
}

// ---------- Subir un audio propio ----------

function FormularioSubida({
  sistemaId,
  onSubido,
  setError,
}: {
  sistemaId: number;
  onSubido: () => Promise<void>;
  setError: (m: string) => void;
}) {
  const [nombre, setNombre] = useState("");
  const [categoria, setCategoria] = useState("Propios");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [subiendo, setSubiendo] = useState(false);
  const entradaRef = useRef<HTMLInputElement>(null);

  async function subir(evento: FormEvent) {
    evento.preventDefault();
    if (!archivo) return;
    setError("");
    setSubiendo(true);
    try {
      await api.subirAmbiente(sistemaId, {
        nombre: nombre || archivo.name.replace(/\.[^.]+$/, ""),
        categoria: categoria || "Propios",
        icono: "🎵",
        bucle: true,
        archivo,
      });
      setNombre("");
      setArchivo(null);
      if (entradaRef.current) entradaRef.current.value = "";
      await onSubido();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubiendo(false);
    }
  }

  return (
    <form className="tarjeta" onSubmit={subir} style={{ marginTop: 12 }}>
      <h3>Subir un audio propio</h3>
      <p className="nota">
        Añade tus propias grabaciones o música (MP3, OGG, WAV). Se reproducen en bucle
        igual que los ambientes integrados.
      </p>
      <div className="fila" style={{ flexWrap: "wrap", gap: 10 }}>
        <label className="campo" style={{ flex: "2 1 180px" }}>
          <span>Nombre</span>
          <input
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Ej. Tema de la posada"
          />
        </label>
        <label className="campo" style={{ flex: "1 1 120px" }}>
          <span>Categoría</span>
          <input
            type="text"
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
            placeholder="Propios"
          />
        </label>
      </div>
      <label className="campo">
        <span>Archivo de audio</span>
        <input
          ref={entradaRef}
          type="file"
          accept="audio/*"
          onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
        />
      </label>
      <button className="boton" type="submit" disabled={!archivo || subiendo}>
        {subiendo ? "Subiendo…" : "Subir ambiente"}
      </button>
    </form>
  );
}
