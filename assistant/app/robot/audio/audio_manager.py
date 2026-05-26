# app/robot/audio/audio_manager.py


class AudioManager:
    """
    Coordinador de audio:
    - TTS
    - STT
    """

    def __init__(self, tts, stt):

        self.tts = tts
        self.stt = stt

    # =========================================================
    # SPEAK
    # =========================================================

    def speak(self, text):

        self.tts.speak(text)

    # =========================================================
    # STOP SPEAKING
    # =========================================================

    def stop(self):

        self.tts.stop()
