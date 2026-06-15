import os
import requests
import time
import json
import statistics
from datetime import datetime
import base64
import random

# Configuración
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)

SERVER_URL = config["server_url"]
ENDPOINT = f"{SERVER_URL}/recognize"

# Carpeta con varias imágenes de prueba
test_images_dir = os.path.join(curr_dir, "test_images")
image_files = [f for f in os.listdir(test_images_dir) if f.lower().endswith(".jpg")]

# Configuración de la prueba
DURACION = 300  # segundos (5 min)
INTERVAL = 1    # segundos
latencias = []
inicio = time.time()

# Fichero para guardar resultados
fecha_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(curr_dir, f"latency_recognize_{fecha_str}.txt")

print(f"Latency measurements of {ENDPOINT} using multiple images...\n")

while time.time() - inicio < DURACION:
    # Escoger imagen aleatoria
    img_file = random.choice(image_files)
    img_path = os.path.join(test_images_dir, img_file)
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    try:
        t0 = time.time()
        r = requests.post(ENDPOINT, json={"image": img_b64}, timeout=10)
        t1 = time.time()
        if r.ok:
            latency = (t1 - t0) * 1000  # ms
            latencias.append(latency)
            num_faces = len(r.json().get("recognized", []))
            print(f"{latency:.2f} ms | rostros: {num_faces} | imagen: {img_file}")
            with open(log_file, "a") as f:
                f.write(f"{time.time():.2f},{latency:.2f},{num_faces},{img_file}\n")
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
