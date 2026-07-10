import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api";
import type { Pantalla } from "../App";

interface Props {
  mapaId: number;
  sistemaId: number;
  navegar: (p: Pantalla) => void;
}

type Modo = "pintar" | "fichas" | "niebla";

/** El mapa de batalla: una cuadrícula que se pinta como en Paint y sobre la
 *  que se colocan y mueven las fichas. Todo funciona con mouse y con el dedo. */
export default function VistaMapa({ mapaId, sistemaId, navegar }: Props) {
  const [mapa, setMapa] = useState<api.MapaDetalle | null>(null);
  const [terrenos, setTerrenos] = useState<Record<string, api.Terreno>>({});
  const [personajes, setPersonajes] = useState<api.Personaje[]>([]);
  const [modo, setModo] = useState<Modo>("pintar");
  const [terrenoSel, setTerrenoSel] = useState("pasto");
  const [tokenSel, setTokenSel] = useState<number | null>(null);
  const [colocando, setColocando] = useState<number | null>(null);
  const [ocultar, setOcultar] = useState(true); // pincel de niebla: tapar o revelar
  const [error, setError] = useState("");

  const lienzo = useRef<HTMLCanvasElement>(null);
  const contenedor = useRef<HTMLDivElement>(null);
  const pintando = useRef(false);
  const cambiosPendientes = useRef(new Map<string, { x: number; y: number; terreno: string }>());
  const temporizadorEnvio = useRef<number | undefined>(undefined);
  const cambiosNiebla = useRef(new Map<string, { x: number; y: number; oculta: boolean }>());
  const temporizadorNiebla = useRef<number | undefined>(undefined);

  useEffect(() => {
    api.verMapa(mapaId).then(setMapa).catch((e) => setError(e.message));
    api.listarTerrenos().then(setTerrenos).catch((e) => setError(e.message));
    api.listarPersonajes(sistemaId).then(setPersonajes).catch((e) => setError(e.message));
  }, [mapaId, sistemaId]);

  // ---------- Dibujo ----------

  const dibujar = useCallback(() => {
    const canvas = lienzo.current;
    const cont = contenedor.current;
    if (!canvas || !cont || !mapa || !Object.keys(terrenos).length) return;

    const celda = Math.max(12, Math.min(48, Math.floor(cont.clientWidth / mapa.ancho)));
    const dpr = window.devicePixelRatio || 1;
    canvas.width = mapa.ancho * celda * dpr;
    canvas.height = mapa.alto * celda * dpr;
    canvas.style.width = `${mapa.ancho * celda}px`;
    canvas.style.height = `${mapa.alto * celda}px`;
    const ctx = canvas.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    for (let y = 0; y < mapa.alto; y++) {
      for (let x = 0; x < mapa.ancho; x++) {
        const terreno = terrenos[mapa.celdas[y][x]];
        ctx.fillStyle = terreno?.color ?? "#333";
        ctx.fillRect(x * celda, y * celda, celda, celda);
        if (terreno?.simbolo) {
          ctx.font = `${celda * 0.65}px serif`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(terreno.simbolo, x * celda + celda / 2, y * celda + celda / 2 + 1);
        }
      }
    }

    // Líneas de la cuadrícula
    ctx.strokeStyle = "rgba(0,0,0,0.25)";
    ctx.lineWidth = 1;
    for (let x = 0; x <= mapa.ancho; x++) {
      ctx.beginPath();
      ctx.moveTo(x * celda + 0.5, 0);
      ctx.lineTo(x * celda + 0.5, mapa.alto * celda);
      ctx.stroke();
    }
    for (let y = 0; y <= mapa.alto; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * celda + 0.5);
      ctx.lineTo(mapa.ancho * celda, y * celda + 0.5);
      ctx.stroke();
    }

    // Fichas
    for (const token of mapa.tokens) {
      const cx = token.x * celda + celda / 2;
      const cy = token.y * celda + celda / 2;
      const radio = celda * 0.38;
      ctx.beginPath();
      ctx.arc(cx, cy, radio, 0, Math.PI * 2);
      ctx.fillStyle = token.es_monstruo ? "#a33b2a" : "#c9a35c";
      ctx.fill();
      ctx.lineWidth = token.id === tokenSel ? 3 : 1.5;
      ctx.strokeStyle = token.id === tokenSel ? "#ffffff" : "rgba(0,0,0,0.55)";
      ctx.stroke();
      ctx.fillStyle = "#1c1712";
      ctx.font = `bold ${celda * 0.42}px Georgia, serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(token.nombre.charAt(0).toUpperCase(), cx, cy + 1);
    }

    // Niebla de guerra: las celdas ocultas se cubren con un velo oscuro.
    // Se dibuja al final para tapar también terreno y fichas de esa zona.
    for (let y = 0; y < mapa.alto; y++) {
      for (let x = 0; x < mapa.ancho; x++) {
        if (!mapa.niebla?.[y]?.[x]) continue;
        ctx.fillStyle = modo === "niebla" ? "rgba(10,8,6,0.72)" : "rgba(6,5,4,0.94)";
        ctx.fillRect(x * celda, y * celda, celda, celda);
      }
    }
  }, [mapa, terrenos, tokenSel, modo]);

  useEffect(() => {
    dibujar();
    window.addEventListener("resize", dibujar);
    return () => window.removeEventListener("resize", dibujar);
  }, [dibujar]);

  // ---------- Pintar ----------

  function celdaDesdeEvento(evento: React.PointerEvent): { x: number; y: number } | null {
    const canvas = lienzo.current;
    if (!canvas || !mapa) return null;
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor(((evento.clientX - rect.left) / rect.width) * mapa.ancho);
    const y = Math.floor(((evento.clientY - rect.top) / rect.height) * mapa.alto);
    if (x < 0 || y < 0 || x >= mapa.ancho || y >= mapa.alto) return null;
    return { x, y };
  }

  function pintarCelda(x: number, y: number) {
    if (!mapa || mapa.celdas[y][x] === terrenoSel) return;
    const celdas = mapa.celdas.map((fila) => fila.slice());
    celdas[y][x] = terrenoSel;
    setMapa({ ...mapa, celdas });
    cambiosPendientes.current.set(`${x},${y}`, { x, y, terreno: terrenoSel });
    window.clearTimeout(temporizadorEnvio.current);
    temporizadorEnvio.current = window.setTimeout(enviarCambios, 600);
  }

  async function enviarCambios() {
    const cambios = [...cambiosPendientes.current.values()];
    if (!cambios.length) return;
    cambiosPendientes.current.clear();
    try {
      await api.pintarCeldas(mapaId, cambios);
    } catch (e) {
      setError((e as Error).message);
      api.verMapa(mapaId).then(setMapa).catch(() => undefined);
    }
  }

  // ---------- Niebla de guerra ----------

  function pintarNieblaCelda(x: number, y: number) {
    if (!mapa || (mapa.niebla?.[y]?.[x] ?? false) === ocultar) return;
    const niebla = mapa.niebla.map((fila) => fila.slice());
    niebla[y][x] = ocultar;
    setMapa({ ...mapa, niebla });
    cambiosNiebla.current.set(`${x},${y}`, { x, y, oculta: ocultar });
    window.clearTimeout(temporizadorNiebla.current);
    temporizadorNiebla.current = window.setTimeout(enviarNiebla, 600);
  }

  async function enviarNiebla() {
    const cambios = [...cambiosNiebla.current.values()];
    if (!cambios.length) return;
    cambiosNiebla.current.clear();
    try {
      await api.pintarNiebla(mapaId, cambios);
    } catch (e) {
      setError((e as Error).message);
      api.verMapa(mapaId).then(setMapa).catch(() => undefined);
    }
  }

  // ---------- Fichas ----------

  async function tocarCelda(x: number, y: number) {
    if (!mapa) return;
    setError("");
    const tokenAqui = mapa.tokens.find((t) => t.x === x && t.y === y);

    try {
      if (colocando !== null) {
        const token = await api.colocarToken(mapaId, { personaje_id: colocando, x, y });
        setMapa({ ...mapa, tokens: [...mapa.tokens, token] });
        setColocando(null);
        setTokenSel(token.id);
      } else if (tokenAqui) {
        setTokenSel(tokenAqui.id === tokenSel ? null : tokenAqui.id);
      } else if (tokenSel !== null) {
        const movido = await api.moverToken(tokenSel, x, y);
        setMapa({
          ...mapa,
          tokens: mapa.tokens.map((t) => (t.id === movido.id ? movido : t)),
        });
      }
    } catch (e) {
      setError((e as Error).message); // ej. "No se puede pasar por ahí: hay muro"
    }
  }

  async function quitarSeleccionado() {
    if (tokenSel === null || !mapa) return;
    try {
      await api.quitarToken(tokenSel);
      setMapa({ ...mapa, tokens: mapa.tokens.filter((t) => t.id !== tokenSel) });
      setTokenSel(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  // ---------- Eventos del lienzo ----------

  function alPresionar(evento: React.PointerEvent) {
    const celda = celdaDesdeEvento(evento);
    if (!celda) return;
    if (modo === "pintar") {
      pintando.current = true;
      pintarCelda(celda.x, celda.y);
    } else if (modo === "niebla") {
      pintando.current = true;
      pintarNieblaCelda(celda.x, celda.y);
    } else {
      tocarCelda(celda.x, celda.y);
    }
  }

  function alMover(evento: React.PointerEvent) {
    if (!pintando.current) return;
    const celda = celdaDesdeEvento(evento);
    if (!celda) return;
    if (modo === "pintar") pintarCelda(celda.x, celda.y);
    else if (modo === "niebla") pintarNieblaCelda(celda.x, celda.y);
  }

  function alSoltar() {
    pintando.current = false;
  }

  if (!mapa) {
    return error ? <div className="error">{error}</div> : <p className="nota">Cargando…</p>;
  }

  const enMapa = new Set(mapa.tokens.map((t) => t.personaje_id));
  const seleccionado = mapa.tokens.find((t) => t.id === tokenSel);

  return (
    <>
      <header className="cabecera">
        <button className="boton-volver" onClick={() => navegar({ nombre: "sistema", sistemaId })}>
          ← Volver
        </button>
        <h1>{mapa.nombre}</h1>
        <span className="subtitulo">
          {mapa.ancho} × {mapa.alto} celdas
        </span>
      </header>

      <div className="pestanas">
        <button className={modo === "pintar" ? "activa" : ""} onClick={() => { setModo("pintar"); setTokenSel(null); setColocando(null); }}>
          🖌 Pintar terreno
        </button>
        <button className={modo === "fichas" ? "activa" : ""} onClick={() => setModo("fichas")}>
          ♟ Fichas
        </button>
        <button className={modo === "niebla" ? "activa" : ""} onClick={() => { setModo("niebla"); setTokenSel(null); setColocando(null); }}>
          🌫 Niebla
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="mapa-disposicion">
        <div className="mapa-lienzo" ref={contenedor}>
          <canvas
            ref={lienzo}
            onPointerDown={alPresionar}
            onPointerMove={alMover}
            onPointerUp={alSoltar}
            onPointerLeave={alSoltar}
            style={{ touchAction: "none", cursor: modo === "fichas" ? "pointer" : "crosshair" }}
          />
        </div>

        <div className="mapa-panel">
          {modo === "niebla" ? (
            <>
              <h3>Niebla de guerra</h3>
              <p className="nota">
                Tapa zonas que el jugador no debe ver todavía y revélalas a medida que
                el grupo explora. Elige el pincel y arrastra sobre el mapa.
              </p>
              <div className="pestanas">
                <button className={ocultar ? "activa" : ""} onClick={() => setOcultar(true)}>
                  🌫 Tapar
                </button>
                <button className={!ocultar ? "activa" : ""} onClick={() => setOcultar(false)}>
                  👁 Revelar
                </button>
              </div>
              <button
                className="boton boton-secundario"
                style={{ marginTop: 12 }}
                onClick={() => {
                  if (!mapa) return;
                  const cambios = [];
                  for (let y = 0; y < mapa.alto; y++)
                    for (let x = 0; x < mapa.ancho; x++)
                      if (mapa.niebla?.[y]?.[x]) cambios.push({ x, y, oculta: false });
                  if (!cambios.length) return;
                  setMapa({ ...mapa, niebla: mapa.niebla.map((f) => f.map(() => false)) });
                  api.pintarNiebla(mapaId, cambios).catch((e) => setError((e as Error).message));
                }}
              >
                Revelar todo el mapa
              </button>
            </>
          ) : modo === "pintar" ? (
            <>
              <h3>Paleta de terrenos</h3>
              <p className="nota">Elige un terreno y pinta arrastrando sobre el mapa.</p>
              <div className="paleta-terrenos">
                {Object.entries(terrenos).map(([clave, t]) => (
                  <button
                    key={clave}
                    className={`terreno ${terrenoSel === clave ? "activo" : ""}`}
                    onClick={() => setTerrenoSel(clave)}
                  >
                    <span className="muestra" style={{ background: t.color }}>
                      {t.simbolo}
                    </span>
                    {t.nombre}
                    {t.bloquea && <span className="nota"> · bloquea</span>}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <>
              <h3>Fichas</h3>
              {seleccionado ? (
                <p className="nota">
                  <strong>{seleccionado.nombre}</strong> seleccionado: toca una celda libre
                  para moverlo.
                </p>
              ) : colocando !== null ? (
                <p className="nota">Toca una celda del mapa para colocar la ficha.</p>
              ) : (
                <p className="nota">
                  Toca una ficha del mapa para seleccionarla, o coloca una nueva:
                </p>
              )}
              {seleccionado && (
                <button className="boton boton-peligro" onClick={quitarSeleccionado} style={{ marginBottom: 12 }}>
                  Quitar del mapa a {seleccionado.nombre}
                </button>
              )}
              {personajes
                .filter((p) => !enMapa.has(p.id))
                .map((p) => (
                  <div key={p.id} className="fila" style={{ marginBottom: 8 }}>
                    <span className="espacio">
                      {p.nombre} {p.es_monstruo && <span className="insignia-monstruo">monstruo</span>}
                    </span>
                    <button
                      className={`boton ${colocando === p.id ? "" : "boton-secundario"}`}
                      onClick={() => setColocando(colocando === p.id ? null : p.id)}
                    >
                      {colocando === p.id ? "Elige celda…" : "Colocar"}
                    </button>
                  </div>
                ))}
              {personajes.length === 0 && (
                <p className="nota">Este sistema aún no tiene fichas: créalas en la pestaña "Fichas".</p>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
