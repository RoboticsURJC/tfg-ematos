from fastapi import FastAPI
import time
import traceback

from models.serv_llama import LlamaServer
from models.gpt_azure import GPTAzure
from models.groq_llama import GroqLlama
from models.gemini import GeminiModel

app = FastAPI()

# =========================
# MODELOS
# =========================
models = {
    "llama": LlamaServer(),
    "mistral": LlamaServer(),  # si lo separas luego → otro puerto
    "gpt": GPTAzure(),
    "groq": GroqLlama(),
    "gemini": GeminiModel()
}


@app.get("/")
def root():
    return {"status": "server running"}


@app.post("/generate")
def generate(payload: dict):
    model_name = payload.get("model")
    prompt = payload.get("prompt")

    if model_name not in models:
        return {"status": "ERROR", "error": "modelo no disponible"}

    if not prompt:
        return {"status": "ERROR", "error": "prompt vacío"}

    model = models[model_name]

    try:
        t0 = time.perf_counter()
        output = model.generate(prompt)
        t1 = time.perf_counter()

        return {
            "status": "OK",
            "model": model_name,
            "output": output,
            "latency": t1 - t0
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "trace": traceback.format_exc()
        }