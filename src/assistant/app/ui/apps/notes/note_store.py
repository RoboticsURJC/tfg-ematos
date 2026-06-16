# app/ui/apps/notes/note_store.py

"""
@file note_store.py
@brief Motor de persistencia para la aplicación de notas.
@details Gestiona la lectura, escritura y búsqueda de objetos de tipo nota 
almacenados en formato JSON dentro del entorno local de la aplicación.
"""

import json
import os
from app.core.logger import logger


class NotesStore:
    """
    @brief Clase encargada de la persistencia de datos (CRUD) para las notas del usuario.
    """

    def __init__(self):
        """
        @brief Inicializa el almacén de datos definiendo la ruta del archivo JSON.
        """
        self.path = os.path.join(os.path.dirname(__file__), "notes.json")
        self.notes = self.load()

    def load(self):
        """
        @brief Carga la lista de notas desde el archivo JSON local.
        @return list Lista de diccionarios con la estructura de notas. Retorna una lista vacía si el archivo no existe.
        """
        if not os.path.exists(self.path):
            logger.info("[STORE] Archivo de notas no encontrado, inicializando lista vacía.")
            return []

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"[STORE] Error crítico al cargar JSON: {e}")
            return []

    def save_all(self):
        """
        @brief Persiste el estado actual de la lista `self.notes` en el archivo JSON.
        """
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.notes, f, indent=4, ensure_ascii=False)
            logger.debug("[STORE] Notas guardadas correctamente en disco.")
        except IOError as e:
            logger.error(f"[STORE] Error al escribir en disco: {e}")

    def add_note(self, title, content):
        """
        @brief Crea una nueva instancia de nota y la guarda de forma persistente.
        
        @param title Título descriptivo de la nota.
        @param content Cuerpo del texto de la nota.
        """
        logger.info(f"[STORE] Agregando nueva nota con título: {title}")
        self.notes.append({
            "title": title,
            "content": content
        })
        self.save_all()

    def search(self, text):
        """
        @brief Realiza una búsqueda insensible a mayúsculas dentro de los campos de las notas.
        
        @param text Cadena de texto a buscar en el título o contenido.
        @return list Lista filtrada de notas que coinciden con el criterio.
        """
        logger.info(f"[STORE] Ejecutando búsqueda para: '{text}'")
        search_term = text.lower()

        return [
            n for n in self.notes
            if search_term in n["title"].lower()
            or search_term in n["content"].lower()
        ]