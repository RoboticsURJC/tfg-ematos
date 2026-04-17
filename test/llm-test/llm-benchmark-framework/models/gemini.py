from core.base import LLMModel
from google import genai
from config import GEMINI_API_KEY
import logging

logger = logging.getLogger("llm.gemini")


class GeminiModel(LLMModel):
    """
    Implementación del modelo Gemini dentro del framework de benchmarking.
    """

    def __init__(self):
        super().__init__("gemini")
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(self, prompt):
        """
        Genera una respuesta usando Gemini API.

        Args:
            prompt (str): texto de entrada

        Returns:
            tuple: (respuesta, metadata)
        """

        try:
            logger.info("Calling Gemini API")

            response = self.client.models.generate_content(
                # model="gemini-1.5-flash",
                model="models/gemini-flash-latest",
                contents=prompt
            )

            text = response.text if response else None

            logger.info("Gemini response received")

            return text, {
                "provider": "gemini",
                "status": "OK"
            }

        except Exception as e:
            logger.exception("Gemini generation failed")

            return None, {
                "provider": "gemini",
                "status": "ERROR",
                "error": str(e)
            }
                            