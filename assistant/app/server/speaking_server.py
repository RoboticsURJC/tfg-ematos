from fastapi import FastAPI
import time
import traceback
import logging
import os
from datetime import datetime

# lanzar con  uvicorn server-llm:app --host 0.0.0.0 --port 8000

app = FastAPI()

# =========================================================
# LOGGING SETUP
# =========================================================

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

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

logger = logging.getLogger("llm-api")

logger.info(" API iniciada correctamente")


##
# @file api_server.py
# @brief API REST para la ejecución de modelos LLM.
#
# Este servicio expone un endpoint HTTP que permite ejecutar distintos modelos
# de lenguaje (locales y cloud) de forma unificada, gestionando la inferencia,
# medición de latencia y manejo de errores.
#

# IMPORTA SOLO MODELOS LOCALES Y CLOUD
from llm_package.models import LlamaServer, GroqLlama, GPTAzure, GeminiModel
# from llm_package.models import LlamaServer
# from models.serv_llama import LlamaServer
# from models.groq_llama import GroqLlama
# from models.gpt_azure import GPTAzure
# from models.gemini import GeminiModel

##
# @brief Registro central de modelos disponibles en la API.
#
# Cada entrada representa un modelo LLM accesible desde el endpoint /generate.
#
models = {
    "llama": LlamaServer(),
    "mistral": LlamaServer(),
    "groq": GroqLlama(),
    "gpt": GPTAzure(),
    "gemini": GeminiModel()
}

logger.info(f"Modelos cargados: {list(models.keys())}")


##
# @brief Endpoint raíz de la API.
#
# @return dict Estado del servidor.
#
@app.get("/")
def root():
    return {"status": "server running"}

##
# @brief Genera texto usando el modelo seleccionado.
#
# Este endpoint recibe un modelo y un prompt, ejecuta la inferencia y devuelve:
# - la respuesta generada
# - la latencia de ejecución
# - el estado de la petición
#
# @param payload Diccionario JSON con:
#        - model: nombre del modelo a utilizar
#        - prompt: texto de entrada
#
# @return dict Resultado de la generación o error en caso de fallo.
#
@app.post("/generate")
def generate(payload: dict):
    model_name = payload.get("model")
    prompt = payload.get("prompt")
    
    logger.info(f"Request recibido | model={model_name} | prompt_len={len(prompt) if prompt else 0}")


    # validaciones básicas
    if model_name not in models:
        logger.warning(f"Modelo inválido: {model_name}")

        return {
            "status": "ERROR",
            "error": f"Modelo '{model_name}' no disponible"
        }

    if not prompt:
        logger.warning("Prompt vacío recibido")

        return {
            "status": "ERROR",
            "error": "Prompt vacío"
        }

    model = models[model_name]

    try:
        start = time.time()

        output = model.generate(prompt)

        latency = time.time() - start
        
        logger.info(f"OK | model={model_name} | latency={latency:.3f}s")


        return {
            "status": "OK",
            "model": model_name,
            "output": output,
            "latency": latency
        }

    except Exception as e:
        
        logger.error(f"ERROR en modelo {model_name}: {str(e)}")
        logger.error(traceback.format_exc())

        # nunca romper el server
        return {
            "status": "ERROR",
            "error": str(e),
            "trace": traceback.format_exc()
        }