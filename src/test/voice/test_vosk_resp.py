import time
import datetime
import threading
import queue
import json
import subprocess
import random

import board
import busio
import digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw

import sounddevice as sd
import vosk

# =========================================================
# -------------------- DISPLAY ----------------------------
# =========================================================
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D23)
rst = digitalio.DigitalInOut(board.D24)

display = ili9341.ILI9341(
    spi, cs=cs, dc=dc, rst=rst,
    baudrate=24000000, width=320, height=240
)
display.fill(0x000000)

# =========================================================
# -------------------- EXPRESIONES ------------------------
# =========================================================
EXPRESIONES = {
    "feliz":     {"boca": "sonrisa", "cejas": "arriba"},
    "neutral":   {"boca": "neutral", "cejas": "plano"},
    "pensando":  {"boca": "neutral", "cejas": "arriba"},
    "hablando":  {"boca": "abierta", "cejas": "plano"},
    "guino":     {"boca": "sonrisa", "cejas": "guino"},
}

emocion_forzada = None
emocion_hasta = 0

def poner_cara(expresion, duracion=2):
    global emocion_forzada, emocion_hasta
    emocion_forzada = expresion
    emocion_hasta = time.time() + duracion

def dibujar_cara(expresion="neutral", ojos_abiertos=True):
    img = Image.new("RGB", (320, 240), "black")
    draw = ImageDraw.Draw(img)

    estado = EXPRESIONES.get(expresion, EXPRESIONES["neutral"])
    cx, cy = 160, 100
    r, sep = 38, 80

    ojo_izq = (cx-sep-r, cy-r, cx-sep+r, cy+r)
    ojo_der = (cx+sep-r, cy-r, cx+sep+r, cy+r)

    # OJOS
    if ojos_abiertos:
        draw.ellipse(ojo_izq, outline="white", width=4)
        draw.ellipse(ojo_der, outline="white", width=4)
    else:
        draw.line((ojo_izq[0], cy, ojo_izq[2], cy), fill="white", width=4)
        draw.line((ojo_der[0], cy, ojo_der[2], cy), fill="white", width=4)

    # CEJAS
    if estado["cejas"] == "arriba":
        draw.line((ojo_izq[0]+10, ojo_izq[1]-20, ojo_izq[2]-10, ojo_izq[1]-30), fill="white", width=4)
        draw.line((ojo_der[0]+10, ojo_der[1]-30, ojo_der[2]-10, ojo_der[1]-20), fill="white", width=4)
    elif estado["cejas"] == "guino":
        draw.line((ojo_izq[0]+10, ojo_izq[1]-30, ojo_izq[2]-10, ojo_izq[1]-40), fill="white", width=4)
        draw.line((ojo_der[0]+10, ojo_der[1]-20, ojo_der[2]-10, ojo_der[1]-20), fill="white", width=4)
    elif estado["cejas"] == "plano":
        pass

    # BOCA
    by = cy + 70
    if estado["boca"] == "sonrisa":
        draw.arc((cx-30, by-10, cx+30, by+20), 0, 180, fill="white", width=4)
    elif estado["boca"] == "abierta":
        draw.ellipse((cx-12, by-12, cx+12, by+12), outline="white", width=4)
    else:
        draw.line((cx-25, by, cx+25, by), fill="white", width=4)

    display.image(img)

# =========================================================
# -------------------- TTS (PIPER) ------------------------
# =========================================================
MODELO_PIPER = "/home/eli/tfg-ematos/test/interaction/es_ES-sharvard-medium.onnx"
robot_hablando = False
cache_tts = {}

def hablar(texto):
    global robot_hablando
    robot_hablando = True
    poner_cara("hablando", duracion=len(texto)*0.06 + 0.5)

    wav = f"/tmp/{hash(texto)}.wav"
    if texto not in cache_tts:
        subprocess.run(
            ["piper", "--model", MODELO_PIPER, "--output_file", wav, texto],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        cache_tts[texto] = wav

    subprocess.run(["aplay", cache_tts[texto]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    robot_hablando = False

# =========================================================
# -------------------- RESPUESTAS -------------------------
# =========================================================
cola_comandos = queue.Queue()

def responder(texto):
    texto = texto.lower()
    print("🧠", texto)

    if "hola" in texto:
        poner_cara("feliz", 2)
        hablar("Hola, aquí estoy")

    elif "hora" in texto:
        ahora = datetime.datetime.now().strftime("%H:%M")
        poner_cara("pensando", 2)
        hablar(f"Son las {ahora}")

    elif "gracias" in texto:
        poner_cara("guino", 2)
        hablar("De nada")

    else:
        poner_cara("pensando", 2)
        hablar("No entendí eso")

def hilo_respuestas():
    while True:
        responder(cola_comandos.get())

threading.Thread(target=hilo_respuestas, daemon=True).start()

# =========================================================
# -------------------- VOSK -------------------------------
# =========================================================
q_audio = queue.Queue()

def audio_callback(indata, frames, time_, status):
    if not robot_hablando:
        q_audio.put(bytes(indata))

model = vosk.Model("/home/eli/tfg-ematos/test/voice/vosk-model-small-es-0.42")
rec = vosk.KaldiRecognizer(model, 16000)

# =========================================================
# -------------------- LOOP PRINCIPAL ----------------------
# =========================================================
parpadeo = time.time() + random.uniform(3,5)

with sd.InputStream(
    samplerate=48000,       # mic soporta 48 kHz
    blocksize=8000,
    dtype="int16",
    channels=1,
    device=2,
    callback=audio_callback
):
    print("🤖 Robot activo")

    while True:
        ahora = time.time()

        # Cara
        if emocion_forzada and ahora < emocion_hasta:
            emocion = emocion_forzada
        else:
            emocion = "neutral"

        # Parpadeo
        if ahora > parpadeo:
            dibujar_cara(emocion, ojos_abiertos=False)
            time.sleep(0.12)
            parpadeo = ahora + random.uniform(4,7)

        dibujar_cara(emocion, ojos_abiertos=True)

        # Voz
        while not q_audio.empty():
            data = q_audio.get()
            # Convertimos 48kHz -> 16kHz
            data_16k = data[::3]

            if rec.AcceptWaveform(data_16k):
                res = json.loads(rec.Result())
                texto = res.get("text", "").strip()
                if texto:
                    cola_comandos.put(texto)

        time.sleep(0.03)
