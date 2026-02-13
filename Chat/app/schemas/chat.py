from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    session_id: str
    language: str = Field(..., description="ta | ml | hi | en")
    content: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    language: str
    created_at: datetime
