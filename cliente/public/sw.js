/* Service worker de Breakcode.
 *
 * Da dos cosas: que la app se pueda "instalar" como aplicación (ícono propio,
 * pantalla completa) y que su interfaz cargue aunque la red falle un instante.
 *
 * Regla clave: NUNCA se cachean las llamadas a la API ni el tiempo real —
 * esos datos deben ser siempre frescos y viajar por la red. Solo se guarda el
 * "casco" de la app (HTML, JavaScript, CSS, íconos), que además llevan un
 * nombre con huella única por versión, así que cachearlos es seguro.
 */

const CACHE = "breakcode-v1";

// Rutas del servidor que jamás deben servirse desde el caché.
const ES_API = /^\/(sistemas|personajes|mapas|tokens|terrenos|ws|salud|docs|openapi\.json)/;

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((claves) => Promise.all(claves.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (evento) => {
  const peticion = evento.request;
  const url = new URL(peticion.url);

  // Solo GET del mismo origen; nada de API, POST ni WebSocket.
  if (peticion.method !== "GET" || url.origin !== location.origin) return;
  if (ES_API.test(url.pathname)) return;

  // Navegaciones (abrir la app): la red manda; si no hay, se sirve lo guardado.
  if (peticion.mode === "navigate") {
    evento.respondWith(
      fetch(peticion)
        .then((respuesta) => {
          const copia = respuesta.clone();
          caches.open(CACHE).then((c) => c.put(peticion, copia));
          return respuesta;
        })
        .catch(() => caches.match(peticion).then((r) => r || caches.match("/"))),
    );
    return;
  }

  // Recursos con huella única (JS/CSS/íconos): del caché primero, es seguro.
  evento.respondWith(
    caches.match(peticion).then(
      (guardado) =>
        guardado ||
        fetch(peticion).then((respuesta) => {
          if (respuesta.ok) {
            const copia = respuesta.clone();
            caches.open(CACHE).then((c) => c.put(peticion, copia));
          }
          return respuesta;
        }),
    ),
  );
});
