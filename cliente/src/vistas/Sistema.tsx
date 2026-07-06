import { FormEvent, useCallback, useEffect, useState } from "react";
import * as api from "../api";
import type { Pantalla } from "../App";
import EditorFormula, { aClave } from "../componentes/EditorFormula";

type PestanaId = "atributos" | "formulas" | "fichas";

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
