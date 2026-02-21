# app/schemas/schemes.py

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime


# ---------------------------
# Request Schemas
# ---------------------------

class SchemeRecommendationRequest(BaseModel):
    query: str = Field(..., example="Subsidy schemes for rice farmers in Tamil Nadu")
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class SchemeInteractionRequest(BaseModel):
    log_id: UUID
    interaction_type: str  # viewed, clicked, applied


# ---------------------------
# Response Schemas
# ---------------------------

class SchemeResponse(BaseModel):
    id: UUID
    title: str
    description: str
    eligibility: Optional[str]
    region: Optional[str]
    crop_type: Optional[str]
    similarity: Optional[float]
    final_score: Optional[float]


class SchemeRecommendationResponse(BaseModel):
    status: str
    count: int
    data: List[SchemeResponse]


class SchemeLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    scheme_id: UUID
    title: str
    similarity_score: Optional[float]
    final_score: Optional[float]
    interaction_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True