# app/robot/audio/stt_service.py

import queue
import json
import vosk
import sounddevice as sd


class STTService:
    """
    Speech-to-text con Vosk.
    """

    def __init__(self, model_path: str):

        self.model = vosk.Model(model_path)

        self.rec = vosk.KaldiRecognizer(
            self.model,
            16000
        )

        self.q = queue.Queue()

    # =========================================================
    # CALLBACK AUDIO
    # =========================================================

    def _callback(self, indata, frames, time, status):

        if status:
            print(status)

        self.q.put(bytes(indata))

    # =========================================================
    # LISTEN LOOP
    # =========================================================

    def listen_loop(self, callback):

        def run():

            with sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype="int16",
                channels=1,
                callback=self._callback,
            ):

                print("[STT] Listening...")

                while True:

                    data = self.q.get()

                    if self.rec.AcceptWaveform(data):

                        result = json.loads(
                            self.rec.Result()
                        )

                        text = result.get("text", "")

                        if text:
                            callback(text)

        import threading

        threading.Thread(target=run, daemon=True).start()
