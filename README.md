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

- **You can use Twitch and Kick at the same time.** Both are on by default. Messages from both chats go into one queue and play in the order they arrive.
- Kick needs Streamer.bot 1.0 or later, with your Kick account connected in Streamer.bot.
- To read only one platform, untick **Read Twitch chat** or **Read Kick chat** in the **Connection** tab.
- Users are matched by name, not by platform. A user with the same name on Twitch and Kick gets the same assigned voice and the same filters.

## Streamer.bot actions: !tts, channel points, bits and Kicks (optional)

The [`streamerbot/`](streamerbot/) folder has six ready-to-import files. Each one is separate, so import only the ones you need.

### Twitch

| File | What it reads | Trigger | After importing |
|---|---|---|---|
| [`tts-twitch-command.txt`](streamerbot/tts-twitch-command.txt) | The text after `!tts` in Twitch chat | `!tts` command (included) | Nothing to do. |
| [`tts-twitch-channel-points.txt`](streamerbot/tts-twitch-channel-points.txt) | The text a viewer types when redeeming a reward | Twitch → Channel Reward → Reward Redemption | Pick your reward in the trigger. |
| [`tts-twitch-bits.txt`](streamerbot/tts-twitch-bits.txt) | The message of a cheer, without the cheermotes | Twitch → Chat → Cheer | Set `minBits` (default `100`). |

### Kick

| File | What it reads | Trigger | After importing |
|---|---|---|---|
| [`tts-kick-command.txt`](streamerbot/tts-kick-command.txt) | The text after `!tts` in Kick chat | `!tts` command (included, Kick chat source) | Nothing to do. |
| [`tts-kick-channel-points.txt`](streamerbot/tts-kick-channel-points.txt) | The text a viewer types when redeeming a reward | Kick → Channel Reward → Reward Redemption | Pick your reward in the trigger. |
| [`tts-kick-kicks.txt`](streamerbot/tts-kick-kicks.txt) | The message sent with Kicks | Kick → Kicks → Gifted | Set `minKicks` (default `100`). |

Kick actions need Streamer.bot 1.0.2 or later.

You can import the Twitch and Kick files together. The two `!tts` commands don't clash: one listens to Twitch chat and the other to Kick chat.

### Importing

1. Download the file: open it on GitHub and click **Download raw file**. You can also copy all of its text instead.
2. In Streamer.bot, click **Import** (top bar).
3. Drag the file onto the **Import String** box, or paste the text there.
4. Click **Import**. If Streamer.bot asks to compile C# code, accept.

The actions appear in the **TTS (edge-tts)** group. The `!tts` commands appear in **Commands**, in the same group.

### What each action contains

| Sub-action | What it does |
|---|---|
| Comment | Explains what to change. |
| Set Argument `minBits` / `minKicks` | Bits and Kicks actions only. Messages with fewer bits or Kicks are not read. |
| Set Argument `ttsPort` | Port of the app's HTTP server (default `7979`). |
| Execute C# Code | Sends the user and the text to the app's `/speak`, URL-encoded. If the app is closed, it writes a warning to the Streamer.bot log. |

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
py test_stream_tts.py
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
