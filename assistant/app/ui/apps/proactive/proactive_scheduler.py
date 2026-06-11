
import threading
import time
from app.core.logger import logger


MEMORY_SUGGESTIONS = [
    {
        "type": "memory", "title": "Ejercita tu memoria",
        "body": "Es un buen momento para jugar\na la Sopa de Letras. Te apuntas?",
        "icon": "🔤", "action": "wordsearch",
        "tts": "Es un buen momento para ejercitar la memoria. Jugamos a la sopa de letras?",
    },
    {
        "type": "memory", "title": "Entrena tu mente",
        "body": "Unas partiditas al Juego de Memoria\nson perfectas para el cerebro.",
        "icon": "🃏", "action": "memory",
        "tts": "Que te parece una partida al juego de memoria para mantener la mente agil?",
    },
    {
        "type": "memory", "title": "Pequeno reto mental",
        "body": "Llevas un rato descansando.\nUn juego rapido te vendra genial!",
        "icon": "🧠", "action": "memory",
        "tts": "Un pequeno juego te ayudara a mantenerte activo mentalmente. Empezamos?",
    },
]

MOBILITY_SUGGESTIONS = [
    {
        "type": "mobility", "title": "Hora de moverse",
        "body": "Haz 5 rotaciones de hombros\nhacia atras y 5 hacia adelante.",
        "icon": "🙆", "action": "mobility",
        "tts": "Te propongo rotar los hombros cinco veces hacia atras y cinco hacia adelante.",
    },
    {
        "type": "mobility", "title": "Estiramiento de cuello",
        "body": "Inclina la cabeza hacia la derecha\n5 segundos, luego hacia la izquierda.",
        "icon": "🧘", "action": "mobility",
        "tts": "Inclina la cabeza hacia la derecha cinco segundos y luego hacia la izquierda.",
    },
    {
        "type": "mobility", "title": "Respiracion profunda",
        "body": "Inspira 4 segundos, aguanta 4,\nespira 4 segundos. Repite 3 veces.",
        "icon": "💨", "action": "mobility",
        "tts": "Inspira cuatro segundos, aguanta cuatro, y espira cuatro. Repitelo tres veces.",
    },
    {
        "type": "mobility", "title": "Ejercicio de manos",
        "body": "Abre y cierra las manos\n10 veces despacio.",
        "icon": "🤲", "action": "mobility",
        "tts": "Abre y cierra las manos despacio diez veces.",
    },
    {
        "type": "mobility", "title": "Levantate un momento",
        "body": "Da 10 pasos por la habitacion.\nEl movimiento es salud!",
        "icon": "🚶", "action": "mobility",
        "tts": "Levantate y da diez pasitos por la habitacion.",
    },
]


class ProactiveScheduler:

    def __init__(self, tts, display=None, on_suggest=None,
                 memory_interval: int = 45 * 60,
                 mobility_interval: int = 30 * 60,
                 start_delay: int = 10 * 60):

        self.tts               = tts
        self.display           = display
        self.on_suggest        = on_suggest
        self.memory_interval   = memory_interval
        self.mobility_interval = mobility_interval
        self.start_delay       = start_delay

        self._thread    = None
        self._stop_evt  = threading.Event()   # ← Event en vez de bool: seguro entre hilos
        self._next_type = "mobility"
        self._mem_idx   = 0
        self._mob_idx   = 0

        logger.info(
            f"[PROACTIVE] Inicializado — "
            f"memoria {memory_interval}s / movilidad {mobility_interval}s / "
            f"delay {start_delay}s"
        )

    def start(self):
        # Si ya hay un hilo vivo, no crear otro
        if self._thread and self._thread.is_alive():
            logger.warning("[PROACTIVE] start() ignorado, hilo ya activo")
            return

        self._stop_evt.clear()
        # Timestamps: memoria vence tras start_delay, movilidad tras start_delay + memory_interval
        now = time.time()
        self._last_memory   = now - self.memory_interval   + self.start_delay
        self._last_mobility = now - self.mobility_interval + self.start_delay + self.memory_interval

        self._thread = threading.Thread(target=self._loop, daemon=True, name="ProactiveLoop")
        self._thread.start()
        logger.info("[PROACTIVE] Scheduler iniciado")

    def stop(self):
        self._stop_evt.set()
        logger.info("[PROACTIVE] Scheduler detenido")

    def _loop(self):
        logger.info(f"[PROACTIVE] Bucle arrancado — delay inicial {self.start_delay}s")

        # Espera interrumpible: si stop() se llama durante el delay, sale limpiamente
        if self._stop_evt.wait(timeout=self.start_delay):
            logger.info("[PROACTIVE] Detenido durante start_delay")
            return

        while not self._stop_evt.is_set():
            try:
                now     = time.time()
                mem_due = (now - self._last_memory)   >= self.memory_interval
                mob_due = (now - self._last_mobility) >= self.mobility_interval

                if mem_due or mob_due:
                    # Si ambos vencen a la vez, disparar solo uno (alternancia)
                    if mem_due and mob_due:
                        fire_type = self._next_type
                    elif mem_due:
                        fire_type = "memory"
                    else:
                        fire_type = "mobility"

                    self._fire(self._pick(fire_type))

                    # Actualizar timestamp y calcular espera exacta
                    now2 = time.time()
                    if fire_type == "memory":
                        self._last_memory = now2
                        self._next_type   = "mobility"
                        wait = self.memory_interval
                    else:
                        self._last_mobility = now2
                        self._next_type     = "memory"
                        wait = self.mobility_interval

                    logger.info(f"[PROACTIVE] Proxima sugerencia en {int(wait)}s")
                    # Espera interrumpible
                    self._stop_evt.wait(timeout=wait)

                else:
                    # Esperar exactamente hasta el próximo vencimiento
                    next_mem = self.memory_interval   - (now - self._last_memory)
                    next_mob = self.mobility_interval - (now - self._last_mobility)
                    wait = max(1.0, min(next_mem, next_mob))
                    logger.info(f"[PROACTIVE] Nada pendiente, comprobando en {int(wait)}s")
                    self._stop_evt.wait(timeout=wait)

            except Exception as e:
                logger.error(f"[PROACTIVE] Error en bucle: {e}")
                self._stop_evt.wait(timeout=10)

        logger.info("[PROACTIVE] Bucle terminado")

    def _pick(self, kind: str) -> dict:
        if kind == "memory":
            s = MEMORY_SUGGESTIONS[self._mem_idx % len(MEMORY_SUGGESTIONS)]
            self._mem_idx += 1
        else:
            s = MOBILITY_SUGGESTIONS[self._mob_idx % len(MOBILITY_SUGGESTIONS)]
            self._mob_idx += 1
        logger.info(f"[PROACTIVE] Disparando '{s['title']}'")
        return s

    def _fire(self, suggestion: dict):
        try:
            self.tts.speak(suggestion["tts"])
        except Exception as e:
            logger.error(f"[PROACTIVE] TTS error: {e}")

        if self.display:
            self.display.set_estado(f"Sugerencia: {suggestion['title'][:28]}")

        if self.on_suggest:
            try:
                self.on_suggest(suggestion)
            except Exception as e:
                logger.error(f"[PROACTIVE] on_suggest error: {e}")

    def trigger_memory(self):
        self._fire(self._pick("memory"))

    def trigger_mobility(self):
        self._fire(self._pick("mobility"))
