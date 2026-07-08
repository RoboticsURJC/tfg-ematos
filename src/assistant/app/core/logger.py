# app/core/logger.py

import json
import logging
import os
from app.core.logs_to_server import RemoteHandler

##
# @file logger.py
# @brief Configuración e inicialización del sistema de logs centralizado del robot.
# @details Instancia un objeto Logger único ("robot") provisto de un doble canal de salida:
# 1. Un manejador de consola estándar (StreamHandler) para depuración en terminal local.
# 2. Un manejador HTTP remoto (RemoteHandler) conectado al Dashboard web de control.
#

# ==========================================================
# CONFIG
# ==========================================================

## Ruta absoluta construida dinámicamente hacia el archivo de configuración JSON.
config_path = os.path.join(
    os.path.dirname(__file__),
    "../config/config.json"
)

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

SERVER_URL = config["server"]["log"]

## URL completa y absoluta del endpoint HTTP del Dashboard donde se transmitirán las trazas en tiempo real.
#SERVER_URL = "http://10.42.0.1:3000/client-log" 


# ==========================================================
# LOGGER
# ==========================================================

## Instancia global del Logger bajo el espacio de nombres de la aplicación "robot".
logger = logging.getLogger("robot")

# Establecer de forma base el nivel de captura más bajo permisible para auditorías completas
logger.setLevel(logging.DEBUG)

# Bloque condicional crítico de salvaguarda: evalúa si la lista de manejadores está vacía.
# Esto evita que sucesivas importaciones del módulo dupliquen los handlers e impriman mensajes repetidos en consola.
if not logger.handlers:

    # --------------------------
    # Consola local
    # --------------------------
    ## Manejador encargado de formatear y volcar los logs directamente en la salida de comandos (stdout/stderr).
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console)

    # --------------------------
    # Remoto (Dashboard)
    # --------------------------
    ## Manejador personalizado encargado de realizar peticiones HTTP POST asíncronas hacia el servidor central.
    remote = RemoteHandler(SERVER_URL)
    remote.setLevel(logging.DEBUG)
    logger.addHandler(remote)

## Desactiva la propagación hacia el Logger raíz (Root Logger) de Python para evitar duplicidad de trazas de librerías terceras.
logger.propagate = False
