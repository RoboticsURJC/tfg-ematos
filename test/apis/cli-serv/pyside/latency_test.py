import requests
import time
import statistics
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime
import base64

# === CONFIGURACIÓN ===
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)

SERVER_URL = config["server_url"]
DURATION = 300  # segundos totales (5 min)
INTERVAL = 1    # intervalo entre pruebas en segundos
latencies = []

# === CARPETA DE IMÁGENES DE PRUEBA ===
test_folder = os.path.join(curr_dir, "test_images")
image_files = [f for f in os.listdir(test_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

if not image_files:
    print("No se encontraron imágenes en la carpeta test_images")
    exit(1)

# === PREPARAR RESULTADOS ===
os.makedirs("results", exist_ok=True)
date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
txt_file = f"results/latencies_{date_time}.txt"
csv_file = f"results/latencies_{date_time}.csv"

print(f"\nMidiendo latencia hacia: {SERVER_URL}/recognize durante {DURATION//60} min...\n")

start_time = time.time()
iteration = 0

with open(txt_file, "w") as f:
    f.write(f"Latency measurements towards {SERVER_URL}/recognize\n")
    f.write(f"Start Date: {date_time}\n\n")

    while time.time() - start_time < DURATION:
        iteration += 1
        # Elegimos una imagen aleatoria de test para enviar
        img_name = image_files[iteration % len(image_files)]
        img_path = os.path.join(test_folder, img_name)
        with open(img_path, "rb") as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode("utf-8")

        try:
            t0 = time.time()
            r = requests.post(
                f"{SERVER_URL}/recognize",
                json={"image": img_b64},
                timeout=10
            )
            t1 = time.time()

            if r.ok:
                latency = (t1 - t0) * 1000  # en ms
                latencies.append(latency)

                avg_10 = statistics.mean(latencies[-10:]) if len(latencies) >= 10 else statistics.mean(latencies)
                color = "\033[92m" if latency < 500 else ("\033[93m" if latency < 1500 else "\033[91m")

                print(f"{color}[{iteration}] {img_name} - {latency:.2f} ms (avg10={avg_10:.1f})\033[0m")
                f.write(f"{datetime.now().strftime('%H:%M:%S')},{img_name},{latency:.2f}\n")

            else:
                print(f"\033[91m❌ Error en la respuesta para {img_name}\033[0m")
                f.write(f"{datetime.now().strftime('%H:%M:%S')},{img_name},Error\n")

        except requests.exceptions.RequestException:
            print(f"\033[91m⚠️ Fallo de conexión para {img_name}\033[0m")
            f.write(f"{datetime.now().strftime('%H:%M:%S')},{img_name},Connection failure\n")

        time.sleep(INTERVAL)

# === RESULTADOS FINALES ===
if latencies:
    avg = statistics.mean(latencies)
    maximo = max(latencies)
    minimo = min(latencies)
    mediana = statistics.median(latencies)

    with open(txt_file, "a") as f:
        f.write(f"\nAvg: {avg:.2f} ms\nMax: {maximo:.2f} ms\nMin: {minimo:.2f} ms\nMedian: {mediana:.2f} ms\n")

    print("\nResultados finales:")
    print(f"Promedio: {avg:.2f} ms")
    print(f"Mínimo:   {minimo:.2f} ms")
    print(f"Máximo:   {maximo:.2f} ms")
    print(f"Mediana:  {mediana:.2f} ms")

    # Guardar CSV
    with open(csv_file, "w") as c:
        c.write("image,latency_ms\n")
        for i, val in enumerate(latencies):
            img_name = image_files[i % len(image_files)]
            c.write(f"{img_name},{val}\n")

    # Gráfico
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
