# app/ui/apps/reminders/reminder_scheduler.py

"""
@file reminder_scheduler.py
@brief Planificador de recordatorios basado en tiempo.
@details Ejecuta un hilo de fondo que monitorea constantemente el almacén de datos
en busca de recordatorios cuya fecha objetivo coincida con el tiempo actual.
"""

import threading
import time
from datetime import datetime
from app.core.logger import logger

class ReminderScheduler:
    """
    @brief Clase encargada de la ejecución de recordatorios programados.
    """

    def __init__(self, store, tts, display=None):
        """
        @brief Constructor del planificador.
        @param store Instancia del almacén de recordatorios (ReminderStore).
        @param tts Motor de texto a voz para notificar al usuario.
        @param display (Opcional) Objeto para actualizar el estado en pantalla.
        """
        self.store = store
        self.tts = tts
        self.display = display
        self.running = False

    def start(self):
        """
        @brief Inicia el hilo de ejecución del bucle de recordatorios.
        """
        logger.info("[REMINDER SCHEDULER] Iniciando hilo de recordatorios.")
        self.running = True
        threading.Thread(target=self._loop, daemon=True, name="ReminderLoop").start()

    def stop(self):
        """
        @brief Detiene el bucle de ejecución de forma segura.
        """
        logger.info("[REMINDER SCHEDULER] Deteniendo hilo de recordatorios.")
        self.running = False

    def _loop(self):
        """
        @brief Bucle principal de monitoreo.
        @details Comprueba cada 5 segundos si existe algún recordatorio pendiente cuya
        fecha de ejecución esté dentro de un margen de 30 segundos respecto al tiempo actual.
        """
        logger.info("[REMINDER SCHEDULER] Bucle de control iniciado.")
        
        while self.running:
            # Sincronización del estado desde disco
            self.store.reminders = self.store.load()
            now = datetime.now()

            # Filtrado de elementos pendientes
            for r in self.store.get_pending():
                try:
                    r_time = datetime.strptime(r["time"], "%Y-%m-%d %H:%M")
                    
                    # Cálculo de proximidad temporal (margen de 30 segundos)
                    if abs((r_time - now).total_seconds()) < 30:
                        
                        logger.info(f"[REMINDER SCHEDULER] Disparando: {r.get('title')}")
                        
                        msg = f"Recordatorio: {r.get('title', 'Sin título')}"
                        self.tts.speak(msg)

                        # Marcado como completado y persistencia
                        r["done"] = True
                        self.store.save()

                        if self.display:
                            self.display.set_estado(msg)
                            
                except KeyError as ke:
                    logger.error(f"[REMINDER SCHEDULER] Formato de recordatorio inválido: {ke}")
                except Exception as e:
                    logger.error(f"[REMINDER SCHEDULER] Error procesando recordatorio: {e}")
                    continue

            # Ciclo de espera para el sondeo de eventos
            time.sleep(5)
            
        logger.info("[REMINDER SCHEDULER] Bucle detenido limpiamente.")