# app/ui/apps/calendar/calendar_store.py

import json
import os

##
# @file calendar_store.py
# @brief Gestor de persistencia local para el almacenamiento de eventos de la agenda.
# @details Implementa una capa de abstracción sobre un archivo plano en formato JSON para 
# guardar, listar y eliminar eventos cronológicos de forma síncrona, manteniendo una copia activa en memoria RAM.
#

class CalendarStore:
    """
    @brief Clase encargada del almacenamiento y serialización física de los eventos en disco.
    """

    def __init__(self):
        """
        @brief Constructor de la clase CalendarStore.
        @details Modela la ruta absoluta hacia el archivo `events.json` de manera dinámica 
        tomando como base la ubicación de este script e inicializa el caché de eventos en memoria RAM.
        """
        ## Ruta absoluta mapeada del archivo de almacenamiento físico JSON.
        self.path = os.path.join(os.path.dirname(__file__), "events.json")
        
        ## Lista/Caché en memoria que almacena los diccionarios con la estructura de eventos vigentes.
        self.events = self.load()

    def load(self):
        """
        @brief Lee y deserializa el archivo JSON alojado en el disco.
        @details Evalúa de forma preventiva si el archivo físico existe. En caso de ausencia, 
        retorna un vector vacío para mitigar fallos de puntero en el primer arranque del módulo.
        
        @return list Lista de diccionarios con la estructura interna de los eventos registrados.
        """
        if not os.path.exists(self.path):
            return []

        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        """
        @brief Serializa y escribe el estado actual de la lista de eventos en el disco.
        @details Fuerza el uso del formato UTF-8 desactivando la bandera `ensure_ascii` para 
        preservar la integridad de los caracteres del castellano (acentos, diéresis, eñes) e inyecta un indentado de 4 espacios.
        """
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.events, f, indent=4, ensure_ascii=False)

    def add_event(self, date, title):
        """
        @brief Inserta un nuevo recordatorio en la estructura de datos y consolida el cambio en disco.
        
        @param date Cadena de texto con formato cronológico estandarizado (ej: 'yyyy-MM-dd').
        @param title Texto descriptivo o cuerpo del evento anotado por el usuario.
        """
        self.events.append({
            "date": date,
            "title": title
        })
        self.save()

    def get_events(self, date):
        """
        @brief Filtra y recupera por lista de comprensión los eventos asociados a una fecha específica.
        
        @param date Cadena con la fecha de consulta formateada bajo la máscara 'yyyy-MM-dd'.
        
        @return list Colección segmentada de diccionarios cuyos campos 'date' coinciden con el parámetro.
        """
        return [e for e in self.events if e["date"] == date]

    def delete_event(self, index):
        """
        @brief Elimina físicamente un evento del registro utilizando su índice de posicionamiento secuencial.
        @details Implementa una cláusula de guarda para validar que el índice solicitado se encuentra 
        dentro de los límites lógicos del vector (`0 <= index < len`), previniendo excepciones fatales de desbordamiento (`IndexError`).
        
        @param index Posición numérica entera (ID de matriz) del objeto que se desea remover de la colección.
        """
        if 0 <= index < len(self.events):
            del self.events[index]
            self.save()