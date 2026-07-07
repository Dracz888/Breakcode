import { FormEvent, useCallback, useEffect, useState } from "react";
import * as api from "../api";
import type { Pantalla } from "../App";

interface Props {
  campanaId: number;
  sistemaId: number;
  navegar: (p: Pantalla) => void;
}

/** La pantalla de una campaña: su historia en arcos y eventos.
 *  Registrar eventos (qué pasó, cuándo, con quién y dónde) construye la línea
 *  de tiempo de la trama. */
export default function VistaCampana({ campanaId, sistemaId, navegar }: Props) {
  const [campana, setCampana] = useState<api.CampanaDetalle | null>(null);
  const [personajes, setPersonajes] = useState<api.PersonajeBreve[]>([]);
  const [lugares, setLugares] = useState<api.MarcadorBreve[]>([]);
  const [error, setError] = useState("");
  const [tituloArco, setTituloArco] = useState("");

  const recargar = useCallback(
    () =>
      api
        .verCampana(campanaId)
        .then(setCampana)
        .catch((e) => setError(e.message)),
    [campanaId],
  );

  useEffect(() => {
    recargar();
    api
      .listarPersonajes(sistemaId)
      .then((ps) =>
        setPersonajes(ps.map((p) => ({ id: p.id, nombre: p.nombre, es_monstruo: p.es_monstruo }))),
      )
      .catch((e) => setError(e.message));
    // Los lugares disponibles son los marcadores de todos los mapas del mundo.
    api
      .listarMundos(sistemaId)
      .then(async (mundos) => {
        const detalles = await Promise.all(mundos.map((m) => api.verMundo(m.id)));
        setLugares(
          detalles.flatMap((d) =>
            d.marcadores.map((m) => ({ id: m.id, nombre: m.nombre, tipo: m.tipo })),
          ),
        );
      })
      .catch((e) => setError(e.message));
  }, [recargar, sistemaId]);

  async function crearArco(evento: FormEvent) {
    evento.preventDefault();
    setError("");
    try {
      await api.crearArco(campanaId, { titulo: tituloArco, descripcion: "" });
      setTituloArco("");
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function borrarArco(arco: api.Arco) {
    if (!confirm(`¿Borrar el arco "${arco.titulo}" y todos sus eventos?`)) return;
    setError("");
    try {
      await api.borrarArco(arco.id);
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (!campana) {
    return error ? <div className="error">{error}</div> : <p className="nota">Cargando…</p>;
  }

  const totalEventos = campana.arcos.reduce((n, a) => n + a.eventos.length, 0);

  return (
    <>
      <header className="cabecera">
        <button className="boton-volver" onClick={() => navegar({ nombre: "sistema", sistemaId })}>
          ← Volver
        </button>
        <h1>📖 {campana.nombre}</h1>
        <span className="subtitulo">
          {campana.descripcion ? `${campana.descripcion} · ` : ""}
          {campana.arcos.length} {campana.arcos.length === 1 ? "arco" : "arcos"} ·{" "}
          {totalEventos} {totalEventos === 1 ? "evento" : "eventos"}
        </span>
      </header>

      {error && <div className="error">{error}</div>}

      {campana.arcos.length === 0 && (
        <p className="nota">
          Aún no hay arcos. Un arco es un capítulo de la historia; dentro de él
          registrarás los eventos. Crea el primero aquí abajo.
        </p>
      )}

      <div className="linea-tiempo">
        {campana.arcos.map((arco) => (
          <Arco
            key={arco.id}
            arco={arco}
            personajes={personajes}
            lugares={lugares}
            recargar={recargar}
            setError={setError}
            onBorrar={() => borrarArco(arco)}
          />
        ))}
      </div>

      <div className="tarjeta" style={{ marginTop: 20 }}>
        <h3>Nuevo arco</h3>
        <form onSubmit={crearArco}>
          <label className="campo">
            <span>Título del arco (capítulo)</span>
            <input
              type="text"
              value={tituloArco}
              onChange={(e) => setTituloArco(e.target.value)}
              placeholder="Ej. La sombra sobre el puerto"
              required
            />
          </label>
          <button className="boton" type="submit">
            Añadir arco
          </button>
        </form>
      </div>
    </>
  );
}

// ---------- Un arco con sus eventos ----------

function Arco({
  arco,
  personajes,
  lugares,
  recargar,
  setError,
  onBorrar,
}: {
  arco: api.Arco;
  personajes: api.PersonajeBreve[];
  lugares: api.MarcadorBreve[];
  recargar: () => Promise<void>;
  setError: (m: string) => void;
  onBorrar: () => void;
}) {
  const [anadiendo, setAnadiendo] = useState(false);
  const [editando, setEditando] = useState<number | null>(null);

  async function borrarEvento(evento: api.Evento) {
    if (!confirm(`¿Borrar el evento "${evento.titulo}"?`)) return;
    setError("");
    try {
      await api.borrarEvento(evento.id);
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="arco">
      <div className="arco-cabecera">
        <h2>{arco.titulo}</h2>
        <button className="boton boton-peligro" onClick={onBorrar}>
          Borrar arco
        </button>
      </div>
      {arco.descripcion && <p className="nota">{arco.descripcion}</p>}

      {arco.eventos.length === 0 && !anadiendo && (
        <p className="nota">Este arco todavía no tiene eventos.</p>
      )}

      <ol className="eventos">
        {arco.eventos.map((evento) =>
          editando === evento.id ? (
            <li key={evento.id} className="evento">
              <EventoEditor
                personajes={personajes}
                lugares={lugares}
                inicial={evento}
                onCancelar={() => setEditando(null)}
                onGuardar={async (datos) => {
                  setError("");
                  try {
                    await api.editarEvento(evento.id, datos);
                    setEditando(null);
                    await recargar();
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              />
            </li>
          ) : (
            <li key={evento.id} className="evento">
              <div className="fila">
                <div className="espacio">
                  <h3>{evento.titulo}</h3>
                  {evento.fecha && <span className="evento-fecha">📅 {evento.fecha}</span>}
                </div>
                <button
                  className="boton boton-secundario"
                  onClick={() => setEditando(evento.id)}
                >
                  Editar
                </button>
                <button className="boton boton-peligro" onClick={() => borrarEvento(evento)}>
                  Borrar
                </button>
              </div>
              {evento.descripcion && <p className="evento-desc">{evento.descripcion}</p>}
              <div className="evento-meta">
                {evento.marcador && (
                  <span className="chip">📍 {evento.marcador.nombre}</span>
                )}
                {evento.personajes.map((p) => (
                  <span key={p.id} className="chip">
                    {p.es_monstruo ? "👹" : "🙂"} {p.nombre}
                  </span>
                ))}
              </div>
            </li>
          ),
        )}
      </ol>

      {anadiendo ? (
        <div className="evento">
          <EventoEditor
            personajes={personajes}
            lugares={lugares}
            onCancelar={() => setAnadiendo(false)}
            onGuardar={async (datos) => {
              setError("");
              try {
                await api.crearEvento(arco.id, datos);
                setAnadiendo(false);
                await recargar();
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          />
        </div>
      ) : (
        <button className="boton boton-secundario" onClick={() => setAnadiendo(true)}>
          + Añadir evento
        </button>
      )}
    </div>
  );
}

// ---------- Editor de un evento (sirve para crear y para editar) ----------

function EventoEditor({
  personajes,
  lugares,
  inicial,
  onGuardar,
  onCancelar,
}: {
  personajes: api.PersonajeBreve[];
  lugares: api.MarcadorBreve[];
  inicial?: api.Evento;
  onGuardar: (datos: {
    titulo: string;
    fecha: string;
    descripcion: string;
    marcador_id: number | null;
    personajes: number[];
  }) => Promise<void>;
  onCancelar: () => void;
}) {
  const [titulo, setTitulo] = useState(inicial?.titulo ?? "");
  const [fecha, setFecha] = useState(inicial?.fecha ?? "");
  const [descripcion, setDescripcion] = useState(inicial?.descripcion ?? "");
  const [marcadorId, setMarcadorId] = useState<number | null>(inicial?.marcador?.id ?? null);
  const [seleccion, setSeleccion] = useState<Set<number>>(
    new Set(inicial?.personajes.map((p) => p.id) ?? []),
  );

  function alternar(id: number) {
    setSeleccion((prev) => {
      const copia = new Set(prev);
      copia.has(id) ? copia.delete(id) : copia.add(id);
      return copia;
    });
  }

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    await onGuardar({
      titulo,
      fecha,
      descripcion,
      marcador_id: marcadorId,
      personajes: [...seleccion],
    });
  }

  return (
    <form onSubmit={enviar}>
      <label className="campo">
        <span>¿Qué pasó?</span>
        <input
          type="text"
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="Ej. Emboscada en el muelle"
          autoFocus
          required
        />
      </label>
      <label className="campo">
        <span>Fecha del mundo (texto libre, opcional)</span>
        <input
          type="text"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
          placeholder="Ej. Día 3 del Ocaso"
        />
      </label>
      <label className="campo">
        <span>Lugar</span>
        <select
          value={marcadorId ?? ""}
          onChange={(e) => setMarcadorId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">— Sin lugar —</option>
          {lugares.map((l) => (
            <option key={l.id} value={l.id}>
              {l.nombre}
            </option>
          ))}
        </select>
        {lugares.length === 0 && (
          <span className="nota">
            No hay lugares aún; márcalos en la pestaña "Mundo" del sistema.
          </span>
        )}
      </label>
      <label className="campo">
        <span>Descripción (opcional)</span>
        <textarea
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          placeholder="Cuenta lo que ocurrió…"
          rows={3}
        />
      </label>
      <div className="campo">
        <span>Personajes involucrados</span>
        {personajes.length === 0 ? (
          <span className="nota">Este sistema aún no tiene fichas.</span>
        ) : (
          <div className="paleta-claves">
            {personajes.map((p) => (
              <button
                key={p.id}
                type="button"
                className={`chip-clave ${seleccion.has(p.id) ? "activo" : ""}`}
                onClick={() => alternar(p.id)}
              >
                {seleccion.has(p.id) ? "✓ " : ""}
                {p.nombre}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="fila">
        <button className="boton" type="submit">
          {inicial ? "Guardar cambios" : "Guardar evento"}
        </button>
        <button className="boton boton-secundario" type="button" onClick={onCancelar}>
          Cancelar
        </button>
      </div>
    </form>
  );
}
