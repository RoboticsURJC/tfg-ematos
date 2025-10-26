import requests
import time
import json
import statistics
from datetime import datetime
import os
import base64

# Configuración
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)

SERVER_URL = config["server_url"]
ENDPOINT = f"{SERVER_URL}/recognize"

# Imagen de prueba (puede ser cualquier jpg)
test_image_path = os.path.join(curr_dir, "..", "..", "test.jpg")
with open(test_image_path, "rb") as f:
    img_bytes = f.read()
img_b64 = base64.b64encode(img_bytes).decode("utf-8")

# Configuración de la prueba
DURACION = 300  # segundos (5 min)
INTERVAL = 1   # segundos

latencias = []
inicio = time.time()

# Fichero para guardar resultados
fecha_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(curr_dir, f"latency_recognize_{fecha_str}.txt")

print(f"Latency measurements of {ENDPOINT} duraning {DURACION//60} min...\n")

while time.time() - inicio < DURACION:
    try:
        t0 = time.time()
        r = requests.post(ENDPOINT, json={"image": img_b64}, timeout=10)
        t1 = time.time()
        if r.ok:
            latency = (t1 - t0) * 1000  # ms
            latencias.append(latency)
            num_faces = len(r.json().get("recognized", []))
            print(f"{latency:.2f} ms | rostros: {num_faces}")
            with open(log_file, "a") as f:
                f.write(f"{time.time():.2f},{latency:.2f},{num_faces}\n")
        else:
            print("Error in server response")
    except requests.exceptions.RequestException:
        print("Connection failure")
    time.sleep(INTERVAL)

# Resumen
if latencias:
    print("\nResults:")
    print(f"Avg: {statistics.mean(latencias):.2f} ms")
    print(f"Max: {max(latencias):.2f} ms")
    print(f"Min: {min(latencias):.2f} ms")
else:
    print("No valid responses were received.")
