import json
import threading
import logging
import os

from app.core.assistant import procesar_texto
from app.llm.client import LLMClient
from app.voice.stt_vosk import VoskSTT
from app.voice.tts import TTS


logger = logging.getLogger("engine")


class AssistantEngine:

    def __init__(self, display, config_path=None):

        self.display = display

        base_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        if config_path is None:

            config_path = os.path.join(
                base_dir,
                "..",
                "config",
                "config.json"
            )

        with open(config_path, "r", encoding="utf-8") as f:

            self.config = json.load(f)

        self.SERVER_URL = self.config["server"]["llm_url"]

        # =========================
        # LLM
        # =========================
        self.llm = LLMClient(
            server_url=self.SERVER_URL,
            model=self.config["server"]["model"],
            timeout=self.config["server"]["timeout"]
        )

        # =========================
        # VOICE
        # =========================
        self.tts = TTS(
            lang=self.config["tts"]["language"]
        )

        self.stt = VoskSTT(
            self.config["voice"]["vosk_model_path"]
        )

        self.user = None

        self.voice_started = False

    # =========================
    # USER AUTH
    # =========================
    def on_user(self, user: str):

        self.user = user

        logger.info(
            f"Usuario autenticado: {user}"
        )

        self.display.set_estado(
            f"Hola {user}"
        )

        self.display.set_hablando(True)

        self.tts.speak(
            f"Hola {user}, sistema activado"
        )

        self.display.set_hablando(False)

        # iniciar voz SOLO UNA VEZ
        if not self.voice_started:

            self.voice_started = True

            threading.Thread(
                target=self._start_voice,
                daemon=True
            ).start()

    # =========================
    # VOICE LOOP
    # =========================
    def _start_voice(self):

        def on_speech(text):

            logger.info(f"USER: {text}")

            self.display.set_estado(
                f"Procesando: {text}"
            )

            # =========================
            # LLM
            # =========================
            respuesta = self.llm.generate(text)

            # fallback
            if not respuesta:

                respuesta = procesar_texto(
                    self.user,
                    text
                )

            # =========================
            # SPEAK
            # =========================
            self.display.set_hablando(True)

            self.display.set_estado(
                "Hablando..."
            )

            self.tts.speak(respuesta)

            self.display.set_hablando(False)

            self.display.set_estado(
                "Escuchando..."
            )

        self.stt.listen_loop(on_speech)