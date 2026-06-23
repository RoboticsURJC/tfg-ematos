# app/voice/stt_vosk.py

"""
@file stt_vosk.py
@brief Reconocimiento de voz local utilizando el motor Vosk (Speech-To-Text).
@details Implementa una máquina de estados para la escucha activa, gestionando 
palabras de activación (Wake Words), palabras de parada (Stop Words) y la 
coordinación con el subsistema TTS.
"""

import json
import queue
import vosk
import time
from app.voice.audio_stream import start_stream
from app.core.logger import logger

# Palabras que interrumpen el TTS aunque esté hablando
STOP_WORDS = {"calla", "para", "silencio", "cállate", "callate", "basta", "stop"}
WAKE_WORDS = {"eliot", "asistente", "rojazz", "hablame", "oye"}

# Segundos que el asistente permanece activo tras la wake word (o tras cada respuesta)
AWAKE_TIMEOUT = 60


class VoskSTT:
    
    """
    @brief Gestor del motor de reconocimiento de voz.
    @details Mantiene el estado de escucha del asistente y procesa el audio 
    entrante para detectar comandos de activación o instrucciones de voz.
    """
    
    def __init__(self, model_path, sample_rate=16000):
        
        """
        @brief Inicializa el modelo de Vosk y configura la máquina de estados.
        @param model_path Ruta al directorio que contiene el modelo acústico.
        @param sample_rate Frecuencia de muestreo esperada (default 16kHz).
        """
        
        logger.info(f"[STT] cargando modelo: {model_path}")
        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, sample_rate)
        self.awake = False
        self.awake_until = 0
        self.running = False
        self._stream = None
        logger.info("[STT] listo")

    def stop(self):
        """@brief Detiene el hilo de captura de audio y marca el servicio como no en ejecución."""
        logger.info("[STT] deteniendo")
        self.running = False
        if self._stream:
            self._stream.stop()

    def _flush_queue(self, q):
        
        """@brief Vacía la cola de audio y resetea el reconocedor (usado tras TTS)."""
        
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
        """
        @brief Verifica si el texto reconocido contiene palabras de interrupción.
        @param text El texto procesado por el reconocedor.
        @return True si contiene alguna 'stop word', False en caso contrario.
        """
        
        words = set(text.lower().split())
        return bool(words & STOP_WORDS)

    def process(self, data):
        
        """
        @brief Procesa un bloque de audio y retorna el texto si se ha completado una frase.
        @param data Bloque de audio en bytes (formato int16, 16kHz).
        @return Texto reconocido o string vacío si no hay resultado completo.
        """
        
        if self.rec.AcceptWaveform(data):
            result = json.loads(self.rec.Result())
            return result.get("text", "").strip()
        partial = json.loads(self.rec.PartialResult())
        p = partial.get("partial", "").strip()
        if p:
            logger.info(f"[STT] parcial: '{p}'")
        return ""

    def _contiene_palabra_inicio(self, text):
        
        """
        @brief Verifica si el texto reconocido contiene palabras de activación.
        @param text Texto reconocido.
        @return True si se detectó una 'wake word'.
        """
        
        words = set(text.lower().split())
        return bool(words & WAKE_WORDS)

    def activar_voz(self, seconds=AWAKE_TIMEOUT):
        
        """@brief Despierta al asistente durante un tiempo determinado."""
        
        self.awake = True
        self.awake_until = time.time() + seconds
        logger.info(f"[STT] Wake Word detectada — activo {seconds}s")

    def _renovar_awake(self):
        """@brief Extiende el tiempo de escucha activa tras cada interacción del usuario."""        
        self.awake_until = time.time() + AWAKE_TIMEOUT

    def _desactivar(self, display=None):
        
        """@brief Pone al asistente en modo reposo (Wake Word necesaria)."""
        
        self.awake = False
        self.awake_until = 0
        logger.info("[STT] volviendo a modo espera (wake word necesaria)")
        if display:
            display.set_estado("Esperando activación...")

    def listen_loop(self, callback, assistant=None, device=None):
        """
        @brief Bucle principal de escucha.
        @details Coordina:
          - La detección de palabras de parada mientras el TTS habla.
          - La lógica de 'despertar' mediante wake words.
          - La limpieza de eco tras finalizar el TTS.
        @param callback Función ejecutada al detectar una frase completa.
        @param assistant Instancia del asistente (para acceder a TTS y display).
        @param device Dispositivo de audio a utilizar.
        """
        
        display = assistant.display if assistant else None

        self._stream, q = start_stream(samplerate=48000, device=device)
        self._stream.start()
        self.running = True
        logger.info("[STT] escucha iniciada")

        # Estado inicial del display: siempre esperando activación al arrancar
        if display:
            display.set_estado("Esperando activación...")

        tts_estaba_hablando = False
        bloques = 0

        while self.running:
            try:
                data = q.get(timeout=0.5)
            except queue.Empty:
                # Aprovechar el timeout para comprobar si expiró el awake
                if self.awake and time.time() > self.awake_until:
                    self._desactivar(display)
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
                # Renovar ventana de escucha tras cada respuesta del asistente
                if self.awake:
                    self._renovar_awake()
                    if display:
                        display.set_estado("Escuchando...")
                continue

            tts_estaba_hablando = tts_hablando

            # --- Mientras el TTS habla: solo procesar stop words ---
            if tts_hablando:
                text = self.process(data)
                if text and self._is_stop_command(text):
                    logger.info(f"[STT] STOP WORD detectada mientras TTS habla: '{text}'")
                    callback(text)
                continue

            # --- Comprobar expiración de awake ---
            if self.awake and time.time() > self.awake_until:
                self._desactivar(display)

            # --- Escucha normal ---
            text = self.process(data)
            if not text:
                continue

            text = text.lower().strip()

            # --- Modo dormido: solo escuchar wake word ---
            if not self.awake:
                if self._contiene_palabra_inicio(text):
                    self.activar_voz()
                    if display:
                        display.set_estado("Escuchando...")
                continue

            # --- Modo activo: procesar texto ---
            logger.info(f"[STT] reconocido: '{text}'")
            

            # Eliminar wake word si aparece en el texto
            for ww in WAKE_WORDS:
                if text.startswith(ww):
                   text = text[len(ww):].strip()
                   break

            if text: # no llamar callback si solo era la wake word
                callback(text)

        logger.info("[STT] bucle terminado")
