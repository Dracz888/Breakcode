// Capa de comunicación con el servidor Python.
// Todas las funciones lanzan un Error con el mensaje en español que envía el servidor.

export interface Sistema {
  id: number;
  nombre: string;
  descripcion: string;
  notas: string;
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

export const editarSistema = (
  id: number,
  datos: { nombre?: string; descripcion?: string; notas?: string },
) => pedir<SistemaDetalle>(`/sistemas/${id}`, { method: "PUT", body: JSON.stringify(datos) });

export const borrarSistema = (id: number) =>
  pedir<void>(`/sistemas/${id}`, { method: "DELETE" });

// Sistema completo como archivo (reglas, fichas y mapas): respaldo y compartir.
export const exportarSistema = (id: number) =>
  pedir<Record<string, unknown>>(`/sistemas/${id}/exportar`);

export const importarSistema = (datos: unknown) =>
  pedir<Sistema>("/sistemas/importar", { method: "POST", body: JSON.stringify(datos) });

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
  vida_actual: number | null;
  vida_maxima: number | null;
}

export interface MapaDetalle extends Mapa {
  celdas: string[][];
  niebla: boolean[][];
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

export const pintarNiebla = (
  mapaId: number,
  cambios: { x: number; y: number; oculta: boolean }[],
) =>
  pedir<MapaDetalle>(`/mapas/${mapaId}/niebla`, {
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

// ---------- Ambientes de sonido ----------

export interface AmbienteIntegrado {
  clave: string;
  nombre: string;
  categoria: string;
  icono: string;
  descripcion: string;
  bucle: boolean;
}

export interface Ambiente {
  id: number;
  sistema_id: number;
  nombre: string;
  categoria: string;
  icono: string;
  tipo_mime: string;
  bucle: boolean;
}

export const listarAmbientesIntegrados = () =>
  pedir<AmbienteIntegrado[]>("/ambientes/integrados");

export const listarAmbientes = (sistemaId: number) =>
  pedir<Ambiente[]>(`/sistemas/${sistemaId}/ambientes`);

export const subirAmbiente = (
  sistemaId: number,
  datos: { nombre: string; categoria: string; icono: string; bucle: boolean; archivo: File },
) => {
  const cuerpo = new FormData();
  cuerpo.append("nombre", datos.nombre);
  cuerpo.append("categoria", datos.categoria);
  cuerpo.append("icono", datos.icono);
  cuerpo.append("bucle", String(datos.bucle));
  cuerpo.append("archivo", datos.archivo);
  // Sin cabecera Content-Type: el navegador la pone con el 'boundary' correcto.
  return pedir<Ambiente>(`/sistemas/${sistemaId}/ambientes`, {
    method: "POST",
    body: cuerpo,
    headers: {},
  });
};

export const borrarAmbiente = (ambienteId: number) =>
  pedir<void>(`/ambientes/${ambienteId}`, { method: "DELETE" });

/** Dirección del audio de un ambiente integrado, lista para un <audio src>. */
export const audioAmbienteIntegrado = (clave: string) =>
  `/ambientes/integrados/${clave}/audio`;

/** Dirección del audio de un ambiente subido, lista para un <audio src>. */
export const audioAmbiente = (ambienteId: number) => `/ambientes/${ambienteId}/audio`;

// ---------- Combate por turnos ----------

export interface ConfigCombate {
  formula_iniciativa: string;
  dado_iniciativa: string;
  estadistica_vida: string;
}

export interface GrupoDados {
  cantidad: number;
  caras: number;
  valores: number[];
}

export interface Tirada {
  id: number;
  mapa_id: number;
  autor: string;
  motivo: string;
  expresion: string;
  grupos: GrupoDados[];
  modificador: number;
  total: number;
  creada_en: string;
}

export interface Participante {
  token_id: number;
  nombre: string;
  iniciativa: number;
}

export interface Combate {
  mapa_id: number;
  ronda: number;
  indice_turno: number;
  orden: Participante[];
  token_en_turno: number | null;
}

export const verConfigCombate = (sistemaId: number) =>
  pedir<ConfigCombate>(`/sistemas/${sistemaId}/config-combate`);

export const guardarConfigCombate = (sistemaId: number, config: ConfigCombate) =>
  pedir<ConfigCombate>(`/sistemas/${sistemaId}/config-combate`, {
    method: "PUT",
    body: JSON.stringify(config),
  });

export const listarTiradas = (mapaId: number) =>
  pedir<Tirada[]>(`/mapas/${mapaId}/tiradas`);

export const tirarDados = (
  mapaId: number,
  datos: { expresion: string; autor?: string; motivo?: string },
) => pedir<Tirada>(`/mapas/${mapaId}/tiradas`, { method: "POST", body: JSON.stringify(datos) });

export const cambiarVida = (tokenId: number, delta: number) =>
  pedir<Token>(`/tokens/${tokenId}/vida`, { method: "PUT", body: JSON.stringify({ delta }) });

export const verCombate = (mapaId: number) =>
  pedir<Combate | null>(`/mapas/${mapaId}/combate`);

export const iniciarCombate = (mapaId: number) =>
  pedir<Combate>(`/mapas/${mapaId}/combate/iniciar`, { method: "POST" });

export const siguienteTurno = (mapaId: number) =>
  pedir<Combate>(`/mapas/${mapaId}/combate/siguiente`, { method: "POST" });

export const terminarCombate = (mapaId: number) =>
  pedir<void>(`/mapas/${mapaId}/combate`, { method: "DELETE" });

// ---------- Multijugador en tiempo real (WebSocket) ----------

export type EventoMapa =
  | { tipo: "terreno"; datos: { cambios: { x: number; y: number; terreno: string }[] } }
  | { tipo: "token_colocado"; datos: Token }
  | { tipo: "token_movido"; datos: Token }
  | { tipo: "token_actualizado"; datos: Token }
  | { tipo: "token_quitado"; datos: { id: number } }
  | { tipo: "tirada"; datos: Tirada }
  | { tipo: "combate"; datos: Combate }
  | { tipo: "combate_terminado"; datos: { mapa_id: number } }
  | { tipo: "presencia"; datos: { conectados: number } };

/**
 * Abre la sala del mapa: escucha las novedades que reparte el servidor y las
 * entrega a `manejar`. Si la conexión se cae, reintenta sola cada 2 s; al
 * reconectar llama a `alReconectar` para que la pantalla vuelva a sincronizarse
 * (por si se perdió algún cambio mientras estaba desconectada).
 *
 * Devuelve una función para cerrar la sala al salir de la pantalla.
 */
export function conectarMapa(
  mapaId: number,
  manejar: (evento: EventoMapa) => void,
  alReconectar?: () => void,
): () => void {
  let socket: WebSocket | null = null;
  let cerrado = false;
  let reintento: ReturnType<typeof setTimeout> | undefined;
  let primeraConexion = true;

  function abrir() {
    const protocolo = location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${protocolo}//${location.host}/ws/mapas/${mapaId}`);

    socket.onopen = () => {
      if (!primeraConexion) alReconectar?.();
      primeraConexion = false;
    };
    socket.onmessage = (mensaje) => {
      try {
        manejar(JSON.parse(mensaje.data) as EventoMapa);
      } catch {
        /* mensaje ilegible: se ignora */
      }
    };
    socket.onclose = () => {
      if (!cerrado) reintento = setTimeout(abrir, 2000);
    };
  }

  abrir();

  return () => {
    cerrado = true;
    clearTimeout(reintento);
    socket?.close();
  };
}

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
