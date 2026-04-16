from fastapi import FastAPI
import time

from models.gpt_azure import GPTAzure
from models.groq_llama import GroqLlama

app = FastAPI()

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
    output = model.generate(prompt)
    latency = time.time() - start

    return {
        "output": output,
        "latency": latency
    }