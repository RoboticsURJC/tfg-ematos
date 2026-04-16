import requests
import time
import json
import os


PC_URL = "http://192.168.1.X:8000/generate"


def run_benchmark(prompts, model="gpt"):
    """
    Ejecuta benchmark contra el servidor PC.
    
    Args:
        prompts (list[str]): lista de prompts
        model (str): nombre del modelo en el server
    
    Returns:
        list[dict]: resultados estructurados
    """

    results = []

    for p in prompts:
        start = time.time()

        try:
            r = requests.post(
                PC_URL,
                json={
                    "model": model,
                    "prompt": p
                },
                timeout=60
            )

            data = r.json()
            total_latency = time.time() - start

            results.append({
                "model": model,
                "prompt": p,
                "latency_total": total_latency,
                "server_latency": data.get("latency"),
                "response": data.get("output"),
                "status": "OK"
            })

        except Exception as e:
            results.append({
                "model": model,
                "prompt": p,
                "latency_total": None,
                "server_latency": None,
                "response": None,
                "status": "ERROR",
                "error": str(e)
            })

    return results


def run_from_json(prompts_path, model="gpt"):
    """
    Ejecuta benchmark leyendo prompts desde un JSON
    y guarda automáticamente resultados en fichero.
    """

    # --- cargar prompts ---
    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)

    # --- ejecutar benchmark ---
    results = run_benchmark(prompts, model=model)

    # --- guardar resultados ---
    timestamp = int(time.time())
    output_file = f"results_{model}_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✔ Resultados guardados en {output_file}")

    return results


# -----------------------------
# ejecución directa
# -----------------------------
if __name__ == "__main__":

    # ejemplo: prompts en archivo JSON
    prompts_file = "prompts.json"

    if not os.path.exists(prompts_file):
        print(" No existe prompts.json")
        exit(1)

    results = run_from_json(prompts_file, model="gpt")

    # resumen rápido en consola
    ok_results = [r for r in results if r["status"] == "OK"]

    print("\n RESUMEN")
    print(f"Total requests: {len(results)}")
    print(f"OK: {len(ok_results)}")

    if ok_results:
        avg_latency = sum(r["latency_total"] for r in ok_results) / len(ok_results)
        print(f"Latencia media: {avg_latency:.3f}s")