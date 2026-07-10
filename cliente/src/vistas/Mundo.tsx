import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api";
import type { Pantalla } from "../App";

interface Props {
  mundoId: number;
  sistemaId: number;
  navegar: (p: Pantalla) => void;
}

/** El mapa geográfico: una imagen (o pergamino) sobre la que se colocan
 *  marcadores de lugares. Se navega con arrastre y zoom, como un mapa digital,
 *  y funciona igual con mouse y con el dedo. */
export default function VistaMundo({ mundoId, sistemaId, navegar }: Props) {
  const [mundo, setMundo] = useState<api.MapaGeograficoDetalle | null>(null);
  const [tipos, setTipos] = useState<Record<string, api.TipoMarcador>>({});
  const [error, setError] = useState("");
  const [colocando, setColocando] = useState(false);
  const [seleccion, setSeleccion] = useState<number | null>(null);
  const [pendiente, setPendiente] = useState<{ x: number; y: number } | null>(null);

  // Estado de la cámara (desplazamiento y zoom).
  const [escala, setEscala] = useState(1);
  const [desp, setDesp] = useState({ x: 0, y: 0 });

  const visor = useRef<HTMLDivElement>(null);
  const fondo = useRef<HTMLDivElement>(null);
  const punteros = useRef(new Map<number, { x: number; y: number }>());
  const arrastre = useRef({ movido: 0, activo: false });
  const pellizco = useRef<{ distancia: number } | null>(null);

  const recargar = useCallback(
    () =>
      api
        .verMundo(mundoId)
        .then(setMundo)
        .catch((e) => setError(e.message)),
    [mundoId],
  );

  useEffect(() => {
    recargar();
    api.listarTiposMarcador().then(setTipos).catch((e) => setError(e.message));
  }, [recargar]);

  // ---------- Cámara: arrastre y zoom ----------

  function zoomEn(factor: number, centroX: number, centroY: number) {
    setEscala((prev) => {
      const nueva = Math.min(6, Math.max(0.4, prev * factor));
      const real = nueva / prev;
      // Mantener fijo el punto bajo el cursor/dedos al hacer zoom.
      setDesp((d) => ({
        x: centroX - (centroX - d.x) * real,
        y: centroY - (centroY - d.y) * real,
      }));
      return nueva;
    });
  }

  function alRodar(evento: React.WheelEvent) {
    evento.preventDefault();
    const rect = visor.current!.getBoundingClientRect();
    zoomEn(
      evento.deltaY < 0 ? 1.1 : 1 / 1.1,
      evento.clientX - rect.left,
      evento.clientY - rect.top,
    );
  }

  function alPresionar(evento: React.PointerEvent) {
    (evento.target as Element).setPointerCapture?.(evento.pointerId);
    punteros.current.set(evento.pointerId, { x: evento.clientX, y: evento.clientY });
    arrastre.current = { movido: 0, activo: true };
    if (punteros.current.size === 2) {
      const [a, b] = [...punteros.current.values()];
      pellizco.current = { distancia: Math.hypot(a.x - b.x, a.y - b.y) };
    }
  }

  function alMover(evento: React.PointerEvent) {
    const previo = punteros.current.get(evento.pointerId);
    if (!previo) return;
    const actual = { x: evento.clientX, y: evento.clientY };
    punteros.current.set(evento.pointerId, actual);

    if (punteros.current.size === 2 && pellizco.current) {
      const [a, b] = [...punteros.current.values()];
      const distancia = Math.hypot(a.x - b.x, a.y - b.y);
      const rect = visor.current!.getBoundingClientRect();
      const centroX = (a.x + b.x) / 2 - rect.left;
      const centroY = (a.y + b.y) / 2 - rect.top;
      zoomEn(distancia / pellizco.current.distancia, centroX, centroY);
      pellizco.current.distancia = distancia;
      arrastre.current.movido += 10;
      return;
    }

    if (arrastre.current.activo) {
      const dx = actual.x - previo.x;
      const dy = actual.y - previo.y;
      arrastre.current.movido += Math.abs(dx) + Math.abs(dy);
      setDesp((d) => ({ x: d.x + dx, y: d.y + dy }));
    }
  }

  function alSoltar(evento: React.PointerEvent) {
    const eraToque = punteros.current.size === 1 && arrastre.current.movido < 6;
    punteros.current.delete(evento.pointerId);
    if (punteros.current.size < 2) pellizco.current = null;
    if (punteros.current.size === 0) arrastre.current.activo = false;
    if (eraToque) tocar(evento);
  }

  // ---------- Colocar marcadores ----------

  function tocar(evento: React.PointerEvent) {
    if (!colocando || !fondo.current) return;
    const rect = fondo.current.getBoundingClientRect();
    const x = (evento.clientX - rect.left) / rect.width;
    const y = (evento.clientY - rect.top) / rect.height;
    if (x < 0 || y < 0 || x > 1 || y > 1) return;
    setPendiente({ x, y });
    setSeleccion(null);
  }

  async function borrar(marcador: api.Marcador) {
    if (!confirm(`¿Borrar el marcador "${marcador.nombre}"?`)) return;
    setError("");
    try {
      await api.borrarMarcador(marcador.id);
      setSeleccion(null);
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (!mundo) {
    return error ? <div className="error">{error}</div> : <p className="nota">Cargando…</p>;
  }

  const marcadorSel = mundo.marcadores.find((m) => m.id === seleccion) ?? null;
  const fondoEstilo = mundo.imagen_url
    ? { backgroundImage: `url(${mundo.imagen_url})` }
    : undefined;

  return (
    <>
      <header className="cabecera">
        <button className="boton-volver" onClick={() => navegar({ nombre: "sistema", sistemaId })}>
          ← Volver
        </button>
        <h1>🗺 {mundo.nombre}</h1>
        <span className="subtitulo">
          Arrastra para moverte, usa la rueda o pellizca para acercarte.
        </span>
      </header>

      <div className="pestanas">
        <button
          className={colocando ? "activa" : ""}
          onClick={() => {
            setColocando((v) => !v);
            setPendiente(null);
          }}
        >
          📍 {colocando ? "Colocando… (toca el mapa)" : "Colocar marcador"}
        </button>
        <button onClick={() => zoomEn(1.25, (visor.current?.clientWidth ?? 0) / 2, (visor.current?.clientHeight ?? 0) / 2)}>
          ＋
        </button>
        <button onClick={() => zoomEn(0.8, (visor.current?.clientWidth ?? 0) / 2, (visor.current?.clientHeight ?? 0) / 2)}>
          －
        </button>
        <button
          onClick={() => {
            setEscala(1);
            setDesp({ x: 0, y: 0 });
          }}
        >
          Centrar
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="mundo-disposicion">
        <div
          className="mundo-visor"
          ref={visor}
          onWheel={alRodar}
          onPointerDown={alPresionar}
          onPointerMove={alMover}
          onPointerUp={alSoltar}
          onPointerCancel={alSoltar}
          style={{ cursor: colocando ? "crosshair" : "grab", touchAction: "none" }}
        >
          <div
            className="mundo-camara"
            style={{ transform: `translate(${desp.x}px, ${desp.y}px) scale(${escala})` }}
          >
            <div className={`mundo-fondo ${mundo.imagen_url ? "" : "pergamino"}`} ref={fondo} style={fondoEstilo}>
              {mundo.marcadores.map((m) => {
                const tipo = tipos[m.tipo];
                return (
                  <button
                    key={m.id}
                    className={`marcador ${seleccion === m.id ? "activo" : ""}`}
                    style={{ left: `${m.x * 100}%`, top: `${m.y * 100}%` }}
                    title={m.nombre}
                    onPointerDown={(e) => e.stopPropagation()}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSeleccion(m.id === seleccion ? null : m.id);
                      setPendiente(null);
                    }}
                  >
                    <span className="pin" style={{ background: tipo?.color ?? "#7a9ec7" }}>
                      {tipo?.simbolo ?? "📍"}
                    </span>
                    <span className="etiqueta">{m.nombre}</span>
                  </button>
                );
              })}
              {pendiente && (
                <span
                  className="marcador-pendiente"
                  style={{ left: `${pendiente.x * 100}%`, top: `${pendiente.y * 100}%` }}
                >
                  ✛
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="mundo-panel">
          {pendiente ? (
            <FormularioMarcador
              tipos={tipos}
              onCancelar={() => setPendiente(null)}
              onGuardar={async (datos) => {
                setError("");
                try {
                  await api.crearMarcador(mundo.id, { ...datos, ...pendiente });
                  setPendiente(null);
                  setColocando(false);
                  await recargar();
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            />
          ) : marcadorSel ? (
            <DetalleMarcador
              marcador={marcadorSel}
              tipos={tipos}
              onBorrar={() => borrar(marcadorSel)}
              onGuardar={async (datos) => {
                setError("");
                try {
                  await api.editarMarcador(marcadorSel.id, datos);
                  await recargar();
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            />
          ) : (
            <>
              <h3>Lugares del mundo</h3>
              {mundo.marcadores.length === 0 ? (
                <p className="nota">
                  Aún no hay lugares. Pulsa "Colocar marcador" y toca el mapa donde
                  quieras poner una ciudad, una mazmorra o un punto de interés.
                </p>
              ) : (
                <p className="nota">
                  Toca un marcador del mapa para ver o editar su lugar. Hay{" "}
                  {mundo.marcadores.length}{" "}
                  {mundo.marcadores.length === 1 ? "lugar marcado" : "lugares marcados"}.
                </p>
              )}
              <ul className="lista-lugares">
                {mundo.marcadores.map((m) => (
                  <li key={m.id}>
                    <button className="chip-clave" onClick={() => setSeleccion(m.id)}>
                      {tipos[m.tipo]?.simbolo ?? "📍"} {m.nombre}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </>
  );
}

// ---------- Formulario de nuevo marcador ----------

function FormularioMarcador({
  tipos,
  onGuardar,
  onCancelar,
}: {
  tipos: Record<string, api.TipoMarcador>;
  onGuardar: (datos: { nombre: string; tipo: string; descripcion: string }) => Promise<void>;
  onCancelar: () => void;
}) {
  const [nombre, setNombre] = useState("");
  const [tipo, setTipo] = useState("ciudad");
  const [descripcion, setDescripcion] = useState("");

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    await onGuardar({ nombre, tipo, descripcion });
  }

  return (
    <>
      <h3>Nuevo lugar</h3>
      <p className="nota">El marcador se pondrá donde tocaste el mapa.</p>
      <form onSubmit={enviar}>
        <label className="campo">
          <span>Nombre</span>
          <input
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Ej. Puerto Gris"
            autoFocus
            required
          />
        </label>
        <label className="campo">
          <span>Tipo</span>
          <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
            {Object.entries(tipos).map(([clave, t]) => (
              <option key={clave} value={clave}>
                {t.simbolo} {t.nombre}
              </option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Descripción (opcional)</span>
          <textarea
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            placeholder="¿Qué es este lugar?"
            rows={3}
          />
        </label>
        <div className="fila">
          <button className="boton" type="submit">
            Guardar lugar
          </button>
          <button className="boton boton-secundario" type="button" onClick={onCancelar}>
            Cancelar
          </button>
        </div>
      </form>
    </>
  );
}

// ---------- Detalle / edición de un marcador ----------

function DetalleMarcador({
  marcador,
  tipos,
  onGuardar,
  onBorrar,
}: {
  marcador: api.Marcador;
  tipos: Record<string, api.TipoMarcador>;
  onGuardar: (datos: { nombre: string; tipo: string; descripcion: string }) => Promise<void>;
  onBorrar: () => void;
}) {
  const [nombre, setNombre] = useState(marcador.nombre);
  const [tipo, setTipo] = useState(marcador.tipo);
  const [descripcion, setDescripcion] = useState(marcador.descripcion);

  useEffect(() => {
    setNombre(marcador.nombre);
    setTipo(marcador.tipo);
    setDescripcion(marcador.descripcion);
  }, [marcador.id, marcador.nombre, marcador.tipo, marcador.descripcion]);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    await onGuardar({ nombre, tipo, descripcion });
  }

  return (
    <>
      <h3>{tipos[marcador.tipo]?.simbolo ?? "📍"} Editar lugar</h3>
      <form onSubmit={enviar}>
        <label className="campo">
          <span>Nombre</span>
          <input type="text" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
        </label>
        <label className="campo">
          <span>Tipo</span>
          <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
            {Object.entries(tipos).map(([clave, t]) => (
              <option key={clave} value={clave}>
                {t.simbolo} {t.nombre}
              </option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Descripción</span>
          <textarea
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            rows={3}
          />
        </label>
        <div className="fila">
          <button className="boton" type="submit">
            Guardar cambios
          </button>
          <button className="boton boton-peligro" type="button" onClick={onBorrar}>
            Borrar
          </button>
        </div>
      </form>
    </>
  );
}
