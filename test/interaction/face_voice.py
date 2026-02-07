import time
import random
import datetime
import threading
import queue
import json
import sounddevice as sd
import vosk

import board
import busio
import digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw

# =====================
# ---------------- DISPLAY ----------------
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
# ---------------- EXPRESIONES ----------------
# =====================
EXPRESIONES = {
    "feliz":     {"boca": "sonrisa", "cejas": "arriba"},
    "neutral":   {"boca": "neutral", "cejas": "plano"},
    "sorpresa":  {"boca": "sorpresa","cejas": "muy_arriba"},
    "enfadado":  {"boca": "neutral", "cejas": "inclinadas"},
    "triste":    {"boca": "neutral", "cejas": "tristes"},
    "guino":     {"boca": "sonrisa", "cejas": "guino"},
    "pensando":  {"boca": "neutral", "cejas": "arriba"},
}

# =====================
# ---------------- DIBUJAR CARA ----------------
# =====================
emocion_forzada = None
emocion_forzada_hasta = 0

def poner_cara(expresion, duracion=2):
    global emocion_forzada, emocion_forzada_hasta
    emocion_forzada = expresion
    emocion_forzada_hasta = time.time() + duracion

def dibujar_cara(expresion="feliz", ojos_abiertos=True):
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)

    estado = EXPRESIONES.get(expresion, EXPRESIONES["neutral"])
    cx = display.width // 2
    cy = display.height // 2 - 20

    radio_ojo = 38
    separacion = 80

    ojo_izq = (cx - separacion - radio_ojo, cy - radio_ojo,
               cx - separacion + radio_ojo, cy + radio_ojo)
    ojo_der = (cx + separacion - radio_ojo, cy - radio_ojo,
               cx + separacion + radio_ojo, cy + radio_ojo)

    # ---------- OJOS ----------
    if ojos_abiertos:
        draw.ellipse(ojo_izq, outline="white", width=4)
        pupila_r = 8
        draw.ellipse((ojo_izq[0]+22, ojo_izq[1]+26,
                      ojo_izq[0]+22+pupila_r*2, ojo_izq[1]+26+pupila_r*2), fill="white")
        draw.ellipse((ojo_izq[0]+45, ojo_izq[1]+20,
                      ojo_izq[0]+50, ojo_izq[1]+25), fill="white")

        if expresion == "guino":
            draw.line((ojo_der[0], cy, ojo_der[2], cy), fill="white", width=4)
        else:
            draw.ellipse(ojo_der, outline="white", width=4)
            draw.ellipse((ojo_der[0]+22, ojo_der[1]+26,
                          ojo_der[0]+22+pupila_r*2, ojo_der[1]+26+pupila_r*2), fill="white")
            draw.ellipse((ojo_der[0]+45, ojo_der[1]+20,
                          ojo_der[0]+50, ojo_der[1]+25), fill="white")
    else:
        draw.line((ojo_izq[0], cy, ojo_izq[2], cy), fill="white", width=4)
        draw.line((ojo_der[0], cy, ojo_der[2], cy), fill="white", width=4)

    # ---------- CEJAS ----------
    if estado["cejas"] == "arriba":
        draw.line((ojo_izq[0]+10, ojo_izq[1]-15, ojo_izq[2]-10, ojo_izq[1]-25), fill="white", width=4)
        draw.line((ojo_der[0]+10, ojo_der[1]-25, ojo_der[2]-10, ojo_der[1]-15), fill="white", width=4)
    elif estado["cejas"] == "muy_arriba":
        draw.line((ojo_izq[0]+10, ojo_izq[1]-25, ojo_izq[2]-10, ojo_izq[1]-35), fill="white", width=4)
        draw.line((ojo_der[0]+10, ojo_der[1]-35, ojo_der[2]-10, ojo_der[1]-25), fill="white", width=4)
    elif estado["cejas"] == "inclinadas":
        draw.line((ojo_izq[0]+5, ojo_izq[1]-10, ojo_izq[2]-5, ojo_izq[1]-25), fill="white", width=4)
        draw.line((ojo_der[0]+5, ojo_der[1]-25, ojo_der[2]-5, ojo_der[1]-10), fill="white", width=4)
    elif estado["cejas"] == "tristes":
        draw.line((ojo_izq[0]+5, ojo_izq[1]-25, ojo_izq[2]-5, ojo_izq[1]-10), fill="white", width=4)
        draw.line((ojo_der[0]+5, ojo_der[1]-10, ojo_der[2]-5, ojo_der[1]-25), fill="white", width=4)
    elif estado["cejas"] == "guino":
        draw.line((ojo_izq[0]+10, ojo_izq[1]-25,
                   ojo_izq[2]-10, ojo_izq[1]-35), fill="white", width=4)
        draw.line((ojo_der[0]+10, ojo_der[1]-15,
                   ojo_der[2]-10, ojo_der[1]-15), fill="white", width=4)

    # ---------- BOCA ----------
    boca_y = cy + 70
    if estado["boca"] == "sonrisa":
        draw.arc((cx-30, boca_y-10, cx+30, boca_y+20), 0, 180, fill="white", width=4)
    elif estado["boca"] == "neutral":
        draw.line((cx-25, boca_y, cx+25, boca_y), fill="white", width=4)
    elif estado["boca"] == "sorpresa":
        draw.ellipse((cx-10, boca_y-10, cx+10, boca_y+10), outline="white", width=4)

    display.image(img)

