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

    # =====================================================
    # INIT
    # =====================================================

    def __init__(
        self,
        display,
        config_path=None
    ):

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

        with open(
            config_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.config = json.load(f)

        logger.info(
            f"Config cargada: {config_path}"
        )

        # =================================================
        # SERVER
        # =================================================

        self.SERVER_URL = (
            self.config["server"]["llm_url"]
        )

        # =================================================
        # LLM
        # =================================================

        self.llm = LLMClient(
            server_url=self.SERVER_URL,
            model=self.config["server"]["model"],
            timeout=self.config["server"]["timeout"]
        )

        # =================================================
        # TTS
        # =================================================

        self.tts = TTS(
            lang=self.config["tts"]["language"]
        )

        # =================================================
        # STT
        # =================================================

        self.stt = VoskSTT(
            self.config["voice"]["vosk_model_path"]
        )

        # =================================================
        # USER
        # =================================================

        self.user = None

        # =================================================
        # FLAGS
        # =================================================

        self.voice_started = False

    # =====================================================
    # USER AUTH
    # =====================================================

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

        self.display.set_estado(
            "Escuchando..."
        )

        # iniciar voz una sola vez
        if not self.voice_started:

            self.voice_started = True

            threading.Thread(
                target=self._start_voice,
                daemon=True
            ).start()

    # =====================================================
    # VOICE LOOP
    # =====================================================

    def _start_voice(self):

        logger.info(
            "VOICE LOOP INICIADO"
        )

        # =================================================
        # CALLBACK STT
        # =================================================

        def on_speech(text):

            logger.info(
                f"USER: {text}"
            )

            text_lower = text.lower()

            # =============================================
            # STOP WORDS
            # =============================================

            stop_words = [
                "calla",
                "para",
                "silencio",
                "cállate"
            ]

            stop_command = any(
                x in text_lower
                for x in stop_words
            )

            # =============================================
            # ROBOT HABLANDO
            # =============================================

            if self.tts.is_speaking:

                # solo aceptar stop
                if stop_command:

                    logger.info(
                        "STOP COMMAND"
                    )

                    self.tts.stop()

                    self.display.set_hablando(
                        False
                    )

                    self.display.set_estado(
                        "Escuchando..."
                    )

                # ignorar resto
                return

            # =============================================
            # NORMAL FLOW
            # =============================================

            self.display.set_estado(
                f"Procesando: {text}"
            )

            try:

                respuesta = self.llm.ask(
                    text
                )

                if not respuesta:

                    respuesta = procesar_texto(
                        self.user,
                        text
                    )

            except Exception as e:

                logger.exception(
                    f"LLM ERROR: {e}"
                )

                respuesta = (
                    "He tenido un problema."
                )

            logger.info(
                f"BOT: {respuesta}"
            )

            # =============================================
            # TTS
            # =============================================

            self.display.set_estado(
                "Preparando voz..."
            )

            self.display.set_hablando(True)

            self.tts.speak(respuesta)

            self.display.set_estado(
                "Escuchando..."
            )

        # =================================================
        # START LOOP
        # =================================================

        logger.info(
            "Llamando a listen_loop"
        )

        try:

            self.stt.listen_loop(
                callback=on_speech,
                device_name=self.config[
                    "voice"
                ].get(
                    "device_name",
                    None
                )
            )

        except Exception as e:

            logger.exception(
                f"VOICE LOOP ERROR: {e}"
            )

        logger.info(
            "listen_loop TERMINÓ"
        )