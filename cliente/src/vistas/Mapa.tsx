import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api";
import type { Pantalla } from "../App";

interface Props {
  mapaId: number;
  sistemaId: number;
  navegar: (p: Pantalla) => void;
}

type Modo = "pintar" | "fichas" | "combate" | "niebla";

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
  const [conectados, setConectados] = useState(1);
  const [tiradas, setTiradas] = useState<api.Tirada[]>([]);
  const [combate, setCombate] = useState<api.Combate | null>(null);
  const [expresion, setExpresion] = useState("1d20");
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
    api.listarTiradas(mapaId).then(setTiradas).catch(() => undefined);
    api.verCombate(mapaId).then(setCombate).catch(() => undefined);
  }, [mapaId, sistemaId]);

  // ---------- Multijugador: escuchar los cambios de los demás ----------

  useEffect(() => {
    const cerrarSala = api.conectarMapa(
      mapaId,
      (evento) => {
        if (evento.tipo === "presencia") {
          setConectados(evento.datos.conectados);
          return;
        }
        if (evento.tipo === "tirada") {
          setTiradas((prev) =>
            (prev.some((t) => t.id === evento.datos.id) ? prev : [...prev, evento.datos]).slice(-50),
          );
          return;
        }
        if (evento.tipo === "combate") {
          setCombate(evento.datos);
          return;
        }
        if (evento.tipo === "combate_terminado") {
          setCombate(null);
          return;
        }
        if (evento.tipo === "token_quitado") {
          const idQuitado = evento.datos.id;
          setTokenSel((sel) => (sel === idQuitado ? null : sel));
        }
        setMapa((prev) => {
          if (!prev) return prev;
          switch (evento.tipo) {
            case "terreno": {
              const celdas = prev.celdas.map((fila) => fila.slice());
              for (const c of evento.datos.cambios) {
                if (celdas[c.y] && c.x >= 0 && c.x < celdas[c.y].length) celdas[c.y][c.x] = c.terreno;
              }
              return { ...prev, celdas };
            }
            case "token_colocado":
            case "token_movido":
            case "token_actualizado": {
              const token = evento.datos;
              const tokens = prev.tokens.some((t) => t.id === token.id)
                ? prev.tokens.map((t) => (t.id === token.id ? token : t))
                : [...prev.tokens, token];
              return { ...prev, tokens };
            }
            case "token_quitado":
              return { ...prev, tokens: prev.tokens.filter((t) => t.id !== evento.datos.id) };
            default:
              return prev;
          }
        });
      },
      // Al reconectar tras una caída, volvemos a pedir el estado completo por si
      // se perdió algún cambio mientras la línea estuvo cortada.
      () => {
        api.verMapa(mapaId).then(setMapa).catch(() => undefined);
        api.listarTiradas(mapaId).then(setTiradas).catch(() => undefined);
        api.verCombate(mapaId).then(setCombate).catch(() => undefined);
      },
    );
    return cerrarSala;
  }, [mapaId]);

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

      // Resaltado de la ficha a la que le toca jugar.
      if (combate?.token_en_turno === token.id) {
        ctx.beginPath();
        ctx.arc(cx, cy, radio + 3, 0, Math.PI * 2);
        ctx.lineWidth = 3;
        ctx.strokeStyle = "#e3bd72";
        ctx.stroke();
      }

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

      // Barra de vida (solo si el sistema define vida).
      if (token.vida_maxima != null && token.vida_actual != null) {
        const ancho = celda * 0.8;
        const alto = Math.max(3, celda * 0.11);
        const bx = cx - ancho / 2;
        const by = token.y * celda + celda - alto - 1;
        const fraccion = token.vida_maxima > 0 ? token.vida_actual / token.vida_maxima : 0;
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.fillRect(bx, by, ancho, alto);
        ctx.fillStyle = fraccion > 0.5 ? "#8fb573" : fraccion > 0.25 ? "#d8b24a" : "#d4735e";
        ctx.fillRect(bx, by, ancho * Math.max(0, fraccion), alto);
      }
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
  }, [mapa, terrenos, tokenSel, combate, modo]);

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

  // ---------- Combate (los cambios vuelven por la sala en tiempo real) ----------

  async function ejecutar(accion: () => Promise<unknown>) {
    setError("");
    try {
      await accion();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function ajustarVida(delta: number) {
    if (tokenSel === null) return;
    await ejecutar(() => api.cambiarVida(tokenSel, delta));
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
          {conectados > 1 && <span className="conectados"> · 👥 {conectados} conectados</span>}
        </span>
      </header>

      <div className="pestanas">
        <button className={modo === "pintar" ? "activa" : ""} onClick={() => { setModo("pintar"); setTokenSel(null); setColocando(null); }}>
          🖌 Pintar terreno
        </button>
        <button className={modo === "fichas" ? "activa" : ""} onClick={() => setModo("fichas")}>
          ♟ Fichas
        </button>
        <button className={modo === "combate" ? "activa" : ""} onClick={() => setModo("combate")}>
          ⚔ Combate
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
          ) : modo === "fichas" ? (
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
          ) : (
            <>
              <h3>Combate por turnos</h3>

              <div className="fila">
                <input
                  type="text"
                  className="entrada formula"
                  value={expresion}
                  onChange={(e) => setExpresion(e.target.value)}
                  placeholder="1d20+5"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") ejecutar(() => api.tirarDados(mapaId, { expresion }));
                  }}
                />
                <button className="boton" onClick={() => ejecutar(() => api.tirarDados(mapaId, { expresion }))}>
                  🎲 Tirar
                </button>
              </div>
              <div className="dados-rapidos">
                {["1d20", "1d12", "1d10", "1d8", "1d6", "1d4", "2d6"].map((d) => (
                  <button key={d} className="chip-dado" onClick={() => setExpresion(d)}>
                    {d}
                  </button>
                ))}
              </div>

              {seleccionado && seleccionado.vida_maxima != null ? (
                <div className="vida-control">
                  <p className="nota">
                    <strong>{seleccionado.nombre}</strong> — {seleccionado.vida_actual}/
                    {seleccionado.vida_maxima} de vida
                  </p>
                  <div className="dados-rapidos">
                    <button className="chip-dado peligro" onClick={() => ajustarVida(-5)}>−5</button>
                    <button className="chip-dado peligro" onClick={() => ajustarVida(-1)}>−1</button>
                    <button className="chip-dado" onClick={() => ajustarVida(1)}>+1</button>
                    <button className="chip-dado" onClick={() => ajustarVida(5)}>+5</button>
                  </div>
                </div>
              ) : (
                <p className="nota">
                  Selecciona una ficha para aplicarle daño o curación (las fichas muestran su
                  barra de vida si el sistema define una).
                </p>
              )}

              <h4>Iniciativa</h4>
              {!combate ? (
                <button className="boton" onClick={() => ejecutar(() => api.iniciarCombate(mapaId))}>
                  Iniciar combate (tira iniciativa)
                </button>
              ) : (
                <>
                  <p className="nota">Ronda {combate.ronda}</p>
                  <ol className="orden-iniciativa">
                    {combate.orden.map((p) => (
                      <li key={p.token_id} className={p.token_id === combate.token_en_turno ? "en-turno" : ""}>
                        <span className="espacio">{p.nombre}</span>
                        <span className="ini">{p.iniciativa}</span>
                      </li>
                    ))}
                  </ol>
                  <div className="fila">
                    <button className="boton" onClick={() => ejecutar(() => api.siguienteTurno(mapaId))}>
                      Siguiente turno →
                    </button>
                    <button className="boton boton-peligro" onClick={() => ejecutar(() => api.terminarCombate(mapaId))}>
                      Terminar
                    </button>
                  </div>
                </>
              )}

              <h4>Dados de la mesa</h4>
              {tiradas.length === 0 ? (
                <p className="nota">Aún no se ha tirado nada.</p>
              ) : (
                <ul className="historial-dados">
                  {[...tiradas].reverse().map((t) => (
                    <li key={t.id}>
                      <span className="tirada-total">{t.total}</span>
                      <span className="tirada-detalle">
                        <strong>{t.expresion}</strong>
                        {t.grupos.map((g, i) => (
                          <span key={i} className="dados-valores"> [{g.valores.join(", ")}]</span>
                        ))}
                        {(t.autor || t.motivo) && (
                          <span className="nota"> — {[t.autor, t.motivo].filter(Boolean).join(": ")}</span>
                        )}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
