import subprocess
import time

class ModelManager:
    def __init__(self):
        self.process = None
        self.server_path = "/home/elisa/uni/llama.cpp/build/bin/llama-server"

    def start_model(self, model_path, port=8080):
        if self.process:
            print("🧹 Cerrando modelo anterior...")
            self.process.terminate()
            time.sleep(1)

        print(f"🚀 Cargando modelo: {model_path}")

        self.process = subprocess.Popen([
            self.server_path,
            "-m", model_path,
            "-c", "4096",
            "--port", str(port)
        ])

        time.sleep(3)