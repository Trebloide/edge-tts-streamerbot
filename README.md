# Stream TTS (edge-tts + Streamer.bot)

**English** · [Español](README.es.md)

Twitch and Kick chat reader that uses Microsoft Edge's neural voices ([edge-tts](https://github.com/rany2/edge-tts)).

The interface is available in English (default) and Spanish. Change it in **Advanced → Language / Idioma**.

## Getting started

You can run the app in one of two ways:

- **Executable (no Python needed):** download `StreamTTS.exe` from [Releases](../../releases) and run it. Settings are saved in `config.json`, next to the `.exe`.
- **From source:** double-click `iniciar.bat`. The first time, it installs `edge-tts`, `pygame` and `pystray`. You need Python 3.

Both need an internet connection, because the voices come from Microsoft's service.

To build the `.exe` yourself, run `build_exe.bat`. It creates `dist\StreamTTS.exe`.

## Connecting to Streamer.bot

1. In Streamer.bot, open **Servers/Clients → WebSocket Server**. Turn on **Auto Start** and click **Start Server**.
2. Set the port to `8800`. Streamer.bot defaults to `8080`, but other programs such as Steam often use that port.
3. The app uses `8800` by default. If you pick another port, enter it in the **Connection** tab and click **Reconnect with these settings**.
4. If you turned on authentication for the WebSocket Server, enter the password.

The app now reads Twitch and Kick chat directly, through the `Twitch.ChatMessage` and `Kick.ChatMessage` events. You don't need to create any action.

- **You can use Twitch and Kick at the same time.** Both are on by default. Messages from both chats go into one queue and play in the order they arrive.
- Kick needs Streamer.bot 1.0 or later, with your Kick account connected in Streamer.bot.
- To read only one platform, untick **Read Twitch chat** or **Read Kick chat** in the **Connection** tab.
- Users are matched by name, not by platform. A user with the same name on Twitch and Kick gets the same assigned voice and the same filters.

## Moderation and anti-spam

The app follows your moderators automatically:

| What happens in chat | What the app does |
|---|---|
| A moderator deletes a message (Twitch) | Removes it from the queue, or cuts it off if it is playing. |
| A user gets a timeout or a ban (Twitch and Kick) | Removes all their pending messages, and cuts off the one playing if it is theirs. |

Kick doesn't send an event for deleted messages, so on Kick only timeouts and bans are followed.

Anti-spam, in **Filters and reading**:

- **Seconds between messages per user** (default `0`, off): messages sent sooner are skipped.
- **Max queued messages per user** (default `3`): extra messages are skipped while the queue already has that many from the same user.
- Moderators and the broadcaster are exempt from both limits.

## Viewers choose their voice

Viewers can pick their own voice from chat, from your **favorite** voices only:

```
!voice dalia      → uses es-MX-DaliaNeural (if it is one of your favorites)
!voice            → lists the available voices
!voice off        → back to the default voice
```

- The commands are `!voice` and `!voz`. You can change them in the **Voices** tab.
- The choice is saved in **Voice per user**, so it survives restarts.
- Voice names are the short names, such as `Dalia`, `Alvaro` or `Ava`. The first letters are enough.
- **Chat replies:** the app can answer in chat (for example "your voice is now Dalia"). Streamer.bot only allows this with authentication: turn it on in the WebSocket Server and enter the password in **Connection**. Without it, the command still works, just silently.

## OBS overlay

The app serves a page that shows the message being read, highlighting each word as it is spoken.

1. In OBS, add a **Browser** source.
2. URL: set it up in the **Overlay** tab (theme, text size, accent color, position, marquee, times…) and click **Copy**. For example `http://127.0.0.1:7979/overlay?theme=retro`.
3. Size: for example 800 × 300, or 1920 × 100 for the marquee. The background is transparent.

The settings go in the URL. After changing them, paste the new URL in OBS. **Open in browser** and **Send a test message** let you preview it first.

Themes (`theme` parameter):

| Theme | Look |
|---|---|
| `default` | Dark card with a purple edge |
| `retro` | Green gaming terminal: monospace text, glow, scanlines and a blinking cursor |
| `light` | White card, dark text |
| `dark` | Solid black card, no colored edge |
| `minimal` | Text only, with a black outline |
| `glass` | Frosted translucent card |
| `outline` | Thin white border, almost no background |
| `bubble` | Chat bubble with a tail |
| `lowerthird` | Full-width TV-style bar with the user name as a red tag |
| `ocean` | Blue gradient card |

**Marquee** (`marquee=1`): the message runs on one line from right to left, like a news ticker. The user name stays fixed on the left. The text first appears still, starts moving after one second (`wait`), keeps scrolling while it is being read (entering again from the right), and disappears once it has fully left the screen.

Optional URL parameters:

