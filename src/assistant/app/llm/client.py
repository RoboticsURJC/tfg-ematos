# app/core/client.py

import requests
import logging
from app.core.logger import logger

##
# @file client.py
# @brief Cliente LLM de red y conector para la API de inferencia del modelo de lenguaje (LLM).
# @details Gestiona las peticiones HTTP síncronas y por flujo (streaming) hacia el backend 
# de inteligencia artificial configurado, encapsulando las directivas del sistema y el control de errores.
#

class LLMClient:
    """
    @brief Clase encargada de la comunicación directa con el servidor de inferencia IA.
    """

    def __init__(self, server_url, model="groq", timeout=90):
        """
        @brief Inicializa los parámetros de red y configura las directrices del modelo.
        @details Limpia la URL base eliminando barras diagonales residuales y anexa el endpoint 
        estricto `/generate` requerido por la arquitectura del servidor de inferencia.
        
        @param server_url Dirección IP o DNS base del microservicio de IA.
        @param model Identificador del motor de inferencia o API a utilizar (por defecto 'groq').
        @param timeout Tiempo límite de espera en segundos para la recepción de tokens.
        """
        ## URL absoluta construida para el endpoint de generación de texto.
        self.server_url = server_url.rstrip("/") + "/generate"
        
        ## Identificador del modelo o backend de procesamiento.
        self.model = model
        
        ## Tiempo máximo de espera para las transacciones HTTP.
        self.timeout = timeout
        
        ## Directivas fijas del sistema que moldean la personalidad afable y segura del asistente.
        self.system_prompt = (
            "Eres un asistente para personas mayores. "
            "Responde siempre en español. "
            "No inventes nada. "
            "Eres un asistente afable y respondes de forma útil."
        )

    def ask(self, prompt: str) -> str:
        """
        @brief Realiza una consulta síncrona al modelo de lenguaje y devuelve la respuesta consolidada.
        @details Concatena las directrices del `system_prompt` con la entrada actual del usuario, 
        valida el código de estado HTTP (`r.raise_for_status`) y extrae el texto plano generado.
        
        @param prompt Texto estructurado con el contexto e historial enviado por el Pipeline.
        
        @return str Texto de respuesta generado de forma completa por la Inteligencia Artificial.
        @retval "No he podido generar respuesta." Mensaje de salvaguarda amigable ante fallos de timeout o red.
        """
        full_prompt = f"{self.system_prompt}\n\nUsuario: {prompt}\nAsistente:"
        
        try:
            r = requests.post(
                self.server_url,
                json={
                    "model": self.model,
                    "prompt": full_prompt
                },
                timeout=self.timeout
            )

            # Lanza una excepción HTTPError si el servidor devuelve un código de error (4xx o 5xx)
            r.raise_for_status()
            data = r.json()

            return str(data.get("output", ""))

        except Exception:
            # Captura y traza la excepción completa en los logs locales y remotos
            logger.exception("[LLM CLIENT] Error crítico en petición síncrona ask()")
            return "No he podido generar respuesta."

    def stream(self, prompt: str):
        """
        @brief Inicia una petición de red por flujo continuo (Streaming) para recibir texto token a token.
        @details Utiliza la directiva `stream=True` de la librería `requests` e itera sobre las líneas 
        de bytes entrantes mediante un generador de Python (`yield`).
        
        @param prompt Texto consolidado de entrada para la generación por flujo.
        
        @return generator Devuelve un generador que emite líneas codificadas en UTF-8 conforme llegan del servidor.
        """
        try:
            r = requests.post(
                self.server_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=self.timeout
            )

            r.raise_for_status()

            # Procesar el cuerpo de la respuesta por líneas físicas conforme se transmiten por la red
            for line in r.iter_lines():
                if line:
                    yield line.decode("utf-8")

        except Exception:
            logger.exception("[LLM CLIENT] Error crítico en flujo continuo stream()")