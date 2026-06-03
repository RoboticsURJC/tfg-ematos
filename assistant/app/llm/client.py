
import requests
import logging

from app.core.logger import logger


class LLMClient:

    def __init__(self, server_url, model="groq", timeout=90):
        self.server_url = server_url.rstrip("/") + "/generate"
        self.model = model
        self.timeout = timeout
        
        self.system_prompt = (
        "Eres un asistente para personas mayores"
        "Respode siempre en español"
        "No inventes nada"
        "Eres un asistente afable y respondes de forma útil"
        )

    def ask(self, prompt: str) -> str:
        
        full_prompt = f"{self.system_prompt}\n\nUsuario: {prompt}\nAsistente"
        
        try:
            r = requests.post(
                self.server_url,
                json={
                    "model": self.model,
                    "prompt": full_prompt
                },
                timeout=self.timeout
            )

            r.raise_for_status()
            data = r.json()

            return str(data.get("output", ""))

        except Exception:
            logger.exception("LLM ERROR")
            return "No he podido generar respuesta."

    def stream(self, prompt: str):
        try:
            r = requests.post(
                self.server_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=self.timeout
            )

            r.raise_for_status()

            for line in r.iter_lines():
                if line:
                    yield line.decode("utf-8")

        except Exception:
            logger.exception("LLM STREAM ERROR")
            
            
            
            
