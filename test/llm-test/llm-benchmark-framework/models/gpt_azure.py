from core.base import LLMModel
from openai import OpenAI
from config import AZURE_API_KEY

##
# @file gpt_azure.py
# @brief Implementación de LLMModel usando modelos de Azure/OpenAI API.
#
# Este módulo integra un modelo GPT desplegado en Azure a través de una
# API compatible con OpenAI, permitiendo su uso dentro del framework de
# benchmarking de LLMs.
#

##
# @class GPTAzure
# @brief Adaptador de modelo GPT basado en Azure OpenAI-compatible API.
#
# Esta clase implementa la interfaz LLMModel para permitir la generación
# de texto utilizando modelos GPT alojados en Azure.
#
class GPTAzure(LLMModel):

    ##
    # @brief Constructor del cliente GPT en Azure.
    #
    # Inicializa el cliente OpenAI apuntando al endpoint de Azure.
    #
    def __init__(self):
        super().__init__("gpt-4-azure")
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=AZURE_API_KEY
        )

    ##
    # @brief Genera una respuesta utilizando el modelo GPT en Azure.
    #
    # Envía el prompt al modelo y devuelve la respuesta generada junto con
    # metadatos del proveedor.
    #
    # @param prompt Texto de entrada del usuario.
    #
    # @return tuple(str, dict) Respuesta generada y metadatos del proveedor.
    #         En caso de error, devuelve None y un diccionario con información
    #         del fallo (por ejemplo rate limit).
    #
    def generate(self, prompt):
        try:
            r = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            return r.choices[0].message.content, {"provider": "azure"}

        except Exception as e:
            return None, {
                "status": "RATE_LIMIT",
                "error": str(e),
                "provider": "azure"
            }