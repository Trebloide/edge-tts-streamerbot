# Stream TTS (edge-tts + Streamer.bot)

[English](README.md) · **Español**

Lector de chat de Twitch y Kick con las voces neuronales de Microsoft Edge ([edge-tts](https://github.com/rany2/edge-tts)).

La interfaz está en inglés (por defecto) y en español. Para ponerla en español, ve a **Advanced → Language / Idioma** y elige **Español**.

## Arrancar

Puedes usar la app de dos formas:

- **Ejecutable (sin instalar Python):** descarga `StreamTTS.exe` desde [Releases](../../releases) y ábrelo. La configuración se guarda en `config.json`, junto al `.exe`.
- **Desde el código:** doble clic en `iniciar.bat`. La primera vez instala `edge-tts`, `pygame` y `pystray`. Necesita Python 3.

Las dos formas necesitan internet, porque las voces vienen del servicio de Microsoft.

Para generar tú el `.exe`, ejecuta `build_exe.bat`. Crea `dist\StreamTTS.exe`.

## Conectar con Streamer.bot

1. En Streamer.bot: **Servers/Clients → WebSocket Server**. Activa **Auto Start** y pulsa **Start Server**.
2. Cambia el puerto a `8800`. Streamer.bot trae `8080`, pero otros programas como Steam suelen ocuparlo.
3. La app ya usa `8800` por defecto. Si eliges otro, cámbialo en la pestaña **Conexión** y pulsa **Reconectar con estos datos**.
4. Si activaste autenticación en el WebSocket Server, escribe la contraseña.

Con eso la app lee directamente el chat de Twitch y el de Kick (eventos `Twitch.ChatMessage` y `Kick.ChatMessage`). No hace falta crear ninguna acción.

- **Puedes usar Twitch y Kick a la vez.** Los dos vienen activados por defecto. Los mensajes de los dos chats van a una sola cola y suenan en el orden en que llegan.
- Kick necesita Streamer.bot 1.0 o posterior, con tu cuenta de Kick conectada en Streamer.bot.
- Para leer solo una plataforma, desmarca **Leer chat de Twitch** o **Leer chat de Kick** en la pestaña **Conexión**.
- Los usuarios se reconocen por el nombre, no por la plataforma. Un usuario con el mismo nombre en Twitch y en Kick tiene la misma voz asignada y los mismos filtros.

## Moderación y anti-spam

La app sigue a tus moderadores sola:

| Qué pasa en el chat | Qué hace la app |
|---|---|
| Un moderador borra un mensaje (Twitch) | Lo quita de la cola, o lo corta si está sonando. |
| Un usuario recibe timeout o ban (Twitch y Kick) | Quita todos sus mensajes pendientes, y corta el que suena si es suyo. |

Kick no avisa cuando se borra un mensaje, así que en Kick solo se siguen los timeouts y los bans.

Anti-spam, en **Filtros y lectura**:

- **Segundos entre mensajes por usuario** (por defecto `0`, desactivado): los mensajes enviados antes de ese tiempo no se leen.
- **Máx. mensajes en cola por usuario** (por defecto `3`): si un usuario ya tiene esos mensajes esperando, los siguientes no se leen.
- Los moderadores y el streamer no cuentan para ninguno de los dos límites.

## Los viewers eligen su voz

Los viewers pueden elegir su voz desde el chat, solo entre tus voces **favoritas**:

```
!voz dalia      → usa es-MX-DaliaNeural (si está en tus favoritas)
!voz            → lista las voces disponibles
!voz off        → vuelve a la voz predeterminada
```

- Los comandos son `!voz` y `!voice`. Puedes cambiarlos en la pestaña **Voces**.
- La elección se guarda en **Voz por usuario**, así que se mantiene al reiniciar.
- Las voces se nombran por su nombre corto, como `Dalia`, `Alvaro` o `Ava`. Basta con las primeras letras.
- **Respuestas en el chat:** la app puede contestar en el chat (por ejemplo "ahora tu voz es Dalia"). Streamer.bot solo lo permite con autenticación: actívala en el WebSocket Server y pon la contraseña en **Conexión**. Sin ella el comando funciona igual, solo que sin contestar.

## Overlay para OBS

La app sirve una página que muestra el mensaje que se está leyendo y resalta cada palabra según suena.

1. En OBS, añade una fuente de **Navegador**.
2. URL: configúrala en la pestaña **Overlay** (tema, tamaño del texto, color de acento, posición, marquesina, tiempos…) y pulsa **Copiar**. Por ejemplo `http://127.0.0.1:7979/overlay?theme=retro`.
3. Tamaño: por ejemplo 800 × 300, o 1920 × 100 para la marquesina. El fondo es transparente.

Los ajustes van en la URL. Después de cambiarlos, pega la URL nueva en OBS. Con **Abrir en el navegador** y **Enviar mensaje de prueba** puedes verlo antes.

Temas (parámetro `theme`):

| Tema | Aspecto |
|---|---|
| `default` | Tarjeta oscura con borde morado |
| `retro` | Terminal gaming verde: letra monoespaciada, brillo, líneas de barrido y cursor parpadeante |
| `light` | Tarjeta blanca con texto oscuro |
| `dark` | Tarjeta negra sólida, sin borde de color |
| `minimal` | Solo texto, con contorno negro |
| `glass` | Tarjeta translúcida tipo cristal esmerilado |
| `outline` | Borde blanco fino, casi sin fondo |
| `bubble` | Bocadillo de chat con pico |
| `lowerthird` | Barra a todo el ancho estilo televisión, con el usuario en una etiqueta roja |
| `ocean` | Tarjeta con degradado azul |

**Marquesina** (`marquee=1`): el mensaje pasa en una sola línea de derecha a izquierda, como un rótulo de noticias. El nombre del usuario se queda fijo a la izquierda. El texto aparece primero quieto, empieza a moverse al segundo (`wait`), sigue pasando mientras se lee (volviendo a entrar por la derecha) y desaparece cuando ha salido del todo de la pantalla.

Parámetros opcionales en la URL:

| Parámetro | Para qué sirve | Ejemplo |
|---|---|---|
| `theme` | Aspecto del overlay (por defecto `default`) | `/overlay?theme=retro` |
| `marquee` | `1` = una línea que se desplaza | `/overlay?marquee=1` |
| `speed` | Velocidad de la marquesina en píxeles por segundo (por defecto `180`) | `/overlay?marquee=1&speed=120` |
| `wait` | Segundos que la marquesina se queda quieta antes de moverse (por defecto `1`) | `/overlay?marquee=1&wait=0` |
| `size` | Tamaño de letra en píxeles (por defecto `30`) | `/overlay?size=40` |
| `hold` | Segundos que se queda el texto al terminar (por defecto `2`; la marquesina no lo usa) | `/overlay?hold=5` |
| `pos` | Posición vertical: `bottom` (abajo, por defecto), `center` o `top` | `/overlay?pos=top` |
| `align` | `left` (por defecto), `center` o `right` (la marquesina no lo usa) | `/overlay?align=center` |
| `accent` | Color de acento en vez del del tema: hex sin `#` o nombre de color CSS | `/overlay?accent=ff4d4d` |
| `user` | `0` = ocultar el nombre del usuario | `/overlay?user=0` |
| `highlight` | `0` = mostrar todo el texto igual, sin resaltar las palabras ya leídas | `/overlay?highlight=0` |

El overlay necesita el servidor HTTP, que viene activado.

## Bandeja del sistema

La app pone un icono en la bandeja del sistema. Desde él puedes mostrar la ventana, pausar o reanudar, saltar, vaciar la cola o salir.

Para que la app siga leyendo al cerrar la ventana, activa **Cerrar a la bandeja del sistema** en **Avanzado**. Para salir del todo, usa **Salir** en el menú de la bandeja.

## Acciones de Streamer.bot: !tts, puntos del canal, bits, Kicks y comandos de mods (opcional)

La carpeta [`streamerbot/`](streamerbot/) trae ocho archivos listos para importar. Van por separado, así que importa solo los que quieras.

### Twitch

| Archivo | Qué lee | Trigger | Después de importar |
|---|---|---|---|
| [`tts-twitch-command.txt`](streamerbot/tts-twitch-command.txt) | El texto después de `!tts` en el chat de Twitch | Comando `!tts` (incluido) | No hay que hacer nada. |
| [`tts-twitch-channel-points.txt`](streamerbot/tts-twitch-channel-points.txt) | El texto que escribe el viewer al canjear una recompensa | Twitch → Channel Reward → Reward Redemption | Elige tu recompensa en el trigger. |
| [`tts-twitch-bits.txt`](streamerbot/tts-twitch-bits.txt) | El mensaje de un cheer, sin los cheermotes | Twitch → Chat → Cheer | Ajusta `minBits` (por defecto `100`). |
| [`tts-twitch-mod-commands.txt`](streamerbot/tts-twitch-mod-commands.txt) | Comandos de mods (ver abajo) | `!ttsskip`, `!ttsclear`, `!ttspause` (incluidos) | No hay que hacer nada. |

### Kick

| Archivo | Qué lee | Trigger | Después de importar |
|---|---|---|---|
| [`tts-kick-command.txt`](streamerbot/tts-kick-command.txt) | El texto después de `!tts` en el chat de Kick | Comando `!tts` (incluido, con el chat de Kick como fuente) | No hay que hacer nada. |
| [`tts-kick-channel-points.txt`](streamerbot/tts-kick-channel-points.txt) | El texto que escribe el viewer al canjear una recompensa | Kick → Channel Reward → Reward Redemption | Elige tu recompensa en el trigger. |
| [`tts-kick-kicks.txt`](streamerbot/tts-kick-kicks.txt) | El mensaje que acompaña a los Kicks | Kick → Kicks → Gifted | Ajusta `minKicks` (por defecto `100`). |
| [`tts-kick-mod-commands.txt`](streamerbot/tts-kick-mod-commands.txt) | Comandos de mods (ver abajo) | `!ttsskip`, `!ttsclear`, `!ttspause` (incluidos, con el chat de Kick como fuente) | No hay que hacer nada. |

Las acciones de Kick necesitan Streamer.bot 1.0.2 o posterior.

Puedes importar a la vez los archivos de Twitch y los de Kick. Los comandos con el mismo nombre no chocan: uno escucha el chat de Twitch y el otro el de Kick.

### Comandos de mods

| Comando | Qué hace |
|---|---|
| `!ttsskip` | Salta el mensaje que se está leyendo. |
| `!ttsclear` | Vacía la cola. |
| `!ttspause` | Pausa o reanuda la lectura. |

Solo los pueden usar los moderadores y el streamer. Para el resto no hacen nada.

### Importar

1. Descarga el archivo: ábrelo en GitHub y pulsa **Download raw file**. También puedes copiar todo su texto.
2. En Streamer.bot, pulsa **Import** (barra superior).
3. Arrastra el archivo al cuadro **Import String** o pega ahí el texto.
4. Pulsa **Import**. Si Streamer.bot pide compilar código C#, acepta.

Las acciones aparecen en el grupo **TTS (edge-tts)**. Los comandos aparecen en **Commands**, en el mismo grupo.

### Qué lleva cada acción

| Sub-acción | Para qué sirve |
|---|---|
| Comment | Explica qué hay que cambiar. |
| Set Argument `minBits` / `minKicks` | Solo en las acciones de bits y Kicks. Los mensajes con menos bits o Kicks no se leen. |
| Set Argument `ttsPort` | Puerto del servidor HTTP de la app (por defecto `7979`). |
| Execute C# Code | Envía el usuario y el texto a `/speak` de la app, codificados para URL, o llama a `/skip`, `/clear` o `/toggle` en los comandos de mods. Si la app está cerrada, deja un aviso en el registro de Streamer.bot. |

Para cambiar un valor, haz doble clic en la sub-acción **Set Argument** y edita **Value**. Por ejemplo, pon `minBits` a `500`.

### Configurar las recompensas de puntos

1. Crea la recompensa en Twitch o Kick y activa la opción que obliga al viewer a escribir texto.
2. En Streamer.bot, abre la acción **TTS · Twitch · Channel points** o **TTS · Kick · Channel points**.
3. Haz doble clic en el trigger y elige tu recompensa de la lista.

### Evitar que se lea dos veces

- **Twitch:** la app no lee del chat los mensajes de puntos y bits. Solo los leen las acciones. Si no usas estas acciones, desmarca esa opción en **Filtros y lectura**.
- **Comando `!tts`:** los comandos no se leen desde el chat, porque **Ignorar comandos** está activado por defecto. Solo los lee la acción.
- **Kick:** la app no puede saber si un mensaje del chat viene de un canje. Si oyes un canje dos veces, desactiva **Leer chat de Kick** o no uses la acción de canjes de Kick.

### Si algo no funciona

- **No se lee nada:**
  1. Comprueba que la app está abierta.
  2. Comprueba que en **Conexión** pone `HTTP en http://127.0.0.1:7979`.
  3. Comprueba que `ttsPort` coincide con ese puerto.
- **La importación falla:** crea la acción a mano. Usa el trigger de las tablas de arriba y una sub-acción **Core → Network → Fetch URL** con la URL de [Servidor HTTP local](#servidor-http-local).
- **Para ver el error:** abre el registro de Streamer.bot y busca las líneas que empiezan por `[TTS]`.

### Regenerar los archivos

Los archivos salen de [`streamerbot/build.py`](streamerbot/build.py). Para cambiar los valores por defecto o el código C#, edita ese script y ejecuta:

```
py streamerbot/build.py
```

## Servidor HTTP local

La app también abre un servidor HTTP local (solo `127.0.0.1`, puerto `7979`):

| URL | Qué hace |
|---|---|
| `/speak?text=...&user=...&voice=...` | Lee el texto. `user` y `voice` son opcionales. |
| `/skip` | Corta el mensaje actual. |
| `/clear` | Vacía la cola. |
| `/pause`, `/resume`, `/toggle` | Pausa, reanuda o alterna la lectura. |
| `/overlay` | La página del overlay de OBS. |

Para crear tu propia acción sin los archivos de importación, usa la sub-acción **Core → Network → Fetch URL** con esta URL:

```
http://127.0.0.1:7979/speak?user=%user%&text=%rawInputUrlEncoded%
```

Asígnale un comando (`!tts`) o un canje de puntos. Si solo quieres leer así, desmarca **Leer chat** en la pestaña Principal.

Para los controles puedes usar una acción con atajo de teclado o un botón del Stream Deck.

## Opciones

- **Voces**: filtra por idioma, género o nombre. Espacio escucha la voz, Enter o doble clic la elige y F la marca como favorita. Las favoritas salen en el desplegable de la pestaña Principal. **Asignar a usuario…** da una voz fija a un viewer. **Voz aleatoria fija** reparte tus favoritas entre los viewers, y cada uno conserva siempre la misma.
- **Sonido**: velocidad, tono, ganancia de la voz (edge-tts), volumen y salida de audio. Elige un cable virtual para separar el TTS en OBS.
- **Prueba**: **Guardar MP3…** guarda el texto de prueba en un archivo, con subtítulos `.srt` si los activas.
- **Filtros**: formato (por ejemplo `{user} dice: {message}`), prefijo obligatorio, ignorar comandos, rol mínimo (subs, VIP, mods), quitar emotes y enlaces, límites de caracteres, de cola y de mensajes por usuario, usuarios ignorados, palabras bloqueadas y reemplazos (`xd=equis de`, también para nombres).
- **Cola** (Ctrl+Q): permite quitar mensajes, saltar el actual, pausar e ignorar a un usuario. Ignorarlo también quita sus mensajes pendientes.
- **Avanzado**: idioma (inglés o español), tema oscuro o claro, precarga del siguiente mensaje, archivo de texto con lo que suena (para una fuente de texto en OBS) y cerrar a la bandeja del sistema. También las opciones de edge-tts: proxy, timeouts y tipo de subtítulos.
- **Atajos**: Ctrl+P pausa, Ctrl+S salta y Ctrl+Q abre la cola.

## Comprobar

```
py test_stream_tts.py
```

## Créditos

Este proyecto se apoya en:

- [edge-tts](https://github.com/rany2/edge-tts) de rany2 (LGPL-3.0): conexión con el servicio de voz de Microsoft Edge, lista de voces, tiempos de cada palabra y subtítulos.
- [pygame](https://www.pygame.org) (LGPL-2.1): reproducción de audio y elección de la salida.
- [aiohttp](https://github.com/aio-libs/aiohttp) (Apache-2.0): cliente WebSocket para Streamer.bot y servidor HTTP local.
- [pystray](https://github.com/moses-palmer/pystray) (LGPL-3.0) y [Pillow](https://python-pillow.org) (MIT-CMU): icono en la bandeja del sistema.
- [PyInstaller](https://pyinstaller.org) (GPL-2.0 con una excepción para el cargador que permite cualquier licencia): genera el `.exe`.
- [Streamer.bot](https://streamer.bot): conexión con Twitch y Kick mediante su [API WebSocket](https://docs.streamer.bot/api/websocket).
- Voces neuronales de Microsoft (Azure Speech), usadas a través del servicio de lectura en voz alta de Microsoft Edge.

Las librerías no se incluyen en este repositorio: se instalan con `pip` desde `requirements.txt` y conservan sus propias licencias. El `.exe` de Releases las incluye sin modificar; puedes generarlo con tus propias versiones usando `build_exe.bat`.

Este proyecto no está afiliado a Microsoft, Twitch, Kick ni Streamer.bot, ni cuenta con su respaldo. edge-tts usa un servicio no oficial de Microsoft que puede cambiar o dejar de funcionar.

## Licencia

[MIT](LICENSE) © 2026 Trebloide
