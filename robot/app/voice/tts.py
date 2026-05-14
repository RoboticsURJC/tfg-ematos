"""
@file tts.py
@brief Motor TTS basado en pico2wave.
"""

import re
import threading
import subprocess


class TTS:

    def __init__(self, lang="es-ES"):

        self.lang = lang

        self.process = None

        self.is_speaking = False

    # =====================================================
    # CLEAN TEXT
    # =====================================================

    def clean_text(self, text: str):

        text = re.sub(
            r"\*\*(.*?)\*\*",
            r"\1",
            text
        )

        text = re.sub(
            r"\*(.*?)\*",
            r"\1",
            text
        )

        text = re.sub(
            r"#+\s*",
            "",
            text
        )

        text = re.sub(
            r"\d+\.\s*",
            "",
            text
        )

        text = re.sub(
            r"^\s*-\s+",
            " ",
            text,
            flags=re.MULTILINE
        )

        text = text.replace("`", "")

        text = re.sub(
            r"\n+",
            ". ",
            text
        )

        return text.strip()

    # =====================================================
    # INTERNAL
    # =====================================================

    def _speak(self, text: str):

        text = self.clean_text(text)

        self.is_speaking = True

        try:

            subprocess.run(
                [
                    "pico2wave",
                    f"-l={self.lang}",
                    "-w=/tmp/voice.wav",
                    text
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.process = subprocess.Popen(
                [
                    "aplay",
                    "/tmp/voice.wav"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.process.wait()

        finally:

            self.process = None

            self.is_speaking = False

    # =====================================================
    # PUBLIC
    # =====================================================

    def speak(self, text: str):

        # detener si ya habla
        if self.is_speaking:
            self.stop()

        threading.Thread(
            target=self._speak,
            args=(text,),
            daemon=True
        ).start()

    def stop(self):

        if self.process:

            self.process.terminate()

            self.process = None

        self.is_speaking = False