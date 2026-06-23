# app/core/proactive_scheduler.py

"""
@file proactive_scheduler.py
@brief Sistema de gestión proactiva de tareas para el bienestar del usuario.
@details Implementa un planificador basado en hilos (threading) que dispara sugerencias 
de memoria y movilidad de forma periódica y no intrusiva. Incluye control de estados,
bloqueos de seguridad (locks) y sincronización con sistemas de TTS y UI.
"""

import threading
import time
from app.core.logger import logger

## Colección de ejercicios cognitivos para la estimulación de la memoria.
MEMORY_SUGGESTIONS = [
    {
        "type": "memory", "title": "Ejercita tu memoria",
        "body": "Es un buen momento para jugar\na la Sopa de Letras. ¿Te apuntas?",
        "icon": "", "action": "wordsearch",
        "tts": "Es un buen momento para ejercitar la memoria. ¿Jugamos a la sopa de letras?",
    },
    {
        "type": "memory", "title": "Entrena tu mente",
        "body": "Unas partiditas al Juego de Memoria\nson perfectas para el cerebro.",
        "icon": "", "action": "memory",
        "tts": "¿Qué te parece una partida al juego de memoria para mantener la mente ágil?",
    },
    {
        "type": "memory", "title": "Pequeño reto mental",
        "body": "Llevas un rato descansando.\n¡Un juego rápido te vendrá genial!",
        "icon": "", "action": "memory",
        "tts": "Un pequeño juego te ayudará a mantenerte activo mentalmente. ¿Empezamos?",
    },
]

## Colección de ejercicios de movilidad física para mejorar la circulación y reducir la rigidez.
MOBILITY_SUGGESTIONS = [
    {
        "type": "mobility", "title": "Hora de moverse",
        "body": "Haz 5 rotaciones de hombros\nhacia atrás y 5 hacia adelante.",
        "icon": "", "action": "mobility",
        "tts": "Te propongo rotar los hombros cinco veces hacia atrás y cinco hacia adelante.",
    },
    {
        "type": "mobility", "title": "Estiramiento de cuello",
        "body": "Inclina la cabeza hacia la derecha\n5 segundos, luego hacia la izquierda.",
        "icon": "", "action": "mobility",
        "tts": "Inclina la cabeza hacia la derecha cinco segundos y luego hacia la izquierda.",
    },
    {
        "type": "mobility", "title": "Respiración profunda",
        "body": "Inspira 4 segundos, aguanta 4,\nespira 4 segundos. Repite 3 veces.",
        "icon": "", "action": "mobility",
        "tts": "Inspira cuatro segundos, aguanta cuatro, y espira cuatro. Repítelo tres veces.",
    },
    {
        "type": "mobility", "title": "Ejercicio de manos",
        "body": "Abre y cierra las manos\n10 veces despacio.",
        "icon": "", "action": "mobility",
        "tts": "Abre y cierra las manos despacio diez veces.",
    },
    {
        "type": "mobility", "title": "Levántate un momento",
        "body": "Da 10 pasos por la habitación.\n¡El movimiento es salud!",
        "icon": "", "action": "mobility",
        "tts": "Levántate y da diez pasitos por la habitación.",
    },
]

## Etiqueta de estado para cuando el asistente está en reposo.
DISPLAY_IDLE     = "Esperando activación..."
## Etiqueta de estado para cuando el asistente está procesando voz.
DISPLAY_AWAKE    = "Escuchando..."
## Segundos límite de espera para la respuesta de la UI antes de auto-cancelar la sugerencia.
SUGGESTION_TIMEOUT = 60


