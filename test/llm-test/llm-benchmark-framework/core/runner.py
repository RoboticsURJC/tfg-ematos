import time
from core.storage import save_result

##
# @file benchmark_runner.py
# @brief Ejecutor principal de benchmarks para modelos LLM.
#
# Este módulo se encarga de coordinar la ejecución de pruebas de rendimiento
# sobre múltiples modelos y prompts, registrando métricas como latencia,
# respuestas generadas y estado de ejecución.
#

##
# @class BenchmarkRunner
# @brief Orquestador del proceso de benchmarking de modelos LLM.
#
# Gestiona la ejecución de múltiples modelos sobre un conjunto de prompts,
# midiendo tiempos de respuesta y almacenando resultados de forma persistente.
#
class BenchmarkRunner:

    ##
    # @brief Constructor del ejecutor de benchmarks.
    #
    # @param models Lista de modelos que serán evaluados.
    #
    def __init__(self, models):
        self.models = models

    ##
    # @brief Ejecuta de forma segura un modelo con un prompt.
    #
    # Este método envuelve la ejecución del modelo para evitar crashes
    # y registrar información de rendimiento como latencia total.
    #
    # @param model Modelo LLM a evaluar.
    # @param prompt Texto de entrada para el modelo.
    #
    # @return dict Diccionario con:
    #         - model: nombre del modelo
    #         - prompt: entrada utilizada
    #         - response: salida generada (o None si falla)
    #         - latency_total: tiempo total de ejecución
    #         - status: "OK" o "FAILED"
    #         - error: mensaje de error (si aplica)
    #
    def safe_run(self, model, prompt):
        try:
            start = time.time()

            response, extra = model.benchmark(prompt)

            end = time.time()

            latency = end - start

            return {
                "model": model.name,
                "prompt": prompt,
                "response": response,
                "latency_total": latency,
                "status": "OK",
            }

        except Exception as e:
            return {
                "model": model.name,
                "prompt": prompt,
                "response": None,
                "latency_total": None,
                "status": "FAILED",
                "error": str(e)
            }

    ##
    # @brief Ejecuta el benchmark completo sobre todos los modelos y prompts.
    #
    # Este método itera sobre múltiples rondas, prompts y modelos,
    # ejecutando pruebas de rendimiento y almacenando resultados.
    #
    # Flujo:
    # 1. Itera sobre rondas de repetición
    # 2. Itera sobre prompts
    # 3. Ejecuta cada modelo de forma segura
    # 4. Guarda resultados en almacenamiento persistente
    #
    # @param prompts Lista de prompts de evaluación.
    # @param repeats Número de veces que se repite el benchmark completo.
    #
    # @return list Lista de resultados generados durante la ejecución.
    #
    def run(self, prompts, repeats=1):
        results = []

        for i in range(repeats):
            print(f"\nROUND {i+1}/{repeats}")

            for prompt in prompts:
                print(f"\n Prompt: {prompt[:60]}...")

                for model in self.models:
                    print(f"▶ {model.name}")

                    result = self.safe_run(model, prompt)

                    results.append(result)

                    save_result(result)

                    # pequeño cooldown para evitar saturación
                    time.sleep(0.5)

        return results