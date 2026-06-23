# api/routes_face.py

from fastapi import APIRouter
from models.schemas import (
    RecognizeRequest,
    RegisterRequest
)
from services.face_service import FaceService

##
# @file routes_face.py
# @brief Enrutador de API para el sistema de reconocimiento facial y gestión de memorias.
# @details Ofrece endpoints para registrar rostros, reconocer personas y gestionar la base de datos de conocimientos/memorias asociadas a los usuarios.
#

router = APIRouter(
    prefix="/face",
    tags=["Face Recognition"]
)


# =====================================================
# RECONOCIMIENTO FACIAL
# =====================================================

@router.post("/recognize")
def recognize(payload: RecognizeRequest):
    """
    @brief Procesa una imagen para reconocer un rostro.
    
    Envía la imagen capturada al servicio de reconocimiento facial para contrastarla con la base de datos de usuarios registrados.
    
    @param payload Objeto RecognizeRequest que contiene la imagen en formato compatible (generalmente Base64 o ruta).
    
    @return dict Datos de la persona identificada (nombre, nivel de confianza) o estado de no reconocido.
    """
    return FaceService.recognize(
        payload.image
    )


# =====================================================
# REGISTRO DE PERSONAS
# =====================================================

@router.post("/register")
def register(payload: RegisterRequest):
    """
    @brief Registra a una nueva persona en el sistema.
    
    Guarda el nombre de un usuario y analiza su conjunto de imágenes para extraer y almacenar sus vectores/patrones faciales característicos.
    
    @param payload Objeto RegisterRequest con el nombre del usuario y la lista de imágenes para el entrenamiento.
    
    @return dict Confirmación del éxito del registro y cantidad de imágenes procesadas.
    """
    return FaceService.register(
        payload.name,
        payload.images
    )


# =====================================================
# MEMORIAS
# =====================================================

@router.get("/memories/{user}")
def get_memories(user: str):
    """
    @brief Recupera los recuerdos o información asociada a un usuario específico.
    
    Consulta en el servicio de reconocimiento facial o su base de datos semántica todo el contenido o datos históricos que el sistema "recuerda" sobre una persona.
    
    @param user Nombre o identificador único del usuario a consultar.
    
    @return list/dict Lista de memorias, notas o datos biográficos vinculados a ese rostro.
    """
    return FaceService.get_memories(user)


# =====================================================
# RECORDAR
# =====================================================

@router.post("/remember")
def remember(payload: dict):
    """
    @brief Almacena un nuevo recuerdo o dato textual para un usuario.
    
    Permite inyectar información contextual a la base de conocimientos de un usuario específico para que el sistema pueda usarla en interacciones futuras tras reconocerlo.
    
    @param payload Diccionario que debe contener obligatoriamente las claves 'user' (str) y 'content' (str).
    
    @return dict Estado del guardado en la memoria semántica.
    """
    user = payload.get("user")
    content = payload.get("content")

    return FaceService.remember(
        user,
        content
    )