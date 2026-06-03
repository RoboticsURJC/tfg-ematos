

"""
@file audio_stream.py
@brief Captura de audio desde el micrófono en tiempo real.

Captura a 48kHz (compatible con la mayoría de micrófonos USB)
y hace downsampling manual a 16kHz para Vosk, igual que el original.
"""

import queue
import sounddevice as sd
from app.core.logger import logger


class AudioStream:
    """
    @brief Gestiona la captura continua de audio desde el micrófono.

    Captura a 48kHz y hace downsampling x3 → 16kHz para Vosk.
    Esto replica el comportamiento del sistema original y garantiza
    compatibilidad con micrófonos USB que no soportan 16kHz nativo.
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

        raw = bytes(indata)
        # Downsampling 48kHz → 16kHz: tomar 1 muestra de cada 3
        # Cada muestra int16 = 2 bytes → paso de 6 bytes
        downsampled = raw[::6] + raw[1::6]  # reconstruir pares de bytes
        # Método más correcto: slice por muestra completa (2 bytes = 1 muestra)
        # Reconstruimos seleccionando muestras completas
        import struct
        samples = struct.unpack(f"{len(raw)//2}h", raw)
        samples_16k = samples[::3]
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
    
    
    
