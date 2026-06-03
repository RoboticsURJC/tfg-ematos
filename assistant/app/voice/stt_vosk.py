

"""
@file stt_vosk.py
@brief Reconocimiento de voz con Vosk (Speech-To-Text).
"""

import json
import queue
import vosk
from app.voice.audio_stream import start_stream
from app.core.logger import logger

# Palabras que interrumpen el TTS aunque esté hablando
STOP_WORDS = {"calla", "para", "silencio", "cállate", "callate", "basta", "stop"}


class VoskSTT:
    def __init__(self, model_path, sample_rate=16000):
        logger.info(f"[STT] cargando modelo: {model_path}")
        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, sample_rate)
        self.running = False
        self._stream = None
        logger.info("[STT] listo")

    def stop(self):
        logger.info("[STT] deteniendo")
        self.running = False
        if self._stream:
            self._stream.stop()

    def _flush_queue(self, q):
        vaciados = 0
        while True:
            try:
                q.get_nowait()
                vaciados += 1
            except queue.Empty:
                break
        if vaciados:
            logger.info(f"[STT] cola vaciada ({vaciados} bloques)")
        self.rec.Reset()

    def _is_stop_command(self, text):
        """Devuelve True si el texto contiene alguna palabra de parada."""
        words = set(text.lower().split())
        return bool(words & STOP_WORDS)

    def process(self, data):
        if self.rec.AcceptWaveform(data):
            result = json.loads(self.rec.Result())
            return result.get("text", "").strip()
        partial = json.loads(self.rec.PartialResult())
        p = partial.get("partial", "").strip()
        if p:
            logger.info(f"[STT] parcial: '{p}'")
        return ""

    def listen_loop(self, callback, assistant=None, device=None):
        self._stream, q = start_stream(samplerate=48000, device=device)
        self._stream.start()
        self.running = True
        logger.info("[STT] escucha iniciada")

        tts_estaba_hablando = False
        bloques = 0

        while self.running:
            try:
                data = q.get(timeout=0.5)
            except queue.Empty:
                continue

            bloques += 1
            if bloques % 50 == 0:
                nivel = max(abs(b) for b in data[::100]) if data else 0
                logger.info(f"[STT] audio OK — bloques={bloques} nivel_max={nivel}")

            tts_hablando = assistant.tts.is_speaking if assistant else False

            # --- Transición hablando → escuchando: limpiar cola ---
            if tts_estaba_hablando and not tts_hablando:
                self._flush_queue(q)
                tts_estaba_hablando = False
                logger.info("[STT] TTS terminó, escuchando de nuevo")
                continue

            tts_estaba_hablando = tts_hablando

            # --- Mientras el TTS habla: solo procesar stop words ---
            if tts_hablando:
                text = self.process(data)
                if text and self._is_stop_command(text):
                    logger.info(f"[STT] STOP WORD detectada mientras TTS habla: '{text}'")
                    callback(text)   # el callback llamará a tts.stop()
                continue

            # --- Escucha normal ---
            text = self.process(data)
            if not text:
                continue

            text = text.lower().strip()
            logger.info(f"[STT] reconocido: '{text}'")
            callback(text)

        logger.info("[STT] bucle terminado")
        
        
        
