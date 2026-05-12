import sounddevice as sd
import queue


## @file audio_stream.py
#  @brief Gestión de captura de audio desde micrófono.
#
#  Este módulo permite:
#   - capturar audio en tiempo real
#   - almacenar fragmentos en una cola
#   - proporcionar datos para sistemas STT
#     (Speech To Text)


# =========================
# COLA GLOBAL DE AUDIO
# =========================

## @brief Cola FIFO utilizada para almacenar fragmentos de audio.
audio_queue = queue.Queue()


# =========================
# CALLBACK DE AUDIO
# =========================

## @brief Callback ejecutado automáticamente por sounddevice.
#
#  Recibe bloques de audio del micrófono y los añade
#  a la cola global para posterior procesamiento STT.
#
#  @param indata Datos de audio capturados.
#  @param frames Número de frames recibidos.
#  @param time Información temporal del stream.
#  @param status Estado del stream de audio.
def audio_callback(indata, frames, time, status):
    """
    Callback del micrófono.
    Mete audio en cola para STT.
    """

    # Mostrar errores/avisos del stream
    if status:
        print("Audio status:", status)

    # Guardar audio en cola
    audio_queue.put(bytes(indata))


# =========================
# STREAM DE MICRÓFONO
# =========================

## @brief Inicia la captura de audio desde el micrófono.
#
#  Configura un InputStream de sounddevice con:
#   - frecuencia de muestreo
#   - tamaño de bloque
#   - formato int16 mono
#
#  @param device Dispositivo de entrada de audio.
#                 Si es None, usa el predeterminado.
#  @param samplerate Frecuencia de muestreo en Hz.
#
#  @return tuple
#   - stream: objeto InputStream configurado.
#   - audio_queue: cola donde se almacenan los bloques de audio.
def start_stream(device=None, samplerate=48000):
    """
    Inicia stream de audio.
    """

    stream = sd.InputStream(
        samplerate=samplerate,
        blocksize=8000,
        dtype="int16",
        channels=1,
        device=device,
        callback=audio_callback
    )

    return stream, audio_queue