import requests
import time

PC_URL = "http://192.168.1.X:8000/generate"

def run_benchmark(prompts, model="gpt"):
    results = []

    for p in prompts:
        start = time.time()

        r = requests.post(
            PC_URL,
            json={
                "model": model,
                "prompt": p
            }
        )

        data = r.json()

        total_latency = time.time() - start

        results.append({
            "model": model,
            "latency_total": total_latency,      # incluye red + PC
            "server_latency": data["latency"],   # solo inferencia PC
            "response": data["output"]
        })

    return results