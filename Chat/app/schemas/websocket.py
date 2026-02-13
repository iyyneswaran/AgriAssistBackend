from pydantic import BaseModel, Field
from typing import Optional, Literal


class WSChatMessage(BaseModel):
    type: Literal["chat_message"]
    session_id: str
    language: str = Field(..., description="ta | ml | hi | en")
    content: str


class WSAIToken(BaseModel):
    type: Literal["ai_token"]
    content: str


class WSAIComplete(BaseModel):
    type: Literal["ai_complete"]


class WSVoiceReady(BaseModel):
    type: Literal["voice_response_ready"]
    audio_url: str
