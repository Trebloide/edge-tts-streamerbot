"""Lector TTS para Twitch y Kick con las voces de Microsoft Edge (edge-tts), conectado a Streamer.bot."""
import asyncio
import base64
import ctypes
import hashlib
import io
import itertools
import json
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
import zlib
from collections import deque
from pathlib import Path
from tkinter import filedialog, simpledialog, ttk

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import aiohttp
import edge_tts
import pygame
from aiohttp import web

try:  # icono en la bandeja del sistema (opcional)
    import pystray
    from PIL import Image
except ImportError:
    pystray = None

# Con el .exe de PyInstaller la configuración va junto al ejecutable y los recursos dentro del paquete
FROZEN = getattr(sys, "frozen", False)
APP_DIR = Path(sys.executable).parent if FROZEN else Path(__file__).resolve().parent
RES_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
CONFIG_PATH = APP_DIR / "config.json"
ICON_PATH = RES_DIR / "icon.ico"
OVERLAY_PATH = RES_DIR / "overlay.html"

# ---------------------------------------------------------------- idiomas

LANGUAGES = {"en": "English", "es": "Español"}
LANG = "en"  # idioma activo; los textos del código están en inglés y ES los traduce

ES = {
    # estado y registro
    "Disconnected": "Desconectado",
    "Connecting to {url}…": "Conectando a {url}…",
    "Connected ✔": "Conectado ✔",
    "Connected to Streamer.bot ({url})": "Conectado a Streamer.bot ({url})",
    "Disconnected · retrying in 5 s": "Desconectado · reintento en 5 s",
    "Streamer.bot closed the connection": "Streamer.bot cerró la conexión",
    "Invalid message from Streamer.bot: {err}": "Mensaje de Streamer.bot no válido: {err}",
    "Streamer.bot: response {status} at {url}. Is another program using that port (Steam often uses 8080)? "
    "Change the WebSocket Server port in Streamer.bot and here.":
        "Streamer.bot: respuesta {status} en {url}. ¿Otro programa usa ese puerto (Steam suele usar el 8080)? "
        "Cambia el puerto del WebSocket Server de Streamer.bot y aquí.",
    "Streamer.bot: {err}": "Streamer.bot: {err}",
    "Streamer.bot has authentication enabled: enter the password in the Connection tab.":
        "Streamer.bot tiene autenticación activada: pon la contraseña en la pestaña Conexión.",
    "Streamer.bot rejected '{id}': {err}": "Streamer.bot rechazó '{id}': {err}",
    "Ignored ({why}): {login}": "Ignorado ({why}): {login}",
    "Could not open output '{name}' ({err}). Using the default one.":
        "No se pudo abrir la salida '{name}' ({err}). Uso la predeterminada.",
    "No audio output: {err}": "Sin salida de audio: {err}",
    "Error reading with {voice}: {err}": "Error al leer con {voice}: {err}",
    "Queue full, dropped: {text}": "Cola llena, descartado: {text}",
    "Could not write {path}: {err}": "No se pudo escribir {path}: {err}",
    "HTTP off": "HTTP apagado",
    "HTTP at http://127.0.0.1:{port}": "HTTP en http://127.0.0.1:{port}",
    "HTTP error (port {port})": "HTTP error (puerto {port})",
    "Could not open HTTP port {port}: {err}": "No se pudo abrir el puerto HTTP {port}: {err}",
    "Could not save the settings: {err}": "No se pudo guardar la configuración: {err}",
    "Could not download the voice list: {err}": "No se pudo descargar la lista de voces: {err}",
    "{n} voices available": "{n} voces disponibles",
    "Main voice: {voice}": "Voz principal: {voice}",
    "Saved {path}": "Guardado {path}",
    " and .srt": " y .srt",
    "Could not save: {err}": "No se pudo guardar: {err}",
    "Ignored from now on: {users}": "Ignorados desde ahora: {users}",
    "Error: {err}": "Error: {err}",
    "Queued: {n}": "En cola: {n}",
    # moderación, anti-spam y comando de voz
    "Removed {n} message(s): {why}": "Quitados {n} mensaje(s): {why}",
    "message deleted by a moderator": "mensaje borrado por un moderador",
    "{user} was timed out or banned": "{user} ha recibido timeout o ban",
    "cooldown": "espera entre mensajes",
    "too many queued": "demasiados en cola",
    "@{user} there are no voices to choose from yet.": "@{user} todavía no hay voces para elegir.",
    "@{user} voices: {names}. Use {cmd} <name> ({cmd} off to reset).":
        "@{user} voces: {names}. Usa {cmd} <nombre> ({cmd} off para quitarla).",
    "@{user} unknown voice. Available: {names}": "@{user} no conozco esa voz. Disponibles: {names}",
    "default": "la predeterminada",
    "{user} chose the voice {voice}": "{user} ha elegido la voz {voice}",
    "@{user} your voice is now {voice}.": "@{user} ahora tu voz es {voice}.",
    "Streamer.bot did not send the chat reply. Replies need authentication: "
    "turn it on in Streamer.bot and enter the password in the Connection tab.":
        "Streamer.bot no ha enviado la respuesta al chat. Las respuestas necesitan autenticación: "
        "actívala en Streamer.bot y pon la contraseña en la pestaña Conexión.",
    "Seconds between messages per user": "Segundos entre mensajes por usuario",
    "0 = no limit · mods and broadcaster are exempt": "0 = sin límite · mods y streamer no cuentan",
    "Max queued messages per user": "Máx. mensajes en cola por usuario",
    "Viewers can choose their voice with": "Los viewers pueden elegir su voz con",
    "Reply in chat (needs the Streamer.bot password)": "Responder en el chat (necesita la contraseña de Streamer.bot)",
    "Only your favorite voices. Example: !voice dalia · !voice off": "Solo tus voces favoritas. Ejemplo: !voz dalia · !voz off",
    "OBS overlay": "Overlay de OBS",
    "Add it in OBS as a Browser source (for example 800×300). Optional URL parameters:\n"
    "size (font px), hold (seconds visible after reading).":
        "Añádelo en OBS como fuente de Navegador (por ejemplo 800×300). Parámetros opcionales en la URL:\n"
        "size (tamaño de letra en px), hold (segundos visible al terminar).",
    "Close to the system tray (keep reading in the background)":
        "Cerrar a la bandeja del sistema (sigue leyendo en segundo plano)",
    "Show window": "Mostrar ventana",
    "Pause / resume": "Pausar / reanudar",
    "Quit": "Salir",
    # motivos para ignorar
    "ignored user": "usuario ignorado",
    "role too low": "rol insuficiente",
    "no prefix": "sin prefijo",
    "command": "comando",
    "channel points/bits": "puntos del canal/bits",
    "blocked word '{w}'": "palabra bloqueada '{w}'",
    "empty message": "mensaje vacío",
    # valores
    "System default": "Predeterminado del sistema",
    "Everyone": "Todos",
    "Subscribers": "Suscriptores",
    "VIP": "VIP",
    "Moderators": "Moderadores",
    "Broadcaster only": "Solo streamer",
    "Dark": "Oscuro",
    "Light": "Claro",
    "Per sentence": "Por frase",
    "Per word": "Por palabra",
    "None": "Ninguno",
    "All": "Todos",
    "Female": "Mujer",
    "Male": "Hombre",
    # pestaña principal
    "Stream TTS · edge-tts + Streamer.bot (Twitch / Kick)": "Stream TTS · edge-tts + Streamer.bot (Twitch / Kick)",
    "Read Twitch chat": "Leer chat de Twitch",
    "Read Kick chat (Streamer.bot 1.0+)": "Leer chat de Kick (Streamer.bot 1.0+)",
    "Main": "Principal",
    "Connect": "Conectar",
    "Disconnect": "Desconectar",
    "Voice:": "Voz:",
    "drop-down = your favorites · all voices in the Voices tab":
        "desplegable = tus favoritas · todas en la pestaña Voces",
    "Sound": "Sonido",
    "Speed (%)": "Velocidad (%)",
    "Pitch (Hz)": "Tono (Hz)",
    "Voice gain (%)": "Ganancia voz (%)",
    "Volume": "Volumen",
    "Audio output": "Salida de audio",
    "Reset speed, pitch and gain": "Restablecer velocidad, tono y ganancia",
    "Test": "Prueba",
    "Hi chat, this is a test of the reader.": "Hola chat, esto es una prueba del lector.",
    "Speak": "Hablar",
    "💾 Save MP3…": "💾 Guardar MP3…",
    "⏸ Pause": "⏸ Pausar",
    "▶ Resume": "▶ Reanudar",
    "⏭ Skip": "⏭ Saltar",
    "🗑 Clear queue": "🗑 Vaciar cola",
    "📋 Show queue": "📋 Ver cola",
    "Read chat": "Leer chat",
    "Shortcuts: Ctrl+P pause · Ctrl+S skip · Ctrl+Q queue": "Atajos: Ctrl+P pausa · Ctrl+S saltar · Ctrl+Q cola",
    # pestaña voces
    "Voices": "Voces",
    "Search": "Buscar",
    "Language": "Idioma",
    "Gender": "Género",
    "Favorites only": "Solo favoritas",
    "Reload list": "Recargar lista",
    "Voice": "Voz",
    "Personality": "Personalidad",
    "Sample": "Muestra",
    "▶ Listen": "▶ Escuchar",
    "★ Favorite": "★ Favorita",
    "✔ Use this voice": "✔ Usar esta voz",
    "Assign to user…": "Asignar a usuario…",
    "Fixed random voice for each user (picked from your favorites)":
        "Voz aleatoria fija para cada usuario (elegida entre tus favoritas)",
    "Double-click/Enter: use · Space: listen · F: favorite": "Doble clic/Enter: usar · Espacio: escuchar · F: favorita",
    "Voice per user": "Voz por usuario",
    "User who will speak with {voice}:": "Usuario que hablará con {voice}:",
    # pestaña filtros
    "Filters and reading": "Filtros y lectura",
    "Format": "Formato",
    "{user} and {message}": "{user} y {message}",
    "Don't repeat the name when the same user writes again": "No repetir el nombre si escribe el mismo usuario seguido",
    "Required prefix": "Prefijo obligatorio",
    "empty = read everything; e.g. !tts": "vacío = leer todo; ej. !tts",
    "Ignore commands (messages starting with !)": "Ignorar comandos (mensajes que empiezan por !)",
    "Don't read channel points and bits from chat (the Streamer.bot actions read them)":
        "No leer del chat los canjes ni los bits (ya los leen las acciones)",
    "Who can use it": "Quién puede usarlo",
    "Remove emotes": "Quitar emotes",
    "Shorten repetitions (hahahahaha → hahaha)": "Acortar repeticiones (jajajajaja → jajaja)",
    "Read links as": "Leer enlaces como",
    "empty = don't read them": "vacío = no leerlos",
    "Max characters": "Máx. caracteres",
    "0 = no limit": "0 = sin límite",
    "Max queued messages": "Máx. mensajes en cola",
    "Ignored users (one per line)": "Usuarios ignorados (uno por línea)",
    "Blocked words (message is not read)": "Palabras bloqueadas (no lee el mensaje)",
    "Replacements (text=how to read it, also for names)": "Reemplazos (texto=cómo leerlo, vale para nombres)",
    "Voice per user (user=voice)": "Voz por usuario (usuario=voz)",
    # pestaña conexión
    "Connection": "Conexión",
    "Streamer.bot (Servers/Clients → WebSocket Server)": "Streamer.bot (Servers/Clients → WebSocket Server)",
    "Address": "Dirección",
    "Port": "Puerto",
    "same as in Streamer.bot": "el mismo que en Streamer.bot",
    "Endpoint": "Endpoint",
    "default /": "por defecto /",
    "Password": "Contraseña",
    "only if you enabled authentication": "solo si activaste autenticación",
    "Connect on startup": "Conectar al abrir",
    "Reconnect with these settings": "Reconectar con estos datos",
    "Local HTTP server (for Streamer.bot actions: Fetch URL)":
        "Servidor HTTP local (para acciones de Streamer.bot: Fetch URL)",
    "Enabled": "Activado",
    "Apply": "Aplicar",
    "Read text": "Leer texto",
    "Controls": "Controles",
    "/speak parameters: text (required), user (optional, uses the format), voice (optional).\n"
    "Example: !tts command or channel point redeem → Core › Network › Fetch URL sub-action with the URL above.\n"
    "The controls work with hotkeys or a Stream Deck. Only listens on 127.0.0.1 (this PC).":
        "Parámetros de /speak: text (obligatorio), user (opcional, usa el formato), voice (opcional).\n"
        "Ejemplo: comando !tts o canje de puntos → sub-acción Core › Network › Fetch URL con la URL de arriba.\n"
        "Los controles sirven para atajos de teclado o Stream Deck. Solo escucha en 127.0.0.1 (este PC).",
    # pestaña avanzado
    "Advanced": "Avanzado",
    "Application": "Aplicación",
    "Theme": "Tema",
    "Synthesize the next message while the current one plays (shorter wait between messages)":
        "Sintetizar el siguiente mensaje mientras suena el actual (menos espera entre mensajes)",
    "Show ignored messages in the log": "Mostrar mensajes ignorados en el registro",
    "Write the message being read to a text file (OBS text source)":
        "Escribir el mensaje que suena en un archivo de texto (fuente de texto en OBS)",
    "File": "Archivo",
    "Proxy": "Proxy",
    "e.g. http://127.0.0.1:3128 · empty = no proxy": "ej. http://127.0.0.1:3128 · vacío = sin proxy",
    "Connect timeout (s)": "Timeout conexión (s)",
    "Receive timeout (s)": "Timeout recepción (s)",
    "Subtitles when saving MP3": "Subtítulos al guardar MP3",
    "per sentence / per word (.srt next to the .mp3)": "por frase / por palabra (.srt junto al .mp3)",
    "Speed, pitch and voice gain are on the Main tab. The proxy is also used to download the voice list.":
        "Velocidad, tono y ganancia de la voz están en Principal. El proxy también se usa para descargar "
        "la lista de voces.",
    "Text": "Texto",
    # ventana de cola
    "Reading queue": "Cola de lectura",
    "Always on top": "Siempre visible",
    "User": "Usuario",
    "▶ now": "▶ ahora",
    "✖ Remove selected": "✖ Quitar seleccionados",
    "🚫 Ignore user": "🚫 Ignorar usuario",
    "⏭ Skip current": "⏭ Saltar actual",
    "Del removes the selection": "Supr quita la selección",
}


