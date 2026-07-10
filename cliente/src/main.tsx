import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./estilos.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Registra el service worker solo en la versión publicada (en desarrollo
// estorbaría a la recarga en caliente de Vite). Es lo que permite instalar la
// app y que su interfaz cargue aunque la red parpadee.
if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  });
}
