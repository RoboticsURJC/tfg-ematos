import requests
import time
import statistics
import json
import os
from datetime import datetime

# Carga tu configuración (igual que en el cliente)
with open("config.json") as f:
    config = json.load(f)
SERVER_URL = config["server_url"]

duracion = 300  # 5 minutos
intervalo = 1   # segundos
latencias = []

# Crear carpeta de resultados si no existe
os.makedirs("resultados", exist_ok=True)

# Nombre del fichero con fecha y hora
fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
archivo = f"resultados/latencias_{fecha_hora}.txt"

with open(archivo, "w") as f:
    f.write(f"Mediciones de latencia hacia {SERVER_URL}/latency\n")
    f.write(f"Fecha de inicio: {fecha_hora}\n\n")

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
                f.write(f"{datetime.now().strftime('%H:%M:%S')} - {latencia:.2f} ms\n")
            else:
                print("Error en respuesta del servidor")
                f.write(f"{datetime.now().strftime('%H:%M:%S')} - Error en respuesta\n")
        except requests.exceptions.RequestException:
            print("Fallo de conexión")
            f.write(f"{datetime.now().strftime('%H:%M:%S')} - Fallo de conexión\n")
        time.sleep(intervalo)

    f.write("\nResultados finales:\n")
    print("\nResultados:")
    if latencias:
        promedio = statistics.mean(latencias)
        maximo = max(latencias)
        minimo = min(latencias)
        f.write(f"Promedio: {promedio:.2f} ms\n")
        f.write(f"Máximo: {maximo:.2f} ms\n")
        f.write(f"Mínimo: {minimo:.2f} ms\n")

        print(f"Promedio: {promedio:.2f} ms")
        print(f"Máximo: {maximo:.2f} ms")
        print(f"Mínimo: {minimo:.2f} ms")
    else:
        f.write("No se recibieron respuestas válidas.\n")
        print("No se recibieron respuestas válidas.")
