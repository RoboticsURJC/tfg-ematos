# main_benchmark.py

import os
import json

from assistant.app.llm_package.core.runner import BenchmarkRunner
from assistant.app.llm_package.core.metrics import compute_stats
from assistant.app.llm_package.core.storage import load_results

from assistant.app.llm_package.models.gpt_azure import GPTAzure
from assistant.app.llm_package.models.groq_llama import GroqLlama
from assistant.app.llm_package.models.gemini import GeminiModel
from assistant.app.llm_package.models.serv_llama import LlamaCPP
from assistant.app.llm_package.models.mistral_llama import MistralServer

##
# @file main_benchmark.py
# @brief Script principal de orquestación y ejecución de la suite de benchmarks para modelos LLM.
# @details Inicializa el entorno físico de pruebas, carga la batería de prompts en memoria, 
# instancia los clientes de los modelos activos y ejecuta los ciclos de estrés guardando métricas estadísticas.
#

## Ruta absoluta del directorio base donde está alojado este script de orquestación.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

## Ruta absoluta del archivo estructurado JSON que contiene la batería de pruebas (prompts).
DATASET_PATH = os.path.join(BASE_DIR, "prompts", "dataset.json")

# Apertura y parseo seguro del dataset de prompts en formato UTF-8
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    prompts = json.load(f)

## Vector que almacena las instancias activas de los modelos que participarán en la evaluación comparativa.
models = [
    GPTAzure(),
    GroqLlama(),
    GeminiModel(),
    # LlamaCPP(),  # Instancia local comentada provisionalmente en esta tanda de pruebas
    MistralServer()
]

## Orquestador del ciclo de vida encargado de iterar y medir las inferencias sobre los modelos.
runner = BenchmarkRunner(models)

# Lanzar la suite ejecutando cada prompt un total de 3 veces consecutivas para promediar latencias
runner.run(prompts, repeats=3)

## Histórico completo de transacciones recuperado directamente desde el archivo persistente JSONL.
results = load_results()

## Diccionario con los agregados estadísticos calculados (medias de latencia, varianza, etc.) por modelo.
stats = compute_stats(results)

# Filtrar las transacciones volátiles en memoria descartando aquellas ejecuciones marcadas como FAILED
results = [r for r in results if r.get("status") == "OK"]

# =========================================================
# SALIDA DE RESULTADOS POR CONSOLA
# =========================================================
print("\n=== RESULTADOS FINALES DE RENDIMIENTO ===\n")

for model, s in stats.items():
    print(f"🔹 Modelo: {model:<15} | Métricas: {s}")