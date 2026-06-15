import requests

from assistant.app.llm_package.core.base import LLMModel

class LlamaServer(LLMModel):
    def __init__(self, url="http://127.0.0.1:8080/completion"):
        super().__init__("llama-cpp")
        self.url = url

    def generate(self, prompt):
        r = requests.post(self.url, json={
            "prompt": prompt,
            "n_predict": 256
        })

        return r.json().get("content", ""), {}