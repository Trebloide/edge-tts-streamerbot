# Stream TTS (edge-tts + Streamer.bot)

**English** · [Español](README.es.md)

Twitch and Kick chat reader that uses Microsoft Edge's neural voices ([edge-tts](https://github.com/rany2/edge-tts)).

The interface is available in English (default) and Spanish. Change it in **Advanced → Language / Idioma**.

## Getting started

Double-click `iniciar.bat`. The first time, it installs `edge-tts` and `pygame`. You need Python 3 and an internet connection.

Settings are saved automatically to `config.json`.

## Connecting to Streamer.bot

1. In Streamer.bot, open **Servers/Clients → WebSocket Server**. Turn on **Auto Start** and click **Start Server**.
2. Set the port to `8800`. Streamer.bot defaults to `8080`, but other programs such as Steam often use that port.
3. The app uses `8800` by default. If you pick another port, enter it in the **Connection** tab and click **Reconnect with these settings**.
4. If you turned on authentication for the WebSocket Server, enter the password.

The app now reads Twitch and Kick chat directly, through the `Twitch.ChatMessage` and `Kick.ChatMessage` events. You don't need to create any action.

- Kick needs Streamer.bot 1.0 or later, with your Kick account connected in Streamer.bot.
- To read only one platform, untick **Read Twitch chat** or **Read Kick chat** in the **Connection** tab.

## Streamer.bot actions: !tts, channel points, bits and Kicks (optional)

The `streamerbot/` folder has six ready-to-import files. Each one is separate, so import only the ones you need:

| File | Action | After importing |
|---|---|---|
| `tts-twitch-command.txt` | `!tts <text>` command in Twitch chat | Nothing to do. |
| `tts-twitch-channel-points.txt` | Reads the text of a Twitch channel point redemption | Edit the trigger and pick your reward. The reward must ask the viewer for text. |
| `tts-twitch-bits.txt` | Reads Twitch cheer messages | Change the `minBits` argument (default `100`) to set the minimum bits. |
| `tts-kick-command.txt` | `!tts <text>` command in Kick chat | Nothing to do. |
| `tts-kick-channel-points.txt` | Reads the text of a Kick channel point redemption | Edit the trigger and pick your reward. The reward must ask the viewer for text. |
| `tts-kick-kicks.txt` | Reads the message sent with Kicks | Change the `minKicks` argument (default `100`) to set the minimum Kicks. |

To import a file:

1. In Streamer.bot, click **Import**.
2. Drag the file onto the window, or paste its content into **Import String**.
3. Click **Import**.

The actions call the app's `/speak` URL on port `7979`. If you change the HTTP port in the app, change the `ttsPort` argument in each action.

The app doesn't read Twitch channel point and bits messages from chat, so they aren't read twice. To turn this off, untick the option in **Filters and reading**.

To rebuild the files, run `py streamerbot/build.py`.

## Local HTTP server

The app also runs a local HTTP server. It listens only on `127.0.0.1`, port `7979`:

| URL | What it does |
|---|---|
| `/speak?text=...&user=...&voice=...` | Reads the text. `user` and `voice` are optional. |
| `/skip` | Stops the current message. |
| `/clear` | Empties the queue. |
| `/pause`, `/resume`, `/toggle` | Pauses, resumes or toggles reading. |

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
  - Limits on message length and queue size.
  - Ignored users, blocked words, and replacements (`lol=laughing out loud`). Replacements also apply to usernames.
- **Queue** (Ctrl+Q): remove messages, skip the current one, pause, or ignore a user. Ignoring a user also removes their pending messages.
- **Advanced**:
  - Language (English or Spanish) and dark or light theme.
  - Prefetching the next message.
  - A text file with the message currently being read, for an OBS text source.
  - edge-tts options: proxy, timeouts and subtitle type.
- **Shortcuts**: Ctrl+P pauses, Ctrl+S skips and Ctrl+Q opens the queue.

## Testing

```
py test_tts_twitch.py
```

## Credits

This project builds on:

- [edge-tts](https://github.com/rany2/edge-tts) by rany2 (LGPL-3.0): connects to Microsoft Edge's speech service and provides the voice list and subtitles.
- [pygame](https://www.pygame.org) (LGPL-2.1): plays the audio and selects the output device.
- [aiohttp](https://github.com/aio-libs/aiohttp) (Apache-2.0): WebSocket client for Streamer.bot and the local HTTP server.
- [Streamer.bot](https://streamer.bot): connects to Twitch and Kick through its [WebSocket API](https://docs.streamer.bot/api/websocket).
- Microsoft neural voices (Azure Speech), used through Microsoft Edge's Read Aloud service.

This repository does not include the libraries. `pip` installs them from `requirements.txt`, and each one keeps its own license.

This project is not affiliated with or endorsed by Microsoft, Twitch, Kick or Streamer.bot. edge-tts uses an unofficial Microsoft service that may change or stop working.

## License

[MIT](LICENSE) © 2026 Trebloide
