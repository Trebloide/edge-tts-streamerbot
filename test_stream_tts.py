"""Comprobaciones del procesado de mensajes. Ejecutar: py test_stream_tts.py"""
import json
import tempfile
from pathlib import Path

import stream_tts
from stream_tts import DEFAULTS, chat_speech, http_speech

cfg = dict(DEFAULTS, template="{user} dice: {message}", link_text="enlace", replacements="xd=equis de",
           user_voices="pepe=es-MX-JorgeNeural")


def msg1(text, login="ana_gamer", name="Ana_Gamer", role=1, sub=False, emotes=(), bits=0, reward=False):
    """Evento con formato Streamer.bot 1.x."""
    return {"text": text, "user": {"login": login, "name": name, "role": role, "subscribed": sub},
            "emotes": [{"Name": e} for e in emotes], "meta": {"isCustomReward": reward},
            "parts": [{"type": "cheer", "text": f"Cheer{bits}"}] if bits else []}


def msg02(text, login="ana_gamer", name="Ana_Gamer", role=1, sub=False, emotes=(), bits=0, reward=False):
    """Evento con formato Streamer.bot 0.2.x."""
    return {"message": {"message": text, "username": login, "displayName": name, "role": role,
                        "subscriber": sub, "emotes": [{"name": e} for e in emotes],
                        "bits": bits, "hasBits": bits > 0, "isCustomReward": reward}}


for make in (msg1, msg02):
    speech, voice, login, why = chat_speech(cfg, make("hola xd Kappa jajajajajaja", emotes=["Kappa"]))
    assert speech == "Ana Gamer dice: hola equis de jajaja", speech
    assert voice == DEFAULTS["voice"] and login == "ana_gamer"
    # mismo usuario seguido: sin nombre
    assert chat_speech(cfg, make("otra vez"), "ana_gamer")[0] == "otra vez"
    assert chat_speech(cfg, make("!comando"))[3] == "command"
    assert chat_speech(cfg, make("hola", login="nightbot", name="Nightbot"))[3] == "ignored user"
    assert chat_speech(cfg, make("mira https://x.com/a"))[0] == "Ana Gamer dice: mira enlace"
    assert chat_speech(cfg, make("Kappa", emotes=["Kappa"]))[3] == "empty message"
    assert chat_speech(cfg, make("hola", login="pepe", name="Pepe"))[1] == "es-MX-JorgeNeural"

    subs = dict(cfg, min_role="subs")
    assert chat_speech(subs, make("hola"))[3] == "role too low"
    assert chat_speech(subs, make("hola", sub=True))[0]
    assert chat_speech(subs, make("hola", role=3))[0]  # mod

    pre = dict(cfg, prefix="!tts")
    assert chat_speech(pre, make("hola"))[3] == "no prefix"
    assert chat_speech(pre, make("!TTS hola"))[0] == "Ana Gamer dice: hola"

    blocked = dict(cfg, blocked_words="feo")
    assert chat_speech(blocked, make("qué FEO"))[3] == "blocked word 'feo'"
    assert chat_speech(blocked, make("feote"))[0]  # solo palabras completas

    # canjes de puntos y bits: los leen las acciones de Streamer.bot, no el chat
    assert chat_speech(cfg, make("hola", bits=100))[3] == "channel points/bits"
    assert chat_speech(cfg, make("hola", reward=True))[3] == "channel points/bits"
    assert chat_speech(dict(cfg, skip_rewards_bits=False), make("hola", reward=True))[0]

# Kick (Streamer.bot 1.x): suscripción en isSubscribed, emotes en parts y etiquetas [emote:id:nombre] en el texto
kick = {"text": "hola [emote:37226:KEKW] kekw que tal", "user": {"login": "kick_fan", "name": "Kick_Fan", "role": 1,
                                                              "isSubscribed": True},
        "parts": [{"type": "text", "text": "hola "}, {"type": "emote", "text": "KEKW"}]}
assert chat_speech(cfg, kick)[:3] == ("Kick Fan dice: hola kekw que tal", DEFAULTS["voice"], "kick_fan")
assert chat_speech(dict(cfg, min_role="subs"), kick)[0]  # isSubscribed cuenta como suscriptor
assert chat_speech(cfg, dict(kick, text="[emote:1:LUL]"))[3] == "empty message"