def tr(text, **kw):
    if LANG == "es":
        text = ES.get(text, text)
    return text.format(**kw) if kw else text


# Valores internos neutros (no dependen del idioma) y su texto en pantalla
ROLES = {"all": 0, "subs": 1, "vip": 2, "mods": 3, "broadcaster": 4}
ROLE_LABELS = {"all": "Everyone", "subs": "Subscribers", "vip": "VIP", "mods": "Moderators",
               "broadcaster": "Broadcaster only"}
THEME_LABELS = {"dark": "Dark", "light": "Light"}
BOUNDARY_LABELS = {"SentenceBoundary": "Per sentence", "WordBoundary": "Per word", "none": "None"}
# Configuraciones guardadas por versiones anteriores, que usaban los textos en español
LEGACY = {
    "min_role": {"Todos": "all", "Suscriptores": "subs", "VIP": "vip", "Moderadores": "mods",
                 "Solo streamer": "broadcaster"},
    "theme": {"Oscuro": "dark", "Claro": "light"},
    "device": {"Predeterminado del sistema": ""},
    "boundary": {"Ninguno": "none"},
}

DEFAULTS = {
    "language": "en",
    "voice": "en-US-EmmaMultilingualNeural",
    "favorites": [],
    "random_voices": False,
    "rate": 0,
    "pitch": 0,
    "tts_volume": 0,
    "volume": 80,
    "device": "",  # vacío = salida predeterminada del sistema
    "sample_text": "Hi chat, this is how I sound.",
    # Streamer.bot
    "sb_host": "127.0.0.1",
    "sb_port": 8800,
    "sb_endpoint": "/",
    "sb_password": "",
    "sb_autoconnect": True,
    "read_chat": True,
    "read_twitch": True,
    "read_kick": True,
    # Servidor HTTP para acciones de Streamer.bot (Fetch URL)
    "http_enabled": True,
    "http_port": 7979,
    # Filtros
    "template": "{user} says: {message}",
    "skip_repeat_name": True,
    "prefix": "",
    "skip_commands": True,
    "skip_rewards_bits": True,
    "min_role": "all",
    "remove_emotes": True,
    "link_text": "link",
    "collapse_repeats": True,
    "max_chars": 200,
    "max_queue": 20,
    "user_cooldown": 0,  # segundos entre mensajes del mismo usuario (0 = sin límite)
    "max_per_user": 3,  # mensajes de un mismo usuario esperando en la cola (0 = sin límite)
    "voice_cmd_enabled": True,
    "voice_command": "!voice !voz",
    "voice_cmd_reply": True,
    "ignored_users": "nightbot\nstreamelements\nstreamlabs\nmoobot\nwizebot\nsery_bot",
    "blocked_words": "",
    "replacements": "",
    "user_voices": "",
    # Avanzado (opciones de edge-tts y de la app)
    "theme": "dark",
    "proxy": "",
    "connect_timeout": 10,
    "receive_timeout": 30,
    "boundary": "SentenceBoundary",
    "prefetch": True,
    "log_ignored": True,
    "now_file_enabled": False,
    "now_file": str(APP_DIR / "now_reading.txt"),
    "close_to_tray": False,
    "geometry": "1000x740",
}

THEMES = {
    "dark": dict(bg="#1e1f22", panel="#2b2d31", field="#313338", border="#404249", fg="#e3e5e8",
                 muted="#949ba4", accent="#9146ff", accent_hi="#a970ff", select="#5c34a8", selfg="#ffffff",
                 hover="#3a3c42"),
    "light": dict(bg="#f2f3f5", panel="#e3e5e8", field="#ffffff", border="#c4c7cc", fg="#1e1f22",
                  muted="#5c5f66", accent="#9146ff", accent_hi="#a970ff", select="#dccbff", selfg="#1e1f22",
                  hover="#d4d7dc"),
}


def load_config():
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            # No pisar una configuración rota: se guarda aparte y se arranca con los valores por defecto.
            CONFIG_PATH.replace(CONFIG_PATH.with_suffix(".json.bak"))
    for key, old in LEGACY.items():
        cfg[key] = old.get(cfg[key], cfg[key])
    cfg["favorites"] = list(cfg["favorites"])  # copia: no modificar la lista de DEFAULTS
    return cfg


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def set_titlebar(win, dark):
    """Barra de título oscura/clara de Windows 10/11."""
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        v = ctypes.c_int(int(dark))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), ctypes.sizeof(v))
    except (AttributeError, OSError):
        pass


# ---------------------------------------------------------------- texto

URL_RE = re.compile(r"(https?://|www\.)\S+", re.I)
KICK_EMOTE_RE = re.compile(r"\[emote:\d+:[^\]]*\]")


def lines(s):
    return [l.strip() for l in s.splitlines() if l.strip()]


def pairs(s):
    out = {}
    for l in lines(s):
        if "=" in l:
            k, v = l.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


def word_re(w):
    return re.compile(r"(?<!\w)" + re.escape(w) + r"(?!\w)", re.I)


def parse_chat(data):
    """Devuelve (nombre, login, texto, rol, suscrito, emotes) de un evento ChatMessage de Twitch o Kick."""
    m = data.get("message")
    if isinstance(m, dict):  # Streamer.bot 0.2.x
        emotes = [e.get("name") or e.get("Name") for e in m.get("emotes") or []]
        return (m.get("displayName") or m.get("username") or "", m.get("username") or "",
                m.get("message") or "", m.get("role", 1), bool(m.get("subscriber")), emotes)
    u = data.get("user") or {}  # Streamer.bot 1.x (Twitch y Kick)
    emotes = [e.get("name") or e.get("Name") for e in data.get("emotes") or []]
    emotes += [p.get("text") for p in data.get("parts") or []  # Kick: emotes dentro de parts
               if isinstance(p, dict) and "emote" in str(p.get("type", "")).lower()]
    text = data.get("text") or (m if isinstance(m, str) else "")
    return (u.get("name") or u.get("login") or "", u.get("login") or "", text,
            u.get("role", 1), bool(u.get("subscribed") or u.get("isSubscribed")), emotes)


def is_reward_or_bits(data):
    """El mensaje de chat es el texto de un canje de puntos o lleva bits (ya lo leen las acciones de Streamer.bot)."""
    m = data.get("message")
    if isinstance(m, dict):  # Streamer.bot 0.2.x
        return bool(m.get("isCustomReward") or m.get("hasBits") or m.get("bits"))
    meta = data.get("meta") or {}
    return bool(meta.get("isCustomReward") or data.get("bits") or data.get("cheer") or any(
        isinstance(p, dict) and str(p.get("type", "")).lower() == "cheer" for p in data.get("parts") or []))


