# app/core/llama_server_model.py

import requests
from assistant.app.llm_package.core.base import LLMModel

##
# @file llama_server_model.py
# @brief Conector HTTP para servidores locales basados en la arquitectura de llama.cpp.
# @details Implementa la interfaz base `LLMModel` consumiendo el endpoint de completado 
# de un servidor local embebido mediante peticiones HTTP POST estructuradas en formato JSON.
#

class LlamaServer(LLMModel):
    """
    @brief Adaptador del servidor llama.cpp local para el pipeline de ejecución de benchmarks del robot.
    """

    def __init__(self, url="http://127.0.0.1:8080/completion"):
        """
        @brief Constructor de la clase LlamaServer.
        @details Invoca al constructor de la clase abstracta padre definiendo el nombre clave 'llama-cpp' 
        y parametriza la dirección de red local (Loopback) y puerto por defecto (8080) de la API.
        
        @param url Dirección URL absoluta del endpoint de completado del servidor local.
        """
        super().__init__("llama-cpp")
        
        ## Dirección URL o socket de red del servidor de inferencia llama.cpp local.
        self.url = url

    def generate(self, prompt):
        """
        @brief Envía una solicitud de inferencia síncrona al backend de llama.cpp en local.
        @details Construye un payload JSON inyectando la cadena del prompt y el parámetro de parada 
        `n_predict` para limitar la longitud máxima de la generación de tokens y optimizar la latencia del benchmark.
        
        @param prompt Instrucción o pregunta limpia destinada a ser evaluada por el modelo de lenguaje.
        
        @return tuple Una tupla `(content_text, extra_metadata)` donde:
               - `content_text` (str): El cuerpo de la respuesta generado por el modelo extraído de la clave 'content'.
               - `extra_metadata` (dict): Un diccionario vacío reservado para metadatos de tokens.
        """
        # Petición síncrona HTTP POST hacia la API del servidor local de llama.cpp
        r = requests.post(
            self.url, 
            json={
                "prompt": prompt,
                "n_predict": 256  # Limita la ventana de salida a un máximo de 256 tokens para estabilizar las pruebas de velocidad
            }
        )

        # Desempaquetado seguro del JSON extrayendo la clave estándar 'content'
        return r.json().get("content", ""), {}