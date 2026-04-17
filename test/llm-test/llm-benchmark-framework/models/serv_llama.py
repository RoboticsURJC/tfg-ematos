import requests

##
# @file llama_server.py
# @brief Cliente de inferencia para un servidor LLM basado en llama.cpp.
#
# Este módulo implementa una interfaz sencilla para interactuar con un
# servidor HTTP local que expone un modelo de lenguaje, permitiendo
# generar texto a partir de prompts.
#

##
# @class LlamaServer
# @brief Cliente para comunicación con un servidor de inferencia LLM.
#
# Encapsula las peticiones HTTP al endpoint de generación de texto,
# facilitando la integración con el sistema de benchmarking.
#
class LlamaServer:

    ##
    # @brief Constructor del cliente del servidor LLM.
    #
    # @param url Endpoint del servidor de inferencia.
    #
    def __init__(self, url="http://127.0.0.1:8080/completion"):
        self.url = url

    ##
    # @brief Genera una respuesta a partir de un prompt.
    #
    # Envía una petición HTTP POST al servidor de inferencia y devuelve
    # el texto generado por el modelo.
    #
    # @param prompt Texto de entrada para el modelo.
    #
    # @return str Respuesta generada por el modelo.
    #
    def generate(self, prompt):
        r = requests.post(self.url, json={
            "prompt": prompt,
            "n_predict": 256
        })

        return r.json().get("content", "")