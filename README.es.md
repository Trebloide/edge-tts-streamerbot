# Stream TTS (edge-tts + Streamer.bot)

[English](README.md) · **Español**

Lector de chat de Twitch y Kick con las voces neuronales de Microsoft Edge ([edge-tts](https://github.com/rany2/edge-tts)).

La interfaz está en inglés (por defecto) y en español. Para ponerla en español, ve a **Advanced → Language / Idioma** y elige **Español**.

## Arrancar

Doble clic en `iniciar.bat` (instala `edge-tts` y `pygame` la primera vez). Necesita Python 3 e internet.

La configuración se guarda sola en `config.json`.

## Conectar con Streamer.bot

1. En Streamer.bot: **Servers/Clients → WebSocket Server**. Activa **Auto Start** y pulsa **Start Server**.
2. Cambia el puerto a `8800`. Streamer.bot trae `8080`, pero otros programas como Steam suelen ocuparlo.
3. La app ya usa `8800` por defecto. Si eliges otro, cámbialo en la pestaña **Conexión** y pulsa **Reconectar con estos datos**.
4. Si activaste autenticación en el WebSocket Server, escribe la contraseña.

Con eso la app lee directamente el chat de Twitch y el de Kick (eventos `Twitch.ChatMessage` y `Kick.ChatMessage`). No hace falta crear ninguna acción.

- Kick necesita Streamer.bot 1.0 o posterior, con tu cuenta de Kick conectada en Streamer.bot.
- Para leer solo una plataforma, desmarca **Leer chat de Twitch** o **Leer chat de Kick** en la pestaña **Conexión**.

## Acciones de Streamer.bot: !tts, puntos del canal, bits y Kicks (opcional)

La carpeta [`streamerbot/`](streamerbot/) trae seis archivos listos para importar. Van por separado, así que importa solo los que quieras.

### Twitch

| Archivo | Qué lee | Trigger | Después de importar |
|---|---|---|---|
| [`tts-twitch-command.txt`](streamerbot/tts-twitch-command.txt) | El texto después de `!tts` en el chat de Twitch | Comando `!tts` (incluido) | No hay que hacer nada. |
| [`tts-twitch-channel-points.txt`](streamerbot/tts-twitch-channel-points.txt) | El texto que escribe el viewer al canjear una recompensa | Twitch → Channel Reward → Reward Redemption | Elige tu recompensa en el trigger. |
| [`tts-twitch-bits.txt`](streamerbot/tts-twitch-bits.txt) | El mensaje de un cheer, sin los cheermotes | Twitch → Chat → Cheer | Ajusta `minBits` (por defecto `100`). |

### Kick

| Archivo | Qué lee | Trigger | Después de importar |
|---|---|---|---|
| [`tts-kick-command.txt`](streamerbot/tts-kick-command.txt) | El texto después de `!tts` en el chat de Kick | Comando `!tts` (incluido, con el chat de Kick como fuente) | No hay que hacer nada. |
| [`tts-kick-channel-points.txt`](streamerbot/tts-kick-channel-points.txt) | El texto que escribe el viewer al canjear una recompensa | Kick → Channel Reward → Reward Redemption | Elige tu recompensa en el trigger. |
| [`tts-kick-kicks.txt`](streamerbot/tts-kick-kicks.txt) | El mensaje que acompaña a los Kicks | Kick → Kicks → Gifted | Ajusta `minKicks` (por defecto `100`). |

Las acciones de Kick necesitan Streamer.bot 1.0.2 o posterior.

### Importar

1. Descarga el archivo: ábrelo en GitHub y pulsa **Download raw file**. También puedes copiar todo su texto.
2. En Streamer.bot, pulsa **Import** (barra superior).
3. Arrastra el archivo al cuadro **Import String** o pega ahí el texto.
4. Pulsa **Import**. Si Streamer.bot pide compilar código C#, acepta.

Las acciones aparecen en el grupo **TTS (edge-tts)**. Los comandos `!tts` aparecen en **Commands**, en el mismo grupo.

### Qué lleva cada acción

| Sub-acción | Para qué sirve |
|---|---|
| Comment | Explica qué hay que cambiar. |
| Set Argument `minBits` / `minKicks` | Solo en las acciones de bits y Kicks. Los mensajes con menos bits o Kicks no se leen. |
| Set Argument `ttsPort` | Puerto del servidor HTTP de la app (por defecto `7979`). |
| Execute C# Code | Envía el usuario y el texto a `/speak` de la app, codificados para URL. Si la app está cerrada, deja un aviso en el registro de Streamer.bot. |

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
- **Filtros**: formato (por ejemplo `{user} dice: {message}`), prefijo obligatorio, ignorar comandos, rol mínimo (subs, VIP, mods), quitar emotes y enlaces, límite de caracteres y de cola, usuarios ignorados, palabras bloqueadas y reemplazos (`xd=equis de`, también para nombres).
- **Cola** (Ctrl+Q): permite quitar mensajes, saltar el actual, pausar e ignorar a un usuario. Ignorarlo también quita sus mensajes pendientes.
- **Avanzado**: idioma (inglés o español), tema oscuro o claro, precarga del siguiente mensaje y archivo de texto con lo que suena (para una fuente de texto en OBS). También las opciones de edge-tts: proxy, timeouts y tipo de subtítulos.
- **Atajos**: Ctrl+P pausa, Ctrl+S salta y Ctrl+Q abre la cola.

## Comprobar

```
py test_tts_twitch.py
```

## Créditos

Este proyecto se apoya en:

- [edge-tts](https://github.com/rany2/edge-tts) de rany2 (LGPL-3.0): conexión con el servicio de voz de Microsoft Edge, lista de voces y subtítulos.
- [pygame](https://www.pygame.org) (LGPL-2.1): reproducción de audio y elección de la salida.
- [aiohttp](https://github.com/aio-libs/aiohttp) (Apache-2.0): cliente WebSocket para Streamer.bot y servidor HTTP local.
- [Streamer.bot](https://streamer.bot): conexión con Twitch y Kick mediante su [API WebSocket](https://docs.streamer.bot/api/websocket).
- Voces neuronales de Microsoft (Azure Speech), usadas a través del servicio de lectura en voz alta de Microsoft Edge.

Las librerías no se incluyen en este repositorio: se instalan con `pip` desde `requirements.txt` y conservan sus propias licencias.

Este proyecto no está afiliado a Microsoft, Twitch, Kick ni Streamer.bot, ni cuenta con su respaldo. edge-tts usa un servicio no oficial de Microsoft que puede cambiar o dejar de funcionar.

## Licencia

[MIT](LICENSE) © 2026 Trebloide
