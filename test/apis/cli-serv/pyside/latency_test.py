import requests
import time
import statistics
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime

# === CONFIGURACIÓN ===
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)
SERVER_URL = config["server_url"]

DURATION = 300  # segundos (5 min)
INTERVAL = 1    # intervalo entre pruebas
latencies = []

# === PREPARAR ARCHIVOS ===
os.makedirs("results", exist_ok=True)
date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
txt_file = f"results/latencies_{date_time}.txt"
csv_file = f"results/latencies_{date_time}.csv"

# === INICIO ===
print(f"\nMidiendo latencia hacia: {SERVER_URL}/latency durante {DURATION//60} min...\n")

with open(txt_file, "w") as f:
    f.write(f"Latency measurements towards {SERVER_URL}/latency\n")
    f.write(f"Start Date: {date_time}\n\n")

start = time.time()
while time.time() - start < DURATION:
    try:
        t0 = time.time()
        r = requests.get(f"{SERVER_URL}/latency", timeout=3)
        t1 = time.time()

        if r.ok:
            latency = (t1 - t0) * 1000
            latencies.append(latency)

            # Promedio móvil (últimos 10)
            avg_10 = statistics.mean(latencies[-10:]) if len(latencies) >= 10 else statistics.mean(latencies)

            color = "\033[92m" if latency < 500 else ("\033[93m" if latency < 1500 else "\033[91m")
            print(f"{color}{datetime.now().strftime('%H:%M:%S')} - {latency:.2f} ms (avg10={avg_10:.1f})\033[0m")

            f.write(f"{datetime.now().strftime('%H:%M:%S')} - {latency:.2f} ms\n")
        else:
            print("\033[91mError in server response\033[0m")
            f.write(f"{datetime.now().strftime('%H:%M:%S')} - Error in response\n")
    except requests.exceptions.RequestException:
        print("\033[91mConnection failure\033[0m")
        f.write(f"{datetime.now().strftime('%H:%M:%S')} - Connection failure\n")

    time.sleep(INTERVAL)

# === RESULTADOS ===
with open(txt_file, "a") as f:
    f.write("\nFinal results:\n")

print("\nResultados finales:")
if latencies:
    avg = statistics.mean(latencies)
    maximo = max(latencies)
    minimo = min(latencies)
    mediana = statistics.median(latencies)

    with open(txt_file, "a") as f:
        f.write(f"Avg: {avg:.2f} ms\n")
        f.write(f"Max: {maximo:.2f} ms\n")
        f.write(f"Min: {minimo:.2f} ms\n")
        f.write(f"Median: {mediana:.2f} ms\n")

    print(f"Promedio: {avg:.2f} ms")
    print(f"Mínimo:   {minimo:.2f} ms")
    print(f"Máximo:   {maximo:.2f} ms")
    print(f"Mediana:  {mediana:.2f} ms")

    # Guardar CSV
    with open(csv_file, "w") as c:
        c.write("timestamp,latency_ms\n")
        for i, val in enumerate(latencies):
            c.write(f"{i},{val}\n")

    # Mostrar gráfico
    plt.figure(figsize=(10, 4))
    plt.plot(latencies, label="Latencia (ms)", linewidth=1)
    plt.axhline(avg, color='orange', linestyle='--', label=f"Promedio {avg:.1f} ms")
    plt.title(f"Latencia hacia {SERVER_URL}")
    plt.xlabel("Muestras")
    plt.ylabel("ms")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

else:
    print("No se recibieron respuestas válidas.")
