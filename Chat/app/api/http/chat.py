from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from app.services.chat.chat_service import generate_ai_response
from app.middleware.rate_limiter import rate_limit
from app.core.security import authenticated_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"
    session_id: Optional[str] = "default"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

from app.services.chat.agent_service import AgentService
from typing import List, Dict, Any

agent_service = AgentService()

@router.post("/generate")
async def generate_chat_response(req: Request, request: ChatRequest, _=Depends(rate_limit), user=Depends(authenticated_user)):
    """
    Internal HTTP endpoint for AI chat generation via Sarvam AI.
    Routes to Seva AI Agent with fallback to legacy chat service.
    """
    try:
        agent_resp = await agent_service.chat([{"role": "user", "content": request.message}])
        return {"response": agent_resp.get("content", "")}
    except Exception as agent_err:
        logger.warning(f"AgentService generation failed ({agent_err}), falling back to chat_service")
        try:
            final_response = await generate_ai_response(
                user_id=user.get('id') or user.get('sub'),
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

class AgentRequest(BaseModel):
    messages: List[Dict[str, Any]]
    language: Optional[str] = "en"

agent_service = AgentService()

@router.post("/agent")
async def generate_agent_response(req: Request, request: AgentRequest, _=Depends(rate_limit)):
    """
    New unified endpoint for AgriAssist Seva AI using Sarvam 105b tool calling.
    """
    try:
        response = await agent_service.chat(request.messages)
        return response
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail="Failed to run agent")
