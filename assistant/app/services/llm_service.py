import requests


class LLMService:
    """
    Wrapper limpio del LLM (stream + normal).
    """

    def __init__(self, base_url, model="llama3", timeout=60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def ask(self, prompt: str) -> str:
        r = requests.post(
            f"{self.base_url}/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=self.timeout
        )

        r.raise_for_status()
        return r.json().get("response", "")

    def stream(self, prompt: str):
        """
        Generador de tokens simulando streaming.
        """
        r = requests.post(
            f"{self.base_url}/generate",
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
            if not line:
                continue

            try:
                yield line.decode("utf-8")
            except Exception:
                continue
