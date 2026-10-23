"""Genera los archivos para importar en Streamer.bot (botón Import). Ejecutar: py streamerbot/build.py

Formato: base64(b"SBAE" + gzip(json)). Los tipos de trigger y sub-acción y sus campos salen de
Streamer.bot 1.0.4: Twitch Cheer = 102, Twitch canje = 112, Kick canje = 35024, Kick Kicks = 35025,
comando = 401, C# = 99999, Set Argument = 123, Comentario = 1009. Fuentes del comando (flags):
mensaje de Twitch = 1, mensaje de Kick = 2097152.
"""
import base64
import gzip
import json
import uuid
from pathlib import Path

OUT = Path(__file__).resolve().parent
GROUP = "TTS (edge-tts)"

# Código C# común: llama a /speak de la app con el usuario y el texto codificados para URL.
CSHARP = r"""using System;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;

public class CPHInline
{
    public bool Execute()
    {
%BODY%
    }

    private string GetArg(string name, string fallback)
    {
        object value;
        if (CPH.TryGetArg(name, out value) && value != null && value.ToString().Length > 0)
            return value.ToString();
        return fallback;
    }

    private int GetInt(string name, int fallback)
    {
        int value;
        return int.TryParse(GetArg(name, ""), out value) ? value : fallback;
    }

    private bool Speak(string text)
    {
        text = (text ?? "").Trim();
        if (text.Length == 0)
            return true;
        return Call("/speak?user=" + Uri.EscapeDataString(GetArg("user", GetArg("userName", "")))
            + "&text=" + Uri.EscapeDataString(text));
    }

    // Moderador o el propio streamer (Twitch: broadcastUserName, Kick: broadcastUsername)
    private bool IsModOrBroadcaster()
    {
        bool mod;
        if (bool.TryParse(GetArg("isModerator", "false"), out mod) && mod)
            return true;
        string user = GetArg("userName", "").ToLowerInvariant();
        string owner = GetArg("broadcastUserName", GetArg("broadcastUsername", "")).ToLowerInvariant();
        return user.Length > 0 && user == owner;
    }

    private bool Call(string pathAndQuery)
    {
        Fetch(pathAndQuery);
        return true;
    }

    // Respuesta de la app, o null si no contesta
    private string Fetch(string pathAndQuery)
    {
        try
        {
            using (WebClient client = new WebClient())
            {
                client.Encoding = Encoding.UTF8;
                return client.DownloadString("http://127.0.0.1:" + GetInt("ttsPort", 7979) + pathAndQuery);
            }
        }
        catch (Exception e)
        {
            CPH.LogWarn("[TTS] The TTS app did not answer (is it open?): " + e.Message);
            return null;
        }
    }
}
"""

BODIES = {
    "command": """        // rawInput = texto después de !tts
        return Speak(GetArg("rawInput", ""));""",
    "channel_points": """        // rawInput = texto que escribió el viewer al canjear la recompensa
        return Speak(GetArg("rawInput", ""));""",
    "bits": """        if (GetInt("bits", 0) < GetInt("minBits", 100))
            return true;
        string text = GetArg("messageCheermotesStripped", GetArg("messageStripped", GetArg("message", "")));
        // shortcut: quita cualquier palabra tipo Cheer100/Kappa50 (también "abc123"), por si llegan cheermotes
        text = Regex.Replace(text, @"\\b[A-Za-z]+\\d+\\b", "");
        return Speak(text);""",
    "kicks": """        if (GetInt("kicks.amount", 0) < GetInt("minKicks", 100))
            return true;
        // rawInput = mensaje que acompaña a los Kicks
        return Speak(GetArg("rawInput", ""));""",
}
# Elegir voz: la app cambia la voz del viewer y devuelve la respuesta, que se manda al chat
for platform, send in (("twitch", "CPH.SendMessage(reply)"), ("kick", "CPH.SendKickMessage(reply)")):
    BODIES["voice_" + platform] = f"""        // rawInput = voz pedida (vacío = lista de voces, off = volver a la normal)
        string login = GetArg("userName", GetArg("user", ""));
        string reply = Fetch("/voice?user=" + Uri.EscapeDataString(login)
            + "&name=" + Uri.EscapeDataString(GetArg("user", login))
            + "&voice=" + Uri.EscapeDataString(GetArg("rawInput", "")));
        if (!string.IsNullOrEmpty(reply) && GetArg("voiceReply", "true").ToLowerInvariant() == "true")
            {send};
        return true;"""
