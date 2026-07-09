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
  voz_id: number | null;
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
  datos: {
    nombre?: string;
    nivel?: number;
    atributos?: Record<string, number>;
    voz_id?: number | null;
  },
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

// ---------- Voces ----------

export interface Voz {
  id: number;
  sistema_id: number;
  nombre: string;
  descripcion: string;
  voz_externa_id: string;
  ajustes: Record<string, unknown>;
}

export interface VozSugerida {
  voz_externa_id: string;
  nombre: string;
  descripcion: string;
  genero: string;
}

export interface EstadoVoces {
  hay_api: boolean;
  sugeridas: VozSugerida[];
  max_caracteres: number;
}

export interface Narracion {
  id: number;
  sistema_id: number;
  personaje_id: number | null;
  voz_id: number | null;
  nombre_locutor: string;
  texto: string;
  tipo_mime: string;
  es_demostracion: boolean;
  creada_en: string;
}

export const estadoVoces = () => pedir<EstadoVoces>("/voces/estado");

export const listarVoces = (sistemaId: number) =>
  pedir<Voz[]>(`/sistemas/${sistemaId}/voces`);

export const crearVoz = (
  sistemaId: number,
  datos: { nombre: string; descripcion: string; voz_externa_id: string },
) =>
  pedir<Voz>(`/sistemas/${sistemaId}/voces`, {
    method: "POST",
    body: JSON.stringify(datos),
  });

export const editarVoz = (vozId: number, datos: Partial<Voz>) =>
  pedir<Voz>(`/voces/${vozId}`, { method: "PUT", body: JSON.stringify(datos) });

export const borrarVoz = (vozId: number) =>
  pedir<void>(`/voces/${vozId}`, { method: "DELETE" });

export const listarNarraciones = (sistemaId: number) =>
  pedir<Narracion[]>(`/sistemas/${sistemaId}/narraciones`);

export const narrar = (
  sistemaId: number,
  datos: { texto: string; personaje_id?: number; voz_id?: number },
) =>
  pedir<Narracion>(`/sistemas/${sistemaId}/narrar`, {
    method: "POST",
    body: JSON.stringify(datos),
  });

export const borrarNarracion = (narracionId: number) =>
  pedir<void>(`/narraciones/${narracionId}`, { method: "DELETE" });

/** Dirección del audio de una narración, lista para un <audio src>. */
export const audioDeNarracion = (narracionId: number) =>
  `/narraciones/${narracionId}/audio`;
