import requests
import logging

logger = logging.getLogger("llm")


class LLMClient:

    def __init__(self, server_url, model="groq", timeout=90):
        self.server_url = server_url
        self.model = model
        self.timeout = timeout

    # =========================
    # NORMAL
    # =========================
    def ask(self, prompt: str) -> str:
        try:
            r = requests.post(
                self.server_url,
                json={
                    "model": self.model,
                    "prompt": prompt
                },
                timeout=self.timeout
            )

            r.raise_for_status()
            data = r.json()

            output = data.get("output", "")

            if isinstance(output, list):
                output = output[0]

            return str(output)

        except Exception:
            logger.exception("LLM ERROR")
            return ""

    # =========================
    # STREAMING
    # =========================
    def stream(self, prompt: str):
        """
        Simulación de streaming (depende de tu backend real)
        """
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

            for line in r.iter_lines():
                if not line:
                    continue

                token = line.decode("utf-8")

                yield token

        except Exception:
            logger.exception("LLM STREAM ERROR")
            return