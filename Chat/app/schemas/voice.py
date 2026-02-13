from pydantic import BaseModel, Field
from typing import Optional


class VoiceUploadResponse(BaseModel):
    file_path: str
    status: str


class VoiceProcessingResult(BaseModel):
    recognized_text: str
    response_text: str
    audio_path: str