# Comandos de moderación: solo mods y el streamer; llaman a los controles de la app
MOD_COMMANDS = [("!ttsskip", "skip", "/skip"), ("!ttsclear", "clear", "/clear"), ("!ttspause", "pause", "/toggle")]
for _, kind, path in MOD_COMMANDS:
    BODIES["mod_" + kind] = f"""        if (!IsModOrBroadcaster())
            return true;
        return Call("{path}");"""


def uid():
    return str(uuid.uuid4())


def sub(type_, index, **fields):
    return {**fields, "id": uid(), "weight": 0.0, "type": type_, "parentId": None, "enabled": True, "index": index}


def comment(text, index):
    return sub(1009, index, value=text, color=None)


def set_arg(name, value, index):
    return sub(123, index, variableName=name, value=value, autoType=True)


def csharp(kind, index):
    code = CSHARP.replace("%BODY%", BODIES[kind])
    return sub(99999, index, name=f"TTS {kind}", description="",
               references=[r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\mscorlib.dll",
                           r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.dll"],
               byteCode=base64.b64encode(code.encode()).decode(), precompile=False, delayStart=False,
               saveResultToVariable=False, saveToVariable="")


def action(name, subs, triggers):
    return {"id": uid(), "queue": None, "enabled": True, "excludeFromHistory": False, "name": name,
            "group": GROUP, "alwaysRun": False, "randomAction": False, "concurrent": False,
            "triggers": triggers, "actions": subs, "actionGroups": [], "collapsedGroups": []}


def trigger(type_, **fields):
    return {**fields, "id": uid(), "type": type_, "enabled": True, "exclusions": []}


def export(path, name, description, actions, commands=()):
    doc = {"meta": {"name": name, "author": "Trebloide", "version": "1.0.0", "description": description,
                    "autoRunAction": None, "minimumVersion": None},
           "data": {"actions": actions, "queues": [], "commands": list(commands),
                    "websocketServers": [], "websocketClients": [], "timers": []},
           "version": 10, "exportedFrom": "0.2.5", "minimumVersion": "0.2.4"}
    s = base64.b64encode(b"SBAE" + gzip.compress(json.dumps(doc, ensure_ascii=False).encode())).decode()
    assert s.startswith("U0JBRR") and json.loads(gzip.decompress(base64.b64decode(s)[4:])) == doc
    path.write_text(s, encoding="ascii")
    print("OK", path.name)


PORT_NOTE = "ttsPort = port of the TTS app's HTTP server / puerto del servidor HTTP de la app (Connection/Conexión)."


REWARD_NOTE = ("Edit the trigger and pick your reward (it must ask the viewer for text). / "
               "Edita el trigger y elige tu recompensa (debe pedir texto al viewer).")
SOURCES = {"Twitch": 1, "Kick": 2097152}


def command(platform, text):
    return {"permittedUsers": [], "permittedGroups": [], "id": uid(), "name": f"TTS {text} ({platform})",
            "enabled": True, "include": False, "mode": 0, "command": text, "regexExplicitCapture": False,
            "location": 0, "ignoreBotAccount": True, "ignoreInternal": True, "sources": SOURCES[platform],
            "persistCounter": False, "persistUserCounter": False, "caseSensitive": False, "globalCooldown": 0,
            "userCooldown": 0, "group": GROUP, "grantType": 0}


def command_file(platform):
    cmd = command(platform, "!tts")
    name = f"TTS · {platform} · !tts command"
    export(OUT / f"tts-{platform.lower()}-command.txt", name,
           f"Reads '!tts <text>' from {platform} chat with the edge-tts app.",
           [action(name, [comment(PORT_NOTE, 0), set_arg("ttsPort", "7979", 1), csharp("command", 2)],
                   [trigger(401, commandId=cmd["id"])])],
           [cmd])


def mod_commands_file(platform):
    actions, commands = [], []
    for text, kind, _ in MOD_COMMANDS:
        cmd = command(platform, text)
        commands.append(cmd)
        actions.append(action(f"TTS · {platform} · {text}",
                              [comment("Only moderators and the broadcaster. / Solo moderadores y el streamer.", 0),
                               comment(PORT_NOTE, 1), set_arg("ttsPort", "7979", 2), csharp("mod_" + kind, 3)],
                              [trigger(401, commandId=cmd["id"])]))
    export(OUT / f"tts-{platform.lower()}-mod-commands.txt", f"TTS · {platform} · Mod commands",
           f"!ttsskip, !ttsclear and !ttspause for {platform} moderators.", actions, commands)


VOICE_NOTE = ("Turn off 'Viewers can choose their voice' in the app's Voices tab, or it answers twice. / "
              "Desactiva 'Los viewers pueden elegir su voz' en la pestaña Voces de la app o contestará dos veces.")
REPLY_NOTE = "voiceReply = true: answer in chat / responder en el chat (false = silent / sin respuesta)."


def voice_file(platform, reward_type):
    """!voice/!voz y un canje de puntos para que el viewer elija su voz entre tus favoritas."""
    commands = [command(platform, text) for text in ("!voice", "!voz")]
    setup = [comment(VOICE_NOTE, 0), comment(PORT_NOTE, 1), set_arg("ttsPort", "7979", 2),
             comment(REPLY_NOTE, 3), set_arg("voiceReply", "true", 4)]
    kind = "voice_" + platform.lower()
    actions = [
        action(f"TTS · {platform} · !voice command",
               setup + [csharp(kind, 5)], [trigger(401, commandId=c["id"]) for c in commands]),
        action(f"TTS · {platform} · Channel points: choose voice",
               [comment(REWARD_NOTE, 0)] + [{**x, "id": uid(), "index": x["index"] + 1} for x in setup]
               + [csharp(kind, 6)], [trigger(reward_type, rewardId=None)]),
    ]
    export(OUT / f"tts-{platform.lower()}-voice.txt", f"TTS · {platform} · Choose voice",
           f"!voice / !voz and a channel point reward so {platform} viewers pick their TTS voice "
           "from your favorites.", actions, commands)


def reward_file(platform, trigger_type):
    name = f"TTS · {platform} · Channel points"
    export(OUT / f"tts-{platform.lower()}-channel-points.txt", name,
           f"Reads the text of a {platform} channel point redemption with the edge-tts app.",
           [action(name, [comment(REWARD_NOTE, 0), comment(PORT_NOTE, 1), set_arg("ttsPort", "7979", 2),
                          csharp("channel_points", 3)],
                   [trigger(trigger_type, rewardId=None)])])


def build():
    command_file("Twitch")
    reward_file("Twitch", 112)
    export(OUT / "tts-twitch-bits.txt", "TTS · Twitch · Bits", "Reads cheer messages with at least minBits bits.",
           [action("TTS · Twitch · Bits",
                   [comment("minBits = minimum bits to read the message / mínimo de bits para leer el mensaje.", 0),
                    set_arg("minBits", "100", 1),
                    comment(PORT_NOTE, 2), set_arg("ttsPort", "7979", 3), csharp("bits", 4)],
                   [trigger(102, min=-1, max=-1)])])
    mod_commands_file("Twitch")
    voice_file("Twitch", 112)

    command_file("Kick")
    mod_commands_file("Kick")
    voice_file("Kick", 35024)
    reward_file("Kick", 35024)
    export(OUT / "tts-kick-kicks.txt", "TTS · Kick · Kicks", "Reads Kicks gift messages with at least minKicks Kicks.",
           [action("TTS · Kick · Kicks",
                   [comment("minKicks = minimum Kicks to read the message / mínimo de Kicks para leer el mensaje.",
                            0),
                    set_arg("minKicks", "100", 1),
                    comment(PORT_NOTE, 2), set_arg("ttsPort", "7979", 3), csharp("kicks", 4)],
                   [trigger(35025, min=-1, max=-1)])])


if __name__ == "__main__":
    build()
