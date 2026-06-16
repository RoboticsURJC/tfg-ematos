# app/core/gpt_azure_model.py

from assistant.app.llm_package.core.base import LLMModel
from openai import OpenAI
from assistant.app.llm_package.config import AZURE_API_KEY

##
# @file gpt_azure_model.py
# @brief Conector adaptado para el consumo de modelos OpenAI a través de Azure AI Model Inference.
# @details Implementa la interfaz base `LLMModel` redirigiendo las peticiones del SDK nativo 
# de OpenAI hacia el catálogo de modelos en la nube de Azure utilizando claves de acceso unificadas.
#

class GPTAzure(LLMModel):
    """
    @brief Adaptador de GPT-4 (Azure AI) para el pipeline de ejecución de benchmarks del robot.
    """

    def __init__(self):
        """
        @brief Constructor de la clase GPTAzure.
        @details Inicializa la clase base bajo el identificador técnico 'gpt-4-azure' y configura 
        el cliente de OpenAI para que apunte al Host de inferencia global de Azure AI.
        """
        super().__init__("gpt-4-azure")
        
        ## Cliente de OpenAI parametrizado con el endpoint de Azure AI Marketplace.
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=AZURE_API_KEY
        )

    def generate(self, prompt):
        """
        @brief Envía una solicitud de inferencia síncrona al modelo gpt-4o-mini alojado en Azure.
        @details Construye la estructura de mensajería conversacional estándar (`messages`) exigida 
        por la API, ejecuta la llamada de forma bloqueante y extrae el texto plano del primer elemento 
        del vector de elecciones (`choices`).
        
        @param prompt Instrucción o pregunta limpia destinada a ser evaluada por el modelo de lenguaje.
        
        @return tuple Una tupla `(content_text, extra_metadata)` donde:
               - `content_text` (str): El cuerpo de la respuesta generado por el modelo.
               - `extra_metadata` (dict): Un diccionario vacío reservado para metadatos de tokens.
        """
        # Petición síncrona utilizando la interfaz de chat de OpenAI mapeada a la infraestructura de Azure
        r = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Desempaquetado del payload de la respuesta del modelo (Choice 0 -> Message -> Content)
        return r.choices[0].message.content, {}