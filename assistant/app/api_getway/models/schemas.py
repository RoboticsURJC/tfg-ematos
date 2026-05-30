# models/schemas.py

from pydantic import BaseModel
from typing import List


# =====================================================
# LLM
# =====================================================

class GenerateRequest(BaseModel):
    model: str
    prompt: str


class GenerateResponse(BaseModel):
    status: str
    model: str | None = None
    output: str | None = None
    latency: float | None = None
    error: str | None = None


# =====================================================
# FACE RECOGNITION
# =====================================================

class RecognizeRequest(BaseModel):
    image: str


class RegisterRequest(BaseModel):
    name: str
    images: List[str]


# =====================================================
# LOGS
# =====================================================

class LogEntry(BaseModel):
    text: str


class LogsResponse(BaseModel):
    logs: List[LogEntry]


# =====================================================
# CONTROL SERVICIOS
# =====================================================

class ServiceResponse(BaseModel):
    status: str
    service: str