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
5. **Editor de sistemas** — el taller donde se diseña el sistema de rol completo desde la pantalla: atributos, fórmulas, mecánica de dados, plantillas de objetos, curva de niveles (ver Módulo 0).
6. **Panel del DJ** — la gestión del día a día de la mesa: monstruos, voces, notas secretas, niebla de guerra.

### Cómo cambia entre celular y PC (diseño adaptable)

La misma aplicación reordena su interfaz según el tamaño de pantalla:

- **En PC** (pantalla ancha): mapa al centro, ficha resumida en un panel lateral, chat/dados en otro panel. Todo visible a la vez.
- **En celular** (pantalla angosta): una vista a la vez, con pestañas grandes abajo (Mapa · Ficha · Dados · Chat) para cambiar con el pulgar. Los botones y tokens se hacen más grandes para usarse con el dedo; el mapa se mueve con arrastre y se acerca con el gesto de pellizco, igual que Google Maps.

En la práctica: el DJ probablemente jugará desde PC (más espacio para dirigir) y los jugadores podrán estar en el sofá con el celular. Ambos en la misma partida.

---

## 3. Las piezas del programa (módulos)

### Módulo 0 — Editor de sistemas (el diferenciador del proyecto)

El principio central: **el programa no trae reglas de rol; trae un taller para fabricarlas.** Dentro de la propia aplicación existe un "Editor de sistemas" donde cualquier persona — empezando por ti — diseña su sistema de rol completo desde la pantalla, sin escribir código jamás:

- **Un "Sistema" es una entidad propia** del programa (como lo es una campaña o una ficha). Puedes tener varios sistemas guardados a la vez —tu sistema de fantasía, uno de ciencia ficción, uno experimental— y cada campaña elige con cuál se juega.
- **Editor de atributos**: creas atributos con nombre, categoría y descripción, desde un formulario. Las categorías también las defines tú (física/mental/mágica son solo el ejemplo inicial, no algo fijo).
- **Editor de fórmulas**: escribes las estadísticas derivadas como en Excel (`fuerza * 10 + nivel * 5`). El editor te asiste: mientras escribes te sugiere los nombres de tus atributos, y una **vista previa en vivo** calcula la fórmula al instante contra un personaje de prueba, para que veas el resultado antes de guardar. Si hay un error (escribiste un atributo que no existe, un paréntesis sin cerrar), te lo dice en el momento y en español claro.
- **Editor de la mecánica de resolución**: qué se tira (d20, pool de dados, porcentual), contra qué se compara y qué cuenta como éxito — configurable por sistema, no fijado en el programa.
- **Editor de plantillas de objetos**: defines qué campos tiene un "arma" o "armadura" en *tu* sistema (daño base, alcance, peso, requisitos... los que tú decidas).
- **Editor de curva de niveles**: la tabla de XP por nivel y qué otorga cada subida, editable como una hoja de cálculo.
- **Cambios con red de seguridad**: si editas una fórmula, todas las fichas existentes se recalculan solas. Si intentas borrar un atributo que alguna ficha o fórmula usa, el programa te avisa qué se rompería antes de dejarte hacerlo.
- **Compartir sistemas**: un sistema se exporta como archivo y otra persona lo importa en su cuenta — así tu sistema puede viajar a otras mesas.

En resumen: "diseñar mi sistema desde cero" no significa pedirle cambios al programador — significa abrir el editor y hacerlo tú, en el momento, incluso a mitad de partida.

### Módulo 1 — Motor de reglas y fichas

El motor que ejecuta lo que el Editor de sistemas define: el programa no sabe qué es "Fuerza" o "Maná" — solo sabe guardar los atributos que tú definiste y calcular tus fórmulas. Diseñar una estadística nueva es agregar una fila, no reprogramar nada.

- Cada ficha pertenece a un sistema y hereda de él sus atributos, fórmulas y plantillas.
- Equipo (armas, armaduras) como objetos con las estadísticas que tu sistema defina, que al equiparse entran en las fórmulas (`arma.daño_base`).
- Progresión según la curva de niveles de tu sistema.
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

0. **Editor de sistemas en pantalla** — el diseño original guardaba las reglas como datos configurables; esta versión va más allá: una interfaz completa dentro de la app para crear y modificar el sistema de rol (atributos, fórmulas con vista previa, mecánica de dados, niveles), con soporte para varios sistemas y para compartirlos entre usuarios.
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
| 0 | **Diseño de reglas en papel** | Decidir la mecánica de resolución, tus primeros 6–10 atributos y 2–3 fórmulas de ejemplo — servirán como el primer sistema de prueba del editor |
| 1 | **Servidor + motor de fórmulas** | El cerebro: crear sistemas, atributos, fichas y fórmulas, y ver que calculan bien (se prueba desde una pantalla técnica automática, sin interfaz aún) |
| 2 | **Editor de sistemas + ficha en pantalla** | Abrir la web en tu celular o PC, diseñar tus atributos y fórmulas desde el editor (con vista previa en vivo), crear un personaje y ver su ficha calculándose sola |
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
