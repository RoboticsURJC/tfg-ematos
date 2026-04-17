import matplotlib.pyplot as plt
from core.storage import load_results
from core.metrics import compute_stats

##
# @file plots.py
# @brief Generación de visualizaciones para el análisis de benchmarks de modelos LLM.
#
# Este módulo construye un dashboard gráfico utilizando Matplotlib para comparar
# el rendimiento de distintos modelos en términos de latencia, throughput y carga.
#

##
# @brief Genera un dashboard de métricas de rendimiento de modelos LLM.
#
# Esta función crea una figura con 4 subgráficos que permiten comparar:
# - Latencia media por modelo
# - Tokens generados por segundo
# - Número de peticiones procesadas
# - Comparación de latencia mínima y máxima
#
# @param stats Diccionario de estadísticas por modelo generado por compute_stats().
#        Estructura esperada:
#        {
#            model_name: {
#                "avg_latency": float,
#                "min_latency": float,
#                "max_latency": float,
#                "num_requests": int,
#                "tokens_per_sec": float (opcional)
#            }
#        }
#
# @return None
#
def plot_metrics(stats):
    models = list(stats.keys())

    avg_latency = [stats[m]["avg_latency"] for m in models]
    tokens_per_sec = [stats[m].get("tokens_per_sec", 0) for m in models]
    num_requests = [stats[m]["num_requests"] for m in models]
    max_latency = [stats[m]["max_latency"] for m in models]
    min_latency = [stats[m]["min_latency"] for m in models]

    # Figura única tipo dashboard
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Benchmark de Modelos LLM", fontsize=16)

    # --- Latencia media ---
    axes[0, 0].bar(models, avg_latency)
    axes[0, 0].set_title("Latencia media")
    axes[0, 0].set_ylabel("segundos")
    axes[0, 0].tick_params(axis='x', rotation=45)

    # --- Tokens por segundo ---
    axes[0, 1].bar(models, tokens_per_sec)
    axes[0, 1].set_title("Tokens por segundo")
    axes[0, 1].tick_params(axis='x', rotation=45)

    # --- Número de requests ---
    axes[1, 0].bar(models, num_requests)
    axes[1, 0].set_title("Requests procesadas")
    axes[1, 0].set_ylabel("cantidad")
    axes[1, 0].tick_params(axis='x', rotation=45)

    # --- Latencia min/max (comparación interesante) ---
    axes[1, 1].bar(models, max_latency, label="Max")
    axes[1, 1].bar(models, min_latency, label="Min")
    axes[1, 1].set_title("Latencia min vs max")
    axes[1, 1].legend()
    axes[1, 1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.show()


##
# @brief Punto de entrada del script de visualización.
#
# Carga los resultados almacenados, calcula estadísticas agregadas
# y genera el dashboard de comparación de modelos.
#
if __name__ == "__main__":
    results = load_results()
    stats = compute_stats(results)

    plot_metrics(stats)