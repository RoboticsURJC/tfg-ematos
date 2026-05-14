"""
@file stt_vosk.py
@brief Speech-To-Text usando Vosk.
"""

import json
import time
import vosk

from app.voice.audio_stream import (
    start_stream,
    audio_queue,
    MIC_SAMPLE_RATE
)


# =========================================================
# CONFIG
# =========================================================

VOSK_SAMPLE_RATE = 16000


# =========================================================
# STT
# =========================================================

class VoskSTT:
    """
    Wrapper STT basado en Vosk.
    """

    def __init__(self, model_path: str):

        self.model = vosk.Model(model_path)

        self.rec = vosk.KaldiRecognizer(
            self.model,
            VOSK_SAMPLE_RATE
        )

    # =====================================================
    # AUDIO
    # =====================================================

    def downsample_audio(self, audio_bytes: bytes):
        """
        Convierte 48kHz -> 16kHz.

        Método rápido/simple.
        """

        return audio_bytes[::3]

    # =====================================================
    # PROCESS
    # =====================================================

    def process_audio(self, audio_bytes: bytes):

        audio_16k = self.downsample_audio(
            audio_bytes
        )

        if self.rec.AcceptWaveform(audio_16k):

            result = json.loads(
                self.rec.Result()
            )

            text = result.get(
                "text",
                ""
            ).strip()

            if text:
                print("FINAL:", text)

            return text

        else:

            partial = json.loads(
                self.rec.PartialResult()
            )

            p = partial.get(
                "partial",
                ""
            )

            if p:
                print("PARCIAL:", p)

        return ""

    # =====================================================
    # LOOP
    # =====================================================

    def listen_loop(
        self,
        callback,
        device_name=None
    ):
        """
        Loop principal STT.

        callback(text)
        """

        print("Iniciando micro...")

        stream, _ = start_stream(
            device_name=device_name
        )

        stream.start()

        print("Micro iniciado")

        try:

            while True:

                data = audio_queue.get()

                text = self.process_audio(
                    data
                )

                if text:
                    callback(text)

                time.sleep(0.005)

        finally:

            stream.stop()
            stream.close()