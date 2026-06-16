# app/ui/apps/reminders/reminder_store.py

"""
@file reminder_store.py
@brief Sistema de persistencia para recordatorios.
@details Gestiona el almacenamiento, carga y manipulación de una lista de 
recordatorios en formato JSON.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from app.core.logger import logger

class ReminderStore:
    """
    @brief Clase encargada de la persistencia de los recordatorios en disco.
    """

    def __init__(self):
        """@brief Inicializa la ruta del archivo y carga los datos existentes."""
        self.path = os.path.join(os.path.dirname(__file__), "reminders.json")
        self.reminders: List[Dict[str, Any]] = self.load()

    def load(self) -> List[Dict[str, Any]]:
        """
        @brief Carga los recordatorios desde el archivo JSON.
        @return Lista de diccionarios de recordatorios. Si el archivo no existe, retorna una lista vacía.
        """
        if not os.path.exists(self.path):
            logger.info("[REMINDER STORE] Archivo no encontrado, creando nueva lista.")
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"[REMINDER STORE] Error al cargar datos: {e}")
            return []

    def save(self) -> None:
        """@brief Persiste la lista actual de recordatorios en el archivo JSON."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, indent=4, ensure_ascii=False)
            logger.info("[REMINDER STORE] Cambios guardados correctamente.")
        except IOError as e:
            logger.error(f"[REMINDER STORE] Error al guardar datos: {e}")

    def add(self, title: str, time_str: str, rtype: str = "general") -> None:
        """
        @brief Añade un nuevo recordatorio a la lista y lo guarda.
        @param title Título del recordatorio.
        @param time_str Fecha y hora en formato 'YYYY-MM-DD HH:MM'.
        @param rtype Categoría del recordatorio (por defecto 'general').
        """
        self.reminders.append({
            "title": title,
            "time": time_str,
            "type": rtype,
            "done": False
        })
        self.save()
        logger.info(f"[REMINDER STORE] Añadido recordatorio: {title}")

    def get_pending(self) -> List[Dict[str, Any]]:
        """
        @brief Filtra y devuelve solo los recordatorios no marcados como completados.
        @return Lista de diccionarios pendientes.
        """
        pending = [r for r in self.reminders if not r.get("done", False)]
        logger.info(f"[REMINDER STORE] Se han encontrado {len(pending)} recordatorios pendientes.")
        return pending

    def mark_done(self, idx: int) -> None:
        """
        @brief Marca un recordatorio como completado según su índice.
        @param idx Índice del recordatorio en la lista.
        """
        try:
            if 0 <= idx < len(self.reminders):
                self.reminders[idx]["done"] = True
                self.save()
                logger.info(f"[REMINDER STORE] Recordatorio {idx} marcado como hecho.")
        except IndexError:
            logger.error(f"[REMINDER STORE] Error: Índice {idx} fuera de rango.")