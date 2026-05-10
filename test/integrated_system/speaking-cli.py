"""
@file asistente_robotico.py
@brief Asistente conversacional con voz, LLM y display emocional.

Este sistema integra:
- Reconocimiento de voz (Vosk)
- Procesamiento inteligente (LLM + tools + web fallback)
- Síntesis de voz (TTS)
- Interfaz visual (pantalla SPI con cara animada)

Autor: Elisa Matos
"""


# =========================================================
# IMPORTS
# =========================================================

import re
import sys

import requests
import time
import json
import os
from bs4 import BeautifulSoup
import logging
from pathlib import Path
from datetime import datetime
import random
import threading
import queue
import subprocess
import socket

import sounddevice as sd
import vosk

import board
import busio
import digitalio
from adafruit_rgb_display import ili9341

from PIL import Image, ImageDraw, ImageFont


PROMPT_DEL_SISTEMA = """
Eres un asistente virtual diseñado para ayudar a personas mayores.

Reglas importantes:
- Siempre responde en español.
- Usa un lenguaje claro, sencillo y amable.
- Explica las cosas paso a paso cuando sea necesario.
- Evita tecnicismos innecesarios.
- Sé paciente, cercano y respetuoso.
- Si no entiendes algo, pide aclaración de forma amable.
- Prioriza respuestas útiles y prácticas.
"""

# =========================================================
# CONFIGURACION DE LOGGING 
# =========================================================

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_filename = os.path.join(
    LOG_DIR,
    datetime.now().strftime("asistente_%Y-%m-%d_%H-%M-%S.log")
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("robot")

logger.info("Sistema iniciado")


# =====================
# CONFIGURACIÓN
# =====================

SERVER_IP = "192.168.1.96"  # IP del PC con Vicuna
SERVER_URL = f"http://{SERVER_IP}:8000/generate"

VOSK_MODEL_PATH = "/home/elisa/tfg-ematos/test/voice/vosk-model-small-es-0.42"


MEMORY_FILE = "memoria_usuarios.json"
LOG_DIR = "logs"

# =========================================================
# CONFIG LOAD
# =========================================================

curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "config copy.json")

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

PC_URL = config["server_url"]

TIMEOUT = 90

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_FILE = f"results_rpi_{timestamp}.json"

TIMEOUT = 90  #  importante para Gemini/GPT



# =========================================================
# MEMORIA PERSISTENTE
# =========================================================

def cargar_memoria():
    """
    @brief Carga la memoria persistente desde archivo JSON.

    @return Diccionario con conversaciones por usuario.
    """
    
    if not os.path.exists(MEMORY_FILE):
        return {}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def guardar_memoria(memoria):
    """
    @brief Guarda la memoria persistente en archivo JSON.

    @param memoria Diccionario de conversaciones.
    """
    
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)


memoria = cargar_memoria()

# =========================================================
# VARIABLES
# =========================================================

robot_hablando = False
estado_texto = "Escuchando..."
puntos = 0   
proceso_audio = None

cola_comandos = queue.Queue()
q_audio = queue.Queue()

proximo_parpadeo = time.time() + random.uniform(3, 6)
parpadeo_fin = 0


# Colores RGB
COLOR_ESCUCHANDO = (0, 255, 0)   # verde
COLOR_HABLANDO = (255, 255, 0)   # amarillo

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except:
    font = ImageFont.load_default()
    
    
# =====================
# DISPLAY
# =====================
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D23)
rst = digitalio.DigitalInOut(board.D24)

display = ili9341.ILI9341(
    spi, cs=cs, dc=dc, rst=rst,
    baudrate=24000000, width=320, height=240
)


