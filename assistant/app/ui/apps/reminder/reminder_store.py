# app/ui/apps/reminders/reminder_store.py

import json
import os
from datetime import datetime
from app.core.logger import logger


class ReminderStore:

    def __init__(self):
        self.path = os.path.join(os.path.dirname(__file__), "reminders.json")
        self.reminders = self.load()

    def load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.reminders, f, indent=4, ensure_ascii=False)

    def add(self, title, time_str, rtype="general"):
        self.reminders.append({
            "title": title,
            "time": time_str,   # "2026-06-07 09:00"
            "type": rtype,
            "done": False
        })
        self.save()
        logger.info("[REMINDER STORE] Añadido recordatorio")

    def get_pending(self):
        logger.info("[REMINDER STORE] Recordatorios pendientes")
        return [r for r in self.reminders if not r["done"]]
        

    def mark_done(self, idx):
        self.reminders[idx]["done"] = True
        self.save()
