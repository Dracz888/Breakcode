# Breakcode — Plataforma de Rol Digital
## Documento de diseño (versión para celular y PC)

> Este documento describe cómo será el programa, qué tecnologías usa y en qué orden se construye. Está escrito para que lo entienda alguien sin conocimientos de programación. Reemplaza al documento anterior basado en Unity.

---

## 1. La decisión más importante: aplicación web, no Unity

El plan original usaba Unity (motor de videojuegos). Se cambió por una **aplicación web** — un programa que vive en internet y se abre desde el navegador (Chrome, Safari, Edge...). Razones:

| | Con Unity | Con aplicación web |
|---|---|---|
| ¿Funciona en celular y PC? | Hay que crear y mantener dos versiones distintas | **Una sola versión funciona en todo**: celular, tablet, PC, Mac |
| ¿Cómo la usan tus amigos? | Deben descargar e instalar el juego (y en celular, pasar por la tienda de apps) | **Abren un enlace y ya están jugando** |
| ¿Cómo se actualiza? | Todos deben reinstalar cada versión nueva | Se actualiza sola: al recargar la página ya tienen lo último |
| ¿Puedes construirla sin saber programar? | No — Unity exige trabajar dentro de su editor visual | **Sí** — todo el programa es código que la IA puede escribir por ti |
| ¿Se siente como app en el celular? | Sí | Sí — se puede "instalar" desde el navegador con su propio ícono, como cualquier app (tecnología llamada PWA) |

Lo único que se pierde frente a Unity son efectos gráficos 3D de alta gama — que este proyecto no necesita: es un juego táctico de fichas, mapas y dados, como un tablero digital.

**Todo lo demás del documento original se conserva**: el motor de reglas genérico, las fichas configurables, los mapas con cuadrícula, las voces, las campañas.

---

## 2. Cómo se ve y se usa (la experiencia)

### Los dos roles

- **Director de juego (DJ)** — tú. Puede crear y editar todo: atributos, fórmulas, fichas, monstruos, mapas, campañas. Ve información oculta (vida de los monstruos, notas secretas).
- **Jugador** — tus amigos. Cada uno ve y controla su propia ficha, mueve su token en el mapa y tira dados. No puede ver datos del DJ ni editar reglas.

### Las pantallas principales

1. **Inicio / Campañas** — lista de campañas; entras a una y ves sus arcos, eventos y personajes.
2. **Ficha de personaje** — la hoja del personaje sobre un fondo decorativo (pergamino/tablero), con atributos, estadísticas derivadas calculadas automáticamente, equipo e imagen del personaje.
3. **Mesa de juego (mapa local)** — la cuadrícula táctica con los tokens de personajes y monstruos. Todos los conectados ven los movimientos en el instante en que ocurren.
4. **Mapa geográfico** — el mapa del mundo con marcadores de lugares; se navega con zoom y arrastre.
5. **Panel del DJ** — donde tú diseñas: catálogo de atributos, fórmulas, objetos, monstruos, curva de niveles, voces.

### Cómo cambia entre celular y PC (diseño adaptable)

La misma aplicación reordena su interfaz según el tamaño de pantalla:

- **En PC** (pantalla ancha): mapa al centro, ficha resumida en un panel lateral, chat/dados en otro panel. Todo visible a la vez.
- **En celular** (pantalla angosta): una vista a la vez, con pestañas grandes abajo (Mapa · Ficha · Dados · Chat) para cambiar con el pulgar. Los botones y tokens se hacen más grandes para usarse con el dedo; el mapa se mueve con arrastre y se acerca con el gesto de pellizco, igual que Google Maps.

En la práctica: el DJ probablemente jugará desde PC (más espacio para dirigir) y los jugadores podrán estar en el sofá con el celular. Ambos en la misma partida.

---

## 3. Las piezas del programa (módulos)

### Módulo 1 — Motor de reglas y fichas

El corazón del proyecto, igual que en el diseño original: el programa no sabe qué es "Fuerza" o "Maná" — tú defines los atributos, y las estadísticas derivadas (Vida, Defensa, Velocidad...) se calculan con **fórmulas que tú escribes como en Excel**: por ejemplo, Vida máxima = `fuerza * 10 + nivel * 5`. Diseñar una estadística nueva es agregar una fila, no reprogramar nada.

