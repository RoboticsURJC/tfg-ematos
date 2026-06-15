from infra.llama_controller import ModelManager
from models.serv_llama import LlamaServer
import json
import time
import sys

##
# @file benchmark_experiment.py
# @brief Script de benchmark para ejecutar UN solo modelo seleccionado.
#

# =========================
# CONFIG
# =========================

models = {
    "llama": "/home/elisa/Downloads/llama-2-7b-chat.Q4_K_M.gguf",
    "mistral": "/home/elisa/Downloads/mistral-7b-v0.1.Q4_K_M.gguf"
}

# =========================
# SELECCIÓN DE MODELO
# =========================

if len(sys.argv) < 2:
    print("Uso: python benchmark_experiment.py [llama|mistral]")
    sys.exit(1)

SELECTED_MODEL = sys.argv[1]

if SELECTED_MODEL not in models:
    print(f"Modelo '{SELECTED_MODEL}' no válido. Opciones: {list(models.keys())}")
    sys.exit(1)

# =========================
# CARGA DE PROMPTS
# =========================

with open("prompts/dataset.json") as f:
    prompts = json.load(f)

# =========================
# INICIALIZACIÓN
# =========================

manager = ModelManager()
client = LlamaServer()

results = []

# =========================
# EJECUCIÓN DEL MODELO
# =========================

name = SELECTED_MODEL
path = models[name]

print(f"Iniciando modelo: {name}")
manager.start_model(path)

for prompt in prompts:
    start = time.time()
    output = client.generate(prompt)
    latency = time.time() - start

    results.append({
        "model": name,
        "prompt": prompt,
        "output": output,
        "latency": latency
    })

    print(f"{name} → {latency:.2f}s")

# =========================
# GUARDADO DE RESULTADOS
# =========================

output_file = f"results_{name}.json"

with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"Benchmark terminado. Resultados guardados en {output_file}")