# =====================
# ---------------- COMANDOS / RECORDATORIOS ----------------
# =====================
recordatorios = []

def revisar_recordatorios():
    while True:
        ahora = datetime.datetime.now()
        for r in recordatorios[:]:
            if ahora >= r["time"]:
                print("⏰ RECORDATORIO:", r["text"])
                poner_cara("sorpresa", 2)
                recordatorios.remove(r)
        time.sleep(1)

threading.Thread(target=revisar_recordatorios, daemon=True).start()

def procesar_texto(texto):
    texto = texto.lower()
    print("🧠 Detectado:", texto)

    if "hora" in texto:
        ahora = datetime.datetime.now().strftime("%H:%M")
        print("🕒 Son las", ahora)
        poner_cara("neutral", 2)

    elif "recuérdame en" in texto:
        try:
            palabras = texto.split()
            minutos = int(palabras[palabras.index("en")+1])
            momento = datetime.datetime.now() + datetime.timedelta(minutes=minutos)
            recordatorios.append({
                "time": momento,
                "text": f"Han pasado {minutos} minutos"
            })
            print(f"📝 Recordatorio en {minutos} minutos")
            poner_cara("pensando", 2)
        except:
            print("❌ No entendí el tiempo")
            poner_cara("triste", 2)

    elif "hola" in texto:
        print("👋 ¡Hola!")
        poner_cara("feliz", 2)

    elif "gracias" in texto:
        print("😊 De nada!")
        poner_cara("guino", 2)

# =====================
# ---------------- VOSK AUDIO ----------------
# =====================
q_audio = queue.Queue()

def audio_callback(indata, frames, time_, status):
    if status:
        print(status)
    q_audio.put(bytes(indata))

model = vosk.Model("/home/eli/tfg-ematos/test/voice/vosk-model-small-es-0.42")
rec = vosk.KaldiRecognizer(model, 16000)

# =====================
# ---------------- LOOP CARA + ESCUCHA ----------------
# =====================
emocion_actual = random.choice(list(EXPRESIONES.keys()))
proximo_cambio = time.time() + random.uniform(2,4)
proximo_parpadeo = time.time() + random.uniform(3,5)

with sd.RawInputStream(
    samplerate=48000,
    blocksize=8000,
    dtype='int16',
    channels=1,
    device=2,   # tu micro AB13X
    callback=audio_callback
):
    print("🤖 Robot activo: escucha y reacciona")
    while True:
        ahora = time.time()

        # --------------- CARA ---------------
        if emocion_forzada and ahora < emocion_forzada_hasta:
            emocion = emocion_forzada
        else:
            emocion_forzada = None
            emocion = emocion_actual
            if ahora > proximo_cambio:
                emocion_actual = random.choice(list(EXPRESIONES.keys()))
                proximo_cambio = ahora + random.uniform(2,4)

        if ahora > proximo_parpadeo:
            dibujar_cara(emocion, ojos_abiertos=False)
            time.sleep(0.12)
            proximo_parpadeo = ahora + random.uniform(5,10)

        dibujar_cara(emocion, ojos_abiertos=True)

        # --------------- VOSK ---------------
        if not q_audio.empty():
            data = q_audio.get()
            data_16k = data[::3]  # 48k -> 16k
            if rec.AcceptWaveform(data_16k):
                result = json.loads(rec.Result())
                if result["text"]:
                    procesar_texto(result["text"])

        time.sleep(0.05)
