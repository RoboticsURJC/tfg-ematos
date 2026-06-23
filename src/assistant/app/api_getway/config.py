# config.py

from pathlib import Path

##
# @file config.py
# @brief Archivo de configuración global del sistema y definición de constantes.
# @details Inicializa las rutas del sistema de archivos (directorios de logs y archivos estáticos),
# define los puntos de enlace de los microservicios y configura los parámetros de red del dashboard.
#

# ==========================================
# BASE DIR
# ==========================================

## Ruta absoluta hacia el directorio base donde se encuentra este archivo de configuración.
BASE_DIR = Path(__file__).resolve().parent

# ==========================================
# STATIC / LOGS
# ==========================================

## Ruta absoluta hacia el directorio encargado de almacenar los archivos estáticos.
STATIC_DIR = BASE_DIR / "static"

## Ruta absoluta hacia el directorio encargado de almacenar los ficheros de logs físicos.
LOG_DIR = BASE_DIR / "logs"

# Asegurar la existencia de los directorios críticos en el sistema de archivos de la Raspberry Pi
STATIC_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# MICROSERVICIOS
# ==========================================

## Dirección URL local y puerto base asignados al microservicio de Reconocimiento Facial.
FACE_SERVER_URL = "http://localhost:5000"

## Dirección URL local y puerto base asignados al microservicio del Modelo de Lenguaje (LLM).
LLM_SERVER_URL = "http://localhost:8000"

# ==========================================
# DASHBOARD
# ==========================================

## Dirección de red (Host) del servidor web del Dashboard (0.0.0.0 permite conexiones de red local).
HOST = "0.0.0.0"

## Puerto de red por el cual escuchará el servidor de la interfaz del Dashboard.
PORT = 3000