| Parameter | What it does | Example |
|---|---|---|
| `theme` | Look of the overlay (default `default`) | `/overlay?theme=retro` |
| `marquee` | `1` = one scrolling line | `/overlay?marquee=1` |
| `speed` | Marquee speed in pixels per second (default `180`) | `/overlay?marquee=1&speed=120` |
| `wait` | Seconds the marquee stays still before moving (default `1`) | `/overlay?marquee=1&wait=0` |
| `size` | Font size in pixels (default `30`) | `/overlay?size=40` |
| `hold` | Seconds the text stays after reading (default `2`, not used by the marquee) | `/overlay?hold=5` |
| `pos` | Vertical position: `bottom` (default), `center` or `top` | `/overlay?pos=top` |
| `align` | `left` (default), `center` or `right` (not used by the marquee) | `/overlay?align=center` |
| `accent` | Accent color instead of the theme's: hex without `#` or a CSS color name | `/overlay?accent=ff4d4d` |
| `user` | `0` = hide the user name | `/overlay?user=0` |
| `highlight` | `0` = show the whole text at once, without highlighting the words already read | `/overlay?highlight=0` |

The overlay needs the HTTP server, which is on by default.

## System tray

The app shows an icon in the system tray. From it you can show the window, pause or resume, skip, clear the queue or quit.

To keep the app reading when you close the window, turn on **Close to the system tray** in **Advanced**. To fully exit, use **Quit** in the tray menu.

## Streamer.bot actions: !tts, channel points, bits, Kicks and mod commands (optional)

The [`streamerbot/`](streamerbot/) folder has eight ready-to-import files. Each one is separate, so import only the ones you need.

### Twitch

| File | What it reads | Trigger | After importing |
|---|---|---|---|
| [`tts-twitch-command.txt`](streamerbot/tts-twitch-command.txt) | The text after `!tts` in Twitch chat | `!tts` command (included) | Nothing to do. |
| [`tts-twitch-channel-points.txt`](streamerbot/tts-twitch-channel-points.txt) | The text a viewer types when redeeming a reward | Twitch → Channel Reward → Reward Redemption | Pick your reward in the trigger. |
| [`tts-twitch-bits.txt`](streamerbot/tts-twitch-bits.txt) | The message of a cheer, without the cheermotes | Twitch → Chat → Cheer | Set `minBits` (default `100`). |
| [`tts-twitch-mod-commands.txt`](streamerbot/tts-twitch-mod-commands.txt) | Mod commands (see below) | `!ttsskip`, `!ttsclear`, `!ttspause` (included) | Nothing to do. |

### Kick

| File | What it reads | Trigger | After importing |
|---|---|---|---|
| [`tts-kick-command.txt`](streamerbot/tts-kick-command.txt) | The text after `!tts` in Kick chat | `!tts` command (included, Kick chat source) | Nothing to do. |
| [`tts-kick-channel-points.txt`](streamerbot/tts-kick-channel-points.txt) | The text a viewer types when redeeming a reward | Kick → Channel Reward → Reward Redemption | Pick your reward in the trigger. |
| [`tts-kick-kicks.txt`](streamerbot/tts-kick-kicks.txt) | The message sent with Kicks | Kick → Kicks → Gifted | Set `minKicks` (default `100`). |
| [`tts-kick-mod-commands.txt`](streamerbot/tts-kick-mod-commands.txt) | Mod commands (see below) | `!ttsskip`, `!ttsclear`, `!ttspause` (included, Kick chat source) | Nothing to do. |

Kick actions need Streamer.bot 1.0.2 or later.

You can import the Twitch and Kick files together. Commands with the same name don't clash: one listens to Twitch chat and the other to Kick chat.

### Mod commands

| Command | What it does |
|---|---|
| `!ttsskip` | Skips the message being read. |
| `!ttsclear` | Empties the queue. |
| `!ttspause` | Pauses or resumes reading. |

Only moderators and the broadcaster can use them. For anyone else they do nothing.

### Importing

1. Download the file: open it on GitHub and click **Download raw file**. You can also copy all of its text instead.
2. In Streamer.bot, click **Import** (top bar).
3. Drag the file onto the **Import String** box, or paste the text there.
4. Click **Import**. If Streamer.bot asks to compile C# code, accept.

The actions appear in the **TTS (edge-tts)** group. The commands appear in **Commands**, in the same group.

### What each action contains

| Sub-action | What it does |
|---|---|
| Comment | Explains what to change. |
| Set Argument `minBits` / `minKicks` | Bits and Kicks actions only. Messages with fewer bits or Kicks are not read. |
| Set Argument `ttsPort` | Port of the app's HTTP server (default `7979`). |
| Execute C# Code | Sends the user and the text to the app's `/speak`, URL-encoded, or calls `/skip`, `/clear` or `/toggle` for the mod commands. If the app is closed, it writes a warning to the Streamer.bot log. |

To change a value, double-click the **Set Argument** sub-action and edit **Value**. For example, set `minBits` to `500`.

### Setting up channel point rewards

1. Create the reward on Twitch or Kick, and turn on the option that makes the viewer type text.
2. In Streamer.bot, open the **TTS · Twitch · Channel points** or **TTS · Kick · Channel points** action.
3. Double-click the trigger and pick your reward from the list.

