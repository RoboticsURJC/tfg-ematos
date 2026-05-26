import requests
from datetime import datetime

from app.core.memory import (
    cargar_memoria,
    guardar_memoria,
    agregar_interaccion,
    obtener_historial
)

from app.core.intent import detectar_intencion


## @file pipeline.py
#  @brief Pipeline principal del asistente virtual.
#
#  Este módulo coordina:
#   - detección de intención
#   - construcción de prompts
#   - llamadas al modelo LLM
#   - herramientas locales
#   - almacenamiento de memoria


# =========================
# CONFIG
# =========================

## @brief Tiempo máximo de espera para peticiones HTTP.
TIMEOUT = 90

## @brief URL del servidor LLM local/remoto.
PC_URL = "http://192.168.1.96:8000/generate"


# =========================
# PROMPT BASE
# =========================

## @brief Prompt principal del sistema.
#
#  Define el comportamiento general del asistente.
PROMPT_DEL_SISTEMA = """
Eres un asistente virtual diseñado para ayudar a personas mayores.

Reglas:
- Español siempre
- Lenguaje claro y amable
- Paso a paso si hace falta
- Sin tecnicismos
"""


# =========================
# MEMORIA GLOBAL
# =========================

## @brief Memoria cargada desde disco.
memoria = cargar_memoria()


# =========================
# PROMPT BUILDER
# =========================

## @brief Construye el prompt completo para el LLM.
#
#  Incluye:
#   - prompt del sistema
#   - historial reciente
#   - mensaje actual del usuario
#
#  @param usuario Nombre o identificador del usuario.
#  @param mensaje Mensaje actual del usuario.
#
#  @return str Prompt completo listo para enviar al modelo.
def construir_prompt(usuario, mensaje):
    historial = obtener_historial(memoria, usuario)

    contexto = ""

    for h in historial:
        contexto += (
            f"Usuario: {h['user']}\n"
            f"Asistente: {h['bot']}\n"
        )

    return f"""
{PROMPT_DEL_SISTEMA}

Historial:
{contexto}

Usuario: {mensaje}
Asistente:
"""


# =========================
# LLM CALL
# =========================

## @brief Envía un prompt al modelo de lenguaje.
#
#  Realiza una petición HTTP al servidor configurado
#  y devuelve la respuesta generada.
#
#  @param prompt Texto completo enviado al modelo.
#
#  @return str Respuesta generada por el modelo.
#  @retval "" Si ocurre un error.
def ask_model(prompt: str) -> str:
    try:
        r = requests.post(
            PC_URL,
            json={
                "model": "groq",
                "prompt": prompt
            },
            timeout=TIMEOUT
        )

        data = r.json()
        output = data.get("output", "")

        # Algunos backends devuelven listas
        if isinstance(output, list):
            output = output[0]

        return str(output)

    except Exception:
        return ""


# =========================
# TOOLS LOCALES
# =========================

## @brief Obtiene la hora actual del sistema.
#
#  @return str Hora actual en formato HH:MM:SS.
def get_time():
    return datetime.now().strftime("%H:%M:%S")


## @brief Obtiene el clima actual de una ciudad.
#
#  Utiliza:
#   - Open-Meteo Geocoding API
#   - Open-Meteo Weather API
#
#  @param city Nombre de la ciudad.
#
#  @return str Información meteorológica resumida.
#  @retval str Mensaje de error si falla la consulta.
def get_weather(city="Madrid"):
    try:
        # Obtener coordenadas
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city}&count=1"
        ).json()

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        # Obtener clima actual
        weather = requests.get(
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}"
            f"&longitude={lon}"
            f"&current_weather=true"
        ).json()

        temp = weather["current_weather"]["temperature"]
        wind = weather["current_weather"]["windspeed"]

        return (
            f"En {city} hay "
            f"{temp}°C y viento de {wind} km/h"
        )

    except Exception:
        return "No puedo obtener el clima ahora mismo."


# =========================
# MAIN PIPELINE
# =========================

## @brief Procesa un mensaje del usuario.
#
#  Flujo principal:
#   1. Detectar intención
#   2. Ejecutar herramienta local o LLM
#   3. Guardar interacción en memoria
#   4. Devolver respuesta
#
#  @param usuario Nombre o identificador del usuario.
#  @param texto Texto introducido por el usuario.
#
#  @return str Respuesta final del asistente.
def procesar_texto(usuario: str, texto: str) -> str:
    global memoria

    # Detectar intención
    intent = detectar_intencion(texto)

    # Herramienta de hora
    if intent == "time":
        respuesta = f"Son las {get_time()}"

    # Herramienta de clima
    elif intent == "weather":
        respuesta = get_weather()

    # Consulta general al LLM
    else:
        prompt = construir_prompt(usuario, texto)

        respuesta = ask_model(prompt)

        if not respuesta:
            respuesta = "No tengo respuesta ahora mismo."

    # Guardar interacción en memoria
    memoria = agregar_interaccion(
        memoria,
        usuario,
        texto,
        respuesta
    )

    guardar_memoria(memoria)

    return respuesta