# assistant.py

import requests
from datetime import datetime

from app.core.memory import (
    cargar_memoria,
    guardar_memoria,
    agregar_interaccion,
    obtener_historial
)
from app.core.intent import detectar_intencion

##
# @file assistant.py
# @brief Pipeline principal del asistente virtual.
# @details Este módulo coordina secuencialmente la detección de intención, 
# la construcción de prompts dinámicos, las llamadas HTTP al modelo LLM remoto,
# la ejecución de herramientas locales y el almacenamiento de la memoria persistente.
#


# =========================
# CONFIG
# =========================

## Tiempo máximo de espera (en segundos) para las peticiones HTTP del sistema.
TIMEOUT = 90

## URL del API Gateway o servidor LLM local/remoto para la generación de texto.
PC_URL = "http://192.168.1.96:8000/generate"


# =========================
# PROMPT BASE
# =========================

## Prompt principal del sistema que define las directrices éticas y de comportamiento del asistente.
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

## Diccionario global de memoria conversacional cargado desde el almacenamiento en disco al inicializar el módulo.
memoria = cargar_memoria()


# =========================
# PROMPT BUILDER
# =========================

def construir_prompt(usuario, mensaje):
    """
    @brief Construye el prompt estructurado completo para enviar al modelo de lenguaje.
    @details Aglutina las directrices fijas del sistema, el historial de los últimos turnos 
    del usuario en particular y la entrada actual para mantener el contexto.
    
    @param usuario Nombre o identificador único del usuario activo.
    @param mensaje Mensaje o transcripción de voz actual remitida por el usuario.
    
    @return str Prompt formateado multilínea listo para la inferencia de la IA.
    """
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

def ask_model(prompt: str) -> str:
    """
    @brief Envía el prompt empaquetado al modelo de lenguaje a través de una petición HTTP POST.
    @details Realiza la llamada al backend configurado, desempaqueta la respuesta JSON y gestiona 
    las excepciones y variaciones en el formato de salida de algunos servidores de inferencia.
    
    @param prompt Texto consolidado con instrucciones e historial que se enviará al modelo.
    
    @return str Texto de salida generado por la Inteligencia Artificial.
    @retval "" Retorna una cadena vacía en caso de que ocurra un error de red o timeout.
    """
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

        # Salvaguarda para backends que encapsulan el texto de salida en listas
        if isinstance(output, list):
            output = output[0]

        return str(output)

    except Exception:
        return ""


# =========================
# TOOLS LOCALES
# =========================

def get_time():
    """
    @brief Obtiene la hora local actual del sistema operativo de la Raspberry Pi o servidor.
    
    @return str Cadena de texto formateada con precisión de segundos ("HH:MM:SS").
    """
    return datetime.now().strftime("%H:%M:%S")


def get_weather(city="Madrid"):
    """
    @brief Consulta las condiciones meteorológicas en tiempo real de una ciudad.
    @details Realiza un flujo encadenado de peticiones HTTP utilizando las APIs públicas de Open-Meteo:
    1. Geocoding API para transformar el nombre de la ciudad en coordenadas geográficas.
    2. Weather API para obtener la temperatura y velocidad del viento actuales mediante dichas coordenadas.
    
    @param city Nombre textual de la localidad o término de búsqueda a consultar.
    
    @return str Cadena resumida lista para el TTS con los grados y viento de la ciudad.
    @retval str Mensaje alternativo de error amigable si falla la resolución o conexión de red.
    """
    try:
        # Obtener coordenadas geográficas mediante el nombre de la ciudad
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city}&count=1"
        ).json()

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        # Obtener el reporte climático actual utilizando la latitud y longitud calculadas
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

def procesar_texto(usuario: str, texto: str) -> str:
    """
    @brief Orquesta el flujo principal (Pipeline) para procesar un mensaje del usuario.
    @details Ejecuta la toma de decisiones del robot siguiendo cuatro etapas claras:
    1. Invoca el módulo analítico para detectar la intención subyacente del texto.
    2. Bifurca el flujo ejecutando una herramienta local rápida (hora, clima) o delegando al LLM.
    3. Anexa el par de interacción pregunta/respuesta a la estructura de datos en memoria.
    4. Sincroniza y escribe la actualización en el almacenamiento persistente en disco.
    
    @param usuario Nombre o identificador único del usuario que emite el mensaje.
    @param texto Transcripción o entrada de texto limpia del usuario.
    
    @return str Respuesta final resuelta que el asistente debe vocalizar o mostrar en pantalla.
    """
    global memoria

    # 1. Detectar intención
    intent = detectar_intencion(texto)

    # 2. Ejecutar herramienta local o LLM según corresponda
    if intent == "time":
        respuesta = f"Son las {get_time()}"

    elif intent == "weather":
        respuesta = get_weather()

    else:
        prompt = construir_prompt(usuario, texto)
        respuesta = ask_model(prompt)

        if not respuesta:
            respuesta = "No tengo respuesta ahora mismo."

    # 3. Guardar interacción en memoria y persistir en disco
    memoria = agregar_interaccion(
        memoria,
        usuario,
        texto,
        respuesta
    )

    guardar_memoria(memoria)

    return respuesta