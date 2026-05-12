import json
import time
import vosk

from app.voice.audio_stream import audio_queue


## @file stt_vosk.py
#  @brief Reconocimiento de voz usando Vosk.
#
#  Este módulo implementa un wrapper sencillo para:
#   - cargar modelos Vosk
#   - procesar audio en tiempo real
#   - detectar texto hablado
#   - ejecutar callbacks con transcripciones


## @class VoskSTT
#  @brief Wrapper de reconocimiento de voz con Vosk.
#
#  Gestiona:
#   - inicialización del modelo
#   - reconocimiento incremental
#   - bucle continuo de escucha
class VoskSTT:
    """
    Wrapper de reconocimiento de voz con Vosk.
    """

    ## @brief Inicializa el reconocedor Vosk.
    #
    #  @param model_path Ruta al modelo Vosk.
    #  @param sample_rate Frecuencia de muestreo esperada.
    def __init__(self, model_path: str, sample_rate=16000):

        ## @brief Modelo de reconocimiento Vosk.
        self.model = vosk.Model(model_path)

        ## @brief Reconocedor Kaldi asociado al modelo.
        self.rec = vosk.KaldiRecognizer(
            self.model,
            sample_rate
        )

        ## @brief Frecuencia de muestreo utilizada.
        self.sample_rate = sample_rate

    ## @brief Procesa un bloque de audio.
    #
    #  Convierte el audio a una versión reducida
    #  aproximada a 16 kHz y lo envía al reconocedor.
    #
    #  @param audio_bytes Bloque de audio en bytes.
    #
    #  @return str Texto reconocido.
    #  @retval "" Si no se detecta una frase completa.
    def process_audio(self, audio_bytes: bytes):
        """
        Procesa bloque de audio.
        """

        # Downsample simple aproximado
        audio_16k = audio_bytes[::3]

        # Procesar audio
        if self.rec.AcceptWaveform(audio_16k):

            # Resultado final de reconocimiento
            result = json.loads(self.rec.Result())

            return result.get("text", "").strip()

        return ""

    ## @brief Inicia el bucle continuo de escucha.
    #
    #  Lee audio desde la cola global y ejecuta
    #  un callback cuando detecta texto válido.
    #
    #  @param callback Función callback(texto).
    def listen_loop(self, callback):
        """
        Bucle principal de escucha.
        callback(texto)
        """

        while True:

            # Esperar nuevo bloque de audio
            data = audio_queue.get()

            # Procesar reconocimiento
            text = self.process_audio(data)

            # Ejecutar callback si hay texto
            if text:
                callback(text)

            # Pequeña pausa para reducir CPU
            time.sleep(0.005)