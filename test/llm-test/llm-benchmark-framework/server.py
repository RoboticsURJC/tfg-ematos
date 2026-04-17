from fastapi import FastAPI
import time
import traceback

app = FastAPI()

##
# @file api_server.py
# @brief API REST para la ejecución de modelos LLM.
#
# Este servicio expone un endpoint HTTP que permite ejecutar distintos modelos
# de lenguaje (locales y cloud) de forma unificada, gestionando la inferencia,
# medición de latencia y manejo de errores.
#

# IMPORTA SOLO MODELOS LOCALES Y CLOUD
from models.serv_llama import LlamaServer
from models.groq_llama import GroqLlama
from models.gpt_azure import GPTAzure
from models.gemini import GeminiModel

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

    # validaciones básicas
    if model_name not in models:
        return {
            "status": "ERROR",
            "error": f"Modelo '{model_name}' no disponible"
        }

    if not prompt:
        return {
            "status": "ERROR",
            "error": "Prompt vacío"
        }

    model = models[model_name]

    try:
        start = time.time()

        output = model.generate(prompt)
        print("MODELS DISPONIBLES:", models.keys(), flush=True)

        latency = time.time() - start

        return {
            "status": "OK",
            "model": model_name,
            "output": output,
            "latency": latency
        }

    except Exception as e:
        # nunca romper el server
        return {
            "status": "ERROR",
            "error": str(e),
            "trace": traceback.format_exc()
        }