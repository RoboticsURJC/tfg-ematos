import json
import os
from datetime import datetime

## @file memoria.py
#  @brief Gestión de memoria conversacional de usuarios.
#
#  Este módulo permite cargar, guardar y consultar
#  el historial de conversaciones almacenado en JSON.

MEMORY_FILE = "memoria_usuarios.json"


## @brief Carga la memoria desde disco.
#
#  Verifica si el archivo de memoria existe y
#  devuelve su contenido como diccionario.
#
#  @return dict Memoria cargada desde el archivo.
#  @retval {} Si el archivo no existe o ocurre un error.
def cargar_memoria():
    """Carga la memoria desde disco."""
    
    if not os.path.exists(MEMORY_FILE):
        return {}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


## @brief Guarda la memoria en disco.
#
#  Serializa el diccionario de memoria en formato JSON.
#
#  @param memoria Diccionario con la información a guardar.
def guardar_memoria(memoria: dict):
    """Guarda la memoria en disco."""
    
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)


## @brief Añade una interacción al historial de un usuario.
#
#  Inserta un nuevo registro con el mensaje del usuario,
#  la respuesta del bot y la marca temporal actual.
#
#  @param memoria Diccionario de memoria global.
#  @param usuario Nombre o identificador del usuario.
#  @param texto_usuario Mensaje enviado por el usuario.
#  @param respuesta_bot Respuesta generada por el bot.
#
#  @return dict Memoria actualizada.
def agregar_interaccion(memoria, usuario, texto_usuario, respuesta_bot):
    """Añade una interacción al historial."""
    
    memoria.setdefault(usuario, []).append({
        "user": texto_usuario,
        "bot": respuesta_bot,
        "time": datetime.now().isoformat()
    })

    return memoria


## @brief Obtiene las últimas interacciones de un usuario.
#
#  Recupera un número limitado de mensajes recientes
#  almacenados en el historial.
#
#  @param memoria Diccionario de memoria global.
#  @param usuario Nombre o identificador del usuario.
#  @param limite Número máximo de interacciones a devolver.
#
#  @return list Lista con las últimas interacciones.
def obtener_historial(memoria, usuario, limite=5):
    """Devuelve últimas interacciones del usuario."""
    
    return memoria.get(usuario, [])[-limite:]