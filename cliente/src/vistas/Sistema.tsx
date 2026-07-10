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
  | "ambientes"
  | "mundo"
  | "campanas"
  | "notas";

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
            ["mundo", "Mundo"],
            ["campanas", "Campañas"],
            ["notas", "Notas del DJ"],
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
      {pestana === "mundo" && (
        <PestanaMundo sistema={sistema} navegar={navegar} setError={setError} />
      )}
      {pestana === "campanas" && (
        <PestanaCampanas sistema={sistema} navegar={navegar} setError={setError} />
      )}
      {pestana === "notas" && (
        <PestanaNotas sistema={sistema} recargar={recargar} setError={setError} />
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

// ---------- Pestaña: Mundo (mapas geográficos) ----------

function PestanaMundo({
  sistema,
  navegar,
  setError,
}: {
  sistema: api.SistemaDetalle;
  navegar: (p: Pantalla) => void;
  setError: (m: string) => void;
}) {
  const [mundos, setMundos] = useState<api.MapaGeografico[]>([]);
  const [nombre, setNombre] = useState("");
  const [imagenUrl, setImagenUrl] = useState("");

  const recargar = useCallback(
    () =>
      api
        .listarMundos(sistema.id)
        .then(setMundos)
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
      const mundo = await api.crearMundo(sistema.id, {
        nombre,
        imagen_url: imagenUrl.trim(),
      });
      navegar({ nombre: "mundo", mundoId: mundo.id, sistemaId: sistema.id });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function borrar(mundo: api.MapaGeografico) {
    if (!confirm(`¿Borrar el mapa del mundo "${mundo.nombre}" y sus marcadores?`)) return;
    setError("");
    try {
      await api.borrarMundo(mundo.id);
      recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="dos-columnas">
      <div>
        {mundos.length === 0 && (
          <p className="nota">
            El mapa del mundo es una imagen grande (un mapa dibujado o generado
            fuera del programa) sobre la que colocas marcadores de ciudades,
            mazmorras y puntos de interés. Crea el primero al lado.
          </p>
        )}
        {mundos.map((m) => (
          <div
            key={m.id}
            className="tarjeta tarjeta-clic"
            onClick={() => navegar({ nombre: "mundo", mundoId: m.id, sistemaId: sistema.id })}
          >
            <div className="fila">
              <div className="espacio">
                <h3>🗺 {m.nombre}</h3>
                <span className="nota">
                  {m.imagen_url ? "con imagen de fondo" : "fondo de pergamino"}
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
        <h3>Nuevo mapa del mundo</h3>
        <form onSubmit={crear}>
          <label className="campo">
            <span>Nombre</span>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej. Continente de Aletheia"
              required
            />
          </label>
          <label className="campo">
            <span>Enlace a la imagen de fondo (opcional)</span>
            <input
              type="text"
              value={imagenUrl}
              onChange={(e) => setImagenUrl(e.target.value)}
              placeholder="https://…/mapa.jpg"
            />
            <span className="nota">
              Puedes dejarlo vacío y añadir la imagen después; sin imagen se usa un
              fondo de pergamino.
            </span>
          </label>
          <button className="boton" type="submit">
            Crear mapa del mundo
          </button>
        </form>
      </div>
    </div>
  );
}

// ---------- Pestaña: Campañas ----------

function PestanaCampanas({
  sistema,
  navegar,
  setError,
}: {
  sistema: api.SistemaDetalle;
  navegar: (p: Pantalla) => void;
  setError: (m: string) => void;
}) {
  const [campanas, setCampanas] = useState<api.Campana[]>([]);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");

  const recargar = useCallback(
    () =>
      api
        .listarCampanas(sistema.id)
        .then(setCampanas)
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
      const campana = await api.crearCampana(sistema.id, { nombre, descripcion });
      navegar({ nombre: "campana", campanaId: campana.id, sistemaId: sistema.id });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function borrar(campana: api.Campana) {
    if (!confirm(`¿Borrar la campaña "${campana.nombre}" con todos sus arcos y eventos?`))
      return;
    setError("");
    try {
      await api.borrarCampana(campana.id);
      recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="dos-columnas">
      <div>
        {campanas.length === 0 && (
          <p className="nota">
            Una campaña es la historia que se juega en este sistema. Se organiza en
            arcos (capítulos) y dentro de cada uno registras los eventos: qué pasó,
            cuándo, con quién y en qué lugar del mapa. Con eso, la campaña reconstruye
            su línea de tiempo. Crea la primera al lado.
          </p>
        )}
        {campanas.map((c) => (
          <div
            key={c.id}
            className="tarjeta tarjeta-clic"
            onClick={() =>
              navegar({ nombre: "campana", campanaId: c.id, sistemaId: sistema.id })
            }
          >
            <div className="fila">
              <div className="espacio">
                <h3>📖 {c.nombre}</h3>
                {c.descripcion && <p className="descripcion">{c.descripcion}</p>}
              </div>
              <button
                className="boton boton-peligro"
                onClick={(e) => {
                  e.stopPropagation();
                  borrar(c);
                }}
              >
                Borrar
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="tarjeta">
        <h3>Nueva campaña</h3>
        <form onSubmit={crear}>
          <label className="campo">
            <span>Nombre</span>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej. La caída del faro"
              required
            />
          </label>
          <label className="campo">
            <span>Descripción (opcional)</span>
            <input
              type="text"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              placeholder="¿De qué trata esta historia?"
            />
          </label>
          <button className="boton" type="submit">
            Crear campaña
          </button>
        </form>
      </div>
    </div>
  );
}

// ---------- Pestaña: Notas del DJ ----------

function PestanaNotas({
  sistema,
  recargar,
  setError,
}: {
  sistema: api.SistemaDetalle;
  recargar: () => Promise<void>;
  setError: (m: string) => void;
}) {
  const [texto, setTexto] = useState(sistema.notas ?? "");
  const [guardado, setGuardado] = useState(false);

  async function guardar() {
    setError("");
    setGuardado(false);
    try {
      await api.editarSistema(sistema.id, { notas: texto });
      await recargar();
      setGuardado(true);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const sinCambios = texto === (sistema.notas ?? "");

  return (
    <div className="tarjeta">
      <h3>Notas privadas del DJ</h3>
      <p className="nota">
        Solo para ti: intrigas, secretos de la trama, recordatorios de la mesa. Los
        jugadores nunca ven esto.
      </p>
      <textarea
        className="area-notas"
        value={texto}
        onChange={(e) => {
          setTexto(e.target.value);
          setGuardado(false);
        }}
        rows={14}
        placeholder="Ej. El posadero es en realidad un espía del Reino Roto…"
      />
      <div className="fila" style={{ marginTop: 12, alignItems: "center" }}>
        <button className="boton espacio" onClick={guardar} disabled={sinCambios}>
          Guardar notas
        </button>
        {guardado && sinCambios && <span className="nota">Guardado ✓</span>}
      </div>
    </div>
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
