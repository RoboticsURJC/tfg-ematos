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
from PIL import Image, ImageDraw, ImageFont

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

# =====================
# VARIABLES
# =====================
robot_hablando = False
estado_texto = "ESCUCHANDO..."
cola_comandos = queue.Queue()
q_audio = queue.Queue()

proximo_parpadeo = time.time() + random.uniform(3, 6)
parpadeo_fin = 0

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except:
    font = ImageFont.load_default()

# =====================
# DIBUJAR CARA
# =====================
def dibujar_cara(expresion="feliz", ojos_abiertos=True):
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)

    cx = display.width // 2
    cy = display.height // 2 - 30
    radio = 35
    sep = 75

    # =====================
    # OJOS
    # =====================
    if ojos_abiertos:
        # Contorno
        draw.ellipse((cx-sep-radio, cy-radio, cx-sep+radio, cy+radio), outline="white", width=4)
        draw.ellipse((cx+sep-radio, cy-radio, cx+sep+radio, cy+radio), outline="white", width=4)

        # Pupilas
        draw.ellipse((cx-sep-10, cy-10, cx-sep+10, cy+10), fill="white")
        draw.ellipse((cx+sep-10, cy-10, cx+sep+10, cy+10), fill="white")

        # ✨ BRILLO FIJO
        draw.ellipse((cx-sep+8, cy-18, cx-sep+16, cy-10), fill="white")
        draw.ellipse((cx+sep+8, cy-18, cx+sep+16, cy-10), fill="white")

        draw.ellipse((cx-sep-15, cy+5, cx-sep-10, cy+10), fill="white")
        draw.ellipse((cx+sep-15, cy+5, cx+sep-10, cy+10), fill="white")

    else:
        # Ojos cerrados (pestañeo)
        draw.line((cx-sep-radio, cy, cx-sep+radio, cy), fill="white", width=5)
        draw.line((cx+sep-radio, cy, cx+sep+radio, cy), fill="white", width=5)

    # =====================
    # CEJAS
    # =====================
    if expresion == "feliz":
        draw.line((cx-sep-20, cy-radio-15, cx-sep+20, cy-radio-25), fill="white", width=4)
        draw.line((cx+sep-20, cy-radio-25, cx+sep+20, cy-radio-15), fill="white", width=4)

    elif expresion == "triste":
        draw.line((cx-sep-20, cy-radio-25, cx-sep+20, cy-radio-10), fill="white", width=4)
        draw.line((cx+sep-20, cy-radio-10, cx+sep+20, cy-radio-25), fill="white", width=4)

    elif expresion == "enfadado":
        draw.line((cx-sep-20, cy-radio-10, cx-sep+20, cy-radio-30), fill="white", width=4)
        draw.line((cx+sep-20, cy-radio-30, cx+sep+20, cy-radio-10), fill="white", width=4)

    elif expresion == "sorpresa":
        draw.line((cx-sep-20, cy-radio-35, cx-sep+20, cy-radio-35), fill="white", width=4)
        draw.line((cx+sep-20, cy-radio-35, cx+sep+20, cy-radio-35), fill="white", width=4)

    else:
        draw.line((cx-sep-20, cy-radio-20, cx-sep+20, cy-radio-20), fill="white", width=4)
        draw.line((cx+sep-20, cy-radio-20, cx+sep+20, cy-radio-20), fill="white", width=4)

    # =====================
    # BOCA
    # =====================
    boca_y = cy + 75

    if robot_hablando:
        apertura = random.randint(10, 18)
        draw.ellipse((cx-15, boca_y-apertura, cx+15, boca_y+apertura), outline="white", width=4)
    else:
        draw.arc((cx-30, boca_y-10, cx+30, boca_y+20), 0, 180, fill="white", width=4)

    # =====================
    # TEXTO INFERIOR
    # =====================
    draw.rectangle((0, 200, 320, 240), fill="black")
    draw.text((10, 210), estado_texto[:35], font=font, fill="white")

    display.image(img)

# =====================
# TTS
# =====================
def hablar(texto):
    global robot_hablando, estado_texto
    robot_hablando = True
    estado_texto = "HABLANDO..."

    def reproducir():
        global robot_hablando, estado_texto
        subprocess.run(["pico2wave", "-l=es-ES", "-w=/tmp/voz.wav", texto],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["aplay", "/tmp/voz.wav"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        robot_hablando = False
        estado_texto = "Escuchando..."

    threading.Thread(target=reproducir, daemon=True).start()

# =====================
# RESPUESTA
# =====================
def responder(texto):
    global estado_texto
    print("🎤 Escuchado:", texto)
    estado_texto = "Procesando..."

    texto = texto.lower()

    if "hola" in texto:
        hablar("Hola, aquí estoy.")
    elif "hora" in texto:
        hora = datetime.datetime.now().strftime("%H:%M")
        hablar(f"Son las {hora}")                                                                                                    
    elif "gracias" in texto:
        hablar("De nada.")
    else:
        hablar("No entendí eso.")

threading.Thread(target=lambda: [responder(cola_comandos.get()) for _ in iter(int, 1)], daemon=True).start()

# =====================
# VOSK
# =====================
model = vosk.Model("/home/eli/tfg-ematos/test/voice/vosk-model-small-es-0.42")
rec = vosk.KaldiRecognizer(model, 16000)

def audio_callback(indata, frames, time_, status):
    if not robot_hablando:
        q_audio.put(bytes(indata))

def hilo_vosk():
    global estado_texto
    while True:
        while not q_audio.empty():
            data = q_audio.get()
            data_16k = data[::3]
            if rec.AcceptWaveform(data_16k):
                res = json.loads(rec.Result())
                texto = res.get("text", "").strip()
                if texto:
                    estado_texto = f"Escuchado: {texto}"
                    cola_comandos.put(texto)
        time.sleep(0.005)

threading.Thread(target=hilo_vosk, daemon=True).start()

# =====================
# LOOP PRINCIPAL
# =====================
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
            dibujar_cara(ojos_abiertos=False)
            parpadeo_fin = ahora + 0.12
            proximo_parpadeo = ahora + random.uniform(4, 8)

        if parpadeo_fin and ahora > parpadeo_fin:
            dibujar_cara(ojos_abiertos=True)
            parpadeo_fin = 0

        dibujar_cara(ojos_abiertos=True)
        time.sleep(0.03)