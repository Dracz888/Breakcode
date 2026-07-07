// Capa de comunicación con el servidor Python.
// Todas las funciones lanzan un Error con el mensaje en español que envía el servidor.

export interface Sistema {
  id: number;
  nombre: string;
  descripcion: string;
}

export interface Atributo {
  clave: string;
  nombre: string;
  categoria: string;
  descripcion: string;
  valor_inicial: number;
}

export interface Estadistica {
  clave: string;
  nombre: string;
  formula: string;
  descripcion: string;
}

export interface SistemaDetalle extends Sistema {
  atributos: Atributo[];
  estadisticas: Estadistica[];
}

export interface Personaje {
  id: number;
  sistema_id: number;
  nombre: string;
  nivel: number;
  es_monstruo: boolean;
  atributos: Record<string, number>;
  estadisticas: Record<string, number>;
  errores_de_formulas: Record<string, string>;
}

export interface FormulaResultado {
  ok: boolean;
  valor: number | null;
  error: string | null;
  valores_usados: Record<string, number>;
}

async function pedir<T>(ruta: string, opciones?: RequestInit): Promise<T> {
  const respuesta = await fetch(ruta, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  if (!respuesta.ok) {
    let mensaje = `Error ${respuesta.status}`;
    try {
      const cuerpo = await respuesta.json();
      if (typeof cuerpo.detail === "string") mensaje = cuerpo.detail;
      else if (Array.isArray(cuerpo.detail) && cuerpo.detail[0]?.msg)
        mensaje = cuerpo.detail[0].msg.replace(/^Value error, /, "");
    } catch {
      /* sin cuerpo JSON: se usa el mensaje genérico */
    }
    throw new Error(mensaje);
  }
  if (respuesta.status === 204) return undefined as T;
  return respuesta.json();
}

// ---------- Sistemas ----------

export const listarSistemas = () => pedir<Sistema[]>("/sistemas");

export const verSistema = (id: number) => pedir<SistemaDetalle>(`/sistemas/${id}`);

export const crearSistema = (datos: { nombre: string; descripcion: string }) =>
  pedir<Sistema>("/sistemas", { method: "POST", body: JSON.stringify(datos) });

export const borrarSistema = (id: number) =>
  pedir<void>(`/sistemas/${id}`, { method: "DELETE" });

// ---------- Atributos ----------

export const crearAtributo = (sistemaId: number, datos: Atributo) =>
  pedir<Atributo>(`/sistemas/${sistemaId}/atributos`, {
    method: "POST",
    body: JSON.stringify(datos),
  });

export const editarAtributo = (
  sistemaId: number,
  clave: string,
  datos: Partial<Atributo>,
) =>
  pedir<Atributo>(`/sistemas/${sistemaId}/atributos/${clave}`, {
    method: "PUT",
    body: JSON.stringify(datos),
  });

export const borrarAtributo = (sistemaId: number, clave: string) =>
  pedir<void>(`/sistemas/${sistemaId}/atributos/${clave}`, { method: "DELETE" });

// ---------- Estadísticas (fórmulas) ----------

export const crearEstadistica = (sistemaId: number, datos: Estadistica) =>
  pedir<Estadistica>(`/sistemas/${sistemaId}/estadisticas`, {
    method: "POST",
    body: JSON.stringify(datos),
  });

export const editarEstadistica = (
  sistemaId: number,
  clave: string,
  datos: Partial<Estadistica>,
) =>
  pedir<Estadistica>(`/sistemas/${sistemaId}/estadisticas/${clave}`, {
    method: "PUT",
    body: JSON.stringify(datos),
  });

export const borrarEstadistica = (sistemaId: number, clave: string) =>
  pedir<void>(`/sistemas/${sistemaId}/estadisticas/${clave}`, { method: "DELETE" });

export const probarFormula = (
  sistemaId: number,
  formula: string,
  valoresDePrueba: Record<string, number> = {},
) =>
  pedir<FormulaResultado>(`/sistemas/${sistemaId}/probar-formula`, {
    method: "POST",
    body: JSON.stringify({ formula, valores_de_prueba: valoresDePrueba }),
  });

// ---------- Personajes ----------

export const listarPersonajes = (sistemaId: number) =>
  pedir<Personaje[]>(`/sistemas/${sistemaId}/personajes`);

export const verPersonaje = (id: number) => pedir<Personaje>(`/personajes/${id}`);

export const crearPersonaje = (
  sistemaId: number,
  datos: { nombre: string; nivel: number; es_monstruo: boolean },
) =>
  pedir<Personaje>(`/sistemas/${sistemaId}/personajes`, {
    method: "POST",
    body: JSON.stringify({ ...datos, atributos: {} }),
  });

export const editarPersonaje = (
  id: number,
  datos: { nombre?: string; nivel?: number; atributos?: Record<string, number> },
) => pedir<Personaje>(`/personajes/${id}`, { method: "PUT", body: JSON.stringify(datos) });

export const borrarPersonaje = (id: number) =>
  pedir<void>(`/personajes/${id}`, { method: "DELETE" });

// ---------- Mapas de batalla ----------

export interface Terreno {
  nombre: string;
  color: string;
  simbolo: string;
  bloquea: boolean;
}

export interface Mapa {
  id: number;
  sistema_id: number;
  nombre: string;
  ancho: number;
  alto: number;
}

export interface Token {
  id: number;
  mapa_id: number;
  personaje_id: number;
  nombre: string;
  es_monstruo: boolean;
  x: number;
  y: number;
}

export interface MapaDetalle extends Mapa {
  celdas: string[][];
  tokens: Token[];
}

export const listarTerrenos = () => pedir<Record<string, Terreno>>("/terrenos");

export const listarMapas = (sistemaId: number) =>
  pedir<Mapa[]>(`/sistemas/${sistemaId}/mapas`);

export const crearMapa = (
  sistemaId: number,
  datos: { nombre: string; ancho: number; alto: number },
) => pedir<Mapa>(`/sistemas/${sistemaId}/mapas`, { method: "POST", body: JSON.stringify(datos) });

export const verMapa = (id: number) => pedir<MapaDetalle>(`/mapas/${id}`);

export const borrarMapa = (id: number) => pedir<void>(`/mapas/${id}`, { method: "DELETE" });

export const pintarCeldas = (
  mapaId: number,
  cambios: { x: number; y: number; terreno: string }[],
) =>
  pedir<MapaDetalle>(`/mapas/${mapaId}/celdas`, {
    method: "PUT",
    body: JSON.stringify({ cambios }),
  });

export const colocarToken = (mapaId: number, datos: { personaje_id: number; x: number; y: number }) =>
  pedir<Token>(`/mapas/${mapaId}/tokens`, { method: "POST", body: JSON.stringify(datos) });

export const moverToken = (tokenId: number, x: number, y: number) =>
  pedir<Token>(`/tokens/${tokenId}`, { method: "PUT", body: JSON.stringify({ x, y }) });

export const quitarToken = (tokenId: number) =>
  pedir<void>(`/tokens/${tokenId}`, { method: "DELETE" });

// ---------- Mapa geográfico (el mundo) ----------

export interface TipoMarcador {
  nombre: string;
  color: string;
  simbolo: string;
}

export interface Marcador {
  id: number;
  mapa_id: number;
  nombre: string;
  tipo: string;
  descripcion: string;
  x: number; // 0..1 relativo al ancho
  y: number; // 0..1 relativo al alto
}

export interface MapaGeografico {
  id: number;
  sistema_id: number;
  nombre: string;
  imagen_url: string;
}

export interface MapaGeograficoDetalle extends MapaGeografico {
  marcadores: Marcador[];
}

export const listarTiposMarcador = () =>
  pedir<Record<string, TipoMarcador>>("/tipos-marcador");

export const listarMundos = (sistemaId: number) =>
  pedir<MapaGeografico[]>(`/sistemas/${sistemaId}/mapas-geograficos`);

export const crearMundo = (
  sistemaId: number,
  datos: { nombre: string; imagen_url: string },
) =>
  pedir<MapaGeografico>(`/sistemas/${sistemaId}/mapas-geograficos`, {
    method: "POST",
    body: JSON.stringify(datos),
  });

export const verMundo = (id: number) =>
  pedir<MapaGeograficoDetalle>(`/mapas-geograficos/${id}`);

export const editarMundo = (
  id: number,
  datos: { nombre?: string; imagen_url?: string },
) =>
  pedir<MapaGeografico>(`/mapas-geograficos/${id}`, {
    method: "PUT",
    body: JSON.stringify(datos),
  });

export const borrarMundo = (id: number) =>
  pedir<void>(`/mapas-geograficos/${id}`, { method: "DELETE" });

export const crearMarcador = (
  mundoId: number,
  datos: { nombre: string; tipo: string; descripcion: string; x: number; y: number },
) =>
  pedir<Marcador>(`/mapas-geograficos/${mundoId}/marcadores`, {
    method: "POST",
    body: JSON.stringify(datos),
  });

export const editarMarcador = (id: number, datos: Partial<Marcador>) =>
  pedir<Marcador>(`/marcadores/${id}`, { method: "PUT", body: JSON.stringify(datos) });

export const borrarMarcador = (id: number) =>
  pedir<void>(`/marcadores/${id}`, { method: "DELETE" });

// ---------- Campañas: arcos y eventos ----------

export interface Campana {
  id: number;
  sistema_id: number;
  nombre: string;
  descripcion: string;
}

export interface PersonajeBreve {
  id: number;
  nombre: string;
  es_monstruo: boolean;
}

export interface MarcadorBreve {
  id: number;
  nombre: string;
  tipo: string;
}

export interface Evento {
  id: number;
  arco_id: number;
  titulo: string;
  fecha: string;
  descripcion: string;
  orden: number;
  marcador: MarcadorBreve | null;
  personajes: PersonajeBreve[];
}

export interface Arco {
  id: number;
  campana_id: number;
  titulo: string;
  descripcion: string;
  orden: number;
  eventos: Evento[];
}

export interface CampanaDetalle extends Campana {
  arcos: Arco[];
}

export const listarCampanas = (sistemaId: number) =>
  pedir<Campana[]>(`/sistemas/${sistemaId}/campanas`);

export const crearCampana = (
  sistemaId: number,
  datos: { nombre: string; descripcion: string },
) =>
  pedir<Campana>(`/sistemas/${sistemaId}/campanas`, {
    method: "POST",
    body: JSON.stringify(datos),
  });

export const verCampana = (id: number) => pedir<CampanaDetalle>(`/campanas/${id}`);

export const editarCampana = (
  id: number,
  datos: { nombre?: string; descripcion?: string },
) => pedir<Campana>(`/campanas/${id}`, { method: "PUT", body: JSON.stringify(datos) });

export const borrarCampana = (id: number) =>
  pedir<void>(`/campanas/${id}`, { method: "DELETE" });

export const crearArco = (campanaId: number, datos: { titulo: string; descripcion: string }) =>
  pedir<Arco>(`/campanas/${campanaId}/arcos`, { method: "POST", body: JSON.stringify(datos) });

export const editarArco = (
  id: number,
  datos: { titulo?: string; descripcion?: string; orden?: number },
) => pedir<Arco>(`/arcos/${id}`, { method: "PUT", body: JSON.stringify(datos) });

export const borrarArco = (id: number) => pedir<void>(`/arcos/${id}`, { method: "DELETE" });

export const crearEvento = (
  arcoId: number,
  datos: {
    titulo: string;
    fecha: string;
    descripcion: string;
    marcador_id: number | null;
    personajes: number[];
  },
) => pedir<Evento>(`/arcos/${arcoId}/eventos`, { method: "POST", body: JSON.stringify(datos) });

export const editarEvento = (
  id: number,
  datos: {
    titulo?: string;
    fecha?: string;
    descripcion?: string;
    marcador_id?: number | null;
    personajes?: number[];
  },
) => pedir<Evento>(`/eventos/${id}`, { method: "PUT", body: JSON.stringify(datos) });

export const borrarEvento = (id: number) =>
  pedir<void>(`/eventos/${id}`, { method: "DELETE" });
