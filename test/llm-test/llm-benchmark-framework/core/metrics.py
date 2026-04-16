import statistics

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

            # tokens por segundo (clave 🔥)
            tokens_per_sec = total_tokens / sum(latencies) if sum(latencies) > 0 else 0

            result.update({
                "avg_tokens": avg_tokens,
                "total_tokens": total_tokens,
                "tokens_per_sec": tokens_per_sec
            })

        output[model] = result

    return output