def user_level(role, subscribed):
    try:
        role = int(role)
    except (TypeError, ValueError):
        role = 1
    return max(role if role >= 2 else 0, 1 if subscribed else 0)


def clean_message(cfg, text, emotes=()):
    """Limpia el mensaje. Devuelve (texto, None) o (None, motivo)."""
    for w in lines(cfg["blocked_words"]):
        if word_re(w).search(text):
            return None, tr("blocked word '{w}'", w=w)
    text = KICK_EMOTE_RE.sub(" ", text)  # etiquetas crudas de Kick, nunca se pueden leer
    if cfg["remove_emotes"] and emotes:
        em = set(emotes)
        text = " ".join(w for w in text.split() if w not in em)
    text = URL_RE.sub(cfg["link_text"], text)
    if cfg["collapse_repeats"]:
        text = re.sub(r"(.{1,3}?)\1{3,}", r"\1\1\1", text)  # jajajajaja -> jajaja
    text = " ".join(text.split())
    if int(cfg["max_chars"]) > 0:
        text = text[: int(cfg["max_chars"])]
    if not re.search(r"\w", text):
        return None, tr("empty message")
    return text, None


def make_speech(cfg, user, text, same_user=False):
    tpl = "{message}" if not user or (same_user and cfg["skip_repeat_name"]) else cfg["template"]
    speech = tpl.replace("{user}", user.replace("_", " ")).replace("{message}", text)
    for k, v in pairs(cfg["replacements"]).items():
        speech = word_re(k).sub(lambda _m, v=v: v, speech)
    return speech


def voice_for(cfg, *names):
    """Voz de un usuario: la asignada a mano, una favorita fija al azar, o la principal."""
    voices = pairs(cfg["user_voices"])
    for n in names:
        if n and n.lower().lstrip("@") in voices:
            return voices[n.lower().lstrip("@")]
    favs = cfg["favorites"]
    if cfg["random_voices"] and favs and names and names[0]:
        return favs[zlib.crc32(names[0].lower().encode()) % len(favs)]  # crc32: misma voz en cada sesión
    return cfg["voice"]


def chat_speech(cfg, data, last_user=None):
    """Decide qué leer de un mensaje de chat. Devuelve (frase, voz, login, motivo_si_se_ignora)."""
    user, login, text, role, sub, emotes = parse_chat(data)
    ignored = {u.lower().lstrip("@") for u in lines(cfg["ignored_users"])}
    if login.lower() in ignored or user.lower() in ignored:
        return None, None, login, tr("ignored user")
    if cfg["skip_rewards_bits"] and is_reward_or_bits(data):
        return None, None, login, tr("channel points/bits")
    if user_level(role, sub) < ROLES.get(cfg["min_role"], 0):
        return None, None, login, tr("role too low")
    prefix = cfg["prefix"].strip()
    if prefix:
        if not text.lower().startswith(prefix.lower()):
            return None, None, login, tr("no prefix")
        text = text[len(prefix):]
    elif cfg["skip_commands"] and text.lstrip().startswith("!"):
        return None, None, login, tr("command")
    text, why = clean_message(cfg, text, emotes)
    if text is None:
        return None, None, login, why
    return make_speech(cfg, user, text, same_user=login == last_user), voice_for(cfg, login, user), login, None


def http_speech(cfg, text, user="", voice=None):
    """Igual que chat_speech para peticiones HTTP: sin filtros de rol, prefijo ni usuarios ignorados."""
    text, why = clean_message(cfg, text)
    if text is None:
        return None, None, why
    return make_speech(cfg, user, text), voice or voice_for(cfg, user), None


def message_id(data):
    m = data.get("message")
    if isinstance(m, dict):  # Streamer.bot 0.2.x
        return m.get("msgId") or m.get("id") or ""
    return data.get("messageId") or ""


def mod_target(data):
    """Login del usuario afectado por un timeout/ban. Kick no documenta el formato: se prueban varios campos."""
    for key in ("targetUser", "user", "bannedUser"):
        u = data.get(key)
        if isinstance(u, dict) and (u.get("login") or u.get("username") or u.get("name")):
            return (u.get("login") or u.get("username") or u.get("name")).lower()
    for key in ("userName", "username", "user_login", "user"):
        if isinstance(data.get(key), str) and data[key]:
            return data[key].lower()
    return ""


def spam_reason(cfg, level, since_last, queued):
    """Anti-spam por usuario (mods y streamer quedan fuera). since_last en segundos, None si es su primer mensaje."""
    if level >= ROLES["mods"]:
        return None
    cooldown = int(cfg["user_cooldown"])
    if cooldown > 0 and since_last is not None and since_last < cooldown:
        return tr("cooldown")
    if 0 < int(cfg["max_per_user"]) <= queued:
        return tr("too many queued")
    return None


def voice_alias(short_name):
    """Nombre corto para el chat: es-MX-DaliaNeural -> Dalia, en-US-AvaMultilingualNeural -> Ava."""
    name = short_name.split("-", 2)[-1]
    return re.sub(r"(Multilingual)?Neural$", "", name) or name


def find_voice(favorites, wanted):
    """Busca entre las favoritas por nombre corto, nombre completo o comienzo del nombre."""
    w = wanted.strip().lower()
    if not w:
        return None
    exact = [v for v in favorites if w in (v.lower(), voice_alias(v).lower())]
    prefix = [v for v in favorites if voice_alias(v).lower().startswith(w)]
    return (exact or prefix or [None])[0]


def voice_command(cfg, text):
    """Si el mensaje es el comando para elegir voz devuelve su argumento ('' si no lleva); si no, None."""
    if not cfg["voice_cmd_enabled"]:
        return None
    first, _, rest = text.strip().partition(" ")
    if first.lower() in cfg["voice_command"].replace(",", " ").lower().split():
        return rest.strip()
    return None


def set_user_voice(text, login, voice):
    """Cambia la línea del usuario en 'voz por usuario' (voice=None la quita)."""
    keep = [l for l in text.splitlines()
            if l.strip() and l.split("=", 1)[0].strip().lower().lstrip("@") != login.lower()]
    if voice:
        keep.append(f"{login.lower()}={voice}")
    return "\n".join(keep)


def word_marks(text, words):
    """Para cada palabra dicha (ms, palabra) busca dónde acaba en el texto: [[ms, fin], ...] para el overlay."""
    marks, pos, low = [], 0, text.lower()
    for ms, word in words:
        i = low.find(word.lower(), pos)
        if i >= 0:
            pos = i + len(word)
            marks.append([round(ms), pos])
    return marks


def b64sha(s):
    return base64.b64encode(hashlib.sha256(s.encode("utf-8")).digest()).decode()


# ---------------------------------------------------------------- motor (hilo asyncio)