favs = ["es-ES-ElviraNeural", "es-MX-DaliaNeural", "es-AR-TomasNeural"]
rnd = dict(cfg, favorites=favs, random_voices=True)
v1 = chat_speech(rnd, msg1("hola", login="luis", name="Luis"))[1]
assert v1 in favs and v1 == chat_speech(rnd, msg1("otra", login="luis", name="Luis"))[1]  # siempre la misma
assert len({chat_speech(rnd, msg1("x", login=f"u{i}", name=f"U{i}"))[1] for i in range(30)}) == 3  # se reparten
assert chat_speech(rnd, msg1("hola", login="pepe", name="Pepe"))[1] == "es-MX-JorgeNeural"  # la asignada manda
assert chat_speech(dict(rnd, favorites=[]), msg1("hola"))[1] == DEFAULTS["voice"]

assert chat_speech(dict(cfg, max_chars=5), msg1("abcdefghij"))[0] == "Ana Gamer dice: abcde"
assert http_speech(cfg, "hola", "pepe") == ("pepe dice: hola", "es-MX-JorgeNeural", None)
assert http_speech(cfg, "hola", voice="en-US-AvaNeural") == ("hola", "en-US-AvaNeural", None)
assert http_speech(cfg, "   ")[2] == "empty message"

# moderación: id del mensaje y usuario afectado
from stream_tts import (find_voice, message_id, mod_target, set_user_voice, spam_reason, voice_alias,
                        voice_command, word_marks)
assert message_id({"messageId": "abc"}) == "abc" and message_id({"message": {"msgId": "x1"}}) == "x1"
assert mod_target({"targetUser": {"login": "Troll", "name": "TROLL"}}) == "troll"
assert mod_target({"user": {"username": "KickTroll"}}) == "kicktroll" and mod_target({"username": "x"}) == "x"
assert mod_target({}) == ""

# anti-spam: mods (nivel 3) y streamer quedan fuera
spam = dict(cfg, user_cooldown=10, max_per_user=2)
assert spam_reason(spam, 0, None, 0) is None
assert spam_reason(spam, 0, 3.0, 0) == "cooldown" and spam_reason(spam, 0, 11.0, 0) is None
assert spam_reason(spam, 1, 11.0, 2) == "too many queued"
assert spam_reason(spam, 3, 1.0, 9) is None
assert spam_reason(dict(spam, user_cooldown=0, max_per_user=0), 0, 0.1, 99) is None

# comando para elegir voz
fav = ["es-MX-DaliaNeural", "en-US-AvaMultilingualNeural", "es-ES-AlvaroNeural"]
assert [voice_alias(v) for v in fav] == ["Dalia", "Ava", "Alvaro"]
assert find_voice(fav, "dalia") == fav[0] and find_voice(fav, "AL") == fav[2] and find_voice(fav, "x") is None
assert find_voice(fav, "en-us-avamultilingualneural") == fav[1]
assert voice_command(cfg, "!VOZ Dalia ") == "Dalia" and voice_command(cfg, "!voice") == ""
assert voice_command(cfg, "!vozz x") is None and voice_command(dict(cfg, voice_cmd_enabled=False), "!voz x") is None
assert set_user_voice("pepe=a\nana=b", "Ana", "c") == "pepe=a\nana=c"
assert set_user_voice("pepe=a\n@ana=b\n", "ana", None) == "pepe=a"

# overlay: dónde acaba cada palabra dicha dentro del texto
assert word_marks("Ana says: hola, ¿qué tal?", [(0, "Ana"), (300, "says"), (700, "hola"), (900, "qué"),
                                               (1100, "tal"), (1200, "nope")]) == \
    [[0, 3], [300, 8], [700, 14], [900, 20], [1100, 24]]

# traducción al español
stream_tts.LANG = "es"
assert chat_speech(cfg, msg1("!comando"))[3] == "comando"
assert chat_speech(dict(cfg, blocked_words="feo"), msg1("feo"))[3] == "palabra bloqueada 'feo'"
assert stream_tts.tr("Queued: {n}", n=3) == "En cola: 3"
stream_tts.LANG = "en"
assert stream_tts.tr("Queued: {n}", n=3) == "Queued: 3"

# las configuraciones antiguas (valores en español) se migran a los códigos nuevos
with tempfile.TemporaryDirectory() as d:
    stream_tts.CONFIG_PATH = Path(d) / "config.json"
    stream_tts.CONFIG_PATH.write_text(json.dumps({"min_role": "Suscriptores", "theme": "Oscuro",
                                                  "device": "Predeterminado del sistema", "boundary": "Ninguno",
                                                  "template": "{user} dice: {message}"}), encoding="utf-8")
    old = stream_tts.load_config()
    assert (old["min_role"], old["theme"], old["device"], old["boundary"]) == ("subs", "dark", "", "none")
    assert old["template"] == "{user} dice: {message}" and old["language"] == "en"
print("OK")
