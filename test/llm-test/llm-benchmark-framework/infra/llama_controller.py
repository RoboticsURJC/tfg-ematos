import subprocess
import time

##
# @file model_manager.py
# @brief Gestión del ciclo de vida de servidores de modelos LLM.
#
# Este módulo se encarga de iniciar y detener procesos de inferencia
# basados en `llama.cpp`, permitiendo cargar distintos modelos dinámicamente
# durante la ejecución de experimentos.
#

##
# @class ModelManager
# @brief Controlador de procesos de servidores de modelos LLM.
#
# Permite iniciar y gestionar instancias de servidores de inferencia
# (por ejemplo llama-server), asegurando que solo un modelo esté activo
# en cada momento.
#
class ModelManager:

    ##
    # @brief Constructor del gestor de modelos.
    #
    # Inicializa el estado interno del proceso y define la ruta del servidor.
    #
    def __init__(self):
        self.process = None
        self.server_path = "/home/elisa/uni/llama.cpp/build/bin/llama-server"

    ##
    # @brief Inicia un modelo LLM en un servidor local.
    #
    # Si existe un modelo previamente cargado, este se detiene antes de iniciar el nuevo.
    # Posteriormente se lanza el servidor de inferencia con el modelo especificado.
    #
    # @param model_path Ruta al archivo del modelo (GGUF u otro formato compatible).
    # @param port Puerto en el que se expondrá el servidor de inferencia.
    #
    # @return None
    #
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