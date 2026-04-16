import requests
from core.base import LLMModel

class MistralServer(LLMModel):
    def __init__(self, url="http://127.0.0.1:8081/completion"):
        super().__init__("mistral-7b")
        self.url = url

    def generate(self, prompt):
        r = requests.post(self.url, json={
            "prompt": prompt,
            "n_predict": 256
        })

        return r.json().get("content", ""), {}