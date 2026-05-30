import requests

from services.log_service import add_log


LLM_URL = "http://localhost:8000"


class LLMService:

    @staticmethod
    def generate(model: str, prompt: str):

        try:

            add_log("llm", f"Generating with {model}")

            r = requests.post(
                f"{LLM_URL}/generate",
                json={
                    "model": model,
                    "prompt": prompt
                },
                timeout=120
            )

            data = r.json()

            if data.get("status") == "OK":
                add_log("llm", "Response generated successfully")
            else:
                add_log("llm", f"LLM error: {data}")

            return data

        except Exception as e:

            add_log("llm", f"ERROR generate: {str(e)}")

            return {"status": "ERROR", "error": str(e)}

    @staticmethod
    def health():

        try:

            r = requests.get(LLM_URL, timeout=5)

            return r.json()

        except Exception as e:

            add_log("llm", f"LLM offline: {str(e)}")

            return {"status": "OFFLINE"}