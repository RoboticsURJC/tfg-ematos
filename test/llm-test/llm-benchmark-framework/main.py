import json

from core.runner import BenchmarkRunner
from core.metrics import compute_stats
from core.storage import load_results

from models.gpt_azure import GPTAzure
from models.groq_llama import GroqLlama
from models.gemini import GeminiModel
from models.serv_llama import LlamaCPP
from models.mistral_llama import MistralServer


import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "prompts", "dataset.json")

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    prompts = json.load(f)



models = [
    GPTAzure(),
    GroqLlama(),
    GeminiModel(),
    # LlamaCPP(),
    MistralServer()
]


runner = BenchmarkRunner(models)

runner.run(prompts, repeats=1)


results = load_results()
stats = compute_stats(results)
results = [r for r in results if r.get("status") == "OK"]
print("\n📊 RESULTADOS FINALES\n")

for model, s in stats.items():
    print(model, s)