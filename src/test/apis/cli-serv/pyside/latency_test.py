import requests
import time
import statistics
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime
import base64
import glob

# === CONFIGURACIÓN ===
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)

SERVER_URL = config["server_url"]
DURATION = 300  # segundos (5 min)
INTERVAL = 1    # intervalo entre pruebas
TEST_IMAGES_DIR = os.path.join(curr_dir, "test_images")
latencies = []

# === Preparar archivos de resultados ===
os.makedirs("results", exist_ok=True)
date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
txt_file = f"results/latencies_{date_time}.txt"
csv_file = f"results/latencies_{date_time}.csv"

# === Cargar imágenes de test ===
image_paths = glob.glob(os.path.join(TEST_IMAGES_DIR, "*.jpg"))
if not image_paths:
    raise FileNotFoundError("No se encontraron imágenes en la carpeta test_images/")

# Pre-codificar las imágenes a base64
images_b64 = []
for path in image_paths:
    with open(path, "rb") as f:
        images_b64.append(base64.b64encode(f.read()).decode("utf-8"))

# === Iniciar medición ===
print(f"\nMidiendo latencia hacia {SERVER_URL}/recognize durante {DURATION//60} min...\n")

with open(txt_file, "w") as f:
    f.write(f"Latency measurements towards {SERVER_URL}/recognize\n")
    f.write(f"Start Date: {date_time}\n\n")

    start_time = time.time()
    img_index = 0

    while time.time() - start_time < DURATION:
        img_b64 = images_b64[img_index % len(images_b64)]
        img_index += 1

        try:
            t0 = time.time()
            r = requests.post(f"{SERVER_URL}/recognize", json={"image": img_b64}, timeout=10)
            t1 = time.time()

            latency = (t1 - t0) * 1000  # ms
            latencies.append(latency)

            avg_10 = statistics.mean(latencies[-10:]) if len(latencies) >= 10 else statistics.mean(latencies)

            color = "\033[92m" if latency < 500 else ("\033[93m" if latency < 1500 else "\033[91m")
            status = "OK" if r.ok else "ERROR"

            print(f"{color}{datetime.now().strftime('%H:%M:%S')} - {latency:.2f} ms (avg10={avg_10:.1f}) - {status}\033[0m")
            f.write(f"{datetime.now().strftime('%H:%M:%S')} - {latency:.2f} ms - {status}\n")

        except requests.exceptions.RequestException:
            print("\033[91m⚠️ Fallo de conexión\033[0m")
            f.write(f"{datetime.now().strftime('%H:%M:%S')} - Connection failure\n")

        time.sleep(INTERVAL)

# === Guardar resultados finales ===
if latencies:
    avg = statistics.mean(latencies)
    maximo = max(latencies)
    minimo = min(latencies)
    mediana = statistics.median(latencies)

    with open(txt_file, "a") as f:
        f.write("\nFinal results:\n")
        f.write(f"Avg: {avg:.2f} ms\n")
        f.write(f"Max: {maximo:.2f} ms\n")
        f.write(f"Min: {minimo:.2f} ms\n")
        f.write(f"Median: {mediana:.2f} ms\n")

    with open(csv_file, "w") as c:
        c.write("timestamp,latency_ms\n")
        for i, val in enumerate(latencies):
            c.write(f"{i},{val}\n")

    print("\nResultados finales:")
    print(f"Promedio: {avg:.2f} ms")
    print(f"Mínimo:   {minimo:.2f} ms")
    print(f"Máximo:   {maximo:.2f} ms")
    print(f"Mediana:  {mediana:.2f} ms")

    # === Gráfico ===
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