def dibujar_cara(ojos_abiertos=True):
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)

    cx = display.width // 2
    cy = display.height // 2 - 30
    radio = 35
    sep = 75

    # Ojos
    if ojos_abiertos:
        draw.ellipse((cx-sep-radio, cy-radio, cx-sep+radio, cy+radio), outline="white", width=4)
        draw.ellipse((cx+sep-radio, cy-radio, cx+sep+radio, cy+radio), outline="white", width=4)
        
        # Pupilas
        draw.ellipse((cx-sep-10, cy-10, cx-sep+10, cy+10), fill="white")
        draw.ellipse((cx+sep-10, cy-10, cx+sep+10, cy+10), fill="white")
       
        # Brillo fijo
        draw.ellipse((cx-sep+8, cy-18, cx-sep+16, cy-10), fill="white")
        draw.ellipse((cx+sep+8, cy-18, cx+sep+16, cy-10), fill="white")
        # draw.ellipse((cx-sep-15, cy+5, cx-sep-10, cy+10), fill="white")
        # draw.ellipse((cx+sep-15, cy+5, cx+sep-10, cy+10), fill="white")
    else:
        draw.line((cx-sep-radio, cy, cx-sep+radio, cy), fill="white", width=5)
        draw.line((cx+sep-radio, cy, cx+sep+radio, cy), fill="white", width=5)

    # Boca
    boca_y = cy + 75
    if robot_hablando:
        apertura = random.randint(10, 18)
        draw.ellipse((cx-15, boca_y-apertura, cx+15, boca_y+apertura), outline="white", width=4)
    else:
        draw.arc((cx-30, boca_y-10, cx+30, boca_y+20), 0, 180, fill="white", width=4)

    # Texto de estado
    draw.rectangle((0, 200, 320, 240), fill="black")
    color = COLOR_HABLANDO if robot_hablando else COLOR_ESCUCHANDO
    draw.text((10, 210), estado_texto[:35], font=font, fill=color)

    display.image(img)
    
    
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
    """
    @brief Busca información en internet si el modelo no sabe responder.
    """
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}"
        r = requests.get(url, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        results = []
        for a in soup.find_all("a", class_="result__a", limit=3):
            results.append(a.get_text())

        return "\n".join(results)

    except Exception as e:
        logger.error(f"WEB SEARCH ERROR: {e}")
        return ""
  
  
# =========================================================
# ACCIONES DEFINIDAS
# =========================================================

def get_current_time():
    """
    @brief Devuelve la hora actual en formato legible.
    """
    return datetime.now().strftime("%H:%M:%S")

def get_weather(city="Madrid"):
    """
    @brief Devuelve el clima actual de la zona
    """
    
    try:
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        ).json()

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        weather = requests.get(
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current_weather=true"
        ).json()

        temp = weather["current_weather"]["temperature"]
        wind = weather["current_weather"]["windspeed"]

        return f"En {city} ahora hay {temp}°C y viento de {wind} km/h"

    except Exception:
        return "No he podido obtener el clima ahora mismo."


def detectar_intencion(text: str):
    """
    @brief Detecta la intención del usuario a partir del texto.

    @param text Texto de entrada.
    @return Tipo de intención: "time", "weather" o "llm".
    """
    
    t = text.lower()

    if any(x in t for x in ["hora", "qué hora", "que hora", "dime la hora"]):
        return "time"

    if any(x in t for x in ["clima", "tiempo", "qué tiempo", "que tiempo"]):
        return "weather"

    return "llm"
  
  

# =========================================================
# LLM + MEMORIA
# =========================================================

def construir_prompt(usuario, mensaje):
    """
    @brief Construye un prompt completo con contexto conversacional.
    """

    historial = memoria.get(usuario, [])[-5:]

    contexto = ""
    for h in historial:
        contexto += f"Usuario: {h['user']}\nAsistente: {h['bot']}\n"

    prompt = f"""
          {PROMPT_DEL_SISTEMA}

          Historial de conversación:
          {contexto}

          Usuario: {mensaje}
          Asistente:
      """

    return prompt


def ask_model(prompt):
    """
    @brief Llama al modelo LLM del servidor.
    @param prompt Texto a enviar al modelo.
    @return Respuesta generada por el modelo (string).
    """

    try:
        r = requests.post(
            PC_URL,
            json={"model": "groq", "prompt": prompt},
            timeout=TIMEOUT
        )
        data = r.json()

        output = data.get("output", "")

        
        if isinstance(output, list):
            output = output[0]

        return str(output)

    except Exception as e:
        logger.error(f"LLM ERROR: {e}")
        return ""
      
      
# =========================================================
# PROCESAMIENTO
# =========================================================

