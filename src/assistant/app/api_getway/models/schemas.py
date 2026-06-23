# models/schemas.py

from pydantic import BaseModel
from typing import List

##
# @file schemas.py
# @brief Esquemas de datos y modelos de validación (Pydantic) para la API.
# @details Define las estructuras de entrada (Requests) y salida (Responses) de los endpoints,
# asegurando la tipificación correcta en todo el sistema.
#


# =====================================================
# LLM
# =====================================================

class GenerateRequest(BaseModel):
    """
    @brief Modelo de petición para la generación de texto con LLM.
    
    @var model Nombre del modelo de lenguaje que se desea utilizar (ej: 'llama3', 'mistral').
    @var prompt Texto de instrucción o pregunta guía para enviar al modelo.
    """
    model: str
    prompt: str


class GenerateResponse(BaseModel):
    """
    @brief Modelo de respuesta tras una solicitud de generación con LLM.
    
    @var status Estado del resultado de la operación (ej: 'success', 'error').
    @var model Nombre del modelo que procesó la solicitud (opcional).
    @var output Texto o respuesta generada por la Inteligencia Artificial (opcional).
    @var latency Tiempo total de procesamiento medido en segundos (opcional).
    @var error Mensaje detallado del fallo en caso de que ocurra alguna anomalía (opcional).
    """
    status: str
    model: str | None = None
    output: str | None = None
    latency: float | None = None
    error: str | None = None


# =====================================================
# FACE RECOGNITION
# =====================================================

class RecognizeRequest(BaseModel):
    """
    @brief Modelo de petición para identificar a una persona mediante su rostro.
    
    @var image Imagen codificada que contiene el rostro a analizar (generalmente en formato Base64 o URL).
    """
    image: str


class RegisterRequest(BaseModel):
    """
    @brief Modelo de petición para dar de alta o entrenar a un nuevo usuario en el sistema.
    
    @var name Nombre o identificador de la persona a registrar de forma única.
    @var images Lista de imágenes (cadenas de texto en Base64/rutas) con diferentes ángulos del rostro para el entrenamiento.
    """
    name: str
    images: List[str]


# =====================================================
# LOGS
# =====================================================

class LogEntry(BaseModel):
    """
    @brief Estructura de una línea o registro de log individual.
    
    @var text Contenido textual del mensaje del evento o comando ejecutado.
    """
    text: str


class LogsResponse(BaseModel):
    """
    @brief Modelo de respuesta que envuelve un conjunto de registros de logs.
    
    @var logs Lista ordenada de objetos LogEntry que pertenecen al historial consultado.
    """
    logs: List[LogEntry]


# =====================================================
# CONTROL SERVICIOS
# =====================================================

class ServiceResponse(BaseModel):
    """
    @brief Modelo de respuesta para las acciones de control sobre los servicios del sistema.
    
    @var status Resultado o estado final del proceso tras la acción (ej: 'running', 'stopped', 'error').
    @var service Nombre o identificador del proceso de aplicación alterado (ej: 'calculator', 'browser').
    """
    status: str
    service: str