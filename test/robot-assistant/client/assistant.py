"""
@file assistant.py
@brief Asistente conversacional con voz, LLM, memoria y conexión a API gateway.
"""

# =========================================================
# IMPORTS
# =========================================================

import os
import json
import time
import queue
import threading
import logging
import requests
import socket
import re
import subprocess
from datetime import datetime
from bs4 import BeautifulSoup

import sounddevice as sd
import vosk

# =========================================================
# CONFIG
# =========================================================

config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# 🔥 IMPORTANTE: ahora SOLO hablas con el GATEWAY
API_URL = config["api_url"]

VOSK_MODEL_PATH = config.get("vosk_model_path", "vosk-model")

MEMORY_FILE = "memoria_usuarios.json"

# =========================================================
# LOGGING
# =========================================================

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "assistant.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("assistant")

# =========================================================
# PROMPT SISTEMA
# =========================================================

PROMPT_DEL_SISTEMA = """
Eres un asistente virtual diseñado para ayudar a personas mayores.

Reglas:
- Español claro y amable
- Explica paso a paso
- Sé paciente y cercano
"""

# =========================================================
# MEMORIA
# =========================================================

def cargar_memoria():
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_memoria(memoria):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)

memoria = cargar_memoria()

USUARIO_ACTUAL = "desconocido"

def set_usuario(u):
    global USUARIO_ACTUAL
    USUARIO_ACTUAL = u
    logger.info(f"Usuario: {u}")

# =========================================================
# UTILIDADES
# =========================================================

def hay_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except:
        return False


def web_search(query):
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        return "\n".join(
            a.get_text()
            for a in soup.find_all("a", class_="result__a", limit=3)
        )
    except:
        return ""

# =========================================================
# INTENCIONES
# =========================================================

def detectar_intencion(text):
    t = text.lower()

    if "hora" in t:
        return "time"

    return "llm"


def get_time():
    return datetime.now().strftime("%H:%M:%S")

# =========================================================
# PROMPT
# =========================================================

def construir_prompt(user, msg):
    hist = memoria.get(user, [])[-5:]

    contexto = ""
    for h in hist:
        contexto += f"Usuario: {h['user']}\nAsistente: {h['bot']}\n"

    return f"""
{PROMPT_DEL_SISTEMA}

Historial:
{contexto}

Usuario: {msg}
Asistente:
"""

# =========================================================
# LLAMADA A BACKEND (API GATEWAY)
# =========================================================

def ask_llm(prompt):
    try:
        r = requests.post(
            f"{API_URL}/chat",
            json={
                "user": USUARIO_ACTUAL,
                "text": prompt
            },
            timeout=60
        )

        data = r.json()
        return data.get("response", "")

    except Exception as e:
        logger.error(e)
        return ""

# =========================================================
# CORE
# =========================================================

def procesar_texto(texto, usuario=None):
    global memoria

    if usuario:
        set_usuario(usuario)

    logger.info(f"{USUARIO_ACTUAL}: {texto}")

    intent = detectar_intencion(texto)

    # ---------------- TIME TOOL ----------------
    if intent == "time":
        respuesta = f"Son las {get_time()}"

    # ---------------- LLM ----------------
    else:
        prompt = construir_prompt(USUARIO_ACTUAL, texto)

        respuesta = ""

        if hay_internet():
            respuesta = ask_llm(prompt)

        # fallback web
        if not respuesta:
            web = web_search(texto)
            if web:
                respuesta = ask_llm(web + "\n" + prompt)

        if not respuesta:
            respuesta = "No tengo respuesta ahora mismo."

    # memoria
    memoria.setdefault(USUARIO_ACTUAL, []).append({
        "user": texto,
        "bot": respuesta,
        "time": datetime.now().isoformat()
    })

    guardar_memoria(memoria)

    return respuesta

# =========================================================
# TTS
# =========================================================

def limpiar_texto(t):
    t = re.sub(r"\*\*(.*?)\*\*", r"\1", t)
    t = re.sub(r"\*(.*?)\*", r"\1", t)
    t = re.sub(r"\n+", ". ", t)
    return t


def hablar(texto):
    texto = limpiar_texto(texto)

    def run():
        subprocess.run([
            "pico2wave", "-l=es-ES",
            "-w=/tmp/voz.wav",
            texto
        ])

        subprocess.run(["aplay", "/tmp/voz.wav"])

    threading.Thread(target=run, daemon=True).start()

# =========================================================
# VOSK
# =========================================================

model = vosk.Model(VOSK_MODEL_PATH)
rec = vosk.KaldiRecognizer(model, 16000)

q_audio = queue.Queue()
cola = queue.Queue()


def audio_callback(indata, frames, time_, status):
    q_audio.put(bytes(indata))


def hilo_vosk():
    while True:
        data = q_audio.get()
        data = data[::3]

        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text = res.get("text", "")

            if text:
                cola.put(text)


def hilo_respuestas():
    while True:
        text = cola.get()

        respuesta = procesar_texto(text)
        hablar(respuesta)

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    threading.Thread(target=hilo_vosk, daemon=True).start()
    threading.Thread(target=hilo_respuestas, daemon=True).start()

    with sd.InputStream(
        samplerate=48000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback
    ):

        print("🧠 Asistente activo")

        while True:
            time.sleep(0.1)