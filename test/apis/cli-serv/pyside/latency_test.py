import requests
import time
import statistics
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime
import base64
import cv2

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

# === IMAGEN DE PRUEBA ===
# Puedes usar cualquier imagen pequeña de prueba
test_image_path = os.path.join(curr_dir, "test_face.jpg")
with open(test_image_path, "rb") as f:
    img_bytes = f.read()
test_image_b64 = base64.b64encode(img_bytes).decode("utf-8")

# === INICIO ===
print(f"\nMidiendo latencia hacia: {SERVER_URL}/recognize durante {DURATION//60} min...\n")

with open(txt_file, "w") as f:
    f.write(f"Latency measurements towards {SERVER_URL}/recognize\n")
    f.write(f"Start Date: {date_time}\n\n")

    start = time.time()
    while time.time() - start < DURATION:
        try:
            t0 = time.time()
            r = requests.post(
                f"{SERVER_URL}/recognize",
                json={"image": test_image_b64},
                timeout=5
            )
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
                print("\033[91m❌ Error en la respuesta del servidor\033[0m")
                f.write(f"{datetime.now().strftime('%H:%M:%S')} - Error in response\n")

        except requests.exceptions.RequestException:
            print("\033[91m⚠️ Fallo de conexión\033[0m")
            f.write(f"{datetime.now().strftime('%H:%M:%S')} - Connection failure\n")

        time.sleep(INTERVAL)

    f.write("\nFinal results:\n")

# === RESULTADOS ===
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

    # === GUARDAR CSV ===
    with open(csv_file, "w") as c:
        c.write("timestamp,latency_ms\n")
        for i, val in enumerate(latencies):
            c.write(f"{i},{val}\n")

    # === GRÁFICO ===
    plt.figure(figsize=(10, 4))
    plt.plot(latencies, label="Latencia (ms)", linewidth=1)
    plt.axhline(avg, color='orange', linestyle='--', label=f"Promedio {avg:.1f} ms")
    plt.axhline(maximo, color='red', linestyle=':', label=f"Máximo {maximo:.1f} ms")
    plt.axhline(minimo, color='green', linestyle=':', label=f"Mínimo {minimo:.1f} ms")
    plt.title(f"Latencia hacia {SERVER_URL}/recognize")
    plt.xlabel("Muestras")
    plt.ylabel("ms")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

else:
    print("No se recibieron respuestas válidas.")
