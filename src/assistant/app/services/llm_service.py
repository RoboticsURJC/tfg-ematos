# app/core/llm_service.py

import requests

##
# @file llm_service.py
# @brief Módulo wrapper y cliente de consumo para los endpoints de la API del servidor LLM.
# @details Simplifica el acceso a las funciones de inferencia de texto, empaquetando 
# las llamadas HTTP POST síncronas estándar y el procesamiento de flujos orientados a tokens (streaming).
#

class LLMService:
    """
    @brief Clase encargada de abstraer el consumo de servicios de inferencia LLM.
    """

    def __init__(self, base_url, model="llama3", timeout=60):
        """
        @brief Constructor de la clase LLMService.
        @details Sanea la URL de entrada eliminando barras residuales finales para prevenir 
        errores de formateo en las concatenaciones de los strings de ruta de endpoints.
        
        @param base_url Dirección IP o DNS base donde escucha el microservicio de inferencia.
        @param model Cadena identificativa del modelo por defecto a instanciar en la API.
        @param timeout Tiempo límite de gracia (en segundos) antes de abortar la petición por falta de respuesta.
        """
        ## URL limpia absoluta para las llamadas de red del servicio.
        self.base_url = base_url.rstrip("/")
        
        ## Identificador del modelo por defecto (ej: 'llama3', 'groq', 'gemini').
        self.model = model
        
        ## Ventana máxima de espera de paquetes de red.
        self.timeout = timeout

    def ask(self, prompt: str) -> str:
        """
        @brief Envía una instrucción al modelo y aguarda de forma bloqueante la respuesta completa.
        @details Envía el flag `stream: False` en el payload. Valida los códigos de estado HTTP 
        y extrae de forma directa el texto generado del campo estructurado de respuesta.
        
        @param prompt Texto plano con la instrucción o pregunta dirigida al modelo.
        
        @return str Texto de respuesta consolidado devuelto por la API de inferencia.
        """
        r = requests.post(
            f"{self.base_url}/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=self.timeout
        )

        # Dispara una excepción HTTPError si el código de estado no pertenece al rango de éxito (2xx)
        r.raise_for_status()
        
        # Mapea de forma segura el retorno. Se añade contingencia para 'output' o 'response' según la versión del backend
        data = r.json()
        return data.get("response", data.get("output", ""))

    def stream(self, prompt: str):
        """
        @brief Inicializa una conexión HTTP orientada a flujos (streaming) para procesar tokens bajo demanda.
        @details Activa el parámetro `stream=True` en el cliente HTTP de `requests`. Genera un bucle 
        no bloqueante de memoria que lee las líneas binarias entrantes del socket, transformándolas en 
        un generador nativo de Python a través de la directiva `yield`.
        
        @param prompt Texto plano con la instrucción o consulta enviada al modelo.
        
        @return generator Emite de forma asíncrona fragmentos (tokens) de texto decodificados en UTF-8.
        """
        r = requests.post(
            f"{self.base_url}/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": True
            },
            stream=True,
            timeout=self.timeout
        )

        r.raise_for_status()

        # Iteración binaria eficiente sobre el flujo de datos del socket de red
        for line in r.iter_lines():
            if not line:
                continue

            try:
                # Decodificación de caracteres e inyección secuencial en el pipeline
                yield line.decode("utf-8")
                
            except Exception:
                # Silencia corrupciones de caracteres huérfanos intermedios para no colapsar la interfaz
                continue