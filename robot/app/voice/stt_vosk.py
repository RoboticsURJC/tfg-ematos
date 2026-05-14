import json
import time
import vosk
from app.voice.audio_stream import start_stream


class VoskSTT:

    def __init__(self, model_path, sample_rate=16000):

        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, sample_rate)

        self.sample_rate = sample_rate

        # WAKE WORD
        self.wake_word = "robot"
        self.active = False

    def process_audio(self, data):

        if self.rec.AcceptWaveform(data):

            result = json.loads(self.rec.Result())
            text = result.get("text", "").strip()

            if text:
                return text

        return ""

    def listen_loop(self, callback, device_name=None):

        stream, q = start_stream(device_name)
        stream.start()

        print("Micro activo")

        while True:

            data = q.get()

            data_16k = data[::3]

            text = self.process_audio(data_16k)

            if not text:
                continue

            print("STT:", text)

            # =========================
            # WAKE WORD
            # =========================
            if not self.active:

                if self.wake_word in text.lower():
                    self.active = True
                    print("WAKE ACTIVATED")

                continue

            callback(text)
            time.sleep(0.01)