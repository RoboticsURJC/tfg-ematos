# api/routes_llm.py

from fastapi import APIRouter

from models.schemas import GenerateRequest
from services.llm_service import LLMService


router = APIRouter(
    prefix="/llm",
    tags=["LLM"]
)


# =====================================================
# GENERATE
# =====================================================

@router.post("/generate")
def generate(payload: GenerateRequest):

    return LLMService.generate(
        payload.model,
        payload.prompt
    )


# =====================================================
# HEALTH CHECK
# =====================================================

@router.get("/health")
def health():

    return LLMService.health()