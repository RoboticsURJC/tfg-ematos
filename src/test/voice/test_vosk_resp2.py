import time
import queue
import threading
import json
import subprocess
import datetime
import board
import busio
import digitalio
from adafruit_rgb_display import ili9341
from PIL import Image, ImageDraw
import sounddevice as sd
import vosk

# ====================== DISPLAY ======================
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D23)
rst = digitalio.DigitalInOut(board.D24)

display = ili9341.ILI9341(
    spi, cs=cs, dc=dc, rst=rst,
    baudrate=24000000, width=320, height=240
)
display.fill(0x000000)

# ====================== EXPRESIONES ======================
EXPRESIONES = {
    "feliz":     {"boca": "sonrisa", "cejas": "arriba"},
    "neutral":   {"boca": "neutral", "cejas": "plano"},
    "sorpresa":  {"boca": "sorpresa", "cejas": "muy_arriba"},
    "enfadado":  {"boca": "neutral", "cejas": "inclinadas"},
    "triste":    {"boca": "neutral", "cejas": "tristes"},
    "guino":     {"boca": "sonrisa", "cejas": "guino"},
    "agradecido":{"boca": "sonrisa", "cejas": "arriba"},
}

emocion_forzada = None
emocion_hasta = 0

def poner_cara(expresion, duracion=2):
    global emocion_forzada, emocion_hasta
    emocion_forzada = expresion
    emocion_hasta = time.time() + duracion

def dibujar_cara(expresion="neutral", ojos_abiertos=True):
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)
    estado = EXPRESIONES.get(expresion, EXPRESIONES["neutral"])

    cx, cy = display.width//2, display.height//2-20
    radio_ojo, sep = 38, 80

    ojo_izq = (cx-sep-radio_ojo, cy-radio_ojo, cx-sep+radio_ojo, cy+radio_ojo)
    ojo_der = (cx+sep-radio_ojo, cy-radio_ojo, cx+sep+radio_ojo, cy+radio_ojo)

    # OJOS
    pupila_r = 8
    if ojos_abiertos:
        draw.ellipse(ojo_izq, outline="white", width=4)
        draw.ellipse((ojo_izq[0]+22, ojo_izq[1]+26, ojo_izq[0]+22+pupila_r*2, ojo_izq[1]+26+pupila_r*2), fill="white")
        draw.ellipse((ojo_izq[0]+45, ojo_izq[1]+20, ojo_izq[0]+50, ojo_izq[1]+25), fill="white")

        if expresion == "guino":
            draw.line((ojo_der[0], cy, ojo_der[2], cy), fill="white", width=4)
        else:
            draw.ellipse(ojo_der, outline="white", width=4)
            draw.ellipse((ojo_der[0]+22, ojo_der[1]+26, ojo_der[0]+22+pupila_r*2, ojo_der[1]+26+pupila_r*2), fill="white")
            draw.ellipse((ojo_der[0]+45, ojo_der[1]+20, ojo_der[0]+50, ojo_der[1]+25), fill="white")
    else:
        draw.line((ojo_izq[0], cy, ojo_izq[2], cy), fill="white", width=4)
        draw.line((ojo_der[0], cy, ojo_der[2], cy), fill="white", width=4)

    # CEJAS
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
        draw.line((ojo_izq[0]+10, ojo_izq[1]-25, ojo_izq[2]-10, ojo_izq[1]-35), fill="white", width=4)
        draw.line((ojo_der[0]+10, ojo_der[1]-15, ojo_der[2]-10, ojo_der[1]-15), fill="white", width=4)

    # BOCA
    boca_y = cy + 70
    if estado["boca"] == "sonrisa":
        draw.arc((cx-30, boca_y-10, cx+30, boca_y+20), 0, 180, fill="white", width=4)
    elif estado["boca"] == "neutral":
        draw.line((cx-25, boca_y, cx+25, boca_y), fill="white", width=4)
    elif estado["boca"] == "sorpresa":
        draw.ellipse((cx-10, boca_y-10, cx+10, boca_y+10), outline="white", width=4)

    display.image(img)

# ====================== TTS ======================
MODELO_PIPER = "/home/eli/tfg-ematos/test/interaction/es_ES-sharvard-medium.onnx"
cache_tts = {}

def hablar(texto):
    poner_cara("hablando", duracion=len(texto)*0.06 + 0.5)
    wav = f"/tmp/{hash(texto)}.wav"
    if texto not in cache_tts:
        subprocess.run(["piper","--model",MODELO_PIPER,"--output_file",wav,texto],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cache_tts[texto] = wav
    subprocess.run(["aplay", cache_tts[texto]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ====================== RESPUESTAS ======================
cola_comandos = queue.Queue()

def responder(texto):
    print("🧠", texto.lower())
    t = texto.lower()
    if "hola" in t:
        poner_cara("feliz",2)
        hablar("Hola, ¿qué tal?")
    elif "hora" in t:
        poner_cara("sorpresa",1.5)
        hablar("Son las " + datetime.datetime.now().strftime("%H:%M"))
    elif "gracias" in t:
        poner_cara("agradecido",2)
        hablar("De nada")
    elif "triste" in t:
        poner_cara("triste",2)
        hablar("Oh, lo siento...")
    else:
        poner_cara("pensando",2)
        hablar("No te he entendido")

def hilo_respuestas():
    while True:
        texto = cola_comandos.get()
        responder(texto)

threading.Thread(target=hilo_respuestas, daemon=True).start()

# ====================== VOSK ======================
q_audio = queue.Queue()

def audio_callback(indata, frames, time_, status):
    if status:
        print(status)
    q_audio.put(bytes(indata))

model = vosk.Model("/home/eli/tfg-ematos/test/voice/vosk-model-small-es-0.42")
rec = vosk.KaldiRecognizer(model, 16000)

# ====================== LOOP PRINCIPAL ======================
parpadeo = time.time() + 4
emocion_actual = "neutral"

with sd.InputStream(samplerate=48000, channels=1, dtype='int16', device=2, callback=audio_callback):
    print("🤖 Robot activo")
    while True:
        ahora = time.time()
        if emocion_forzada and ahora < emocion_hasta:
            emocion = emocion_forzada
        else:
            emocion = emocion_actual

        if ahora > parpadeo:
            dibujar_cara(emocion, ojos_abiertos=False)
            time.sleep(0.12)
            parpadeo = ahora + 5

        dibujar_cara(emocion, ojos_abiertos=True)

        # Procesar audio
        if not q_audio.empty():
            data = q_audio.get()
            data_16k = data[::3]  # downsample 48k -> 16k
            if rec.AcceptWaveform(data_16k):
                res = json.loads(rec.Result())
                texto = res.get("text","").strip()
                if texto:
                    cola_comandos.put(texto)

        time.sleep(0.02)
