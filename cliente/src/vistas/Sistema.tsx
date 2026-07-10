import { FormEvent, useCallback, useEffect, useState } from "react";
import * as api from "../api";
import type { Pantalla } from "../App";
import EditorFormula, { aClave } from "../componentes/EditorFormula";
import Narrador from "../componentes/Narrador";
import MesaDeSonido from "../componentes/MesaDeSonido";

type PestanaId =
  | "atributos"
  | "formulas"
  | "fichas"
  | "mapas"
  | "voces"
  | "ambientes";

interface Props {
  sistemaId: number;
  navegar: (p: Pantalla) => void;
}

export default function VistaSistema({ sistemaId, navegar }: Props) {
  const [sistema, setSistema] = useState<api.SistemaDetalle | null>(null);
  const [pestana, setPestana] = useState<PestanaId>("atributos");
  const [error, setError] = useState("");

  const recargar = useCallback(
    () =>
      api
        .verSistema(sistemaId)
        .then(setSistema)
        .catch((e) => setError(e.message)),
    [sistemaId],
  );

  useEffect(() => {
    recargar();
  }, [recargar]);

  if (!sistema) {
    return (
      <>
        {error ? <div className="error">{error}</div> : <p className="nota">Cargando…</p>}
      </>
    );
  }

  const clavesDisponibles = [
    ...sistema.atributos.map((a) => a.clave),
    ...sistema.estadisticas.map((e) => e.clave),
    "nivel",
  ];

  return (
    <>
      <header className="cabecera">
        <button className="boton-volver" onClick={() => navegar({ nombre: "inicio" })}>
          ← Sistemas
        </button>
        <h1>{sistema.nombre}</h1>
        {sistema.descripcion && <span className="subtitulo">{sistema.descripcion}</span>}
      </header>

      <nav className="pestanas">
        {(
          [
            ["atributos", "Atributos"],
            ["formulas", "Fórmulas"],
            ["fichas", "Fichas"],
            ["mapas", "Mapas"],
            ["voces", "Voces"],
            ["ambientes", "Ambientes"],
          ] as [PestanaId, string][]
        ).map(([id, titulo]) => (
          <button
            key={id}
            className={pestana === id ? "activa" : ""}
            onClick={() => setPestana(id)}
          >
            {titulo}
          </button>
        ))}
      </nav>

      {error && <div className="error">{error}</div>}

      {pestana === "atributos" && (
        <PestanaAtributos sistema={sistema} recargar={recargar} setError={setError} />
      )}
      {pestana === "formulas" && (
        <PestanaFormulas
          sistema={sistema}
          clavesDisponibles={clavesDisponibles}
          recargar={recargar}
          setError={setError}
        />
      )}
      {pestana === "fichas" && (
        <PestanaFichas sistema={sistema} navegar={navegar} setError={setError} />
      )}
      {pestana === "mapas" && (
        <PestanaMapas sistema={sistema} navegar={navegar} setError={setError} />
      )}
      {pestana === "voces" && <PestanaVoces sistema={sistema} setError={setError} />}
      {pestana === "ambientes" && (
        <MesaDeSonido sistemaId={sistema.id} setError={setError} />
      )}
    </>
  );
}

// ---------- Pestaña: Voces ----------

