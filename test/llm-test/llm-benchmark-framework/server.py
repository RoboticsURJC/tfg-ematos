# server.py (en el PC)

from fastapi import FastAPI
import time

app = FastAPI()

# importa tus modelos reales
from models.gpt_azure import GPTAzure
from models.groq_llama import GroqLlama

models = {
    "gpt": GPTAzure(),
    "groq": GroqLlama()
}

@app.post("/generate")
def generate(payload: dict):
    model_name = payload["model"]
    prompt = payload["prompt"]

    model = models[model_name]

    start = time.time()
    output = model.generate(prompt)  # tu lógica actual
    latency = time.time() - start

    return {
        "output": output,
        "latency": latency
    }