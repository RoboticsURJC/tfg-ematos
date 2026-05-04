from fastapi import FastAPI
import requests
import logging

app = FastAPI()

FACE_URL = "http://localhost:5000"
LLM_URL = "http://localhost:8000"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")


# =========================================================
# IDENTIFICACIÓN FACIAL
# =========================================================
@app.post("/identify")
def identify(data: dict):
    try:
        r = requests.post(
            f"{FACE_URL}/recognize",
            json={"image": data["image"]},
            timeout=10
        )

        return r.json()

    except Exception as e:
        logger.error(e)
        return {"recognized": [], "error": str(e)}


# =========================================================
# CHAT LLM
# =========================================================
@app.post("/chat")
def chat(data: dict):

    user = data.get("user", "anon")
    text = data.get("text", "")

    if not text:
        return {"error": "empty"}

    try:
        r = requests.post(
            f"{LLM_URL}/generate",
            json={
                "model": "groq",
                "prompt": text
            },
            timeout=60
        )

        out = r.json()

        return {
            "user": user,
            "response": out.get("output", "")
        }

    except Exception as e:
        return {
            "user": user,
            "response": "Error del sistema"
        }