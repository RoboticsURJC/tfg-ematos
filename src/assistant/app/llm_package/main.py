import json

from assistant.app.llm_package.core.runner import BenchmarkRunner
from assistant.app.llm_package.core.metrics import compute_stats
from assistant.app.llm_package.core.storage import load_results

from assistant.app.llm_package.models.gpt_azure import GPTAzure
from assistant.app.llm_package.models.groq_llama import GroqLlama
from assistant.app.llm_package.models.gemini import GeminiModel
from assistant.app.llm_package.models.serv_llama import LlamaCPP
from assistant.app.llm_package.models.mistral_llama import MistralServer


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

runner.run(prompts, repeats=3)


results = load_results()
stats = compute_stats(results)
results = [r for r in results if r.get("status") == "OK"]
print("\n RESULTADOS FINALES\n")

for model, s in stats.items():
    print(model, s)