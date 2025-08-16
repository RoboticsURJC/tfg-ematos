import os
import datetime
from picamera2 import Picamera2, Preview
from time import sleep

# --- Configuración ---
carpeta = "fotos_magicas"

if not os.path.exists(carpeta):
    os.makedirs(carpeta)

# --- Iniciar cámara con vista previa ---
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration(display="main"))
picam2.start_preview(Preview.QT)  # Usa ventana gráfica QT
picam2.start()

print("📷 Vista previa activa. Pulsa Enter para capturar una foto. Ctrl+C para salir.")

try:
    while True:
        input("👉 Pulsa Enter para capturar...")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{carpeta}/foto_{timestamp}.jpg"
        picam2.capture_file(filename)
        print(f"📸 Foto guardada como {filename}")
except KeyboardInterrupt:
    print("\n🛑 Programa detenido por el usuario.")
finally:
    picam2.stop()
