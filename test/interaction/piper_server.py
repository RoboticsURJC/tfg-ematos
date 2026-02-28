# archivo: piper_server.py
import os
import sys
from flask import Flask, request, send_file
import subprocess
import threading
import hashlib

app = Flask(__name__)

# Ruta a tu modelo
MODELO_PIPER = "/home/eli/tfg-ematos/test/interaction/es_ES-sharvard-medium.onnx"
cache_tts = {}

lock = threading.Lock()

@app.route("/speak", methods=["POST"])
def speak():
    texto = request.form.get("text", "")
    if not texto.strip():
        return "No text", 400

    # Generar hash para cache
    h = hashlib.md5(texto.encode("utf-8")).hexdigest()
    wav_path = f"/tmp/{h}.wav"

    with lock:  # evitar llamadas simultáneas que rompan Piper
        if texto not in cache_tts:
            subprocess.run(
                ["piper", "--model", MODELO_PIPER, "--output_file", wav_path, texto],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            cache_tts[texto] = wav_path

    return send_file(wav_path, mimetype="audio/wav")

if __name__ == "__main__":
    print("📢 Piper server iniciado en http://0.0.0.0:5002")
    app.run(host="0.0.0.0", port=5002, threaded=True)