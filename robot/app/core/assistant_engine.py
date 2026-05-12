import json
import threading
import logging
import os

from app.core.assistant import procesar_texto
from app.llm.client import LLMClient
from app.voice.stt_vosk import VoskSTT
from app.voice.tts import TTS
from app.ui.display import FaceDisplay

logger = logging.getLogger("engine")


class AssistantEngine:

    def __init__(self, config_path=None):

        base_dir = os.path.dirname(os.path.abspath(__file__))

        if config_path is None:
            config_path = os.path.join(base_dir, "..", "config", "config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.SERVER_URL = self.config["server"]["llm_url"]

        self.llm = LLMClient(
            server_url=self.SERVER_URL,
            model=self.config["server"]["model"],
            timeout=self.config["server"]["timeout"]
        )

        self.tts = TTS(lang=self.config["tts"]["language"])
        self.stt = VoskSTT(self.config["voice"]["vosk_model_path"])

        self.display = FaceDisplay(config_path)

        self.user = None

    # =========================
    # USER LOGIN
    # =========================
    def on_user(self, user: str):

        self.user = user

        self.display.set_estado(f"Hola {user}")

        self.tts.speak(f"Hola {user}, sistema activado")

        # VOZ
        threading.Thread(target=self._start_voice, daemon=True).start()

        # DISPLAY físico
        threading.Thread(target=self._start_display, daemon=True).start()

    # =========================
    # VOZ
    # =========================
    def _start_voice(self):

        def on_speech(text):

            self.display.set_estado(f"Procesando: {text}")

            #  LLM REAL
            respuesta = self.llm.generate(text)

            if not respuesta:
                respuesta = procesar_texto(self.user, text)

            self.display.set_hablando(True)
            self.display.set_estado("Hablando...")

            self.tts.speak(respuesta)

            self.display.set_hablando(False)
            self.display.set_estado("Escuchando...")

        self.stt.listen_loop(on_speech)

    # =========================
    # DISPLAY THREAD
    # =========================
    def _start_display(self):
        try:
            self.display.start()
        except Exception as e:
            logger.exception(f"Error display: {e}")