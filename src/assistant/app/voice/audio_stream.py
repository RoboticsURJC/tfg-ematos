# app/voice/audio_stream.py

"""
@file audio_stream.py
@brief Captura de audio desde el micrófono en tiempo real.
@details Implementa la captura de audio utilizando sounddevice, realizando un 
downsampling manual de 48kHz a 16kHz, formato requerido por los modelos 
de reconocimiento de voz como Vosk.
"""



import queue
import struct
import sounddevice as sd
from app.core.logger import logger


class AudioStream:
    """
    @brief Gestiona la captura continua de audio desde el micrófono.
    @details Configura un flujo (stream) de entrada Raw, captura a 48kHz para 
    asegurar compatibilidad con hardware USB y procesa el downsampling a 16kHz
    en el callback para optimizar el consumo de la librería Vosk.
    """

    def __init__(self, device=None, samplerate=48000, blocksize=8000):
        """
        @param device  Índice o nombre del dispositivo de audio (None = default).
        @param samplerate Frecuencia de captura (48000 Hz recomendado).
        @param blocksize  Tamaño del bloque de audio por callback.
        """
        self.q = queue.Queue()
        self.samplerate = samplerate
        logger.info(f"[AUDIO] init device={device} sr={samplerate}")

        self.stream = sd.RawInputStream(
            samplerate=samplerate,
            blocksize=blocksize,
            device=device,
            dtype="int16",
            channels=1,
            callback=self._callback
        )

    def _callback(self, indata, frames, time, status):
        """
        @brief Callback interno: recibe bloques de audio y los encola.

        Aplica downsampling 3:1 (48kHz → 16kHz) tomando 1 de cada 3 muestras,
        igual que el sistema original (data[::3]).

        @param indata  Datos de audio en bruto (int16).
        @param frames  Número de frames del bloque.
        @param time    Información temporal del stream.
        @param status  Estado del stream (errores, underrun, etc.).
        """
        if status:
            logger.warning(f"[AUDIO STATUS] {status}")

        # Convertir bytes a muestras int16
        raw = bytes(indata)
        samples = struct.unpack(f"{len(raw)//2}h", raw)
        
        # Downsampling 48kHz → 16kHz: tomar 1 muestra de cada 3
        samples_16k = samples[::3]
        
        # Empaquetar de nuevo a formato de bytes para Vosk
        data_16k = struct.pack(f"{len(samples_16k)}h", *samples_16k)
        self.q.put(data_16k)

    def start(self):
        """@brief Inicia la captura de audio."""
        logger.info("[AUDIO] start")
        self.stream.start()

    def stop(self):
        """@brief Detiene la captura de audio."""
        logger.info("[AUDIO] stop")
        try:
            self.stream.stop()
            self.stream.close()
        except Exception as e:
            logger.warning(f"[AUDIO] stop error: {e}")


def encontrar_micro(nombre_clave):
    """
    @brief Busca un dispositivo de entrada por nombre parcial.

    @param nombre_clave Cadena a buscar en el nombre del dispositivo.
    @return Índice del dispositivo encontrado, o None si no existe.
    """
    dispositivos = sd.query_devices()
    for i, d in enumerate(dispositivos):
        if d["max_input_channels"] > 0 and nombre_clave.lower() in d["name"].lower():
            logger.info(f"[AUDIO] micrófono encontrado: {d['name']} (idx={i})")
            return i
    logger.warning(f"[AUDIO] micrófono '{nombre_clave}' no encontrado")
    return None


def start_stream(device=None, samplerate=48000, blocksize=8000):
    """
    @brief Crea e inicia un AudioStream listo para usar.

    @param device     Dispositivo de audio (índice o nombre).
    @param samplerate Frecuencia de muestreo de captura.
    @param blocksize  Tamaño del bloque por callback.
    @return Tupla (stream, queue) donde queue contiene bytes a 16kHz.
    """
    stream = AudioStream(device=device, samplerate=samplerate, blocksize=blocksize)
    return stream, stream.q
    
    
    