function PestanaVoces({
  sistema,
  setError,
}: {
  sistema: api.SistemaDetalle;
  setError: (m: string) => void;
}) {
  const [voces, setVoces] = useState<api.Voz[]>([]);
  const [estado, setEstado] = useState<api.EstadoVoces | null>(null);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [vozExterna, setVozExterna] = useState("");

  const recargar = useCallback(
    () =>
      api
        .listarVoces(sistema.id)
        .then(setVoces)
        .catch((e) => setError(e.message)),
    [sistema.id, setError],
  );

  useEffect(() => {
    recargar();
    api.estadoVoces().then(setEstado).catch((e) => setError(e.message));
  }, [recargar, setError]);

  async function crear(evento: FormEvent) {
    evento.preventDefault();
    setError("");
    try {
      await api.crearVoz(sistema.id, {
        nombre,
        descripcion,
        voz_externa_id: vozExterna.trim(),
      });
      setNombre("");
      setDescripcion("");
      setVozExterna("");
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function borrar(voz: api.Voz) {
    if (!confirm(`¿Borrar la voz "${voz.nombre}"? Los personajes que la usen quedarán sin voz.`))
      return;
    setError("");
    try {
      await api.borrarVoz(voz.id);
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  // Al elegir una voz sugerida se rellena el formulario para no copiar ids a mano.
  function usarSugerida(clave: string) {
    const s = estado?.sugeridas.find((v) => v.voz_externa_id === clave);
    if (!s) return;
    setVozExterna(s.voz_externa_id);
    if (!nombre) setNombre(s.nombre);
    if (!descripcion) setDescripcion(s.descripcion);
  }

  return (
    <>
      <div className="dos-columnas">
        <div>
          {voces.length === 0 && (
            <p className="nota">
              Una voz guarda una descripción («ogro grave y monstruoso») y su timbre de
              ElevenLabs. Después se la asignas a un personaje desde su ficha. Crea la
              primera al lado.
            </p>
          )}
          {voces.map((v) => (
            <div key={v.id} className="tarjeta">
              <div className="fila">
                <div className="espacio">
                  <h3>{v.nombre}</h3>
                  {v.descripcion && <p className="descripcion">{v.descripcion}</p>}
                  <span className="nota">
                    voz: <code>{v.voz_externa_id}</code>
                  </span>
                </div>
                <button className="boton boton-peligro" onClick={() => borrar(v)}>
                  Borrar
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="tarjeta">
          <h3>Nueva voz</h3>
          <form onSubmit={crear}>
            <label className="campo">
              <span>Nombre</span>
              <input
                type="text"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Ej. Ogro cavernario"
                required
              />
            </label>
            <label className="campo">
              <span>Descripción del timbre</span>
              <input
                type="text"
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                placeholder="Ej. grave, monstruoso, arrastra las palabras"
              />
            </label>
            <label className="campo">
              <span>Identificador de voz (ElevenLabs)</span>
              <input
                type="text"
                value={vozExterna}
                onChange={(e) => setVozExterna(e.target.value)}
                placeholder="Elige una sugerida abajo o pega el tuyo"
                required
              />
            </label>
            {estado && estado.sugeridas.length > 0 && (
              <>
                <span className="nota">Voces sugeridas (haz clic para usar una):</span>
                <div className="paleta-claves">
                  {estado.sugeridas.map((s) => (
                    <button
                      key={s.voz_externa_id}
                      type="button"
                      className="chip-clave"
                      title={s.descripcion}
                      onClick={() => usarSugerida(s.voz_externa_id)}
                    >
                      {s.nombre}
                    </button>
                  ))}
                </div>
              </>
            )}
            <button className="boton" type="submit">
              Crear voz
            </button>
          </form>
        </div>
      </div>

      {estado && (
        <Narrador
          sistemaId={sistema.id}
          voces={voces}
          hayApi={estado.hay_api}
          maxCaracteres={estado.max_caracteres}
        />
      )}
    </>
  );
}

// ---------- Pestaña: Atributos ----------

function PestanaAtributos({
  sistema,
  recargar,
  setError,
}: {
  sistema: api.SistemaDetalle;
  recargar: () => Promise<void>;
  setError: (m: string) => void;
}) {
  const [nombre, setNombre] = useState("");
  const [categoria, setCategoria] = useState("");
  const [valorInicial, setValorInicial] = useState(0);

  async function crear(evento: FormEvent) {
    evento.preventDefault();
    setError("");
    try {
      await api.crearAtributo(sistema.id, {
        clave: aClave(nombre),
        nombre,
        categoria: categoria.trim().toLowerCase(),
        descripcion: "",
        valor_inicial: valorInicial,
      });
      setNombre("");
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function borrar(atributo: api.Atributo) {
    if (!confirm(`¿Borrar el atributo "${atributo.nombre}"?`)) return;
    setError("");
    try {
      await api.borrarAtributo(sistema.id, atributo.clave);
      await recargar();
    } catch (e) {
      setError((e as Error).message); // ej. "lo usan estas fórmulas: ..."
    }
  }

  return (
    <div className="dos-columnas">
      <div>
        {sistema.atributos.length === 0 && (
          <p className="nota">
            Los atributos son las capacidades base de tus personajes (Fuerza,
            Intelecto, Voluntad Arcana…). Crea el primero a la derecha.
          </p>
        )}
        {sistema.atributos.map((a) => (
          <div key={a.clave} className="tarjeta">
            <div className="fila">
              <div className="espacio">
                <h3>{a.nombre}</h3>
                <span className="nota">
                  en fórmulas: <code>{a.clave}</code> · valor inicial {a.valor_inicial}
                </span>
              </div>
              {a.categoria && <span className={`chip ${a.categoria}`}>{a.categoria}</span>}
              <button className="boton boton-peligro" onClick={() => borrar(a)}>
                Borrar
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="tarjeta">
        <h3>Nuevo atributo</h3>
        <form onSubmit={crear}>
          <label className="campo">
            <span>Nombre</span>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej. Voluntad Arcana"
              required
            />
            {nombre && (
              <span className="nota">En las fórmulas se usará como: {aClave(nombre)}</span>
            )}
          </label>
          <label className="campo">
            <span>Categoría (la que tú quieras: física, mental, mágica…)</span>
            <input
              type="text"
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
              placeholder="Ej. mágica"
            />
          </label>
          <label className="campo">
            <span>Valor inicial (con el que nacen los personajes)</span>
            <input
              type="number"
              value={valorInicial}
              onChange={(e) => setValorInicial(Number(e.target.value))}
            />
          </label>
          <button className="boton" type="submit">
            Crear atributo
          </button>
        </form>
      </div>
    </div>
  );
}

// ---------- Pestaña: Fórmulas ----------

function PestanaFormulas({
  sistema,
  clavesDisponibles,
  recargar,
  setError,
}: {
  sistema: api.SistemaDetalle;
  clavesDisponibles: string[];
  recargar: () => Promise<void>;
  setError: (m: string) => void;
}) {
  const [editando, setEditando] = useState<string | null>(null);

  async function borrar(estadistica: api.Estadistica) {
    if (!confirm(`¿Borrar la estadística "${estadistica.nombre}"?`)) return;
    setError("");
    try {
      await api.borrarEstadistica(sistema.id, estadistica.clave);
      await recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="dos-columnas">
      <div>
        {sistema.estadisticas.length === 0 && (
          <p className="nota">
            Las estadísticas derivadas (Vida, Defensa, Velocidad…) se calculan solas a
            partir de los atributos, con fórmulas que escribes como en Excel.
          </p>
        )}
        {sistema.estadisticas.map((e) => (
          <div key={e.clave} className="tarjeta">
            {editando === e.clave ? (
              <EditorFormula
                sistemaId={sistema.id}
                clavesDisponibles={clavesDisponibles}
                inicial={e}
                onCancelar={() => setEditando(null)}
                onGuardar={async (datos) => {
                  await api.editarEstadistica(sistema.id, e.clave, {
                    nombre: datos.nombre,
                    formula: datos.formula,
                  });
                  setEditando(null);
                  await recargar();
                }}
              />
            ) : (
              <div className="fila">
                <div className="espacio">
                  <h3>{e.nombre}</h3>
                  <code className="nota">
                    {e.clave} = {e.formula}
                  </code>
                </div>
                <button
                  className="boton boton-secundario"
                  onClick={() => setEditando(e.clave)}
                >
                  Editar
                </button>
                <button className="boton boton-peligro" onClick={() => borrar(e)}>
                  Borrar
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="tarjeta">
        <h3>Nueva estadística</h3>
        <EditorFormula
          sistemaId={sistema.id}
          clavesDisponibles={clavesDisponibles}
          onGuardar={async (datos) => {
            await api.crearEstadistica(sistema.id, { ...datos, descripcion: "" });
            await recargar();
          }}
        />
      </div>
    </div>
  );
}

// ---------- Pestaña: Mapas ----------

function PestanaMapas({
  sistema,
  navegar,
  setError,
}: {
  sistema: api.SistemaDetalle;
  navegar: (p: Pantalla) => void;
  setError: (m: string) => void;
}) {
  const [mapas, setMapas] = useState<api.Mapa[]>([]);
  const [nombre, setNombre] = useState("");
  const [ancho, setAncho] = useState(16);
  const [alto, setAlto] = useState(12);

  const recargar = useCallback(
    () =>
      api
        .listarMapas(sistema.id)
        .then(setMapas)
        .catch((e) => setError(e.message)),
    [sistema.id, setError],
  );

  useEffect(() => {
    recargar();
  }, [recargar]);

  async function crear(evento: FormEvent) {
    evento.preventDefault();
    setError("");
    try {
      const mapa = await api.crearMapa(sistema.id, { nombre, ancho, alto });
      navegar({ nombre: "mapa", mapaId: mapa.id, sistemaId: sistema.id });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function borrar(mapa: api.Mapa) {
    if (!confirm(`¿Borrar el mapa "${mapa.nombre}"?`)) return;
    setError("");
    try {
      await api.borrarMapa(mapa.id);
      recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="dos-columnas">
      <div>
        {mapas.length === 0 && (
          <p className="nota">
            Los mapas de batalla son cuadrículas que pintas con terrenos (pasto, agua,
            muros…) y donde colocas y mueves las fichas. Crea el primero al lado.
          </p>
        )}
        {mapas.map((m) => (
          <div
            key={m.id}
            className="tarjeta tarjeta-clic"
            onClick={() => navegar({ nombre: "mapa", mapaId: m.id, sistemaId: sistema.id })}
          >
            <div className="fila">
              <div className="espacio">
                <h3>{m.nombre}</h3>
                <span className="nota">
                  {m.ancho} × {m.alto} celdas
                </span>
              </div>
              <button
                className="boton boton-peligro"
                onClick={(e) => {
                  e.stopPropagation();
                  borrar(m);
                }}
              >
                Borrar
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="tarjeta">
        <h3>Nuevo mapa</h3>
        <form onSubmit={crear}>
          <label className="campo">
            <span>Nombre</span>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej. Claro del bosque"
              required
            />
          </label>
          <div className="fila">
            <label className="campo" style={{ flex: 1 }}>
              <span>Ancho (celdas)</span>
              <input
                type="number"
                min={4}
                max={80}
                value={ancho}
                onChange={(e) => setAncho(Number(e.target.value))}
              />
            </label>
            <label className="campo" style={{ flex: 1 }}>
              <span>Alto (celdas)</span>
              <input
                type="number"
                min={4}
                max={80}
                value={alto}
                onChange={(e) => setAlto(Number(e.target.value))}
              />
            </label>
          </div>
          <button className="boton" type="submit">
            Crear mapa
          </button>
        </form>
      </div>
    </div>
  );
}

// ---------- Pestaña: Fichas ----------

function PestanaFichas({
  sistema,
  navegar,
  setError,
}: {
  sistema: api.SistemaDetalle;
  navegar: (p: Pantalla) => void;
  setError: (m: string) => void;
}) {
  const [personajes, setPersonajes] = useState<api.Personaje[]>([]);
  const [nombre, setNombre] = useState("");
  const [esMonstruo, setEsMonstruo] = useState(false);

  const recargar = useCallback(
    () =>
      api
        .listarPersonajes(sistema.id)
        .then(setPersonajes)
        .catch((e) => setError(e.message)),
    [sistema.id, setError],
  );

  useEffect(() => {
    recargar();
  }, [recargar]);

  async function crear(evento: FormEvent) {
    evento.preventDefault();
    setError("");
    try {
      const p = await api.crearPersonaje(sistema.id, {
        nombre,
        nivel: 1,
        es_monstruo: esMonstruo,
      });
      navegar({ nombre: "ficha", personajeId: p.id, sistemaId: sistema.id });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="dos-columnas">
      <div>
        {personajes.length === 0 && (
          <p className="nota">
            Todavía no hay fichas en este sistema. Personajes y monstruos usan el mismo
            motor: sus estadísticas se calculan solas con tus fórmulas.
          </p>
        )}
        {personajes.map((p) => (
          <div
            key={p.id}
            className="tarjeta tarjeta-clic"
            onClick={() =>
              navegar({ nombre: "ficha", personajeId: p.id, sistemaId: sistema.id })
            }
          >
            <div className="fila">
              <div className="espacio">
                <h3>{p.nombre}</h3>
                <span className="nota">Nivel {p.nivel}</span>
              </div>
              {p.es_monstruo && <span className="insignia-monstruo">monstruo</span>}
            </div>
          </div>
        ))}
      </div>

      <div className="tarjeta">
        <h3>Nueva ficha</h3>
        <form onSubmit={crear}>
          <label className="campo">
            <span>Nombre</span>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej. Kaelith"
              required
            />
          </label>
          <label className="campo" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={esMonstruo}
              onChange={(e) => setEsMonstruo(e.target.checked)}
              style={{ width: "auto", minHeight: "auto" }}
            />
            <span style={{ margin: 0 }}>Es un monstruo</span>
          </label>
          <button className="boton" type="submit">
            Crear ficha
          </button>
        </form>
      </div>
    </div>
  );
}