def procesar_texto(texto):
    """
    @brief Procesa el texto del usuario y genera una respuesta.

    Flujo:
    - Detecta intención (hora, clima o LLM)
    - Ejecuta herramientas locales si procede
    - Consulta al modelo LLM
    - Aplica fallback web si es necesario
    - Guarda la interacción en memoria persistente

    @param texto Texto del usuario.
    @return Respuesta generada.
    """
    
    global memoria

    logger.info(f"USER({USUARIO_ACTUAL}): {texto}")

    intent = detectar_intencion(texto)

    if intent == "time":
        respuesta = f"Son las {get_current_time()}"
    elif intent == "weather":
        respuesta = get_weather()
    else:
        prompt = construir_prompt(USUARIO_ACTUAL, texto)

        respuesta = ""
        if hay_internet():
            respuesta = ask_model(prompt)

        if not respuesta:
            web = web_search(texto)
            if web:
                respuesta = ask_model(web + "\n" + prompt)

        if not respuesta:
            respuesta = "No tengo respuesta."

    #  GUARDAR MEMORIA
    memoria.setdefault(USUARIO_ACTUAL, []).append({
        "user": texto,
        "bot": respuesta,
        "time": datetime.now().isoformat()
    })

    guardar_memoria(memoria)

    logger.info(f"BOT: {respuesta}")
    logger.info("-" * 50)

    return respuesta


# =========================================================
# TTS
# =========================================================

def limpiar_texto(texto: str) -> str:
    
    """
    @brief Elimina formato Markdown para que la voz suene natural.
    @param texto Texto del usuario.
    @return Respuesta generada "limpia".
    """

    texto = re.sub(r"\*\*(.*?)\*\*", r"\1", texto)
    texto = re.sub(r"\*(.*?)\*", r"\1", texto)

    texto = re.sub(r"#+\s*", "", texto)
    texto = re.sub(r"\d+\.\s*", "", texto)

    texto = re.sub(r"^\s*-\s+", " ", texto, flags=re.MULTILINE)

    texto = texto.replace("`", "")
    texto = re.sub(r"\n+", ". ", texto)

    return texto.strip()

   