class Engine:
    def __init__(self, cfg, emit):
        self.cfg, self.emit = cfg, emit  # emit(tipo, valor) se llama desde el hilo del motor
        self.paused = False
        self.last_user = None
        # mensajes en espera: {"id", "text", "voice", "user", "platform", "msg_id"}
        self.pending = deque()
        self.current = None
        self._ids = itertools.count(1)
        self._prefetch = {}  # id -> tarea de síntesis adelantada
        self._skip_id = None  # id del mensaje actual que hay que cortar aunque aún se esté sintetizando
        self._last_read = {}  # (plataforma, login) -> momento del último mensaje leído (anti-spam)
        self._sound = None
        self._sb_task = None
        self._ws = None
        self._reply_warned = False
        self._http_runner = None
        self._overlay_clients = set()
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.call(self._init()).result()

    def call(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def soon(self, fn, *args):
        self.loop.call_soon_threadsafe(fn, *args)

    def log(self, msg):
        self.emit("log", msg)

    async def _init(self):
        self._open_device(self.cfg["device"])
        self.loop.create_task(self._player())

    # --- audio
    def _open_device(self, name):
        pygame.mixer.quit()
        try:
            # buffer grande: el valor por defecto (512) se queda corto y la voz se entrecorta
            pygame.mixer.init(buffer=4096, devicename=name or None)
        except pygame.error as e:
            self.log(tr("Could not open output '{name}' ({err}). Using the default one.", name=name, err=e))
            try:
                pygame.mixer.init(buffer=4096)
            except pygame.error as e:
                self.log(tr("No audio output: {err}", err=e))

    async def list_devices(self):
        from pygame._sdl2 import audio
        return list(audio.get_audio_device_names(False)) if pygame.mixer.get_init() else []

    def set_device(self, name):
        self.soon(self._open_device, name)

    def set_volume(self, v):
        self.soon(lambda: self._sound and self._sound.set_volume(v / 100))

    def _stop_current(self):
        if self.current:
            self._skip_id = self.current["id"]
        if pygame.mixer.get_init():
            pygame.mixer.stop()

    def skip(self):
        self.soon(self._stop_current)

    def clear(self):
        def _clear():
            self.pending.clear()
            self._prune_prefetch()
            self._emit_queue()
            self._stop_current()
        self.soon(_clear)

    def remove(self, pred):
        """Quita de la cola los mensajes para los que pred(item) es verdadero."""
        def _remove():
            for item in [i for i in self.pending if pred(i)]:
                self.pending.remove(item)
            self._prune_prefetch()
            self._emit_queue()
        self.soon(_remove)

    def _drop(self, pred, why):
        """Moderación: quita de la cola lo que cumple pred y corta el mensaje actual si también lo cumple."""
        removed = [i for i in self.pending if pred(i)]
        for item in removed:
            self.pending.remove(item)
        now = bool(self.current and pred(self.current))
        if now:
            self._stop_current()
        if removed or now:
            self._prune_prefetch()
            self._emit_queue()
            self.log(tr("Removed {n} message(s): {why}", n=len(removed) + now, why=why))

    def _prune_prefetch(self):
        alive = {i["id"] for i in self.pending}
        for k in [k for k in self._prefetch if k not in alive]:
            self._prefetch.pop(k).cancel()

    def _emit_queue(self):
        self.emit("queue", (self.current, list(self.pending)))

    def set_paused(self, paused):
        def _set():
            self.paused = paused
            if pygame.mixer.get_init():
                (pygame.mixer.pause if paused else pygame.mixer.unpause)()
            self.emit("paused", paused)
            self._overlay({"type": "pause" if paused else "resume"})
        self.soon(_set)

    def _communicate(self, text, voice, boundary):
        c = self.cfg
        return edge_tts.Communicate(
            text, voice, rate=f"{int(c['rate']):+d}%", volume=f"{int(c['tts_volume']):+d}%",
            pitch=f"{int(c['pitch']):+d}Hz", boundary=boundary, proxy=c["proxy"].strip() or None,
            connect_timeout=int(c["connect_timeout"]), receive_timeout=int(c["receive_timeout"]))

    async def _synth(self, text, voice, boundary="WordBoundary", submaker=None):
        """Devuelve (audio mp3, [(ms, palabra), ...]); las palabras sirven para el overlay."""
        audio, words = [], []
        async for ch in self._communicate(text, voice, boundary).stream():
            if ch["type"] == "audio":
                audio.append(ch["data"])
            else:
                words.append((ch["offset"] / 10000, ch["text"]))  # offset en unidades de 100 ns
                if submaker is not None:
                    submaker.feed(ch)
        return b"".join(audio), words

    async def save(self, text, voice, mp3_path, subtitles):
        sub = edge_tts.SubMaker() if subtitles else None
        boundary = self.cfg["boundary"] if subtitles else "SentenceBoundary"
        audio, _ = await self._synth(text, voice, boundary, sub)
        Path(mp3_path).write_bytes(audio)
        if sub:
            Path(mp3_path).with_suffix(".srt").write_text(sub.get_srt(), encoding="utf-8")

    def _write_now(self, text):
        if self.cfg["now_file_enabled"] and self.cfg["now_file"]:
            try:
                Path(self.cfg["now_file"]).write_text(text, encoding="utf-8")
            except OSError as e:
                self.log(tr("Could not write {path}: {err}", path=self.cfg["now_file"], err=e))

    def _prefetch_next(self):
        if self.cfg["prefetch"] and self.pending and self.pending[0]["id"] not in self._prefetch:
            nxt = self.pending[0]
            self._prefetch[nxt["id"]] = self.loop.create_task(self._synth(nxt["text"], nxt["voice"]))

    async def _player(self):
        while True:
            while self.paused or not self.pending:
                await asyncio.sleep(0.05)
            self.current = item = self.pending.popleft()
            self._emit_queue()
            task = self._prefetch.pop(item["id"], None) or self.loop.create_task(
                self._synth(item["text"], item["voice"]))
            try:
                audio, words = await task
                if self._skip_id == item["id"]:  # saltado o moderado mientras se sintetizaba
                    continue
                # Se decodifica entero antes de sonar: así no hay cortes por decodificar en directo
                self._sound = pygame.mixer.Sound(io.BytesIO(audio))
                self._sound.set_volume(int(self.cfg["volume"]) / 100)
                channel = self._sound.play()
                self.log(f"▶ [{item['voice']}] {item['text']}")
                self._write_now(item["text"])
                self._overlay({"type": "start", "user": item["name"], "text": item["text"],
                               "marks": word_marks(item["text"], words)})
                while channel.get_busy() or self.paused:
                    self._prefetch_next()  # sintetiza el siguiente mientras suena este
                    await asyncio.sleep(0.05)
            except Exception as e:
                self.log(tr("Error reading with {voice}: {err}", voice=item["voice"], err=f"{type(e).__name__}: {e}"))
            finally:
                self.current = None
                self._write_now("")
                self._overlay({"type": "end"})
                self._emit_queue()

    def speak(self, text, voice=None, user=""):
        self.soon(self._enqueue, text, voice or self.cfg["voice"], user)

    def _enqueue(self, text, voice, user="", platform="", msg_id="", name=""):
        if len(self.pending) >= int(self.cfg["max_queue"]) > 0:
            self.log(tr("Queue full, dropped: {text}", text=text))
            return
        self.pending.append({"id": next(self._ids), "text": text, "voice": voice, "user": user,
                             "platform": platform, "msg_id": msg_id, "name": name or user})
        self._emit_queue()

    # --- overlay para OBS (fuente de navegador)
    def _overlay(self, msg):
        for ws in list(self._overlay_clients):
            self.loop.create_task(self._overlay_send(ws, msg))

    async def _overlay_send(self, ws, msg):
        try:
            await ws.send_json(msg)
        except Exception:
            self._overlay_clients.discard(ws)

    async def _h_overlay(self, req):
        return web.FileResponse(OVERLAY_PATH)

    async def _h_overlay_ws(self, req):
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(req)
        self._overlay_clients.add(ws)
        try:
            async for _ in ws:  # el overlay solo escucha
                pass
        finally:
            self._overlay_clients.discard(ws)
        return ws

    # --- Streamer.bot (WebSocket)
    def connect_sb(self, on=True):
        def _restart():
            if self._sb_task:
                self._sb_task.cancel()
            self._sb_task = self.loop.create_task(self._sb_loop()) if on else None
            if not on:
                self.emit("sb", tr("Disconnected"))
        self.soon(_restart)

    async def _sb_loop(self):
        c = self.cfg
        url = f"ws://{c['sb_host']}:{int(c['sb_port'])}/{c['sb_endpoint'].lstrip('/')}"
        while True:
            self.emit("sb", tr("Connecting to {url}…", url=url))
            try:
                async with aiohttp.ClientSession() as s, s.ws_connect(url, heartbeat=20) as ws:
                    await self._sb_handshake(ws)
                    # por separado: si Streamer.bot no conoce Kick (0.2.x), Twitch sigue funcionando
                    await ws.send_json({"request": "Subscribe", "id": "tts-sub", "events": {
                        "Twitch": ["ChatMessage", "ChatMessageDeleted", "UserTimedOut", "UserBanned"]}})
                    await ws.send_json({"request": "Subscribe", "id": "tts-sub-kick", "events": {
                        "Kick": ["ChatMessage", "UserTimedOut", "UserBanned"]}})
                    self._ws = ws
                    self.emit("sb", tr("Connected ✔"))
                    self.log(tr("Connected to Streamer.bot ({url})", url=url))
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                self._sb_message(json.loads(msg.data))
                            except Exception as e:
                                self.log(tr("Invalid message from Streamer.bot: {err}",
                                            err=f"{type(e).__name__}: {e}"))
                self.log(tr("Streamer.bot closed the connection"))
            except asyncio.CancelledError:
                raise
            except aiohttp.WSServerHandshakeError as e:
                self.log(tr("Streamer.bot: response {status} at {url}. Is another program using that port "
                            "(Steam often uses 8080)? Change the WebSocket Server port in Streamer.bot and here.",
                            status=e.status, url=url))
            except Exception as e:
                self.log(tr("Streamer.bot: {err}", err=f"{type(e).__name__}: {e}"))
            finally:
                self._ws = None
            self.emit("sb", tr("Disconnected · retrying in 5 s"))
            await asyncio.sleep(5)

    async def _sb_handshake(self, ws):
        try:
            hello = await ws.receive_json(timeout=5)
        except asyncio.TimeoutError:
            return  # versiones antiguas no mandan Hello
        auth = hello.get("authentication")
        if not auth:
            return
        if not self.cfg["sb_password"]:
            self.log(tr("Streamer.bot has authentication enabled: enter the password in the Connection tab."))
            return
        secret = b64sha(self.cfg["sb_password"] + auth["salt"])
        await ws.send_json({"request": "Authenticate", "id": "tts-auth",
                            "authentication": b64sha(secret + auth["challenge"])})

    def _reply(self, platform, message):
        """Responde en el chat (SendMessage de Streamer.bot, que exige contraseña)."""
        if self.cfg["voice_cmd_reply"] and self._ws is not None:
            self.loop.create_task(self._ws.send_json({"request": "SendMessage", "id": "tts-reply",
                                                      "platform": platform.lower(), "bot": False,
                                                      "internal": False, "message": message}))

    def _voice_cmd(self, platform, user, login, arg):
        favs = self.cfg["favorites"]
        names = ", ".join(voice_alias(v) for v in favs)
        cmd = self.cfg["voice_command"].replace(",", " ").split()[0]
        if not favs:
            self._reply(platform, tr("@{user} there are no voices to choose from yet.", user=user))
            return
        if not arg:
            self._reply(platform, tr("@{user} voices: {names}. Use {cmd} <name> ({cmd} off to reset).",
                                     user=user, names=names, cmd=cmd))
            return
        voice = None if arg.lower() in ("off", "reset", "default") else find_voice(favs, arg)
        if voice is None and arg.lower() not in ("off", "reset", "default"):
            self._reply(platform, tr("@{user} unknown voice. Available: {names}", user=user, names=names))
            return
        self.cfg["user_voices"] = set_user_voice(self.cfg["user_voices"], login, voice)
        self.emit("user_voices", self.cfg["user_voices"])
        shown = voice_alias(voice) if voice else tr("default")
        self.log(tr("{user} chose the voice {voice}", user=login, voice=voice or tr("default")))
        self._reply(platform, tr("@{user} your voice is now {voice}.", user=user, voice=shown))

    def _sb_message(self, d):
        if d.get("id") in ("tts-auth", "tts-sub", "tts-sub-kick", "tts-reply") and d.get("status") == "error":
            if d["id"] != "tts-reply":
                self.log(tr("Streamer.bot rejected '{id}': {err}", id=d["id"], err=d.get("error", d)))
            elif not self._reply_warned:
                self._reply_warned = True
                self.log(tr("Streamer.bot did not send the chat reply. Replies need authentication: "
                            "turn it on in Streamer.bot and enter the password in the Connection tab."))
        ev = d.get("event") or {}
        src, typ, data = ev.get("source"), ev.get("type"), d.get("data") or {}
        if src not in ("Twitch", "Kick"):
            return
        if typ == "ChatMessageDeleted":
            mid = data.get("messageId") or ""
            if mid:
                self._drop(lambda i: i["msg_id"] == mid, tr("message deleted by a moderator"))
        elif typ in ("UserTimedOut", "UserBanned"):
            target = mod_target(data)
            if target:
                self._drop(lambda i: i["platform"] == src and i["user"].lower() == target,
                           tr("{user} was timed out or banned", user=target))
        elif typ == "ChatMessage" and self.cfg["read_chat"] and self.cfg["read_" + src.lower()]:
            self._chat(src, data)

    def _chat(self, platform, data):
        user, login, text, role, sub, _ = parse_chat(data)
        arg = voice_command(self.cfg, text)
        if arg is not None:
            if login and login.lower() not in {u.lower().lstrip("@") for u in lines(self.cfg["ignored_users"])}:
                self._voice_cmd(platform, user, login, arg)
            return
        speech, voice, login, why = chat_speech(self.cfg, data, self.last_user)
        if speech is None:
            if self.cfg["log_ignored"]:
                self.log(tr("Ignored ({why}): {login}", why=why, login=login))
            return
        key, now = (platform, login.lower()), time.monotonic()
        last = self._last_read.get(key)
        queued = sum(1 for i in self.pending if i["platform"] == platform and i["user"].lower() == key[1])
        why = spam_reason(self.cfg, user_level(role, sub), None if last is None else now - last, queued)
        if why:
            if self.cfg["log_ignored"]:
                self.log(tr("Ignored ({why}): {login}", why=why, login=login))
            return
        self._last_read[key] = now
        self.last_user = login
        self._enqueue(speech, voice, login, platform, message_id(data), user)

    # --- servidor HTTP local para acciones de Streamer.bot
    def restart_http(self):
        self.soon(lambda: self.loop.create_task(self._restart_http()))

    async def _restart_http(self):
        if self._http_runner:
            await self._http_runner.cleanup()
            self._http_runner = None
        if not self.cfg["http_enabled"]:
            self.emit("http", tr("HTTP off"))
            return
        app = web.Application()
        app.router.add_route("*", "/speak", self._h_speak)
        app.router.add_get("/overlay", self._h_overlay)
        app.router.add_get("/overlay/ws", self._h_overlay_ws)
        for path, fn in (("/skip", self.skip), ("/clear", self.clear),
                         ("/pause", lambda: self.set_paused(True)), ("/resume", lambda: self.set_paused(False)),
                         ("/toggle", lambda: self.set_paused(not self.paused))):
            app.router.add_route("*", path, self._simple_handler(fn))
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(self.cfg["http_port"])
        try:
            await web.TCPSite(runner, "127.0.0.1", port).start()  # solo local
        except OSError as e:
            await runner.cleanup()
            self.log(tr("Could not open HTTP port {port}: {err}", port=port, err=e))
            self.emit("http", tr("HTTP error (port {port})", port=port))
            return
        self._http_runner = runner
        self.emit("http", tr("HTTP at http://127.0.0.1:{port}", port=port))

    @staticmethod
    def _simple_handler(fn):
        async def handler(req):
            fn()
            return web.Response(text="ok")
        return handler

    async def _h_speak(self, req):
        p = dict(req.query)
        if req.method == "POST":
            p.update(await req.post())
        user = p.get("user", "")
        speech, voice, why = http_speech(self.cfg, p.get("text", ""), user, p.get("voice"))
        if speech is None:
            return web.Response(text=f"ignored: {why}")
        self._enqueue(speech, voice, user)
        return web.Response(text="ok")


# ---------------------------------------------------------------- interfaz

class App:
    def __init__(self, root):
        global LANG
        self.root = root
        self.cfg = load_config()
        LANG = self.cfg["language"]
        self.events = queue.Queue()
        self.vars = {}
        self.voices = []
        self._save_job = None
        self.queue_win = None
        self.queue_state = (None, [])  # (leyendo ahora, pendientes)
        self.engine = Engine(self.cfg, lambda k, v: self.events.put((k, v)))

        root.withdraw()  # se muestra ya con el tema puesto, sin parpadeo blanco
        root.minsize(820, 580)
        try:
            root.geometry(self.cfg["geometry"])
        except tk.TclError:
            pass
        root.report_callback_exception = lambda *exc: self.log(tr("Error: {err}", err=repr(exc[1])))
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.sb_status = tk.StringVar(value=tr("Disconnected"))
        self.http_status = tk.StringVar(value="")
        self.queue_status = tk.StringVar()
        self.pause_text = tk.StringVar()
        self.url_speak, self.url_ctl, self.url_overlay = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.var("http_port").trace_add("write", self.update_urls)
        self.build()
        root.deiconify()
        self.tray = self._start_tray()

        root.bind_all("<Control-q>", lambda _: self.open_queue())
        root.bind_all("<Control-p>", lambda _: self.toggle_pause())
        root.bind_all("<Control-s>", lambda _: self.engine.skip())

        self.root.after(100, self._pump)
        self.reload_voices()
        self.engine.restart_http()
        if self.cfg["sb_autoconnect"]:
            self.engine.connect_sb(True)

    def build(self):
        """Crea (o vuelve a crear, al cambiar de idioma) todas las pestañas."""
        self.texts = {}
        self.root.title(tr("Stream TTS · edge-tts + Streamer.bot (Twitch / Kick)"))
        self.queue_status.set(tr("Queued: {n}", n=len(self.queue_state[1])))
        self.pause_text.set(tr("▶ Resume") if self.engine.paused else tr("⏸ Pause"))
        self.update_urls()
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)
        self._tab_main(self.nb)
        self._tab_voices(self.nb)
        self._tab_filters(self.nb)
        self._tab_connection(self.nb)
        self._tab_advanced(self.nb)
        self.apply_theme()
        self.refresh_devices()
        if self.voices:
            self._voices_loaded(quiet=True)

    def switch_language(self):
        global LANG
        LANG = self.cfg["language"]
        log = self.logbox.get("1.0", "end-1c")
        tab = self.nb.index("current")
        if self.queue_win and self.queue_win.winfo_exists():
            self.queue_win.destroy()
        self.nb.destroy()
        self.build()
        self.nb.select(tab)
        self.logbox.configure(state="normal")
        self.logbox.insert("1.0", log)
        self.logbox.configure(state="disabled")
        self.engine.restart_http()  # vuelve a mostrar el estado HTTP en el idioma nuevo

    # --- tema
    def apply_theme(self):
        p = THEMES.get(self.cfg["theme"], THEMES["dark"])
        s = ttk.Style(self.root)
        s.theme_use("clam")
        s.configure(".", background=p["bg"], foreground=p["fg"], fieldbackground=p["field"], bordercolor=p["border"],
                    lightcolor=p["bg"], darkcolor=p["bg"], troughcolor=p["field"], focuscolor=p["accent"],
                    selectbackground=p["select"], selectforeground=p["selfg"], insertcolor=p["fg"],
                    arrowcolor=p["fg"], font=("Segoe UI", 10))
        s.map(".", background=[("disabled", p["bg"])], foreground=[("disabled", p["muted"])])
        s.configure("TButton", background=p["panel"], padding=(10, 4), lightcolor=p["panel"], darkcolor=p["panel"])
        s.map("TButton", background=[("pressed", p["select"]), ("active", p["hover"])])
        s.configure("Accent.TButton", background=p["accent"], foreground="#ffffff",
                    lightcolor=p["accent"], darkcolor=p["accent"])
        s.map("Accent.TButton", background=[("pressed", p["select"]), ("active", p["accent_hi"])])
        s.configure("TNotebook", background=p["bg"], bordercolor=p["border"])
        s.configure("TNotebook.Tab", background=p["panel"], padding=(14, 6), bordercolor=p["border"],
                    lightcolor=p["panel"])
        s.map("TNotebook.Tab", background=[("selected", p["bg"]), ("active", p["hover"])],
              foreground=[("selected", p["accent_hi"])], lightcolor=[("selected", p["accent"])])
        s.configure("Treeview", background=p["field"], fieldbackground=p["field"], foreground=p["fg"],
                    rowheight=26, bordercolor=p["border"])
        s.map("Treeview", background=[("selected", p["select"])], foreground=[("selected", p["selfg"])])
        s.configure("Treeview.Heading", background=p["panel"], foreground=p["fg"], relief="flat",
                    lightcolor=p["panel"], darkcolor=p["panel"])
        s.map("Treeview.Heading", background=[("active", p["hover"])])
        s.configure("TCheckbutton", indicatorbackground=p["field"], indicatorforeground="#ffffff")
        s.map("TCheckbutton", indicatorbackground=[("selected", p["accent"])], background=[("active", p["bg"])])
        for w in ("TEntry", "TCombobox", "TSpinbox"):
            s.configure(w, fieldbackground=p["field"], background=p["panel"], foreground=p["fg"],
                        insertcolor=p["fg"], lightcolor=p["field"], darkcolor=p["field"])
            s.map(w, fieldbackground=[("readonly", p["field"])], foreground=[("readonly", p["fg"])],
                  bordercolor=[("focus", p["accent"])], lightcolor=[("focus", p["accent"])])
        s.map("TCombobox", selectbackground=[("readonly", p["field"])], selectforeground=[("readonly", p["fg"])])
        s.configure("TLabelframe", background=p["bg"], bordercolor=p["border"], lightcolor=p["bg"], darkcolor=p["bg"])
        s.configure("TLabelframe.Label", background=p["bg"], foreground=p["muted"])
        s.configure("Hint.TLabel", foreground=p["muted"])
        s.configure("Title.TLabel", font=("Segoe UI", 10, "bold"))
        s.configure("TScrollbar", background=p["panel"], troughcolor=p["bg"], bordercolor=p["bg"],
                    arrowcolor=p["muted"], lightcolor=p["panel"], darkcolor=p["panel"])
        s.map("TScrollbar", background=[("active", p["hover"])])
        s.configure("Horizontal.TScale", background=p["accent"], troughcolor=p["field"], bordercolor=p["border"],
                    lightcolor=p["accent"], darkcolor=p["accent"])
        s.map("Horizontal.TScale", background=[("active", p["accent_hi"])])
        # widgets clásicos de Tk (diálogos, listas desplegables, textos)
        for pat, val in (("*Background", p["bg"]), ("*Foreground", p["fg"]),
                         ("*TCombobox*Listbox.background", p["field"]), ("*TCombobox*Listbox.foreground", p["fg"]),
                         ("*TCombobox*Listbox.selectBackground", p["select"]),
                         ("*TCombobox*Listbox.selectForeground", p["selfg"])):
            self.root.option_add(pat, val)
        stack = [self.root]
        while stack:
            w = stack.pop()
            stack.extend(w.winfo_children())
            self._theme_widget(w, p)

    def _theme_widget(self, w, p):
        if isinstance(w, (tk.Tk, tk.Toplevel)):
            w.configure(bg=p["bg"])
            set_titlebar(w, self.cfg["theme"] == "dark")
        elif isinstance(w, tk.Text):
            w.configure(bg=p["field"], fg=p["fg"], insertbackground=p["fg"], selectbackground=p["select"],
                        selectforeground=p["selfg"], highlightthickness=1, highlightbackground=p["border"],
                        highlightcolor=p["accent"], relief="flat", bd=0)
        elif isinstance(w, ttk.Combobox):
            pd = w.tk.eval(f"ttk::combobox::PopdownWindow {w}")
            w.tk.call(f"{pd}.f.l", "configure", "-background", p["field"], "-foreground", p["fg"],
                      "-selectbackground", p["select"], "-selectforeground", p["selfg"])

    def switch_theme(self):
        self.apply_theme()
        for win in [self.root] + [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)]:
            win.withdraw()  # Windows solo repinta la barra de título al volver a mostrar la ventana
            win.deiconify()

    # --- helpers
    def var(self, key):
        if key in self.vars:
            return self.vars[key]
        cur = self.cfg[key]
        kind = tk.BooleanVar if isinstance(cur, bool) else tk.IntVar if isinstance(cur, int) else tk.StringVar
        v = kind(value=cur)

        def changed(*_):
            try:
                self.cfg[key] = v.get()
            except tk.TclError:
                return  # número a medio escribir
            self._changed(key)
        v.trace_add("write", changed)
        self.vars[key] = v
        return v

    def choice(self, parent, key, options, **kw):
        """Desplegable que muestra textos traducidos y guarda en la configuración el código interno."""
        labels = {code: tr(label) for code, label in options.items()}
        codes = {label: code for code, label in labels.items()}
        shown = tk.StringVar(value=labels.get(self.cfg[key], self.cfg[key]))
        cb = ttk.Combobox(parent, textvariable=shown, values=list(labels.values()), state="readonly", **kw)
        cb.bind("<<ComboboxSelected>>", lambda _: self.var(key).set(codes[shown.get()]))
        return cb

    def slider(self, parent, key, lo, hi):
        frame = ttk.Frame(parent)
        v = self.var(key)
        ttk.Scale(frame, from_=lo, to=hi, orient="horizontal", variable=v,
                  command=lambda val: v.set(round(float(val)))).pack(side="left", fill="x", expand=True)
        ttk.Label(frame, textvariable=v, width=5, anchor="e").pack(side="left")
        return frame

    def scroll_text(self, parent, height=5, **kw):
        frame = ttk.Frame(parent)
        t = tk.Text(frame, height=height, width=28, wrap="word", padx=6, pady=4, font=("Segoe UI", 9), **kw)
        sb = ttk.Scrollbar(frame, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=sb.set)
        t.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        return frame, t

    def text_box(self, parent, key, height=5):
        frame, t = self.scroll_text(parent, height)
        t.insert("1.0", self.cfg[key])
        t.edit_modified(False)

        def changed(_=None):
            if t.edit_modified():
                t.edit_modified(False)
                self.cfg[key] = t.get("1.0", "end-1c")
                self._changed(key)
        t.bind("<<Modified>>", changed)
        self.texts[key] = t
        return frame

    def _changed(self, key):
        if key == "volume":
            self.engine.set_volume(int(self.cfg["volume"]))
        elif key == "device":
            self.engine.set_device(self.cfg["device"])
        elif key == "theme":
            self.switch_theme()
        elif key == "language":
            self.root.after_idle(self.switch_language)  # fuera del evento del desplegable que se va a destruir
        self.schedule_save()

    def schedule_save(self):
        if self._save_job:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(800, self.save)

    def save(self):
        self._save_job = None
        try:
            save_config(self.cfg)
        except OSError as e:
            self.log(tr("Could not save the settings: {err}", err=e))

    def log(self, msg):
        self.logbox.configure(state="normal")
        self.logbox.insert("end", time.strftime("%H:%M:%S ") + msg + "\n")
        if int(self.logbox.index("end-1c").split(".")[0]) > 1000:
            self.logbox.delete("1.0", "200.0")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")

    def _pump(self):
        try:
            while True:
                kind, val = self.events.get_nowait()
                if kind == "log":
                    self.log(val)
                elif kind == "sb":
                    self.sb_status.set(val)
                elif kind == "http":
                    self.http_status.set(val)
                elif kind == "queue":
                    self.queue_state = val
                    self.queue_status.set(tr("Queued: {n}", n=len(val[1])))
                    self.fill_queue()
                elif kind == "paused":
                    self.pause_text.set(tr("▶ Resume") if val else tr("⏸ Pause"))
                elif kind == "voices":
                    self._voices_loaded()
                elif kind == "user_voices":  # un viewer eligió voz con el comando
                    t = self.texts["user_voices"]
                    t.delete("1.0", "end")
                    t.insert("1.0", val)
                elif kind == "tray":
                    self._tray_action(val)
        except queue.Empty:
            pass
        self.root.after(100, self._pump)

    def row(self, parent, r, label, widget, hint=""):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", padx=(0, 8), pady=3)
        widget.grid(row=r, column=1, sticky="we", pady=3)
        if hint:
            ttk.Label(parent, text=hint, style="Hint.TLabel").grid(row=r, column=2, sticky="w", padx=8)

    # --- pestaña principal
    def _tab_main(self, nb):
        f = ttk.Frame(nb, padding=10)
        nb.add(f, text=tr("Main"))

        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="Streamer.bot:", style="Title.TLabel").pack(side="left")
        ttk.Label(top, textvariable=self.sb_status).pack(side="left", padx=6)
        ttk.Button(top, text=tr("Connect"), command=lambda: self.engine.connect_sb(True)).pack(side="left", padx=2)
        ttk.Button(top, text=tr("Disconnect"), command=lambda: self.engine.connect_sb(False)).pack(side="left", padx=2)
        ttk.Label(top, textvariable=self.http_status, style="Hint.TLabel").pack(side="right")

        voice = ttk.Frame(f)
        voice.pack(fill="x", pady=(10, 0))
        ttk.Label(voice, text=tr("Voice:"), style="Title.TLabel").pack(side="left")
        self.fav_box = ttk.Combobox(voice, textvariable=self.var("voice"), width=34)
        self.fav_box.pack(side="left", padx=6)
        self.update_fav_box()
        ttk.Label(voice, text=tr("drop-down = your favorites · all voices in the Voices tab"),
                  style="Hint.TLabel").pack(side="left")

        snd = ttk.LabelFrame(f, text=tr("Sound"), padding=8)
        snd.pack(fill="x", pady=10)
        snd.columnconfigure(1, weight=1)
        for r, (key, label, lo, hi) in enumerate([("rate", "Speed (%)", -50, 100),
                                                  ("pitch", "Pitch (Hz)", -50, 50),
                                                  ("tts_volume", "Voice gain (%)", -50, 100),
                                                  ("volume", "Volume", 0, 100)]):
            self.row(snd, r, tr(label), self.slider(snd, key, lo, hi))
        dev = ttk.Frame(snd)
        self.device_shown = tk.StringVar(value=self.cfg["device"] or tr("System default"))
        self.device_box = ttk.Combobox(dev, textvariable=self.device_shown, state="readonly")
        self.device_box.bind("<<ComboboxSelected>>", lambda _: self.var("device").set(
            "" if self.device_box.current() == 0 else self.device_shown.get()))
        self.device_box.pack(side="left", fill="x", expand=True)
        ttk.Button(dev, text="↻", width=3, command=self.refresh_devices).pack(side="left", padx=4)
        self.row(snd, 4, tr("Audio output"), dev)
        ttk.Button(snd, text=tr("Reset speed, pitch and gain"),
                   command=lambda: [self.var(k).set(0) for k in ("rate", "pitch", "tts_volume")]
                   ).grid(row=5, column=1, sticky="w", pady=(4, 0))

        test = ttk.LabelFrame(f, text=tr("Test"), padding=8)
        test.pack(fill="x")
        self.test_text = tk.StringVar(value=tr("Hi chat, this is a test of the reader."))
        e = ttk.Entry(test, textvariable=self.test_text)
        e.pack(side="left", fill="x", expand=True)
        e.bind("<Return>", lambda _: self.engine.speak(self.test_text.get()))
        ttk.Button(test, text=tr("Speak"), style="Accent.TButton",
                   command=lambda: self.engine.speak(self.test_text.get())).pack(side="left", padx=4)
        ttk.Button(test, text=tr("💾 Save MP3…"), command=self.save_mp3).pack(side="left")

        ctl = ttk.Frame(f)
        ctl.pack(fill="x", pady=8)
        ttk.Button(ctl, textvariable=self.pause_text, command=self.toggle_pause).pack(side="left")
        ttk.Button(ctl, text=tr("⏭ Skip"), command=self.engine.skip).pack(side="left", padx=4)
        ttk.Button(ctl, text=tr("🗑 Clear queue"), command=self.engine.clear).pack(side="left")
        ttk.Button(ctl, text=tr("📋 Show queue"), command=self.open_queue).pack(side="left", padx=4)
        ttk.Checkbutton(ctl, text=tr("Read chat"), variable=self.var("read_chat")).pack(side="left", padx=12)
        ttk.Label(ctl, textvariable=self.queue_status).pack(side="right")

        frame, self.logbox = self.scroll_text(f, height=8, state="disabled")
        self.logbox.configure(font=("Consolas", 9))
        frame.pack(fill="both", expand=True)
        ttk.Label(f, text=tr("Shortcuts: Ctrl+P pause · Ctrl+S skip · Ctrl+Q queue"),
                  style="Hint.TLabel").pack(anchor="w")

    def toggle_pause(self):
        self.engine.set_paused(not self.engine.paused)

    def refresh_devices(self):
        names = self.engine.call(self.engine.list_devices()).result(timeout=5)
        self.device_box["values"] = [tr("System default")] + names

    def save_mp3(self):
        path = filedialog.asksaveasfilename(parent=self.root, defaultextension=".mp3",
                                            filetypes=[("MP3", "*.mp3")], initialfile="tts.mp3")
        if not path:
            return
        subs = self.cfg["boundary"] != "none"

        def done(fut):
            err = fut.exception()
            self.events.put(("log", tr("Could not save: {err}", err=err) if err else
                             tr("Saved {path}", path=path) + (tr(" and .srt") if subs else "")))
        self.engine.call(self.engine.save(self.test_text.get(), self.cfg["voice"], path, subs)).add_done_callback(done)

    # --- pestaña voces
    def _tab_voices(self, nb):
        f = ttk.Frame(nb, padding=10)
        nb.add(f, text=tr("Voices"))

        flt = ttk.Frame(f)
        flt.pack(fill="x")
        self.search = tk.StringVar()
        self.lang = tk.StringVar(value=self.cfg["voice"].split("-")[0])
        self.gender = tk.StringVar(value=tr("All"))
        self.only_favs = tk.BooleanVar(value=False)
        ttk.Label(flt, text=tr("Search")).pack(side="left")
        ttk.Entry(flt, textvariable=self.search, width=22).pack(side="left", padx=(4, 12))
        ttk.Label(flt, text=tr("Language")).pack(side="left")
        self.lang_box = ttk.Combobox(flt, textvariable=self.lang, width=8, state="readonly")
        self.lang_box.pack(side="left", padx=(4, 12))
        ttk.Label(flt, text=tr("Gender")).pack(side="left")
        ttk.Combobox(flt, textvariable=self.gender, width=8, state="readonly",
                     values=[tr("All"), tr("Female"), tr("Male")]).pack(side="left", padx=4)
        ttk.Checkbutton(flt, text=tr("Favorites only"), variable=self.only_favs).pack(side="left", padx=12)
        ttk.Button(flt, text=tr("Reload list"), command=self.reload_voices).pack(side="right")
        for v in (self.search, self.lang, self.gender, self.only_favs):
            v.trace_add("write", lambda *_: self.fill_voices())

        cols = ("voz", "idioma", "genero", "estilo")
        tf = ttk.Frame(f)
        tf.pack(fill="both", expand=True, pady=8)
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        for c, title, w in zip(cols, ("Voice", "Language", "Gender", "Personality"), (300, 90, 80, 260)):
            self.tree.heading(c, text=tr(title))
            self.tree.column(c, width=w, stretch=c in ("voz", "estilo"))
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.tree.bind("<Double-1>", lambda _: self.use_voice())
        self.tree.bind("<Return>", lambda _: self.use_voice())
        self.tree.bind("<space>", lambda _: self.preview_voice())
        self.tree.bind("f", lambda _: self.toggle_favorite())

        bot = ttk.Frame(f)
        bot.pack(fill="x")
        ttk.Label(bot, text=tr("Sample")).pack(side="left")
        ttk.Entry(bot, textvariable=self.var("sample_text")).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(bot, text=tr("▶ Listen"), command=self.preview_voice).pack(side="left", padx=2)
        ttk.Button(bot, text=tr("★ Favorite"), command=self.toggle_favorite).pack(side="left", padx=2)
        ttk.Button(bot, text=tr("✔ Use this voice"), style="Accent.TButton",
                   command=self.use_voice).pack(side="left", padx=2)
        ttk.Button(bot, text=tr("Assign to user…"), command=self.assign_voice).pack(side="left", padx=2)

        opts = ttk.Frame(f)
        opts.pack(fill="x", pady=(6, 0))
        ttk.Checkbutton(opts, text=tr("Fixed random voice for each user (picked from your favorites)"),
                        variable=self.var("random_voices")).pack(side="left")
        ttk.Label(opts, text=tr("Double-click/Enter: use · Space: listen · F: favorite"),
                  style="Hint.TLabel").pack(side="right")

        cmd = ttk.Frame(f)
        cmd.pack(fill="x", pady=(6, 0))
        ttk.Checkbutton(cmd, text=tr("Viewers can choose their voice with"),
                        variable=self.var("voice_cmd_enabled")).pack(side="left")
        ttk.Entry(cmd, textvariable=self.var("voice_command"), width=14).pack(side="left", padx=4)
        ttk.Checkbutton(cmd, text=tr("Reply in chat (needs the Streamer.bot password)"),
                        variable=self.var("voice_cmd_reply")).pack(side="left", padx=8)
        ttk.Label(f, text=tr("Only your favorite voices. Example: !voice dalia · !voice off"),
                  style="Hint.TLabel").pack(anchor="w")

    def reload_voices(self):
        def done(fut):
            try:
                self.voices = sorted(fut.result(), key=lambda v: v["ShortName"])
            except Exception as e:
                self.events.put(("log", tr("Could not download the voice list: {err}", err=e)))
                return
            self.events.put(("voices", None))  # Tk solo se toca desde su hilo
        proxy = self.cfg["proxy"].strip() or None
        self.engine.call(edge_tts.list_voices(proxy=proxy)).add_done_callback(done)

    def _voices_loaded(self, quiet=False):
        self.lang_box["values"] = [tr("All")] + sorted({v["Locale"].split("-")[0] for v in self.voices})
        self.fill_voices()
        if not quiet:
            self.log(tr("{n} voices available", n=len(self.voices)))

    def fill_voices(self):
        self.tree.delete(*self.tree.get_children())
        q, lang, gender = self.search.get().lower(), self.lang.get(), self.gender.get()
        favs = set(self.cfg["favorites"])
        for v in self.voices:
            name = v["ShortName"]
            g = tr(v["Gender"])
            if self.only_favs.get():
                if name not in favs:
                    continue
            elif lang != tr("All") and not v["Locale"].startswith(lang + "-"):
                continue
            if gender != tr("All") and g != gender:
                continue
            if q and q not in name.lower() and q not in v.get("FriendlyName", "").lower():
                continue
            style = ", ".join(v.get("VoiceTag", {}).get("VoicePersonalities", []))
            label = ("★ " if name in favs else "    ") + name
            self.tree.insert("", "end", iid=name, values=(label, v["Locale"], g, style))
        if self.tree.exists(self.cfg["voice"]):
            self.tree.selection_set(self.cfg["voice"])
            self.tree.see(self.cfg["voice"])

    def selected_voice(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def preview_voice(self):
        if v := self.selected_voice():
            self.engine.speak(self.cfg["sample_text"], v)

    def use_voice(self):
        if v := self.selected_voice():
            self.var("voice").set(v)
            self.log(tr("Main voice: {voice}", voice=v))

    def toggle_favorite(self):
        v = self.selected_voice()
        if not v:
            return
        favs = self.cfg["favorites"]
        if v in favs:
            favs.remove(v)
        else:
            favs.append(v)
            favs.sort()
        self.fill_voices()
        if self.tree.exists(v):
            self.tree.selection_set(v)
            self.tree.focus(v)
        self.update_fav_box()
        self.schedule_save()

    def update_fav_box(self):
        self.fav_box["values"] = self.cfg["favorites"] or [self.cfg["voice"]]

    def assign_voice(self):
        v = self.selected_voice()
        if not v:
            return
        user = simpledialog.askstring(tr("Voice per user"), tr("User who will speak with {voice}:", voice=v),
                                      parent=self.root)
        if user and user.strip():
            t = self.texts["user_voices"]
            current = t.get("1.0", "end-1c").rstrip()
            t.delete("1.0", "end")
            t.insert("1.0", (current + "\n" if current else "") + f"{user.strip().lstrip('@').lower()}={v}")

    # --- pestaña filtros
    def _tab_filters(self, nb):
        f = ttk.Frame(nb, padding=10)
        nb.add(f, text=tr("Filters and reading"))
        g = ttk.Frame(f)
        g.pack(fill="x")
        g.columnconfigure(1, weight=1)
        self.row(g, 0, tr("Format"), ttk.Entry(g, textvariable=self.var("template")), tr("{user} and {message}"))
        self.row(g, 1, "", ttk.Checkbutton(g, text=tr("Don't repeat the name when the same user writes again"),
                                           variable=self.var("skip_repeat_name")))
        self.row(g, 2, tr("Required prefix"), ttk.Entry(g, textvariable=self.var("prefix")),
                 tr("empty = read everything; e.g. !tts"))
        self.row(g, 3, "", ttk.Checkbutton(g, text=tr("Ignore commands (messages starting with !)"),
                                           variable=self.var("skip_commands")))
        self.row(g, 4, "", ttk.Checkbutton(g, text=tr(
            "Don't read channel points and bits from chat (the Streamer.bot actions read them)"),
            variable=self.var("skip_rewards_bits")))
        self.row(g, 5, tr("Who can use it"), self.choice(g, "min_role", ROLE_LABELS))
        self.row(g, 6, "", ttk.Checkbutton(g, text=tr("Remove emotes"), variable=self.var("remove_emotes")))
        self.row(g, 7, "", ttk.Checkbutton(g, text=tr("Shorten repetitions (hahahahaha → hahaha)"),
                                           variable=self.var("collapse_repeats")))
        self.row(g, 8, tr("Read links as"), ttk.Entry(g, textvariable=self.var("link_text")),
                 tr("empty = don't read them"))
        self.row(g, 9, tr("Max characters"),
                 ttk.Spinbox(g, from_=0, to=2000, textvariable=self.var("max_chars")), tr("0 = no limit"))
        self.row(g, 10, tr("Max queued messages"),
                 ttk.Spinbox(g, from_=0, to=500, textvariable=self.var("max_queue")), tr("0 = no limit"))
        self.row(g, 11, tr("Seconds between messages per user"),
                 ttk.Spinbox(g, from_=0, to=600, textvariable=self.var("user_cooldown")),
                 tr("0 = no limit · mods and broadcaster are exempt"))
        self.row(g, 12, tr("Max queued messages per user"),
                 ttk.Spinbox(g, from_=0, to=50, textvariable=self.var("max_per_user")),
                 tr("0 = no limit · mods and broadcaster are exempt"))

        boxes = ttk.Frame(f)
        boxes.pack(fill="both", expand=True, pady=(10, 0))
        for i, (key, title) in enumerate([("ignored_users", "Ignored users (one per line)"),
                                          ("blocked_words", "Blocked words (message is not read)"),
                                          ("replacements", "Replacements (text=how to read it, also for names)"),
                                          ("user_voices", "Voice per user (user=voice)")]):
            lf = ttk.LabelFrame(boxes, text=tr(title), padding=4)
            lf.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)
            self.text_box(lf, key).pack(fill="both", expand=True)
            boxes.columnconfigure(i % 2, weight=1)
            boxes.rowconfigure(i // 2, weight=1)

    # --- pestaña conexión
    def _tab_connection(self, nb):
        f = ttk.Frame(nb, padding=10)
        nb.add(f, text=tr("Connection"))

        sb = ttk.LabelFrame(f, text=tr("Streamer.bot (Servers/Clients → WebSocket Server)"), padding=8)
        sb.pack(fill="x")
        sb.columnconfigure(1, weight=1)
        self.row(sb, 0, tr("Address"), ttk.Entry(sb, textvariable=self.var("sb_host")))
        self.row(sb, 1, tr("Port"), ttk.Entry(sb, textvariable=self.var("sb_port"), width=8),
                 tr("same as in Streamer.bot"))
        self.row(sb, 2, tr("Endpoint"), ttk.Entry(sb, textvariable=self.var("sb_endpoint")), tr("default /"))
        self.row(sb, 3, tr("Password"), ttk.Entry(sb, textvariable=self.var("sb_password"), show="•"),
                 tr("only if you enabled authentication"))
        self.row(sb, 4, "", ttk.Checkbutton(sb, text=tr("Connect on startup"), variable=self.var("sb_autoconnect")))
        self.row(sb, 5, "", ttk.Checkbutton(sb, text=tr("Read Twitch chat"), variable=self.var("read_twitch")))
        self.row(sb, 6, "", ttk.Checkbutton(sb, text=tr("Read Kick chat (Streamer.bot 1.0+)"),
                                            variable=self.var("read_kick")))
        self.row(sb, 7, "", ttk.Button(sb, text=tr("Reconnect with these settings"),
                                       command=lambda: self.engine.connect_sb(True)))

        http = ttk.LabelFrame(f, text=tr("Local HTTP server (for Streamer.bot actions: Fetch URL)"), padding=8)
        http.pack(fill="x", pady=10)
        http.columnconfigure(1, weight=1)
        self.row(http, 0, "", ttk.Checkbutton(http, text=tr("Enabled"), variable=self.var("http_enabled")))
        self.row(http, 1, tr("Port"), ttk.Entry(http, textvariable=self.var("http_port"), width=8))
        self.row(http, 2, "", ttk.Button(http, text=tr("Apply"), command=self.engine.restart_http))
        self.row(http, 3, tr("Read text"), ttk.Entry(http, textvariable=self.url_speak, state="readonly"))
        self.row(http, 4, tr("Controls"), ttk.Entry(http, textvariable=self.url_ctl, state="readonly"))
        ttk.Label(http, style="Hint.TLabel", justify="left", text=tr(
            "/speak parameters: text (required), user (optional, uses the format), voice (optional).\n"
            "Example: !tts command or channel point redeem → Core › Network › Fetch URL sub-action with the URL above.\n"
            "The controls work with hotkeys or a Stream Deck. Only listens on 127.0.0.1 (this PC).")
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(6, 0))

        ov = ttk.LabelFrame(f, text=tr("OBS overlay"), padding=8)
        ov.pack(fill="x")
        ov.columnconfigure(1, weight=1)
        self.row(ov, 0, "URL", ttk.Entry(ov, textvariable=self.url_overlay, state="readonly"))
        ttk.Label(ov, style="Hint.TLabel", justify="left", text=tr(
            "Add it in OBS as a Browser source (for example 800×300). Optional URL parameters:\n"
            "size (font px), hold (seconds visible after reading).")
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))

    def update_urls(self, *_):
        base = f"http://127.0.0.1:{self.cfg['http_port']}"
        self.url_speak.set(f"{base}/speak?user=%user%&text=%rawInputUrlEncoded%")
        self.url_ctl.set(f"{base}/skip  ·  /clear  ·  /pause  ·  /resume  ·  /toggle")
        self.url_overlay.set(f"{base}/overlay")

    # --- pestaña avanzado
    def _tab_advanced(self, nb):
        f = ttk.Frame(nb, padding=10)
        nb.add(f, text=tr("Advanced"))

        app = ttk.LabelFrame(f, text=tr("Application"), padding=8)
        app.pack(fill="x")
        app.columnconfigure(1, weight=1)
        self.row(app, 0, "Language / Idioma", self.choice(app, "language", LANGUAGES, width=12))
        self.row(app, 1, tr("Theme"), self.choice(app, "theme", THEME_LABELS, width=12))
        self.row(app, 2, "", ttk.Checkbutton(app, text=tr(
            "Synthesize the next message while the current one plays (shorter wait between messages)"),
            variable=self.var("prefetch")))
        self.row(app, 3, "", ttk.Checkbutton(app, text=tr("Show ignored messages in the log"),
                                             variable=self.var("log_ignored")))
        self.row(app, 4, "", ttk.Checkbutton(app, text=tr(
            "Write the message being read to a text file (OBS text source)"), variable=self.var("now_file_enabled")))
        nf = ttk.Frame(app)
        ttk.Entry(nf, textvariable=self.var("now_file")).pack(side="left", fill="x", expand=True)
        ttk.Button(nf, text="…", width=3, command=self.pick_now_file).pack(side="left", padx=4)
        self.row(app, 5, tr("File"), nf)
        if pystray:
            self.row(app, 6, "", ttk.Checkbutton(app, text=tr(
                "Close to the system tray (keep reading in the background)"), variable=self.var("close_to_tray")))

        tts = ttk.LabelFrame(f, text="edge-tts", padding=8)
        tts.pack(fill="x", pady=10)
        tts.columnconfigure(1, weight=1)
        self.row(tts, 0, tr("Proxy"), ttk.Entry(tts, textvariable=self.var("proxy")),
                 tr("e.g. http://127.0.0.1:3128 · empty = no proxy"))
        self.row(tts, 1, tr("Connect timeout (s)"),
                 ttk.Spinbox(tts, from_=1, to=120, textvariable=self.var("connect_timeout"), width=6))
        self.row(tts, 2, tr("Receive timeout (s)"),
                 ttk.Spinbox(tts, from_=1, to=300, textvariable=self.var("receive_timeout"), width=6))
        self.row(tts, 3, tr("Subtitles when saving MP3"), self.choice(tts, "boundary", BOUNDARY_LABELS, width=18),
                 tr("per sentence / per word (.srt next to the .mp3)"))
        ttk.Label(tts, style="Hint.TLabel", justify="left", text=tr(
            "Speed, pitch and voice gain are on the Main tab. The proxy is also used to download the voice list.")
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))

    def pick_now_file(self):
        path = filedialog.asksaveasfilename(parent=self.root, defaultextension=".txt",
                                            filetypes=[("Text", "*.txt")], initialfile="now_reading.txt")
        if path:
            self.var("now_file").set(path)

    # --- ventana de cola
    def open_queue(self):
        if self.queue_win and self.queue_win.winfo_exists():
            self.queue_win.deiconify()
            self.queue_win.lift()
            return
        w = self.queue_win = tk.Toplevel(self.root)
        w.title(tr("Reading queue"))
        w.geometry("720x380")
        f = ttk.Frame(w, padding=8)
        f.pack(fill="both", expand=True)

        top = ttk.Frame(f)
        top.pack(fill="x")
        on_top = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text=tr("Always on top"), variable=on_top,
                        command=lambda: w.attributes("-topmost", on_top.get())).pack(side="left")
        ttk.Button(top, textvariable=self.pause_text, command=self.toggle_pause).pack(side="left", padx=12)
        ttk.Label(top, textvariable=self.queue_status).pack(side="right")

        tf = ttk.Frame(f)
        tf.pack(fill="both", expand=True, pady=6)
        cols = (("n", "#", 70), ("user", tr("User"), 120), ("voz", tr("Voice"), 170), ("texto", tr("Text"), 340))
        self.queue_tree = ttk.Treeview(tf, columns=[c[0] for c in cols], show="headings", selectmode="extended")
        for c, title, width in cols:
            self.queue_tree.heading(c, text=title)
            self.queue_tree.column(c, width=width, stretch=c == "texto")
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=sb.set)
        self.queue_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.queue_tree.bind("<Delete>", lambda _: self.remove_selected())

        bot = ttk.Frame(f)
        bot.pack(fill="x")
        ttk.Button(bot, text=tr("✖ Remove selected"), command=self.remove_selected).pack(side="left")
        ttk.Button(bot, text=tr("🚫 Ignore user"), command=self.ignore_selected_users).pack(side="left", padx=4)
        ttk.Button(bot, text=tr("⏭ Skip current"), command=self.engine.skip).pack(side="left")
        ttk.Button(bot, text=tr("🗑 Clear queue"), command=self.engine.clear).pack(side="left", padx=4)
        ttk.Label(bot, text=tr("Del removes the selection"), style="Hint.TLabel").pack(side="right")
        self.apply_theme()
        self.fill_queue()

    def fill_queue(self):
        if not (self.queue_win and self.queue_win.winfo_exists()):
            return
        t = self.queue_tree
        selected = set(t.selection())
        t.delete(*t.get_children())
        current, pending = self.queue_state
        if current:
            t.insert("", "end", iid="now", values=(tr("▶ now"), current["user"], current["voice"], current["text"]))
        for n, item in enumerate(pending, 1):
            t.insert("", "end", iid=str(item["id"]), values=(n, item["user"], item["voice"], item["text"]))
        t.selection_set([i for i in selected if t.exists(i)])

    def remove_selected(self):
        sel = self.queue_tree.selection()
        if "now" in sel:
            self.engine.skip()
        ids = {int(i) for i in sel if i != "now"}
        self.engine.remove(lambda item: item["id"] in ids)

    def ignore_selected_users(self):
        users = {str(self.queue_tree.set(i, "user")).lower() for i in self.queue_tree.selection()} - {""}
        if not users:
            return
        t = self.texts["ignored_users"]
        known = {u.lower() for u in lines(t.get("1.0", "end-1c"))}
        new = sorted(users - known)
        if new:
            t.insert("end", ("\n" if t.get("1.0", "end-1c").strip() else "") + "\n".join(new))
        if "now" in self.queue_tree.selection():
            self.engine.skip()
        self.engine.remove(lambda item: item["user"].lower() in users)
        self.log(tr("Ignored from now on: {users}", users=", ".join(sorted(users))))

    # --- bandeja del sistema
    def _start_tray(self):
        if not pystray or not ICON_PATH.exists():
            return None

        def send(action):  # pystray llama desde su propio hilo: Tk solo se toca desde _pump
            return lambda *_: self.events.put(("tray", action))
        menu = pystray.Menu(pystray.MenuItem(tr("Show window"), send("show"), default=True),
                            pystray.MenuItem(tr("Pause / resume"), send("pause")),
                            pystray.MenuItem(tr("⏭ Skip"), send("skip")),
                            pystray.MenuItem(tr("🗑 Clear queue"), send("clear")),
                            pystray.MenuItem(tr("Quit"), send("quit")))
        try:
            icon = pystray.Icon("stream_tts", Image.open(ICON_PATH), "Stream TTS", menu)
            icon.run_detached()
            return icon
        except Exception as e:
            self.log(tr("Error: {err}", err=e))
            return None

    def _tray_action(self, action):
        if action == "show":
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        elif action == "pause":
            self.toggle_pause()
        elif action == "skip":
            self.engine.skip()
        elif action == "clear":
            self.engine.clear()
        elif action == "quit":
            self.quit()

    def close(self):
        if self.tray and self.cfg["close_to_tray"]:
            self.cfg["geometry"] = self.root.geometry()
            self.save()
            self.root.withdraw()
        else:
            self.quit()

    def quit(self):
        if self.root.state() != "withdrawn":
            self.cfg["geometry"] = self.root.geometry()
        self.save()
        if self.tray:
            self.tray.stop()
        self.root.destroy()


def main():
    try:  # texto nítido en pantallas con escalado
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        # ID propio: la barra de tareas muestra nuestro icono y no el de Python
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("stream.tts.edge")
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    if ICON_PATH.exists():
        root.iconbitmap(default=str(ICON_PATH))  # default: también para la ventana de cola y diálogos
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
