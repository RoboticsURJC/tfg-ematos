import json
import os
from datetime import datetime

##
# @file storage.py
# @brief Módulo de almacenamiento y carga de resultados de benchmarking.
#
# Este módulo gestiona la persistencia de los resultados generados durante
# la evaluación de modelos LLM, utilizando un formato JSON Lines (JSONL),
# donde cada línea corresponde a una ejecución independiente.
#

##
# @brief Ruta del archivo de almacenamiento de resultados.
#
# El archivo se almacena en la carpeta `results/` del proyecto.
#
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE_DIR, "..", "results", "results.jsonl")

##
# @brief Carga todos los resultados almacenados en disco.
#
# Lee el archivo JSONL línea por línea y reconstruye la lista de resultados.
#
# @return list Lista de diccionarios con los resultados almacenados.
#         Si el archivo no existe, devuelve una lista vacía.
#
def load_results():
    if not os.path.exists(FILE):
        return []

    results = []
    with open(FILE, "r", encoding="utf-8") as f:
        for line in f:
            results.append(json.loads(line))
    return results

##
# @brief Guarda un nuevo resultado en el archivo de almacenamiento.
#
# Añade automáticamente un timestamp en formato ISO-8601 y escribe el
# resultado en modo append dentro del archivo JSONL.
#
# @param result Diccionario con los datos del experimento.
#        Se recomienda incluir campos como:
#        - model: nombre del modelo
#        - prompt: entrada utilizada
#        - response: salida generada
#        - latency_total: tiempo de ejecución
#        - status: estado de ejecución
#
def save_result(result):
    result["timestamp"] = datetime.now().isoformat()

    os.makedirs(os.path.dirname(FILE), exist_ok=True)

    with open(FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")