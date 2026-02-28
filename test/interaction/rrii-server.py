# server_vicuna.py
import subprocess
from flask import Flask, request, jsonify
import threading
import queue
import time

app = Flask(__name__)

# =====================
# ======= Config ======
# =====================
MODEL_PATH = "/home/eli/llama.cpp/models/vicuna-13b-v1.5.Q4_K_M.gguf"
NUM_THREADS = 8
CMD_QUEUE = queue.Queue()

# =====================
# ==== Generador LLM ===
# =====================
def generar_respuesta(prompt):
    """
    Llama al ejecutable de llama.cpp para generar respuesta.
    Devuelve texto plano.
    """
    try:
        cmd = [
            "./main",               # ejecutable llama.cpp
            "-m", MODEL_PATH,
            "-t", str(NUM_THREADS),
            "--prompt", prompt,
            "--n_predict", "256",
            "--color", "false"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error al generar respuesta: {e}"

# =====================
# ======= API =========
# =====================
@app.route("/", methods=["POST"])
def conversar():
    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"response": "No recibí ningún texto"}), 400

    # Se puede agregar cola si quieres procesar en orden
    respuesta = generar_respuesta(prompt)
    return jsonify({"response": respuesta})

# =====================
# ======= Main ========
# =====================
if __name__ == "__main__":
    print("🤖 Servidor Vicuna listo en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)