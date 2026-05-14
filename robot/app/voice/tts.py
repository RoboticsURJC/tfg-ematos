import re
import threading
import subprocess


class TTS:

    def __init__(self, lang="es-ES"):
        self.lang = lang
        self.process = None
        self.is_speaking = False

    def clean(self, text):
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)
        text = re.sub(r"#+\s*", "", text)
        text = text.replace("`", "")
        text = re.sub(r"\n+", ". ", text)
        return text.strip()

    def _run(self, text):

        text = self.clean(text)
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
                ["aplay", "/tmp/voice.wav"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            self.process.wait()

        finally:
            self.process = None
            self.is_speaking = False

    def speak(self, text):
        if self.is_speaking:
            self.stop()

        threading.Thread(
            target=self._run,
            args=(text,),
            daemon=True
        ).start()

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None

        self.is_speaking = False