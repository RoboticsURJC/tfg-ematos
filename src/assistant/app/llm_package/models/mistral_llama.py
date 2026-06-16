# app/core/mistral_server_model.py

import requests
from assistant.app.llm_package.core.base import LLMModel

##
# @file mistral_server_model.py
# @brief Conector HTTP para servidores locales de inferencia que ejecutan Mistral 7B.
# @details Implementa la interfaz base `LLMModel` consumiendo el endpoint de completado 
# de un servidor local autohospedado (como llama.cpp, vLLM o LM Studio) mediante peticiones HTTP POST estándar.
#

class MistralServer(LLMModel):
    """
    @brief Adaptador del servidor local Mistral para el pipeline de ejecución de benchmarks del robot.
    """

    def __init__(self, url="http://127.0.0.1:8081/completion"):
        """
        @brief Constructor de la clase MistralServer.
        @details Invoca al constructor de la clase abstracta padre definiendo el nombre clave 'mistral-7b' 
        y parametriza la dirección de red local (Loopback) por defecto para el socket de inferencia.
        
        @param url Dirección URL absoluta del endpoint del servidor de inferencia local.
        """
        super().__init__("mistral-7b")
        
        ## Dirección URL o socket de red del servidor de inferencia local.
        self.url = url

    def generate(self, prompt):
        """
        @brief Envía una solicitud de inferencia síncrona al servidor local Mistral.
        @details Construye un payload JSON estructurado inyectando la cadena del prompt y 
        el parámetro de parada `n_predict` para limitar la longitud máxima de la generación de tokens.
        
        @param prompt Instrucción o pregunta limpia destinada a ser evaluada por el modelo de lenguaje.
        
        @return tuple Una tupla `(content_text, extra_metadata)` donde:
               - `content_text` (str): El cuerpo de la respuesta generado por Mistral extraído de la clave 'content'.
               - `extra_metadata` (dict): Un diccionario vacío reservado para metadatos de tokens.
        """
        # Petición síncrona HTTP POST hacia el servidor de completado local
        r = requests.post(
            self.url, 
            json={
                "prompt": prompt,
                "n_predict": 256  # Limita la ventana de salida a un máximo de 256 tokens para optimizar el benchmark
            }
        )

        # Desempaquetado seguro del JSON extrayendo la clave estándar 'content'
        return r.json().get("content", ""), {}