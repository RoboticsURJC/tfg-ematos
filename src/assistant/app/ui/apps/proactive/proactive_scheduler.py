"""
@file proactive_scheduler.py
@brief Lanzar sugerencias proactivas de forma reactiva y limpia.
"""

import threading
import time
from app.core.logger import logger


MEMORY_SUGGESTIONS = [
    {
        "type": "memory", "title": "Ejercita tu memoria",
        "body": "Es un buen momento para jugar\na la Sopa de Letras. ¿Te apuntas?",
        "icon": "🔤", "action": "wordsearch",
        "tts": "Es un buen momento para ejercitar la memoria. ¿Jugamos a la sopa de letras?",
    },
    {
        "type": "memory", "title": "Entrena tu mente",
        "body": "Unas partiditas al Juego de Memoria\nson perfectas para el cerebro.",
        "icon": "🃏", "action": "memory",
        "tts": "¿Qué te parece una partida al juego de memoria para mantener la mente ágil?",
    },
    {
        "type": "memory", "title": "Pequeño reto mental",
        "body": "Llevas un rato descansando.\n¡Un juego rápido te vendrá genial!",
        "icon": "🧠", "action": "memory",
        "tts": "Un pequeño juego te ayudará a mantenerte activo mentalmente. ¿Empezamos?",
    },
]

MOBILITY_SUGGESTIONS = [
    {
        "type": "mobility", "title": "Hora de moverse",
        "body": "Haz 5 rotaciones de hombros\nhacia atrás y 5 hacia adelante.",
        "icon": "🙆", "action": "mobility",
        "tts": "Te propongo rotar los hombros cinco veces hacia atrás y cinco hacia adelante.",
    },
    {
        "type": "mobility", "title": "Estiramiento de cuello",
        "body": "Inclina la cabeza hacia la derecha\n5 segundos, luego hacia la izquierda.",
        "icon": "🧘", "action": "mobility",
        "tts": "Inclina la cabeza hacia la derecha cinco segundos y luego hacia la izquierda.",
    },
    {
        "type": "mobility", "title": "Respiración profunda",
        "body": "Inspira 4 segundos, aguanta 4,\nespira 4 segundos. Repite 3 veces.",
        "icon": "💨", "action": "mobility",
        "tts": "Inspira cuatro segundos, aguanta cuatro, y espira cuatro. Repítelo tres veces.",
    },
    {
        "type": "mobility", "title": "Ejercicio de manos",
        "body": "Abre y cierra las manos\n10 veces despacio.",
        "icon": "🤲", "action": "mobility",
        "tts": "Abre y cierra las manos despacio diez veces.",
    },
    {
        "type": "mobility", "title": "Levántate un momento",
        "body": "Da 10 pasos por la habitación.\n¡El movimiento es salud!",
        "icon": "🚶", "action": "mobility",
        "tts": "Levántate y da diez pasitos por la habitación.",
    },
]

# Estado al que vuelve el display cuando el asistente está en reposo.
DISPLAY_IDLE     = "Esperando activación..."
DISPLAY_AWAKE    = "Escuchando..."

# Segundos máximos que se espera respuesta de la UI antes de auto-cerrar la sugerencia.
SUGGESTION_TIMEOUT = 60


