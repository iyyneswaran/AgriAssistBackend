from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.chat.chat_service import generate_ai_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"
    session_id: Optional[str] = "default"

@router.post("/generate")
async def generate_chat_response(request: ChatRequest):
    """
    Internal HTTP endpoint for AI chat generation via Pollinations AI.
    Called by the Express server (which already authenticates the user).
    """
    try:
        response_text = await generate_ai_response(
            user_id="internal",
            session_id=request.session_id,
            language=request.language,
            content=request.message,
        )
        
        return {"response": response_text}
    except Exception as e:
        logger.error(f"Chat generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")
