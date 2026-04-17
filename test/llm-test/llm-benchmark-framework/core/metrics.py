import statistics

##
# @file metrics.py
# @brief Cálculo de métricas agregadas para resultados de benchmarking de modelos LLM.
#

##
# @brief Calcula estadísticas por modelo a partir de resultados de ejecución.
#
# Esta función procesa una lista de resultados de inferencia de modelos LLM,
# filtrando ejecuciones correctas y agrupando métricas por modelo.
#
# Se calculan métricas como:
# - Latencia media, mínima, máxima y desviación estándar
# - Número de peticiones válidas
# - Tokens medios, totales y tokens por segundo (si están disponibles)
#
# @param results Lista de diccionarios con resultados de ejecución.
#        Cada elemento debe contener al menos:
#        - "model": nombre del modelo
#        - "status": estado de ejecución ("OK" para válidos)
#        - "latency_total": tiempo total de inferencia
#        - "tokens_total": número de tokens generados (opcional)
#
# @return dict Diccionario con estadísticas agregadas por modelo.
#         Estructura:
#         {
#             model_name: {
#                 "avg_latency": float,
#                 "min_latency": float,
#                 "max_latency": float,
#                 "std_latency": float,
#                 "num_requests": int,
#                 "avg_tokens": float (opcional),
#                 "total_tokens": int (opcional),
#                 "tokens_per_sec": float (opcional)
#             }
#         }
#
def compute_stats(results):
    stats = {}

    for r in results:
        model = r.get("model")

        # Ignorar fallos
        if r.get("status") != "OK":
            continue

        latency = r.get("latency_total")
        tokens = r.get("tokens_total")

        if latency is None:
            continue

        if model not in stats:
            stats[model] = {
                "latencies": [],
                "tokens": []
            }

        stats[model]["latencies"].append(latency)

        if tokens is not None:
            stats[model]["tokens"].append(tokens)

    output = {}

    for model, data in stats.items():
        latencies = data["latencies"]
        tokens = data["tokens"]

        if len(latencies) == 0:
            continue

        avg_latency = sum(latencies) / len(latencies)

        result = {
            "avg_latency": avg_latency,
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "std_latency": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            "num_requests": len(latencies)
        }

        # métricas de tokens (si existen)
        if len(tokens) > 0:
            total_tokens = sum(tokens)
            avg_tokens = total_tokens / len(tokens)

            # tokens por segundo (clave )
            tokens_per_sec = total_tokens / sum(latencies) if sum(latencies) > 0 else 0

            result.update({
                "avg_tokens": avg_tokens,
                "total_tokens": total_tokens,
                "tokens_per_sec": tokens_per_sec
            })

        output[model] = result

    return output