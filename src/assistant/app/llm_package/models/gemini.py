# app/core/gemini_model.py

from assistant.app.llm_package.core.base import LLMModel
from google import genai
from assistant.app.llm_package.config import GEMINI_API_KEY
import time

##
# @file gemini_model.py
# @brief Conector especializado para el modelo de lenguaje Gemini de Google.
# @details Implementa la interfaz base `LLMModel` consumiendo el SDK oficial `google-genai`.
# Incorpora una política de reintentos y mitigación de saturación de cuotas (Rate Limits).
#

class GeminiModel(LLMModel):
    """
    @brief Adaptador del modelo Gemini para el pipeline de ejecución de benchmarks del robot.
    """

    def __init__(self):
        """
        @brief Constructor de la clase GeminiModel.
        @details Invoca al constructor de la clase abstracta padre definiendo el nombre clave 'gemini' 
        e inicializa el cliente seguro de GenAI inyectando la API Key del archivo de configuración.
        """
        super().__init__("gemini")
        
        ## Cliente autenticado de la API de Google GenAI.
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(self, prompt):
        """
        @brief Genera texto a partir de un prompt utilizando el modelo ligero y rápido Gemini Flash.
        @details Envuelve la llamada en un bucle tolerante de hasta 3 intentos. Si el servidor de Google 
        devuelve un error HTTP 429 (Resource Exhausted / Rate Limit), el hilo de ejecución se congela 
        de forma incremental antes de reintentar la inferencia.
        
        @note La fórmula de espera ante un error 429 aplica un retraso lineal/exponencial básico: 
        `espera = 10 * (intento_actual + 1)`. Esto se traduce en pausas sucesivas de 10, 20 y 30 segundos.
        
        @param prompt Texto estructurado con el contexto e instrucciones para el modelo.
        
        @return tuple Una tupla `(response_text, extra_metadata)` donde `response_text` es el string generado.
        @retval (None, dict) Retorna un diccionario con una bandera de error si se agotan todos los reintentos permitidos.
        
        @exception Exception Relanza cualquier excepción ajena al Rate Limit (como errores de API Key inválida o 403 Forbidden).
        """
        for attempt in range(3):
            try:
                # Inferencia síncrona contra el backend oficial de Google Cloud
                response = self.client.models.generate_content(
                    model="models/gemini-flash-latest",
                    contents=prompt
                )

                return response.text, {}

            except Exception as e:
                msg = str(e)

                # Control y mitigación del rebasamiento de cuotas (Rate Limit / Too Many Requests)
                if "429" in msg:
                    wait = 10 * (attempt + 1)
                    # Detiene el hilo actual de forma segura antes de saltar a la siguiente iteración
                    time.sleep(wait)
                    continue

                # Cláusula de escape inmediata ante errores fatales de configuración o red
                raise e

        # Retorno de salvaguarda si el bucle de reintentos expira sin éxito
        return None, {"error": "Gemini failed after retries"}