class ProactiveScheduler:
    """
    @brief Clase encargada de programar y ejecutar disparos proactivos de sugerencias.
    """

    def __init__(self, tts, display=None, on_suggest=None,
                 get_stt_state=None,
                 memory_interval: int = 45 * 60,
                 mobility_interval: int = 30 * 60,
                 start_delay: int = 10 * 60):
        """
        @brief Constructor del planificador proactivo.
        
        @param tts Motor de texto a voz para la locución de las sugerencias.
        @param display Objeto de control de la pantalla para mostrar mensajes de estado.
        @param on_suggest Callback invocado para renderizar la tarjeta de sugerencia en la UI.
        @param get_stt_state Función que devuelve un booleano sobre si el sistema escucha activamente.
        @param memory_interval Intervalo en segundos entre sugerencias de memoria.
        @param mobility_interval Intervalo en segundos entre sugerencias de movilidad.
        @param start_delay Tiempo de espera inicial tras el inicio antes de la primera sugerencia.
        """
        self.tts               = tts
        self.display           = display
        self.on_suggest        = on_suggest
        self.get_stt_state     = get_stt_state
        self.memory_interval   = memory_interval
        self.mobility_interval = mobility_interval
        self.start_delay       = start_delay

        self._thread    = None
        self._stop_evt  = threading.Event()
        self._next_type = "mobility"
        self._mem_idx   = 0
        self._mob_idx   = 0

        self._suggestion_active    = False
        self._suggestion_fired_at  = 0.0   
        self._fire_lock            = threading.Lock()

        logger.info(
            f"[PROACTIVE] Inicializado — "
            f"memoria {memory_interval}s / movilidad {mobility_interval}s / "
            f"delay {start_delay}s"
        )

    # ------------------------------------------------------------------
    # API pública para la sincronización con la UI
    # ------------------------------------------------------------------

    def on_suggestion_dismissed(self):
        """
        @brief Procesa el cierre de una sugerencia, sea aceptada o rechazada.
        @details Limpia el estado interno y restaura el mensaje del display al modo reposo.
        """
        if self._suggestion_active:
            self._suggestion_active   = False
            self._suggestion_fired_at = 0.0
            self._restore_display()
            logger.info("[PROACTIVE] Evento UI procesado: pantalla cerrada. Display restaurado.")

    def _restore_display(self):
        """
        @brief Función interna para restaurar el texto en pantalla según el estado del STT.
        """
        if not self.display:
            return

        if self.get_stt_state and self.get_stt_state():
            self.display.set_estado(DISPLAY_AWAKE)
            logger.info("[PROACTIVE] Display restaurado -> Escuchando...")
        else:
            self.display.set_estado(DISPLAY_IDLE)
            logger.info("[PROACTIVE] Display restaurado -> Esperando activación...")

    # ------------------------------------------------------------------
    # Ciclo de Control Adaptativo
    # ------------------------------------------------------------------

    def start(self):
        """
        @brief Inicia el hilo de control para el sondeo de sugerencias.
        """
        if self._thread and self._thread.is_alive():
            logger.warning("[PROACTIVE] start() ignorado, hilo ya activo")
            return

        self._stop_evt.clear()
        now = time.time()
        mobility_extra = min(5 * 60, self.mobility_interval // 2)

        self._last_memory   = now - self.memory_interval   + self.start_delay
        self._last_mobility = now - self.mobility_interval + self.start_delay + mobility_extra

        self._thread = threading.Thread(target=self._loop, daemon=True, name="ProactiveLoop")
        self._thread.start()
        logger.info("[PROACTIVE] Scheduler iniciado de forma segura")

    def stop(self):
        """
        @brief Detiene de forma controlada el hilo de ejecución del scheduler.
        """
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("[PROACTIVE] Scheduler detenido completamente")

    def _loop(self):
        """
        @brief Bucle principal de control que gestiona los tiempos de disparo.
        @details Evalúa el transcurso del tiempo respecto a los intervalos configurados 
        y delega el disparo de las sugerencias.
        """
        logger.info(f"[PROACTIVE] Bucle arrancado — Esperando delay de inicio: {self.start_delay}s")

        if self._stop_evt.wait(timeout=self.start_delay):
            logger.info("[PROACTIVE] Detenido durante el inicio")
            return

        while not self._stop_evt.is_set():
            try:
                if self._suggestion_active:
                    if time.time() - self._suggestion_fired_at > SUGGESTION_TIMEOUT:
                        logger.warning("[PROACTIVE] Timeout de sugerencia — restaurando display")
                        self.on_suggestion_dismissed()
                    else:
                        self._stop_evt.wait(timeout=1.0)
                    continue

                now     = time.time()
                mem_due = (now - self._last_memory)   >= self.memory_interval
                mob_due = (now - self._last_mobility) >= self.mobility_interval

                if mem_due or mob_due:
                    if mem_due and mob_due: fire_type = self._next_type
                    elif mem_due:           fire_type = "memory"
                    else:                   fire_type = "mobility"

                    self._fire(self._pick(fire_type))

                    now2 = time.time()
                    if fire_type == "memory":
                        self._last_memory = now2
                        self._next_type   = "mobility"
                    else:
                        self._last_mobility = now2
                        self._next_type     = "memory"

                self._stop_evt.wait(timeout=1.0)
            except Exception as e:
                logger.error(f"[PROACTIVE] Error crítico en bucle: {e}")
                self._stop_evt.wait(timeout=5.0)

    def _pick(self, kind: str) -> dict:
        """
        @brief Selecciona la siguiente sugerencia de la lista, alternando por índice.
        @param kind Tipo de sugerencia ('memory' o 'mobility').
        @return dict Diccionario con los datos de la sugerencia seleccionada.
        """
        if kind == "memory":
            s = MEMORY_SUGGESTIONS[self._mem_idx % len(MEMORY_SUGGESTIONS)]
            self._mem_idx += 1
        else:
            s = MOBILITY_SUGGESTIONS[self._mob_idx % len(MOBILITY_SUGGESTIONS)]
            self._mob_idx += 1
        return s

    def _fire(self, suggestion: dict):
        """
        @brief Ejecuta el disparo de una sugerencia de forma segura y síncrona.
        @details Utiliza un Lock para evitar colisiones entre el bucle y los disparos manuales.
        @param suggestion Objeto que contiene los metadatos de la sugerencia.
        """
        if self._suggestion_active:
            return

        if not self._fire_lock.acquire(blocking=False):
            return

        try:
            self._suggestion_active   = True
            self._suggestion_fired_at = time.time()
            logger.info(f"[PROACTIVE] Disparando: '{suggestion['title']}'")

            if self.display:
                self.display.set_estado(f"Sugerencia: {suggestion['title'][:28]}")

            try:
                self.tts.speak(suggestion["tts"])
                deadline = time.time() + 15
                while getattr(self.tts, "is_speaking", False) and time.time() < deadline:
                    if self._stop_evt.wait(timeout=0.2): break
            except Exception as e:
                logger.error(f"[PROACTIVE] Error en TTS: {e}")

            if self.on_suggest and not self._stop_evt.is_set():
                try:
                    self.on_suggest(suggestion)
                except Exception as e:
                    logger.error(f"[PROACTIVE] Error en on_suggest: {e}")
                    self._suggestion_active = False
                    self._restore_display()
        finally:
            self._fire_lock.release()

    def trigger_memory(self):
        """@brief Inyección manual de una sugerencia de memoria."""
        if not self._suggestion_active: self._fire(self._pick("memory"))

    def trigger_mobility(self):
        """@brief Inyección manual de una sugerencia de movilidad."""
        if not self._suggestion_active: self._fire(self._pick("mobility"))
