import requests
import time
import json
import os
import logging
from pathlib import Path
from datetime import datetime

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
# CONFIG LOAD
# =========================================================

curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "config.json")

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

PC_URL = config["pc_url"]

TIMEOUT = 90

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_FILE = f"results_rpi_{timestamp}.json"

TIMEOUT = 90  #  importante para Gemini/GPT


# =========================================================
# CONFIGURACIÓN DEL LOG
# =========================================================

LOG_DIR = os.path.join(curr_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"benchmark_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("llm-benchmark")

logger.info("Chat iniciado")

# =========================================================
# BUSQUEDA EN INTERNET (DUCKDUCKGO SIMPLE SCRAPER)
# =========================================================

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
# LLAMADA AL MODELO
# =========================================================

def build_prompt(user_text):
    return f"""
    {PROMPT_DEL_SISTEMA}

    Usuario: {user_text}
    Asistente:
    """
    
def ask_model(prompt):
    """
    @brief Llama al modelo LLM del servidor.
    """
    
    full_prompt = PROMPT_DEL_SISTEMA + "\n\nUsuario: " + prompt
    r = requests.post(
        PC_URL,
        json={"model": "groq", "prompt": build_prompt(prompt)},
        timeout=TIMEOUT
    )

    try:
        return r.json()
    except:
        return {"output": "", "status": "ERROR"}


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


def mapeo_acciones(text: str):
    """
    @brief En funcio de la pregunta recibida devuelve una intencion
    """
    
    t = text.lower()

    if any(x in t for x in ["hora", "qué hora", "que hora", "dime la hora"]):
        return "time"

    if any(x in t for x in ["clima", "tiempo", "qué tiempo", "que tiempo"]):
        return "weather"

    return "llm"


def handle_tool(intent, user_text):
    """
    @brief Segun la intención, genera la respuesta
    """
    if intent == "time":
        return f"Ahora son las {get_current_time()}."

    if intent == "weather":
        return get_weather("Madrid")

    return None

# =========================================================
# CHAT LOOP INTELIGENTE
# =========================================================
##
# @brief Bucle principal del asistente conversacional.
#
# Este bucle gestiona la interacción en tiempo real con el usuario.
# Orquesta tres capas de respuesta:
#   1. Herramientas locales (hora, clima, llamadas)
#   2. Modelo LLM (Groq / Llama 3.3)
#   3. Búsqueda web como fallback en caso de desconocimiento
#
# El sistema prioriza respuestas rápidas mediante herramientas locales
# antes de consultar al modelo o a internet.
#
def chat_loop():
    print("\n Chat con herramientas + LLM + web fallback")
    print("Escribe 'exit' para salir\n")

    while True:
        
        ##
        # @brief Entrada del usuario en tiempo real
        #
        prompt = input(" Tú: ")

        ##
        # @brief Condición de salida del bucle
        #
        if prompt.lower() in ["exit", "quit"]:
            logger.info("Chat finalizado")
            break

        # =====================================================
        # 1. ROUTER DE INTENCIONES (NUEVO)
        # =====================================================
        ##
        # @brief Clasifica la intención del usuario
        #
        # Posibles valores:
        #   - time
        #   - weather
        #   - llm (por defecto)
        #
        intent = mapeo_acciones(prompt)

        tool_output = None

        # =====================================================
        # 2. HERRAMIENTAS LOCALES (hora, clima, llamadas)
        # =====================================================
        
        ##
        # @brief Respuesta mediante herramientas deterministas
        #
        # Estas herramientas no dependen del LLM y son instantáneas.
        #
        
        if intent == "time":
            tool_output = get_current_time()

        elif intent == "weather":
            tool_output = get_weather("Madrid")

        ##
        # @brief Si se ejecuta una herramienta, se devuelve directamente
        #
        if tool_output:
            print(f"\n {tool_output}\n")
            logger.info(f"USER: {prompt}")
            logger.info(f"TOOL RESPONSE: {tool_output}")
            logger.info("-" * 60)
            continue

        # =====================================================
        # 3. CONSULTA AL MODELO LLM
        # =====================================================

        ##
        # @brief Llamada al modelo de lenguaje principal
        #
        # Usa Groq (Llama 3.3) como backend principal.
        #
        start = time.perf_counter()
        response = ask_model(prompt)
        output = response.get("output", "")
        latency = time.perf_counter() - start

        logger.info(f"USER: {prompt}")
        logger.info(f"AI: {output}")

        # =====================================================
        # 4. DETECCIÓN DE DESCONOCIMIENTO
        # =====================================================

        ##
        # @brief Detecta si el modelo no tiene suficiente información
        #
        # Si ocurre, se activa el fallback a búsqueda web.
        #
        needs_web = (
            not output
            or "no sé" in output.lower()
            or "no tengo información" in output.lower()
            or len(output) < 10
        )

        # =====================================================
        # 5. FALLBACK WEB
        # =====================================================

        ##
        # @brief Enriquecimiento con información de internet
        #
        # Se utiliza si el modelo no puede responder correctamente.
        #
        if needs_web:
            logger.info("Activando búsqueda web...")

            web_data = web_search(prompt)

            if web_data:
                enriched_prompt = f"""
                            Usa esta información para responder de forma clara y en español:

                            {web_data}

                            Pregunta: {prompt}
                            """

                response = ask_model(enriched_prompt)
                output = response.get("output", "")

        ## =====================================================
        # 6. SALIDA FINAL
        # =====================================================

        ##
        # @brief Respuesta final mostrada al usuario
        #
        print(f"\n {output}\n")

        logger.info(f"FINAL RESPONSE: {output}")
        logger.info(f"LATENCY: {latency:.3f}s")
        logger.info("-" * 60)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    chat_loop()