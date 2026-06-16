# app/core/config.py

import os
from dotenv import load_dotenv

##
# @file config.py
# @brief Módulo central de configuración y carga de variables de entorno del sistema.
# @details Consume la librería `python-dotenv` para deserializar el archivo oculto `.env` 
# e inyectar de forma segura las credenciales y llaves privadas en las variables del sistema operativo.
#

# Carga e inicialización de las variables de entorno locales desde el archivo físico `.env`
load_dotenv()

## Token de autenticación privado para el consumo de modelos OpenAI a través de Azure AI Model Inference.
AZURE_API_KEY = os.getenv("AZURE_API_KEY")

## Llave de acceso secreta (API Key) necesaria para autenticar las peticiones asíncronas en la infraestructura de Groq.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

## Credencial privada indispensable para el funcionamiento del cliente oficial del SDK de Google Gemini.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")