import os
from dotenv import load_dotenv

##
# @file config.py
# @brief Gestión de variables de entorno y claves de API.
#
# Este módulo centraliza la carga de credenciales sensibles desde un archivo
# .env, evitando la exposición directa de claves en el código fuente.
#

##
# @brief Carga las variables de entorno desde el archivo .env.
#
load_dotenv()

##
# @brief Clave de API para servicios de Azure.
#
AZURE_API_KEY = os.getenv("AZURE_API_KEY")

##
# @brief Clave de API para servicios de Groq.
#
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

##
# @brief Clave de API para servicios de Google Gemini.
#
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")