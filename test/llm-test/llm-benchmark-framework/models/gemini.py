from core.base import LLMModel
from google import genai
from config import GEMINI_API_KEY
import time


class GeminiModel(LLMModel):
    def __init__(self):
        super().__init__("gemini")
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(self, prompt):
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model="models/gemini-flash-latest",
                    contents=prompt
                )

                return response.text, {}

            except Exception as e:
                msg = str(e)

                # rate limit
                if "429" in msg:
                    wait = 10 * (attempt + 1)
                    time.sleep(wait)
                    continue

                raise e

        return None, {"error": "Gemini failed after retries"}