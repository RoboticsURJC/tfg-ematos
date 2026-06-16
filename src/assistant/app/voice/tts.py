# app/voice/tts.py


"""
@file tts.py
@brief Síntesis de voz (Text-To-Speech) mediante SVOX Pico y reproducción con ALSA.
@details Utiliza la utilidad `pico2wave` para convertir texto a un archivo .wav 
temporal y `aplay` para la reproducción de audio. Incluye lógica de limpieza 
de texto para eliminar formato Markdown antes de la síntesis.
"""

import subprocess
import threading
import re
import time
from app.core.logger import logger


class TTS:
    
    """
    @brief Gestor de síntesis de voz.
    @details Mantiene el estado de la reproducción, gestiona la interrupción de 
    procesos de audio y normaliza el texto para mejorar la calidad de lectura.
    """
    
    def __init__(self, lang="es-ES"):
        
        """
        @brief Inicializa el motor TTS.
        @param lang Código de idioma (default: "es-ES").
        """
        
        self.lang = lang
        self.process = None
        self.is_speaking = False
        self._done_event = threading.Event()
        self._done_event.set()
        self._stop_event = threading.Event()
        
        logger.info(f"[TTS] init lang={lang}")

    def clean(self, text):
        """
        @brief Elimina formato Markdown y caracteres especiales del texto.
        @details Filtra asteriscos, encabezados, bloques de código, links y otros 
        símbolos que podrían ser leídos literalmente por el motor de síntesis.
        @param text Texto original.
        @return Texto normalizado listo para ser sintetizado.
        """
        
        
        # Negrita e itálica
        text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
        # Encabezados
        text = re.sub(r"#+\s*", "", text)
        # Listas numeradas
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
        # Listas con guión o asterisco
        text = re.sub(r"^\s*[-*•]\s+", "", text, flags=re.MULTILINE)
        # Código inline y bloques
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"`([^`]*)`", r"\1", text)
        # Corchetes y paréntesis de links  [texto](url)
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
        # Corchetes sueltos
        text = re.sub(r"[\[\]]", "", text)
        # Símbolos que pico2wave lee en voz alta
        text = re.sub(r"[_~|><^\\]", "", text)
        # Múltiples espacios/saltos
        text = re.sub(r"\n+", ". ", text)
        text = re.sub(r"\s{2,}", " ", text)
        # Puntuación duplicada
        text = re.sub(r"\.{2,}", ".", text)
        return text.strip()

    def speak(self, text, on_done=None):
        """
        @brief Inicia la síntesis y reproducción de audio en un hilo independiente.
        @details Activa `is_speaking` inmediatamente para sincronizar con el STT, 
        genera el audio y gestiona la interrupción del proceso vía `_stop_event`.
        @param text Texto a pronunciar.
        @param on_done Callback opcional a ejecutar al finalizar.
        """
        
        # Activar ANTES del hilo (evita race condition con STT)
        self.is_speaking = True
        self._done_event.clear()
        self._stop_event.clear()

        def _run():
            clean_text = self.clean(text)
            logger.info(f"[TTS] hablando: {clean_text[:80]}")
            logger.info(f"[TTS] hile={threading.get_ident()}")
            try:
                subprocess.run(
                    ["pico2wave", f"-l={self.lang}", "-w=/tmp/voice.wav", clean_text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=15
                )
                
                if self._stop_event.is_set():
                    logger.info("[TTS] Cancelado antes de reproducir")
                    return
                    
                self.process = subprocess.Popen(
                    ["aplay", "/tmp/voice.wav"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                logger.info(f"[TTS] PID aplay={self.process.pid}")
                # ~ self.process.wait()
                
                while self.process.poll() is None:
                    if self._stop_event.is_set():
                        try:
                            self.process.kill()
                        except Exception:
                            pass
                        return
                        
                    time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"[TTS] error: {e}")
            finally:
                self.is_speaking = False
                self.process = None
                self._done_event.set()
                
                if on_done:
                   on_done()
                logger.info("[TTS] fin")

        threading.Thread(target=_run, daemon=True).start()

    def wait_until_done(self, timeout=None):
        """
        @brief Bloquea la ejecución hasta que la reproducción actual finalice.
        @param timeout Tiempo máximo de espera en segundos.
        @return True si finalizó, False si hubo timeout.
        """
        return self._done_event.wait(timeout=timeout)

    def stop(self):
        """
        @brief Detiene de forma agresiva cualquier proceso de síntesis o audio activo.
        @details Utiliza `SIGKILL` para asegurar que el hardware de audio se libere 
        inmediatamente, limpiando también procesos residuales con `pkill`.
        """
        
        
        logger.info("[TTS] stop solicitado")
        
        self._stop_event.set()
        
        # Matar el proceso aplay activo
        if self.process:
            logger.info(f"[TTS] matado PID={self.process.pid} poll={self.process.poll()} ")
            try:
                self.process.kill()   # SIGKILL, más agresivo que terminate()
            except Exception:
                pass
        # Matar cualquier proceso aplay/pico2wave residual del sistema
        try:
            subprocess.run(["pkill", "-9", "-f", "aplay"], stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-9", "-f", "pico2wave"], stderr=subprocess.DEVNULL)
            result = subprocess.run(
                ["pgrep", "-a", "aplay"],
                capture_output=True,
                text=True
            )
            
            logger.info(f"[TTS] aplay restantes: {result.stdout}")
            
        except Exception:
            pass
        self.is_speaking = False
        self.process = None
        self._done_event.set()
