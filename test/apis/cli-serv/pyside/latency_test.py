import requests
import time
import statistics
import json

# Carga tu configuración (igual que en el cliente)
with open("config.json") as f:
    config = json.load(f)
SERVER_URL = config["server_url"]

duracion = 300  # 5 minutos
intervalo = 1   # segundos
latencias = []

print(f"Midiendo latencia hacia {SERVER_URL}/latency durante {duracion//60} minutos...\n")

inicio = time.time()
while time.time() - inicio < duracion:
    try:
        t0 = time.time()
        r = requests.get(f"{SERVER_URL}/latency", timeout=3)
        t1 = time.time()
        if r.ok:
            latencia = (t1 - t0) * 1000
            latencias.append(latencia)
            print(f" {latencia:.2f} ms")
        else:
            print("Error en respuesta del servidor")
    except requests.exceptions.RequestException:
        print("Fallo de conexión")
    time.sleep(intervalo)

print("\nResultados:")
if latencias:
    print(f"Promedio: {statistics.mean(latencias):.2f} ms")
    print(f"Máximo: {max(latencias):.2f} ms")
    print(f"Mínimo: {min(latencias):.2f} ms")
else:
    print("No se recibieron respuestas válidas.")
