import json
import os
from app.core.logger import logger


class NotesStore:

    def __init__(self):
        self.path = os.path.join(os.path.dirname(__file__), "notes.json")
        self.notes = self.load()

    def load(self):
        if not os.path.exists(self.path):
            return []

        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_all(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, indent=4, ensure_ascii=False)

    def add_note(self, title, content):
        logger.info("Añadir nota")
        self.notes.append({
            "title": title,
            "content": content
        })
        self.save_all()

    def search(self, text):
        logger.info("Buscar notas")
        text = text.lower()

        return [
            n for n in self.notes
            if text in n["title"].lower()
            or text in n["content"].lower()
        ]
