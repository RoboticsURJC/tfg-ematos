# app/core/groq_llama_model.py

from assistant.app.llm_package.core.base import LLMModel
from assistant.app.llm_package.config import GROQ_API_KEY
from groq import Groq

##
# @file groq_llama_model.py
# @brief Conector de ultra baja latencia para los modelos Llama a través de la API de Groq.
# @details Implementa la interfaz base `LLMModel` consumiendo el SDK oficial de `groq`.
# Aprovecha las unidades de procesamiento LPU (Language Processing Units) de Groq para acelerar los benchmarks.
#

class GroqLlama(LLMModel):
    """
    @brief Adaptador de Llama 3 (Groq) para el pipeline de ejecución de benchmarks del robot.
    """

    def __init__(self):
        """
        @brief Constructor de la clase GroqLlama.
        @details Inicializa la clase base bajo el identificador técnico 'llama-3-groq' y configura 
        el cliente seguro de Groq inyectando la clave de acceso privada (API Key).
        """
        super().__init__("llama-3-groq")
        
        ## Cliente autenticado del SDK nativo de Groq.
        self.client = Groq(api_key=GROQ_API_KEY)

    def generate(self, prompt):
        """
        @brief Envía una solicitud de inferencia síncrona al backend de Groq usando el modelo Llama 3.3.
        @details Llama de forma bloqueante al endpoint de completions parametrizando el modelo versátil 
        de 70 billones de parámetros (`llama-3.3-70b-versatile`) y extrae el texto plano generado.
        
        @param prompt Instrucción o pregunta limpia destinada a ser evaluada por el modelo de lenguaje.
        
        @return tuple Una tupla `(content_text, extra_metadata)` donde:
               - `content_text` (str): El cuerpo de la respuesta generado por Llama.
               - `extra_metadata` (dict): Un diccionario vacío reservado para telemetría secundaria de tokens.
        """
        # Petición síncrona optimizada para hardware LPU
        r = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        # Desempaquetado del payload de la respuesta del modelo (Choice 0 -> Message -> Content)
        return r.choices[0].message.content, {}