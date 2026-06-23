# services/llm_service.py

import requests
from services.log_service import add_log

##
# @file llm_service.py
# @brief Servicio cliente para la comunicación con el microservicio de Modelos de Lenguaje (LLM).
# @details Gestiona las peticiones de inferencia de texto inteligente y las pruebas de conectividad (Health Check) con el backend local de IA.
#

LLM_URL = "http://localhost:8000"


class LLMService:
    """
    @brief Clase estática que encapsula las operaciones con el motor de Inteligencia Artificial (LLM).
    """

    @staticmethod
    def generate(model: str, prompt: str):
        """
        @brief Envía una petición de generación de texto al modelo especificado.
        
        Registra el inicio de la inferencia, realiza una llamada HTTP POST al microservicio y maneja el almacenamiento de los resultados o respuestas en el log.
        
        @param model Nombre o identificador del modelo LLM que procesará el texto (ej: 'llama3', 'mistral').
        @param prompt Texto descriptivo, instrucción o consulta que sirve de entrada para el modelo.
        
        @return dict Diccionario con la respuesta del microservicio que incluye el estado, texto generado y métricas, o estructura de error si falla.
        """
        try:
            add_log("llm", f"Generating with {model}")

            r = requests.post(
                f"{LLM_URL}/generate",
                json={
                    "model": model,
                    "prompt": prompt
                },
                timeout=120
            )

            data = r.json()

            if data.get("status") == "OK":
                add_log("llm", "Response generated successfully")
            else:
                add_log("llm", f"LLM error: {data}")

            return data

        except Exception as e:
            add_log("llm", f"ERROR generate: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    @staticmethod
    def health():
        """
        @brief Verifica si el servidor del modelo de lenguaje está activo y accesible.
        
        Realiza una llamada rápida HTTP GET a la raíz de la URL del LLM para monitorizar su disponibilidad.
        
        @return dict Estado del servicio devuelto por el backend si está activo, o un diccionario con estado {"status": "OFFLINE"} ante cualquier fallo de conexión.
        """
        try:
            r = requests.get(LLM_URL, timeout=5)
            return r.json()

        except Exception as e:
            add_log("llm", f"LLM offline: {str(e)}")
            return {"status": "OFFLINE"}