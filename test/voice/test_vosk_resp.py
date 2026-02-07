import time
import random
import datetime
import threading
import queue
import json
import subprocess

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
    spi,
    cs=cs,
    dc=dc,
    rst=rst,
    baudrate=24000000,
    width=320,
    height=240,
)

display.fill(0x000000)

# =========================================================
# -------------------- EXPRESIONES -------------------------
# =========================================================
EXPRESIONES = {
    "feliz":     {"boca": "sonrisa", "cejas": "arriba"},
    "neutral":   {"boca": "neutral", "cejas": "plano"},
    "pensando":  {"boca": "neutral", "cejas": "arriba"},
    "hablando":  {"boca": "abierta", "cejas": "plano"},
    "guino":     {"boca": "sonrisa", "cejas": "guino"},
}

emocion_forzada = None
emocion_forzada_hasta = 0

def poner_cara(expresion, duracion=2):
    global emocion_forzada, emocion_forzada_hasta
    emocion_forzada = expresion
    emocion_forzada_hasta = time.time() + duracion

# =========================================================
# -------------------- DIBUJAR CARA ------------------------
# =========================================================
def dibujar_cara(expresion="neutral", ojos_abiertos=True):
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)

    estado = EXPRESIONES.get(expresion, EXPRESIONES["neutral"])
    cx = display.width // 2
    cy = display.height // 2 - 20

    radio = 38
    sep = 80

    ojo_izq = (cx-sep-radio, cy-radio, cx-sep+radio, cy+radio)
    ojo_der = (cx+sep-radio, cy-radio, cx+sep+radio, cy+radio)

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

    # BOCA
    boca_y = cy + 70
    if estado["boca"] == "sonrisa":
        draw.arc((cx-30, boca_y-10, cx+30, boca_y+20), 0, 180, fill="white", width=4)
    elif estado["boca"] == "abierta":
        draw.ellipse((cx-12, boca_y-12, cx+12, boca_y+12), outline="white", width=4)
    else:
        draw.line((cx-25, boca_y, cx+25, boca_y), fill="white", width=4)

    display.image(img)

# =========================================================
# -------------------- TTS (PIPER) -------------------------
# =========================================================
MODELO_PIPER = "/home/eli/tfg-ematos/test/interaction/es_ES-sharvard-medium.onnx"

def hablar(texto):
    poner_cara("hablando", duracion=len(texto)*0.06 + 0.5)
    wav = "/tmp/tts.wav"
    subprocess.run(["piper", "--model", MODELO_PIPER, "--output_file", wav, texto])
    subprocess.run(["aplay", wav])

# =========================================================
# -------------------- RESPUESTAS --------------------------
# =========================================================
cola_comandos = queue.Queue()

def responder(texto):
    print("🧠", texto)

    if "hola" in texto:
        hablar("Hola, aquí estoy")

    elif "hora" in texto:
        ahora = datetime.datetime.now().strftime("%H:%M")
        hablar(f"Son las {ahora}")

    elif "gracias" in texto:
        hablar("De nada")
        poner_cara("guino", 2)

    else:
        poner_cara("pensando", 2)
        hablar("No estoy seguro de haber entendido eso")

def bucle_respuestas():
    while True:
        texto = cola_comandos.get()
        responder(texto)

threading.Thread(target=bucle_respuestas, daemon=True).start()

# =========================================================
# -------------------- VOSK -------------------------------
# =========================================================
q_audio = queue.Queue()

def audio_callback(indata, frames, time_, status):
    if status:
        print(status)
    q_audio.put(bytes(indata))

model = vosk.Model("/home/eli/tfg-ematos/test/voice/vosk-model-small-es-0.42")
rec = vosk.KaldiRecognizer(model, 16000)

# =========================================================
# -------------------- LOOP PRINCIPAL ----------------------
# =========================================================
emocion_actual = "neutral"
parpadeo = time.time() + random.uniform(3,5)

with sd.RawInputStream(
    samplerate=48000,
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
        if emocion_forzada and ahora < emocion_forzada_hasta:
            emocion = emocion_forzada
        else:
            emocion = emocion_actual

        if ahora > parpadeo:
            dibujar_cara(emocion, ojos_abiertos=False)
            time.sleep(0.12)
            parpadeo = ahora + random.uniform(4,7)

        dibujar_cara(emocion, ojos_abiertos=True)

        # Voz
        if not q_audio.empty():
            data = q_audio.get()
            data_16k = data[::3]

            if rec.AcceptWaveform(data_16k):
                res = json.loads(rec.Result())
                texto = res.get("text", "").strip()
                if texto:
                    cola_comandos.put(texto)

        time.sleep(0.05)