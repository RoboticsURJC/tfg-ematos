# api/routes_llm.py

from fastapi import APIRouter
from models.schemas import GenerateRequest
from services.llm_service import LLMService

##
# @file routes_llm.py
# @brief Enrutador de API para interactuar con los Modelos de Lenguaje (LLM).
# @details Proporciona endpoints para la generación de texto inteligente y la comprobación del estado del motor de IA.
#

router = APIRouter(
    prefix="/llm",
    tags=["LLM"]
)


# =====================================================
# GENERATE
# =====================================================

@router.post("/generate")
def generate(payload: GenerateRequest):
    """
    @brief Genera una respuesta de texto basada en un prompt.
    
    Envía la petición al servicio LLM utilizando el modelo especificado y el texto guía (prompt) 
    proporcionado por el usuario para obtener una respuesta inteligente.
    
    @param payload Objeto GenerateRequest que contiene los campos 'model' y 'prompt'.
    
    @return dict/str Respuesta generada por el modelo de IA o estructura de error en caso de fallo.
    """
    return LLMService.generate(
        payload.model,
        payload.prompt
    )


# =====================================================
# HEALTH CHECK
# =====================================================

@router.get("/health")
def health():
    """
    @brief Comprueba la disponibilidad y estado del servicio LLM.
    
    Verifica que el backend de IA (Ollama, OpenAI API, o el motor local configurado) esté 
    respondiendo correctamente y listo para procesar peticiones.
    
    @return dict Estado de salud del servicio (ej: {"status": "healthy"} o información de conexión).
    """
    return LLMService.health()