- Atributos organizados en tus tres categorías: física / mental / mágica (y las que quieras añadir después).
- Equipo (armas, armaduras) como objetos con sus propias estadísticas, que al equiparse entran en las fórmulas (`arma.daño_base`).
- Curva de niveles configurable: cuánta experiencia pide cada nivel y qué otorga.
- Monstruos: usan el mismo motor que los personajes, solo son fichas más simples. Un solo sistema para todo.

### Módulo 2 — Mapas

- **Mapa local (batalla)**: cuadrícula donde cada token ocupa una celda. Incluye un editor de "pintar" el mapa: eliges un tipo de terreno (pasto, agua, muro, árbol...) de una paleta y lo colocas celda por celda — como pintar con un pincel en Paint. En la web esto se dibuja con una tecnología estándar del navegador (canvas), muy adecuada para esto.
- **Mapa geográfico (mundo)**: una imagen grande (dibujada o generada fuera del programa) sobre la que se colocan marcadores de ciudades, mazmorras y puntos de interés.
- Movimiento y ataque limitados por las estadísticas: la Velocidad define cuántas celdas te mueves, el arma define el alcance del ataque.

### Módulo 3 — Combate por turnos

- Iniciativa calculada desde un atributo (configurable, como todo).
- Economía de acciones por turno (ej. 1 movimiento + 1 acción).
- Mecánica de resolución recomendada para empezar: **dado de 20 caras + modificador contra una dificultad** (estilo D&D) — simple de entender y de balancear. Queda configurada como dato, así que se puede cambiar después sin rehacer el programa.
- Tirador de dados integrado con historial visible para todos (transparencia en la mesa).

### Módulo 4 — Multijugador en tiempo real

Cuando alguien mueve un token, ataca o tira dados, todos los demás lo ven al instante. Técnicamente se hace con una conexión permanente entre cada jugador y el servidor (WebSocket). Al ser un juego por turnos con un grupo pequeño de amigos, no se necesita infraestructura pesada de videojuegos en línea: el servidor es la única "fuente de verdad" y reparte las novedades a todos.

### Módulo 5 — Voces (texto a voz)

Igual que el diseño original: **ElevenLabs**, un servicio que crea voces a partir de una descripción escrita ("ogro grave y monstruoso", "anciana de voz rasposa", "hombre serpiente que sisea"). El DJ escribe la línea de diálogo, elige la voz del personaje de un catálogo, y el audio suena para todos los conectados. Funciona en español.

### Módulo 6 — Campañas e historia

La estructura del documento original se mantiene tal cual:

```
Campaña
 └── Arco (capítulo)
      └── Evento (fecha, descripción, personajes involucrados, lugar del mapa)
```

Con solo registrar eventos, el programa puede reconstruir la línea de tiempo de la trama, el historial de cada personaje y un mapa de "por dónde ha pasado el grupo".

---

## 4. Tecnologías elegidas (y qué significa cada una)

| Pieza | Tecnología | En palabras simples |
|---|---|---|
| Lo que ves (interfaz) | **React + TypeScript** | La forma más común de construir aplicaciones web modernas; enorme cantidad de ejemplos, ideal para desarrollo con IA |
| El mapa táctico | **Canvas (PixiJS)** | El "lienzo de dibujo" del navegador, acelerado por la tarjeta gráfica; mueve mapas y tokens con fluidez incluso en celulares |
| App instalable | **PWA** | Permite "instalar" la web en el celular con su ícono, pantalla completa y sin barra del navegador |
| El cerebro (servidor) | **Python + FastAPI** | Se conserva del diseño original: guarda los datos, calcula las fórmulas, coordina a los jugadores |
| Tiempo real | **WebSockets** | La conexión permanente que hace que todos vean lo mismo al instante |
| Memoria (base de datos) | **SQLite → PostgreSQL** | Donde se guardan fichas, mapas y campañas. SQLite para desarrollar (cero configuración), PostgreSQL al publicar |
| Fórmulas | **simpleeval** | Evalúa tus fórmulas tipo Excel de forma segura, sin poder ejecutar nada peligroso |
| Voces | **ElevenLabs** | El servicio de voces descrito arriba |
| Publicación (hosting) | **Render / Railway / Fly.io** | Servicios que ponen tu programa en internet para que tus amigos entren desde cualquier lugar; tienen niveles gratuitos o muy baratos para empezar |

### Qué necesitas tú (y qué no)

**No necesitas instalar nada para programar** — el desarrollo lo hace la IA directamente sobre este repositorio. Solo necesitarás, cuando toque:

