import subprocess
import threading
import re


## @file tts.py
#  @brief Motor Text-To-Speech basado en pico2wave.
#
#  Este módulo proporciona:
#   - síntesis de voz
#   - reproducción de audio
#   - limpieza de texto Markdown
#   - reproducción asíncrona mediante hilos


## @class TTS
#  @brief Motor de voz simple basado en pico2wave.
#
#  Utiliza:
#   - pico2wave para generar audio WAV
#   - aplay para reproducir audio
#
#  Incluye soporte para:
#   - reproducción en segundo plano
#   - detener audio activo
#   - limpiar formato Markdown
class TTS:
    """
    Motor de voz simple basado en pico2wave.
    """

    ## @brief Inicializa el motor TTS.
    #
    #  @param lang Idioma utilizado por pico2wave.
    def __init__(self, lang="es-ES"):

        ## @brief Idioma de síntesis.
        self.lang = lang

        ## @brief Proceso de reproducción activo.
        self.process = None

        ## @brief Estado de reproducción.
        self.is_speaking = False

    ## @brief Limpia texto antes de sintetizar voz.
    #
    #  Elimina:
    #   - Markdown
    #   - títulos
    #   - backticks
    #   - saltos de línea excesivos
    #
    #  @param texto Texto original.
    #
    #  @return str Texto limpio listo para TTS.
    def limpiar_texto(self, texto: str) -> str:
        """
        Limpia markdown y formato raro.
        """

        # Eliminar negritas
        texto = re.sub(r"\*\*(.*?)\*\*", r"\1", texto)

        # Eliminar cursivas
        texto = re.sub(r"\*(.*?)\*", r"\1", texto)

        # Eliminar títulos markdown
        texto = re.sub(r"#+\s*", "", texto)

        # Eliminar backticks
        texto = texto.replace("`", "")

        # Reemplazar saltos de línea
        texto = re.sub(r"\n+", ". ", texto)

        return texto.strip()

    ## @brief Ejecuta internamente la síntesis de voz.
    #
    #  Genera un archivo WAV temporal y lo reproduce.
    #
    #  @param text Texto a sintetizar.
    def _speak(self, text: str):
        """
        Ejecución interna de TTS.
        """

        # Limpiar texto
        text = self.limpiar_texto(text)

        self.is_speaking = True

        # Generar WAV usando pico2wave
        subprocess.run(
            [
                "pico2wave",
                f"-l={self.lang}",
                "-w=/tmp/voice.wav",
                text
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Reproducir audio
        self.process = subprocess.Popen(
            ["aplay", "/tmp/voice.wav"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Esperar a que termine reproducción
        self.process.wait()

        self.is_speaking = False
        self.process = None

    ## @brief Inicia reproducción TTS en un hilo.
    #
    #  Permite continuar ejecución sin bloquear.
    #
    #  @param text Texto a reproducir.
    def speak(self, text: str):
        """
        Lanza TTS en hilo.
        """

        threading.Thread(
            target=self._speak,
            args=(text,),
            daemon=True
        ).start()

    ## @brief Detiene la reproducción de audio actual.
    #
    #  Finaliza el proceso de reproducción si existe.
    def stop(self):
        """
        Detiene audio si está hablando.
        """

        if self.process:
            self.process.terminate()
            self.process = None

        self.is_speaking = False