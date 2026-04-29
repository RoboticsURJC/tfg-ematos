import json
import os

from core.runner import BenchmarkRunner
from core.metrics import compute_stats
from core.storage import load_results

from models.gpt_azure import GPTAzure
from models.groq_llama import GroqLlama
from models.gemini import GeminiModel
from models.serv_llama import LlamaServer

##
# @file main_experiment.py
# @brief Punto de entrada principal del sistema de benchmarking de LLMs.
#
# Este script ejecuta el flujo completo del experimento:
# - Carga del dataset de prompts
# - Inicialización de modelos (cloud y locales)
# - Ejecución del benchmark
# - Cálculo de métricas
# - Visualización de resultados finales
#

import os
import json

##
# @brief Ruta del dataset de evaluación.
#
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "prompts", "dataset.json")

##
# @brief Carga del conjunto de prompts de evaluación.
#
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    prompts = json.load(f)

##
# @brief Lista de modelos a evaluar en el experimento.
#
# Incluye modelos cloud (GPT, Groq, Gemini) y locales (LlamaServer).
#
models = [
    GPTAzure(),
    GroqLlama(),
    GeminiModel(),
    # LlamaServer(),
]

##
# @brief Inicialización del ejecutor de benchmarks.
#
runner = BenchmarkRunner(models)

##
# @brief Ejecución del experimento completo.
#
# Se ejecuta el benchmark sobre todos los prompts con repetición configurada.
#
runner.run(prompts, repeats=1)

##
# @brief Carga de resultados almacenados tras la ejecución.
#
results = load_results()

##
# @brief Cálculo de estadísticas agregadas por modelo.
#
stats = compute_stats(results)

##
# @brief Filtrado de resultados válidos.
#
results = [r for r in results if r.get("status") == "OK"]

print("\n RESULTADOS FINALES\n")

##
# @brief Impresión de métricas finales por modelo.
#
for model, s in stats.items():
    print(model, s)