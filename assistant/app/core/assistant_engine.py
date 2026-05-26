import json
import threading
import logging
import os
import time

from app.llm.client import LLMClient
from app.voice.stt_vosk import VoskSTT
from app.voice.tts import TTS

logger = logging.getLogger("engine")


class AssistantEngine:

    def __init__(self, ui_state, face_display, config_path=None):

        self.display = face_display

        base = os.path.dirname(os.path.abspath(__file__))

        if config_path is None:
            config_path = os.path.join(base, "..", "config", "config.json")

        with open(config_path, "r") as f:
            self.config = json.load(f)

        # =========================
        # COMPONENTS
        # =========================
        self.llm = LLMClient(
            self.config["server"]["llm_url"],
            self.config["server"]["model"],
            self.config["server"]["timeout"]
        )

        self.tts = TTS(self.config["tts"]["language"])

        self.stt = VoskSTT(
            self.config["voice"]["vosk_model_path"]
        )

        # =========================
        # STATE
        # =========================
        self.user = None
        self.voice_started = False
        self.interrupt = False

    # =========================
    # USER
    # =========================
    def set_user(self, user):

        self.user = user

        self.display.set_estado(f"Hola {user}")
        self.tts.speak(f"Hola {user}")

        if not self.voice_started:
            self.voice_started = True
            threading.Thread(
                target=self._voice_loop,
                daemon=True
            ).start()

    # =========================
    # VOICE LOOP
    # =========================
    def _voice_loop(self):

        def on_speech(text):

            t = text.lower()

            stop_words = ["calla", "para", "silencio", "cállate"]

            is_stop = any(w in t for w in stop_words)

            # =========================
            # INTERRUPCIÓN
            # =========================
            if self.tts.is_speaking:

                if is_stop:
                    self.tts.stop()
                    self.display.set_estado("Escuchando")
                    self.display.set_emotion("neutral")

                return

            # =========================
            # EMOTION THINKING
            # =========================
            self.display.set_emotion("thinking")
            self.display.set_estado(f"Procesando: {text}")

            # =========================
            # STREAM LLM
            # =========================
            buffer = ""

            try:
                for token in self.llm.stream(text):

                    if self.interrupt:
                        break

                    buffer += token
                    self.display.set_estado(buffer[-40:])

            except Exception:
                buffer = self.llm.ask(text)

            # =========================
            # SPEAK
            # =========================
            self.display.set_emotion("speaking")
            self.tts.speak(buffer)

            self.display.set_estado("Escuchando")
            self.display.set_emotion("listening")

        # START
        self.stt.listen_loop(on_speech)