1. Tu cuenta de GitHub (ya la tienes — aquí vive el código).
2. Una cuenta en un servicio de hosting (Render o similar) cuando queramos ponerlo en internet. Gratis o pocos dólares al mes.
3. Una cuenta de ElevenLabs cuando lleguemos al módulo de voces (tiene nivel gratuito para probar).
4. Imágenes: fondos de ficha, retratos, tiles de terreno. Para empezar se usan assets gratuitos (Kenney.nl, game-icons.net) y luego se reemplazan por arte propio si quieres.

---

## 5. Cosas añadidas al diseño original (propuestas)

1. **Tirador de dados con historial compartido** — imprescindible en una mesa virtual y barato de construir; estaba implícito y ahora es pieza de primera clase.
2. **Chat de la partida** — texto entre jugadores dentro de la app, donde también caen los resultados de dados y los avisos del sistema ("Kaelith recibe 7 de daño").
3. **Niebla de guerra** — el DJ revela el mapa por zonas a medida que el grupo explora. Estándar en mesas virtuales y muy efectivo para el suspenso.
4. **Roles y permisos** — distinción DJ / jugador desde el primer día: qué ve y qué puede tocar cada quien.
5. **Notas y diario** — notas privadas del DJ, notas por jugador y un diario compartido de la campaña.
6. **Exportar/importar** — descargar la campaña completa como archivo (respaldo) y volverla a cargar. Tranquilidad de no perder años de partida.
7. **Música ambiental** *(futuro)* — que el DJ ponga música/ambientes de fondo sincronizados, complemento natural de las voces.

## 6. Cosas eliminadas o aplazadas respecto al diseño original

1. **Unity y todo su ecosistema** (Tilemap, Cinemachine, DOTween, NativeWebSocket, A* Pathfinding) — sustituido por la aplicación web.
2. **Herramientas de mapas de pago** (Wonderdraft, Dungeondraft, Inkarnate) — no se compran al inicio; el editor propio + tiles gratuitos cubren el arranque. Siguen siendo compatibles después: sus mapas se exportan como imagen y se usan de fondo.
3. **Cálculo automático de rutas para monstruos** — aplazado; al empezar, el DJ mueve los monstruos a mano, como en una mesa física.
4. **Streaming de voz en tiempo real** — al inicio, el audio se genera y luego se reproduce (1–2 segundos de espera), que es mucho más simple. Si la espera molesta, se optimiza después.

---

## 7. Hoja de ruta por fases

Cada fase produce algo que se puede ver y probar. No se avanza a la siguiente sin validar la anterior.

| Fase | Qué se construye | Qué podrás hacer al terminarla |
|---|---|---|
| 0 | **Diseño de reglas en papel** | Decidir la mecánica de resolución, tus primeros 6–10 atributos y 2–3 fórmulas de ejemplo |
| 1 | **Servidor + motor de fórmulas** | El cerebro: crear atributos, fichas y fórmulas, y ver que calculan bien (se prueba desde una pantalla técnica automática, sin interfaz aún) |
| 2 | **Ficha de personaje en pantalla** | Abrir la web en tu celular o PC, crear un personaje y ver su ficha con las estadísticas calculándose solas |
| 3 | **Mapa local + editor + tokens** | Pintar un mapa de batalla y mover fichas por la cuadrícula |
| 4 | **Multijugador** | Dos personas (tu PC y tu celular, por ejemplo) viendo el mismo mapa moverse a la vez |
| 5 | **Combate por turnos** | Iniciativa, ataques, daño aplicado con tus fórmulas, dados con historial |
| 6 | **Publicación en internet** | Enviar un enlace a tus amigos y jugar cada uno desde su casa |
| 7 | **Mapa geográfico + campañas** | El mapa del mundo con marcadores y el registro de arcos y eventos |
| 8 | **Voces** | Catálogo de voces por personaje y narración con audio para todos |
| 9 | **Refinamiento** | Niebla de guerra, notas, exportar/importar, música, pulido visual |

---

## 8. Referencias

- FastAPI — WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- simpleeval — motor de fórmulas seguro: https://github.com/danthedeckie/simpleeval
- ElevenLabs — Voice Design: https://elevenlabs.io/docs/eleven-creative/voices/voice-design
- PixiJS — dibujo 2D acelerado en navegador: https://pixijs.com/
- PWA (apps web instalables): https://web.dev/explore/progressive-web-apps
- Kenney.nl — assets gratuitos para prototipar: https://kenney.nl/assets
- Foundry VTT — referencia de mesa virtual extensible: https://foundryvtt.com/
