from core.base import LLMModel
from config import GROQ_API_KEY
from groq import Groq

class GroqLlama(LLMModel):
    def __init__(self):
        super().__init__("llama-3-groq")
        self.client = Groq(api_key=GROQ_API_KEY)

    def generate(self, prompt):
        r = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        return r.choices[0].message.content, {}