def hablar(texto):
    
    """
    @brief Reproduce una frase en voz mediante síntesis TTS.

    Esta función genera audio a partir de texto usando pico2wave y
    lo reproduce mediante aplay. Se ejecuta en un hilo separado para
    no bloquear el sistema principal.

    Flujo:
    - Limpia el texto de formato innecesario
    - Genera un archivo de audio temporal (/tmp/voz.wav)
    - Reproduce el audio con el sistema
    - Actualiza el estado del robot durante la reproducción

    @param texto Texto que se desea convertir a voz.
    @return None
    """

    global robot_hablando
    global estado_texto
    global proceso_audio

    estado_texto = "Preparando voz..."

    def _run():

        global robot_hablando
        global estado_texto
        global proceso_audio

        texto_limpio = limpiar_texto(texto)

        # Generar audio
        subprocess.run(
            [
                "pico2wave",
                "-l=es-ES",
                "-w=/tmp/voz.wav",
                texto_limpio
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Ahora sí empieza a hablar
        robot_hablando = True
        estado_texto = "Hablando..."

        proceso_audio = subprocess.Popen(
            ["aplay", "/tmp/voz.wav"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        proceso_audio.wait()

        robot_hablando = False
        estado_texto = "Escuchando..."
        proceso_audio = None

    threading.Thread(target=_run, daemon=True).start()
    
    
# =========================================================
# VOSK
# =========================================================

model = vosk.Model(VOSK_MODEL_PATH)
rec = vosk.KaldiRecognizer(model, 16000)

def encontrar_micro(nombre_clave):
    """
    @brief Encuentra micro 

    Este método recibe un nombre clave para buscarlo en la lista 
    de dispositivos conectados.

    @param nombre_clave Nombre del dispositivo a buscar.
    """
    
    dispositivos = sd.query_devices()

    for i, d in enumerate(dispositivos):
        if d["max_input_channels"] > 0 and nombre_clave.lower() in d["name"].lower():
            return i
    
    return None

def detener_voz():
    
    """
    @brief Detiene la locución del robot.

    Este método detiene al robot si está hablando

    """
    
    global robot_hablando, estado_texto, proceso_audio
    
    if proceso_audio is not None:
       proceso_audio.terminate() 
       proceso_audio = None
       
    robot_hablando = False
    estado_texto = "Escuchando..."

def audio_callback(indata, frames, time_, status):
    """
    @brief Callback de entrada de audio en tiempo real.

    Este método recibe bloques de audio del micrófono y los añade
    a la cola para su posterior procesamiento con Vosk.

    @param indata Datos de audio en bruto.
    @param frames Número de frames.
    @param time_ Información temporal.
    @param status Estado del stream de audio.
    """
    
    if status:
        print("Audio status:", status)

    q_audio.put(bytes(indata))
        
        
def hilo_vosk():
    """
    @brief Hilo de reconocimiento de voz.

    Procesa continuamente los datos de audio capturados y utiliza
    el modelo Vosk para convertirlos en texto.

    Cuando detecta una frase válida, la envía a la cola de comandos.
    """
    
    global estado_texto

    while True:
        data = q_audio.get()

        #  Convertir 48kHz → 16kHz (rápido y suficiente)
        data_16k = data[::3]

        if rec.AcceptWaveform(data_16k):
            res = json.loads(rec.Result())
            texto = res.get("text", "").strip()

            if texto:
                print("Texto:", texto)
                estado_texto = f"Escuchado: {texto}"
                cola_comandos.put(texto)

        time.sleep(0.005)
        
        
# =========================================================
# RESPUESTAS
# =========================================================

def hilo_respuestas():
    """
        @brief Hilo principal de procesamiento de comandos de voz.

        Este hilo ejecuta un bucle infinito que consume texto reconocido
        desde una cola, interpreta comandos del usuario y genera respuestas
        mediante el sistema de procesamiento del asistente.

        Funciones principales:
        - Extrae texto de la cola de comandos de voz
        - Detecta órdenes de parada (ej: "calla", "para", "silencio")
        - Cancela la reproducción de voz si se solicita
        - Procesa el texto mediante el sistema inteligente (NLP/LLM)
        - Genera y reproduce la respuesta en voz

        El hilo funciona de forma continua y asíncrona, manteniendo el
        flujo conversacional del asistente activo en tiempo real.

        @note Este hilo es bloqueante internamente pero debe ejecutarse
            en un thread separado.
    """
    
    global estado_texto

    while True:
        texto = cola_comandos.get()

        texto_lower = texto.lower()

        # COMANDOS DE PARADA
        if any(x in texto_lower for x in [
            "calla",
            "para",
            "silencio",
            "cállate"
        ]):
            detener_voz()
            continue

        estado_texto = "Pensando..."
            
        try:
            respuesta = procesar_texto(texto)
        except Exception as e:
            logger.error(f"ERROR: {e}")
            respuesta = "He tenido un problema."

        hablar(respuesta)



# =========================================================
# MAIN
# =========================================================

USUARIO_ACTUAL = sys.argv[1] if len(sys.argv) > 1 else "invitado"
logger.info(f"Asistente iniciado para usuario: {USUARIO_ACTUAL}")
    
if __name__ == "__main__":

    threading.Thread(target=hilo_vosk, daemon=True).start()
    threading.Thread(target=hilo_respuestas, daemon=True).start()

    logger.info(f"Arrancando sistema para {USUARIO_ACTUAL}")
    logger.info(f"config_path: {config_path}")
    logger.info(f"url: {SERVER_URL}")

    # Saludo personalizado al inicio
    historial = memoria.get(USUARIO_ACTUAL, [])
    if historial:
        hablar(f"Hola de nuevo, {USUARIO_ACTUAL}. ¿En qué te puedo ayudar?")
    else:
        hablar(f"Hola {USUARIO_ACTUAL}, soy tu asistente. ¿En qué te puedo ayudar?")
        
    micro_id = encontrar_micro("AB13X")
    print(micro_id)

    with sd.InputStream(
        samplerate=48000,   #  antes 16000 → ERROR
        blocksize=8000,
        dtype='int16',
        channels=1,
        device=micro_id, 
        callback=audio_callback
    ):


        print("Asistente con memoria activo")

        while True:
            
            if estado_texto.startswith("Pensando"):
                puntos = (puntos + 1) % 4
                estado_texto = "Pensando" + "." * puntos
            
            
            # Parpadeo
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