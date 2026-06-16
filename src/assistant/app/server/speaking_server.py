# server-llm.py

"""
@file server-llm.py
@brief Servidor de API REST asíncrono para el despacho unificado de inferencias LLM.
@details Expone un microservicio optimizado con FastAPI que actúa como pasarela (Gateway)
entre el Pipeline principal del robot y los diferentes motores de IA (locales o en la nube),
midiendo el rendimiento físico (latencia) y abstrayendo fallos del backend.
"""

from fastapi import FastAPI
import time
import traceback
import logging
import os
from datetime import datetime

# Importación de adaptadores de la suite de modelos unificados
from llm_package.models import LlamaServer, GroqLlama, GPTAzure, GeminiModel

# Instrucción operativa para despliegue: uvicorn server-llm:app --host 0.0.0.0 --port 8000

## Instancia central de la aplicación asíncrona FastAPI.
app = FastAPI(
    title="Robot LLM Inference API",
    description="Gateway unificado para el procesamiento distribuido de modelos de lenguaje.",
    version="1.0.0"
)

# =========================================================
# LOGGING SETUP
# =========================================================

## Directorio absoluto asignado para el almacenamiento físico de trazas de inferencia.
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

## Nombre dinámico del archivo de log con estampa horaria de resolución por segundos.
log_file = os.path.join(
    LOG_DIR,
    f"llm_api_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

## Registrador (logger) dedicado a eventos de red e inferencia IA.
logger = logging.getLogger("llm-api")
logger.info("API iniciada correctamente")


# =========================================================
# REGISTRO CENTRAL DE MODELOS
# =========================================================

## Diccionario global indexado que actúa como registro de instancias de modelos LLM activos.
models = {
    "llama": LlamaServer(),
    "mistral": LlamaServer(),
    "groq": GroqLlama(),
    "gpt": GPTAzure(),
    "gemini": GeminiModel()
}

logger.info(f"Modelos cargados en el mapa de ruteo: {list(models.keys())}")


# =========================================================
# ENDPOINTS
# =========================================================

@app.get("/")
def root():
    """
    @brief Endpoint raíz (Heartbeat) para verificar la disponibilidad de la API.
    
    @return dict Diccionario de estado con la bandera de actividad del sistema.
    """
    return {"status": "server running"}


@app.post("/generate")
def generate(payload: dict):
    """
    @brief Endpoint HTTP POST: Orquesta la inferencia del modelo y audita sus tiempos.
    @details Valida la existencia del proveedor en el diccionario `models`, intercepta strings 
    vacíos para economizar recursos de red y captura excepciones a nivel de socket mediante `traceback` 
    para impedir el colapso del hilo de ejecución asíncrono (Fail-Safe).
    
    @param payload Diccionario JSON que debe cumplir estrictamente con la estructura:
           - `model` (str): Identificador clave del modelo (ej: 'groq', 'gemini').
           - `prompt` (str): Texto plano con la instrucción o contexto conversacional.
    
    @return dict Datos de salida estructurados para el Pipeline o reporte de error detallado:
            - `status` (str): Estado de la transacción ('OK' o 'ERROR').
            - `model` (str): Confirmación del motor que procesó la inferencia.
            - `output` (str): Texto plano devuelto por la IA.
            - `latency` (float): Tiempo exacto del viaje de ida y vuelta en segundos.
    """
    model_name = payload.get("model")
    prompt = payload.get("prompt")
    
    logger.info(f"Request recibido | model={model_name} | prompt_len={len(prompt) if prompt else 0}")

    # --- VALIDACIONES DE ENTRADA ---
    if model_name not in models:
        logger.warning(f"Modelo inválido o no configurado en diccionario: {model_name}")
        return {
            "status": "ERROR",
            "error": f"Modelo '{model_name}' no disponible"
        }

    if not prompt:
        logger.warning("Prompt vacío recibido en el cuerpo del payload")
        return {
            "status": "ERROR",
            "error": "Prompt vacío"
        }

    # Resolución dinámica del cliente de destino
    model = models[model_name]

    try:
        # Cronometrado de alta resolución para auditoría de latencia
        start = time.time()

        # Invocación de la rutina de generación abstracta
        output = model.generate(prompt)

        # Diferencial de tiempo de ejecución total
        latency = time.time() - start
        
        logger.info(f"OK | model={model_name} | latency={latency:.3f}s")

        return {
            "status": "OK",
            "model": model_name,
            "output": output,
            "latency": latency
        }

    except Exception as e:
        # Cláusula de salvaguarda: Impide rupturas físicas o bloqueos persistentes en el puerto web
        logger.error(f"ERROR crítico en modelo {model_name}: {str(e)}")
        logger.error(traceback.format_exc())

        return {
            "status": "ERROR",
            "error": str(e),
            "trace": traceback.format_exc()  # Volcado de la pila de errores para depuración rápida
        }