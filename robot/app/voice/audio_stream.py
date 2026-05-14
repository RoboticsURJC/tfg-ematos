"""
@file audio_stream.py
@brief Captura de audio desde micrófono.
"""

import queue
import sounddevice as sd


# =========================================================
# CONFIG
# =========================================================

MIC_SAMPLE_RATE = 48000
BLOCKSIZE = 8000
CHANNELS = 1
DTYPE = "int16"


# =========================================================
# COLA GLOBAL
# =========================================================

audio_queue = queue.Queue()


# =========================================================
# UTILIDADES
# =========================================================

def find_input_device(name_hint=None):
    """
    Busca dispositivo de entrada.

    @param name_hint Texto opcional para filtrar.
    @return índice dispositivo o None.
    """

    devices = sd.query_devices()

    for idx, dev in enumerate(devices):

        if dev["max_input_channels"] <= 0:
            continue

        if name_hint:

            if name_hint.lower() in dev["name"].lower():
                return idx

        else:
            return idx

    return None


# =========================================================
# CALLBACK
# =========================================================

def audio_callback(indata, frames, time_, status):
    """
    Callback de captura de audio.
    """

    if status:
        print("Audio status:", status)

    audio_queue.put(bytes(indata))


# =========================================================
# STREAM
# =========================================================

def start_stream(device_name=None):
    """
    Inicia stream de micrófono.

    @param device_name Nombre parcial dispositivo.
    @return (stream, audio_queue)
    """

    device_id = find_input_device(device_name)

    print("INPUT DEVICE:", device_id)

    stream = sd.InputStream(
        samplerate=MIC_SAMPLE_RATE,
        blocksize=BLOCKSIZE,
        dtype=DTYPE,
        channels=CHANNELS,
        device=device_id,
        callback=audio_callback
    )

    return stream, audio_queue