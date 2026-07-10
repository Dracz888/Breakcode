import { FormEvent, useEffect, useRef, useState } from "react";
import * as api from "../api";
import type { Pantalla } from "../App";

export default function Inicio({ navegar }: { navegar: (p: Pantalla) => void }) {
  const [sistemas, setSistemas] = useState<api.Sistema[]>([]);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const entradaArchivo = useRef<HTMLInputElement>(null);

  const recargar = () =>
    api
      .listarSistemas()
      .then(setSistemas)
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false));

  useEffect(() => {
    recargar();
  }, []);

  async function crear(evento: FormEvent) {
    evento.preventDefault();
    setError("");
    try {
      const sistema = await api.crearSistema({ nombre, descripcion });
      navegar({ nombre: "sistema", sistemaId: sistema.id });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function exportar(sistema: api.Sistema) {
    setError("");
    try {
      const datos = await api.exportarSistema(sistema.id);
      const nombreArchivo =
        sistema.nombre.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-") || "sistema";
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(datos, null, 2)], { type: "application/json" }),
      );
      const enlace = document.createElement("a");
      enlace.href = url;
      enlace.download = `${nombreArchivo}.breakcode.json`;
      enlace.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function importar(evento: FormEvent<HTMLInputElement>) {
    const archivo = evento.currentTarget.files?.[0];
    evento.currentTarget.value = ""; // permite reimportar el mismo archivo
    if (!archivo) return;
    setError("");
    try {
      const datos = JSON.parse(await archivo.text());
      const sistema = await api.importarSistema(datos);
      navegar({ nombre: "sistema", sistemaId: sistema.id });
    } catch (e) {
      const msg = (e as Error).message;
      setError(
        msg.includes("JSON") ? "Ese archivo no es un sistema de Breakcode válido." : msg,
      );
    }
  }

  async function borrar(sistema: api.Sistema) {
    if (!confirm(`¿Borrar el sistema "${sistema.nombre}" con todo su contenido?`)) return;
    setError("");
    try {
      await api.borrarSistema(sistema.id);
      recargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <>
      <header className="cabecera">
        <h1>⚔ Breakcode</h1>
        <span className="subtitulo">
          Fábrica de sistemas de rol — diseña tus propias reglas, sin programar
        </span>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="fila" style={{ alignItems: "center" }}>
        <h2 className="espacio">Tus sistemas</h2>
        <input
          ref={entradaArchivo}
          type="file"
          accept=".json,application/json"
          onChange={importar}
          style={{ display: "none" }}
        />
        <button
          className="boton boton-secundario"
          onClick={() => entradaArchivo.current?.click()}
        >
          Importar sistema
        </button>
      </div>

      {cargando && <p className="nota">Cargando…</p>}
      {!cargando && sistemas.length === 0 && (
        <p className="nota">
          Aún no tienes ningún sistema. Crea el primero aquí abajo: un sistema es un
          juego de reglas completo (sus atributos, sus fórmulas, sus fichas).
        </p>
      )}
      {sistemas.map((s) => (
        <div
          key={s.id}
          className="tarjeta tarjeta-clic"
          onClick={() => navegar({ nombre: "sistema", sistemaId: s.id })}
        >
          <div className="fila">
            <div className="espacio">
              <h3>{s.nombre}</h3>
              {s.descripcion && <p className="descripcion">{s.descripcion}</p>}
            </div>
            <button
              className="boton boton-secundario"
              title="Descargar este sistema como archivo (respaldo o para compartir)"
              onClick={(e) => {
                e.stopPropagation();
                exportar(s);
              }}
            >
              Exportar
            </button>
            <button
              className="boton-peligro boton"
              onClick={(e) => {
                e.stopPropagation();
                borrar(s);
              }}
            >
              Borrar
            </button>
          </div>
        </div>
      ))}

      <div className="tarjeta" style={{ marginTop: 24 }}>
        <h3>Crear un sistema nuevo</h3>
        <form onSubmit={crear}>
          <label className="campo">
            <span>Nombre</span>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej. Crónicas del Reino Roto"
              required
            />
          </label>
          <label className="campo">
            <span>Descripción (opcional)</span>
            <input
              type="text"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              placeholder="¿De qué trata este mundo?"
            />
          </label>
          <button className="boton" type="submit">
            Crear sistema
          </button>
        </form>
      </div>
    </>
  );
}
