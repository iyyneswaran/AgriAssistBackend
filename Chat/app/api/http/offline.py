from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from app.core.rate_limiter import rate_limit_dependency

router = APIRouter(prefix="/offline", tags=["Offline"])


class OfflineMessage(BaseModel):
    message_id: str
    session_id: str
    language: str
    content: str


@router.post("/sync", dependencies=[Depends(rate_limit_dependency)])
async def sync_offline_messages(messages: List[OfflineMessage]):
    return {
        "status": "synced",
        "received_count": len(messages)
    }
