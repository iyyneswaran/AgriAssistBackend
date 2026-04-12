from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from app.services.chat.chat_service import generate_ai_response
from app.middleware.rate_limiter import rate_limit
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"
    session_id: Optional[str] = "default"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@router.post("/generate")
async def generate_chat_response(req: Request, request: ChatRequest, _=Depends(rate_limit)):
    """
    Internal HTTP endpoint for AI chat generation via Sarvam AI.
    Called by the Express server (which already authenticates the user).
    Sarvam-m natively responds in the user's language.
    """
    try:
        # Get AI Response natively
        final_response = await generate_ai_response(
            user_id="internal",
            session_id=request.session_id,
            language=request.language or "en",
            content=request.message,
            latitude=request.latitude,
            longitude=request.longitude,
        )
        
        return {"response": final_response}
    except Exception as e:
        logger.error(f"Chat generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")
