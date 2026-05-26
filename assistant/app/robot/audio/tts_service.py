# app/robot/audio/tts_service.py

import threading
import pyttsx3


class TTSService:
    """
    Text-to-Speech simple y offline.
    """

    def __init__(self, config=None):

        self.engine = pyttsx3.init()

        self.is_speaking = False

        self._stop_flag = False

        # velocidad
        self.engine.setProperty("rate", 170)

    # =========================================================
    # SPEAK
    # =========================================================

    def speak(self, text: str):

        def run():

            self.is_speaking = True
            self._stop_flag = False

            try:
                self.engine.say(text)
                self.engine.runAndWait()

            except Exception as e:
                print("[TTS ERROR]", e)

            self.is_speaking = False

        threading.Thread(target=run, daemon=True).start()

    # =========================================================
    # STOP
    # =========================================================

    def stop(self):

        self._stop_flag = True

        try:
            self.engine.stop()
        except Exception:
            pass
