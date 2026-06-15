# api/routes_face.py

from fastapi import APIRouter

from models.schemas import (
    RecognizeRequest,
    RegisterRequest
)

from services.face_service import FaceService


router = APIRouter(
    prefix="/face",
    tags=["Face Recognition"]
)


# =====================================================
# RECONOCIMIENTO FACIAL
# =====================================================

@router.post("/recognize")
def recognize(payload: RecognizeRequest):

    return FaceService.recognize(
        payload.image
    )


# =====================================================
# REGISTRO DE PERSONAS
# =====================================================

@router.post("/register")
def register(payload: RegisterRequest):

    return FaceService.register(
        payload.name,
        payload.images
    )


# =====================================================
# MEMORIAS
# =====================================================

@router.get("/memories/{user}")
def get_memories(user: str):

    return FaceService.get_memories(user)


# =====================================================
# RECORDAR
# =====================================================

@router.post("/remember")
def remember(payload: dict):

    user = payload.get("user")
    content = payload.get("content")

    return FaceService.remember(
        user,
        content
    )