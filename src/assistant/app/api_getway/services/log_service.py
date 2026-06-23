# services/log_service.py

from datetime import datetime
from threading import Lock

##
# @file log_service.py
# @brief Servicio de almacenamiento y gestión de registros de eventos (Logs) en memoria.
# @details Proporciona funciones con seguridad de hilos (Thread-safe) para añadir, consultar 
# y vaciar los registros de auditoría de los distintos componentes del sistema.
#

## Diccionario interno que almacena los registros categorizados por servicio.
_logs = {
    "llm": [],
    "recognition": [],
    "system": []
}

## Cerrojo (Mutex) de sincronización para garantizar la seguridad de hilos al acceder al diccionario de logs.
_lock = Lock()

## Límite máximo de líneas de registro que se almacenarán por cada servicio para evitar fugas de memoria.
MAX_LOGS = 300


def add_log(service: str, message: str):
    """
    @brief Añade una nueva entrada de registro para un servicio específico.
    
    Crea una estructura con la hora exacta y el mensaje recibido, la anexa a la lista del servicio 
    correspondiente y trunca el historial si supera el límite establecido en MAX_LOGS.
    Este método está protegido de forma concurrente mediante un cerrojo.
    
    @param service Nombre de la categoría o componente (ej: 'llm', 'recognition', 'system').
    @param message Texto descriptivo del evento o error que se desea registrar.
    """
    with _lock:
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "text": message
        }

        if service not in _logs:
            _logs[service] = []

        _logs[service].append(entry)

        # Si el historial supera el máximo permitido, se descartan los registros más antiguos
        if len(_logs[service]) > MAX_LOGS:
            _logs[service] = _logs[service][-MAX_LOGS:]


def get_logs(service: str):
    """
    @brief Recupera la lista completa de registros pertenecientes a un servicio.
    
    Accede al contenedor global bajo exclusión mutua para evitar lecturas sucias concurrentes.
    
    @param service Nombre del servicio a consultar.
    
    @return list Lista de diccionarios con formato {"time": "HH:MM:SS", "text": "mensaje"}.
    """
    with _lock:
        return _logs.get(service, [])


def clear_logs(service: str):
    """
    @brief Vacía por completo el historial de registros de un servicio específico.
    
    Reinicia a una lista vacía el canal indicado de manera segura.
    
    @param service Nombre del servicio cuyo log se desea limpiar.
    """
    with _lock:
        _logs[service] = []   


def get_all_logs():
    """
    @brief Obtiene una copia superficial de todo el ecosistema de logs global.
    
    Devuelve un volcado completo de todas las categorías en un diccionario para la inspección global del sistema.
    
    @return dict Diccionario donde las claves son los nombres de los servicios y los valores son sus listas de logs.
    """
    with _lock:
        return dict(_logs)