### Avoiding double reading

- **Twitch:** the app doesn't read channel point and bits messages from chat. Only the actions read them. If you don't use these actions, untick that option in **Filters and reading**.
- **`!tts` command:** commands are not read from chat, because **Ignore commands** is on by default. Only the action reads them.
- **Kick:** the app can't tell whether a chat message comes from a redemption. If you see a redemption read twice, turn off **Read Kick chat** or don't use the Kick redemption action.

### If something doesn't work

- **Nothing is read:**
  1. Check that the app is open.
  2. Check that **Connection** shows `HTTP at http://127.0.0.1:7979`.
  3. Check that `ttsPort` matches that port.
- **The import fails:** create the action by hand instead. Use the trigger from the tables above and a **Core → Network → Fetch URL** sub-action with the URL from [Local HTTP server](#local-http-server).
- **To see the error:** open the Streamer.bot log and look for lines that start with `[TTS]`.

### Rebuilding the files

The files are generated by [`streamerbot/build.py`](streamerbot/build.py). To change the default values or the C# code, edit that script and run:

```
py streamerbot/build.py
```

## Local HTTP server

The app also runs a local HTTP server. It listens only on `127.0.0.1`, port `7979`:

| URL | What it does |
|---|---|
| `/speak?text=...&user=...&voice=...` | Reads the text. `user` and `voice` are optional. |
| `/skip` | Stops the current message. |
| `/clear` | Empties the queue. |
| `/pause`, `/resume`, `/toggle` | Pauses, resumes or toggles reading. |
| `/overlay` | The OBS overlay page. |

To build your own action without the import files, use the **Core → Network → Fetch URL** sub-action with this URL:

```
http://127.0.0.1:7979/speak?user=%user%&text=%rawInputUrlEncoded%
```

Trigger it with a command (`!tts`) or a channel point redeem. To read only this way, untick **Read chat** in the **Main** tab.

You can trigger the control URLs from a hotkey action or a Stream Deck button.

## Options

- **Voices**: filter by language, gender or name. Space plays a sample, Enter or double-click selects the voice, and F marks it as a favorite. Favorites appear in the drop-down on the **Main** tab. **Assign to user…** gives a viewer a fixed voice. **Fixed random voice** gives each viewer one of your favorite voices, and that viewer always keeps the same one.
- **Sound**: speed, pitch, voice gain (edge-tts), volume and audio output device. Pick a virtual audio cable to put TTS on its own track in OBS.
- **Test**: **Save MP3…** saves the test text to a file, with `.srt` subtitles if you turn them on.
- **Filters and reading**:
  - Message format (`{user} says: {message}`), a required prefix, and an option to skip commands.
  - Minimum role (subs, VIP, mods), plus removing emotes and links.
  - Limits on message length, queue size and messages per user.
  - Ignored users, blocked words, and replacements (`lol=laughing out loud`). Replacements also apply to usernames.
- **Queue** (Ctrl+Q): remove messages, skip the current one, pause, or ignore a user. Ignoring a user also removes their pending messages.
- **Advanced**:
  - Language (English or Spanish) and dark or light theme.
  - Prefetching the next message.
  - A text file with the message currently being read, for an OBS text source.
  - Close to the system tray.
  - edge-tts options: proxy, timeouts and subtitle type.
- **Shortcuts**: Ctrl+P pauses, Ctrl+S skips and Ctrl+Q opens the queue.

## Testing

```
py test_stream_tts.py
```

## Credits

This project builds on:

- [edge-tts](https://github.com/rany2/edge-tts) by rany2 (LGPL-3.0): connects to Microsoft Edge's speech service and provides the voice list, word timings and subtitles.
- [pygame](https://www.pygame.org) (LGPL-2.1): plays the audio and selects the output device.
- [aiohttp](https://github.com/aio-libs/aiohttp) (Apache-2.0): WebSocket client for Streamer.bot and the local HTTP server.
- [pystray](https://github.com/moses-palmer/pystray) (LGPL-3.0) and [Pillow](https://python-pillow.org) (MIT-CMU): system tray icon.
- [PyInstaller](https://pyinstaller.org) (GPL-2.0 with a bootloader exception that allows any license): builds the `.exe`.
- [Streamer.bot](https://streamer.bot): connects to Twitch and Kick through its [WebSocket API](https://docs.streamer.bot/api/websocket).
- Microsoft neural voices (Azure Speech), used through Microsoft Edge's Read Aloud service.

This repository does not include the libraries. `pip` installs them from `requirements.txt`, and each one keeps its own license. The `.exe` in Releases bundles them unchanged; you can rebuild it with your own versions using `build_exe.bat`.

This project is not affiliated with or endorsed by Microsoft, Twitch, Kick or Streamer.bot. edge-tts uses an unofficial Microsoft service that may change or stop working.

## License

[MIT](LICENSE) © 2026 Trebloide
