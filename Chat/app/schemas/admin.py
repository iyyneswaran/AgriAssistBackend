from pydantic import BaseModel, Field


class InitiateCallRequest(BaseModel):
    farmer_id: str
    phone_number: str
    message: str
    language: str = Field(..., description="ta | ml | hi | en")


class InitiateCallResponse(BaseModel):
    status: str
    audio_path: str