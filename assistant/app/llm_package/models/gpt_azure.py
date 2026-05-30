from assistant.app.llm_package.core.base import LLMModel
from openai import OpenAI
from assistant.app.llm_package.config import AZURE_API_KEY

class GPTAzure(LLMModel):
    def __init__(self):
        super().__init__("gpt-4-azure")
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=AZURE_API_KEY
        )

    def generate(self, prompt):
        r = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content, {}