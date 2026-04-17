from core.base import LLMModel
from config import GROQ_API_KEY
from groq import Groq

##
# @file groq_llama.py
# @brief Implementación de LLMModel utilizando la API de Groq.
#
# Este módulo proporciona una implementación concreta del modelo base
# LLMModel, utilizando el modelo LLaMA 3.3 alojado en la infraestructura
# de Groq Cloud.
#

##
# @class GroqLlama
# @brief Adaptador de modelo LLM basado en la API de Groq.
#
# Esta clase implementa la interfaz LLMModel para permitir la generación
# de texto mediante un modelo LLaMA alojado en la nube (Groq API).
#
class GroqLlama(LLMModel):

    ##
    # @brief Constructor del modelo GroqLlama.
    #
    # Inicializa el cliente de Groq con la clave API y define el nombre del modelo.
    #
    def __init__(self):
        super().__init__("llama-3-groq")
        self.client = Groq(api_key=GROQ_API_KEY)

    ##
    # @brief Genera una respuesta utilizando la API de Groq.
    #
    # Envía un prompt al modelo LLaMA 3.3 alojado en Groq Cloud y devuelve
    # la respuesta generada.
    #
    # @param prompt Texto de entrada del usuario.
    #
    # @return tuple(str, dict) Respuesta generada por el modelo y diccionario
    #         de metadatos (vacío en esta implementación).
    #
    def generate(self, prompt):
        r = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        return r.choices[0].message.content, {}