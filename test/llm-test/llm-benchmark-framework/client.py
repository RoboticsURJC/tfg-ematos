import requests
import time
import json
import os
from pathlib import Path
from datetime import datetime

# =========================
# CONFIG
# =========================
PC_URL = "http://192.168.1.:8000/generate"

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_FILE = f"results_rpi_{timestamp}.json"

REQUEST_TIMEOUT = 60


# =========================
# FIND PROMPTS
# =========================
def find_prompts_file(filename="prompts.json", start_dir="."):
    start_path = Path(start_dir).resolve()

    for path in start_path.rglob(filename):
        return str(path)

    return None


def load_prompts():
    path = find_prompts_file()

    if not path:
        print(" No se encontró prompts.json")
        exit(1)

    print(f" Usando prompts desde: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# BENCHMARK CORE
# =========================
def run_benchmark(prompts, model="llama"):
    results = []

    for i, prompt in enumerate(prompts):
        print(f"➡️ [{i+1}/{len(prompts)}] {prompt[:60]}...")

        try:
            t0 = time.perf_counter()

            r = requests.post(
                PC_URL,
                json={
                    "model": model,
                    "prompt": prompt
                },
                timeout=REQUEST_TIMEOUT
            )

            t1 = time.perf_counter()

            total_latency = t1 - t0

            # HTTP error
            if r.status_code != 200:
                results.append({
                    "id": i,
                    "model": model,
                    "prompt": prompt,
                    "status": "HTTP_ERROR",
                    "http_code": r.status_code,
                    "latency_total": total_latency
                })
                print(f" HTTP {r.status_code}")
                continue

            data = r.json()

            results.append({
                "id": i,
                "model": model,
                "prompt": prompt,
                "output": data.get("output"),
                "status": data.get("status"),
                "server_latency": data.get("latency"),
                "latency_total": total_latency,
                "timestamp": time.time()
            })

            if data.get("status") != "OK":
                print(f" Status: {data.get('status')}")

        except requests.exceptions.RequestException as e:
            results.append({
                "id": i,
                "model": model,
                "prompt": prompt,
                "status": "CONNECTION_ERROR",
                "error": str(e),
                "latency_total": None,
                "timestamp": time.time()
            })

            print(f" Error conexión: {e}")

        time.sleep(0.3)

    return results


# =========================
# SAVE
# =========================
def save_results(results):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n Resultados guardados en: {OUTPUT_FILE}")


# =========================
# SUMMARY
# =========================
def print_summary(results):
    ok = [r for r in results if r.get("status") == "OK"]

    print("\n RESUMEN")
    print(f"Total: {len(results)}")
    print(f"OK: {len(ok)}")

    if ok:
        avg_total = sum(r["latency_total"] for r in ok) / len(ok)
        avg_server = sum(r.get("server_latency", 0) for r in ok) / len(ok)

        print(f"Latencia total media: {avg_total:.3f}s")
        print(f" Latencia server media: {avg_server:.3f}s")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    prompts = load_prompts()

    model = "llama"  # cambia aquí fácilmente

    results = run_benchmark(prompts, model=model)

    save_results(results)

    print_summary(results)