import requests
import time
import statistics
import json
import os
from datetime import datetime

# Carga tu configuración (igual que en el cliente)
curr_dir = os.path.dirname(__file__)
config_path = os.path.join(curr_dir, "..", "config.json")

with open(config_path) as f:
    config = json.load(f)
SERVER_URL = config["server_url"]

duration = 300  # 5 minutes
intervalo = 1   # seconds
latencies = []

# Crear carpeta de resultados si no existe
os.makedirs("results", exist_ok=True)

# Nombre del fichero con fecha y hora
date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
file = f"results/latencies_{date_time}.txt"

with open(file, "w") as f:
    f.write(f"Latency measurements towards {SERVER_URL}/latency\n")
    f.write(f"Start Date: {date_time}\n\n")

    print(f"Latency measurements towards {SERVER_URL}/latency during {duration//60} minutes...\n")
    start = time.time()
    while time.time() - start < duration:
        try:
            t0 = time.time()
            r = requests.get(f"{SERVER_URL}/latency", timeout=3)
            t1 = time.time()
            if r.ok:
                latency = (t1 - t0) * 1000
                latencies.append(latency)
                print(f" {latency:.2f} ms")
                f.write(f"{datetime.now().strftime('%H:%M:%S')} - {latency:.2f} ms\n")
            else:
                print("Error in server response")
                f.write(f"{datetime.now().strftime('%H:%M:%S')} - Error in response\n")
        except requests.exceptions.RequestException:
            print("Connection failure")
            f.write(f"{datetime.now().strftime('%H:%M:%S')} - Connection failure\n")
        time.sleep(intervalo)

    f.write("\nFinal results:\n")
    print("\nResults:")
    if latencies:
        avg = statistics.mean(latencies)
        maximo = max(latencies)
        minimo = min(latencies)
        f.write(f"Avg: {avg:.2f} ms\n")
        f.write(f"Max: {maximo:.2f} ms\n")
        f.write(f"Min: {minimo:.2f} ms\n")

        print(f"Avg: {avg:.2f} ms")
        print(f"Max: {maximo:.2f} ms")
        print(f"Min: {minimo:.2f} ms")
    else:
        f.write("No valid responses were received.\n")
        print("No valid responses were received.")
