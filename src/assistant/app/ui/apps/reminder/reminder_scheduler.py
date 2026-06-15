# app/ui/apps/reminders/reminder_scheduler.py
import threading
import time
from datetime import datetime
from app.core.logger import logger

class ReminderScheduler:

    def __init__(self, store, tts, display=None):
        self.store = store
        self.tts = tts
        self.display = display
        self.running = False

    def start(self):
        logger.info("[REMINDER SCHEDULER] Iniciar recordatorio")
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _loop(self):
        
        logger.info("[REMINDER SCHEDULER] Bucle iniciado")
        
        while self.running:
            logger.info("[REMINDER SCHEDULER] Comprobando recordatorios")
            
            self.store.remiders = self.store.load()
            
            now = datetime.now()

            for i, r in enumerate(self.store.get_pending()):
                try:
                    logger.info(f"[REMINDER SCHEDULER] Revisando: {r}")
                    
                    r_time = datetime.strptime(r["time"], "%Y-%m-%d %H:%M")

                    if abs((r_time - now).total_seconds()) < 30:
                        
                        logger.info(f"[REMINDER SCHEDULE] Disparando {['title']}")
                        
                        msg = f" Recordatorio: {r['title']}"
                        self.tts.speak(msg)

                        r["done"] = True
                        self.store.save()

                        if self.display:
                            self.display.set_estado(msg)

                except Exception as e:
                    logger.error(f"[REMINDER SCHEDULER] Error procesando recordatorio {e}")
                    continue

            time.sleep(5)
