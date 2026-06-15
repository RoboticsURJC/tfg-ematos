from datetime import datetime


## @file datetime_tools.py
#  @brief Utilidades de fecha y hora.
#
#  Este módulo proporciona funciones simples para:
#   - obtener la hora actual
#   - obtener la fecha actual
#   - devolver formatos legibles para usuarios


## @brief Obtiene la hora actual del sistema.
#
#  Devuelve la hora local en formato:
#   HH:MM:SS
#
#  @return str Hora actual formateada.
def get_time() -> str:
    """
    Devuelve la hora actual en formato legible.
    """

    return datetime.now().strftime("%H:%M:%S")


## @brief Obtiene la fecha actual del sistema.
#
#  Devuelve la fecha local en formato:
#   DD/MM/YYYY
#
#  @return str Fecha actual formateada.
def get_date() -> str:
    """
    Devuelve la fecha actual.
    """

    return datetime.now().strftime("%d/%m/%Y")