class ProactiveScheduler:

    def __init__(self, tts, display=None, on_suggest=None,
                 get_stt_state=None,
                 memory_interval: int = 45 * 60,
                 mobility_interval: int = 30 * 60,
                 start_delay: int = 10 * 60):

        self.tts               = tts
        self.display           = display
        self.on_suggest        = on_suggest
        # callable opcional → bool: devuelve True si el STT está activo (awake)
        self.get_stt_state     = get_stt_state
        self.memory_interval   = memory_interval
        self.mobility_interval = mobility_interval
        self.start_delay       = start_delay

        self._thread    = None
        self._stop_evt  = threading.Event()
        self._next_type = "mobility"
        self._mem_idx   = 0
        self._mob_idx   = 0

        # Control de estado de la sugerencia actual
        self._suggestion_active    = False
        self._suggestion_fired_at  = 0.0   # timestamp del último _fire()
        # Lock que garantiza que nunca se disparan dos sugerencias a la vez,
        # ni desde el bucle ni desde los triggers manuales.
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
        Llamar OBLIGATORIAMENTE desde la UI tanto si el usuario ACEPTA como
        si RECHAZA (Ahora no) la sugerencia interactiva.
        """
        if self._suggestion_active:
            self._suggestion_active   = False
            self._suggestion_fired_at = 0.0
            self._restore_display()
            logger.info("[PROACTIVE] Evento UI procesado: pantalla cerrada. Display restaurado.")

    def _restore_display(self):
        """
        Restaura el display al estado correcto según si el STT está activo o no.
        Así no pisamos el mensaje 'Escuchando...' si el asistente sigue despierto.
        """
        if not self.display:
            return

        if self.get_stt_state and self.get_stt_state():
            self.display.set_estado(DISPLAY_AWAKE)
            logger.info("[PROACTIVE] Display restaurado → Escuchando...")
        else:
            self.display.set_estado(DISPLAY_IDLE)
            logger.info("[PROACTIVE] Display restaurado → Esperando activación...")

    # ------------------------------------------------------------------
    # Ciclo de Control Adaptativo (Resolución a 1 segundo)
    # ------------------------------------------------------------------

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning("[PROACTIVE] start() ignorado, hilo ya activo")
            return

        self._stop_evt.clear()

        # FIX: el offset extra de movilidad se escala al intervalo para no
        # dejar _last_mobility en el futuro cuando se usan intervalos cortos
        # en desarrollo (p.ej. mobility_interval=3).
        now = time.time()
        mobility_extra = min(5 * 60, self.mobility_interval // 2)

        self._last_memory   = now - self.memory_interval   + self.start_delay
        self._last_mobility = now - self.mobility_interval + self.start_delay + mobility_extra

        self._thread = threading.Thread(target=self._loop, daemon=True, name="ProactiveLoop")
        self._thread.start()
        logger.info("[PROACTIVE] Scheduler iniciado de forma segura")

    def stop(self):
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("[PROACTIVE] Scheduler detenido completamente")

    def _loop(self):
        logger.info(f"[PROACTIVE] Bucle arrancado — Esperando delay de inicio: {self.start_delay}s")

        # Retardo inicial seguro
        if self._stop_evt.wait(timeout=self.start_delay):
            logger.info("[PROACTIVE] Detenido durante el inicio")
            return

        # Ventana de sondeo continuo de alta frecuencia
        while not self._stop_evt.is_set():
            try:
                if self._suggestion_active:
                    # FIX: auto-cierre si la UI no respondió en SUGGESTION_TIMEOUT segundos
                    if time.time() - self._suggestion_fired_at > SUGGESTION_TIMEOUT:
                        logger.warning(
                            "[PROACTIVE] Timeout de sugerencia sin respuesta de la UI — "
                            "restaurando display automáticamente"
                        )
                        self.on_suggestion_dismissed()
                    else:
                        self._stop_evt.wait(timeout=1.0)
                    continue

                now     = time.time()
                mem_due = (now - self._last_memory)   >= self.memory_interval
                mob_due = (now - self._last_mobility) >= self.mobility_interval

                if mem_due or mob_due:
                    # Selección equitativa de tipos de ejercicio
                    if mem_due and mob_due:
                        fire_type = self._next_type
                    elif mem_due:
                        fire_type = "memory"
                    else:
                        fire_type = "mobility"

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
                logger.error(f"[PROACTIVE] Error crítico en bucle interno: {e}")
                self._stop_evt.wait(timeout=5.0)

        logger.info("[PROACTIVE] Bucle terminado limpiamente")

    def _pick(self, kind: str) -> dict:
        if kind == "memory":
            s = MEMORY_SUGGESTIONS[self._mem_idx % len(MEMORY_SUGGESTIONS)]
            self._mem_idx += 1
        else:
            s = MOBILITY_SUGGESTIONS[self._mob_idx % len(MOBILITY_SUGGESTIONS)]
            self._mob_idx += 1
        return s

    def _fire(self, suggestion: dict):
        """
        Lanza la sugerencia de forma síncrona y segura.
        El lock garantiza que nunca se ejecutan dos _fire() en paralelo,
        ni desde el bucle ni desde los triggers manuales.
        """
        # Si ya hay una sugerencia activa, ignorar completamente este disparo.
        if self._suggestion_active:
            logger.warning(
                f"[PROACTIVE] Disparo ignorado (ya hay sugerencia activa): '{suggestion['title']}'"
            )
            return

        # Adquirir el lock de forma no bloqueante — si otro hilo ya lo tiene, salir.
        if not self._fire_lock.acquire(blocking=False):
            logger.warning("[PROACTIVE] Disparo ignorado (lock ocupado)")
            return

        try:
            self._suggestion_active   = True
            self._suggestion_fired_at = time.time()
            logger.info(f"[PROACTIVE] Disparando sugerencia: '{suggestion['title']}'")

            if self.display:
                self.display.set_estado(f"Sugerencia: {suggestion['title'][:28]}")

            # 1. Hablar primero — esperar a que el TTS termine antes de abrir la tarjeta UI,
            #    así la voz y la pantalla nunca se solapan con otra sugerencia anterior.
            try:
                self.tts.speak(suggestion["tts"])
                # Esperar a que el TTS termine de reproducir (máx. 15 s por seguridad)
                deadline = time.time() + 15
                while getattr(self.tts, "is_speaking", False) and time.time() < deadline:
                    if self._stop_evt.wait(timeout=0.2):
                        break  # Scheduler detenido mientras esperábamos
            except Exception as e:
                logger.error(f"[PROACTIVE] Error en TTS: {e}")

            # 2. Mostrar la tarjeta UI solo después de que el TTS haya terminado.
            if self.on_suggest and not self._stop_evt.is_set():
                try:
                    self.on_suggest(suggestion)
                except Exception as e:
                    logger.error(f"[PROACTIVE] Error al renderizar on_suggest: {e}")
                    # Rescate automático si la UI falla
                    self._suggestion_active   = False
                    self._suggestion_fired_at = 0.0
                    self._restore_display()

        finally:
            self._fire_lock.release()

    # ------------------------------------------------------------------
    # Disparos manuales (Inyecciones forzadas desde botones de testeo)
    # ------------------------------------------------------------------

    def trigger_memory(self):
        if not self._suggestion_active:
            self._fire(self._pick("memory"))

    def trigger_mobility(self):
        if not self._suggestion_active:
            self._fire(self._pick("mobility"))
