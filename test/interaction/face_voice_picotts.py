import time
import random
import datetime
import threading
import queue
import json
import subprocess
import sounddevice as sd
import vosk

import board
import busio
import digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw

# =====================
# DISPLAY
# =====================
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D23)
rst = digitalio.DigitalInOut(board.D24)

display = ili9341.ILI9341(
    spi,
    cs=cs,
    dc=dc,
    rst=rst,
    baudrate=24000000,
    width=320,
    height=240,
)
display.fill(0x000000)

# =====================
# EXPRESIONES
# =====================
EXPRESIONES = {
    "feliz": {"boca": "sonrisa"},
    "neutral": {"boca": "neutral"},
    "sorpresa": {"boca": "sorpresa"},
    "triste": {"boca": "neutral"},
    "hablando": {"boca": "abierta"},
}

emocion_actual = "feliz"
robot_hablando = False

def dibujar_cara(expresion="feliz", ojos_abiertos=True):
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)

    cx = display.width // 2
    cy = display.height // 2 - 20

    radio_ojo = 35
    separacion = 75

    ojo_izq = (cx - separacion - radio_ojo, cy - radio_ojo,
               cx - separacion + radio_ojo, cy + radio_ojo)
    ojo_der = (cx + separacion - radio_ojo, cy - radio_ojo,
               cx + separacion + radio_ojo, cy + radio_ojo)

    if ojos_abiertos:
        draw.ellipse(ojo_izq, outline="white", width=4)
        draw.ellipse(ojo_der, outline="white", width=4)
    else:
        draw.line((ojo_izq[0], cy, ojo_izq[2], cy), fill="white", width=4)
        draw.line((ojo_der[0], cy, ojo_der[2], cy), fill="white", width=4)

    boca_y = cy + 70
    boca = EXPRESIONES.get(expresion, EXPRESIONES["feliz"])["boca"]

    if boca == "sonrisa":
        draw.arc((cx-30, boca_y-10, cx+30, boca_y+20), 0, 180, fill="white", width=4)
    elif boca == "neutral":
        draw.line((cx-25, boca_y, cx+25, boca_y), fill="white", width=4)
    elif boca == "sorpresa":
        draw.ellipse((cx-10, boca_y-10, cx+10, boca_y+10), outline="white", width=4)
    elif boca == "abierta":
        apertura = random.randint(8, 16)
        draw.ellipse((cx-12, boca_y-apertura, cx+12, boca_y+apertura), outline="white", width=4)

    display.image(img)

# =====================
# TTS - PICOTTS
# =====================
def hablar(texto):
    global robot_hablando
    robot_hablando = True

    # Micro pausas naturales
    texto = texto.replace(",", ", ... ")
    texto = texto.replace(".", ". ... ")

    def reproducir():
        global robot_hablando

        subprocess.run(
            ["pico2wave", "-l=es-ES", "-w=/tmp/voz.wav", texto],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        subprocess.run(
            ["aplay", "/tmp/voz.wav"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        robot_hablando = False

    threading.Thread(target=reproducir, daemon=True).start()

# =====================
# RESPUESTAS
# =====================
cola_comandos = queue.Queue()

def responder(texto):
    texto = texto.lower()
    print("🧠", texto)

    if "hola" in texto:
        hablar("Hola, estoy lista.")
    elif "hora" in texto:
        hablar(f"Son las {datetime.datetime.now().strftime('%H:%M')}")
    elif "gracias" in texto:
        hablar("De nada.")
    else:
        hablar("No entendí eso.")

threading.Thread(target=lambda: [responder(cola_comandos.get()) for _ in iter(int, 1)], daemon=True).start()

# =====================
# VOSK
# =====================
q_audio = queue.Queue()

def audio_callback(indata, frames, time_, status):
    if not robot_hablando:
        q_audio.put(bytes(indata))

model = vosk.Model("/home/eli/tfg-ematos/test/voice/vosk-model-small-es-0.42")
rec = vosk.KaldiRecognizer(model, 16000)

def hilo_vosk():
    while True:
        while not q_audio.empty():
            data = q_audio.get()
            data_16k = data[::3]
            if rec.AcceptWaveform(data_16k):
                res = json.loads(rec.Result())
                texto = res.get("text", "").strip()
                if texto:
                    cola_comandos.put(texto)
        time.sleep(0.005)

threading.Thread(target=hilo_vosk, daemon=True).start()

# =====================
# LOOP PRINCIPAL
# =====================
proximo_parpadeo = time.time() + random.uniform(3,5)
parpadeo_fin = 0

with sd.InputStream(
    samplerate=48000,
    blocksize=4000,
    dtype='int16',
    channels=1,
    device=2,
    callback=audio_callback
):
    print("🤖 Robot activo")
    while True:
        ahora = time.time()

        if ahora > proximo_parpadeo:
            dibujar_cara("neutral", ojos_abiertos=False)
            parpadeo_fin = ahora + 0.12
            proximo_parpadeo = ahora + random.uniform(4,8)

        if parpadeo_fin and ahora > parpadeo_fin:
            dibujar_cara("feliz", ojos_abiertos=True)
            parpadeo_fin = 0

        if robot_hablando:
            dibujar_cara("hablando", ojos_abiertos=True)
        else:
            dibujar_cara("feliz", ojos_abiertos=True)

        time.sleep(0.03)