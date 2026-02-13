from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.security import get_current_user, verify_role
from app.core.rate_limiter import rate_limit_dependency

router = APIRouter(prefix="/admin", tags=["Admin"])


class InitiateCallRequest(BaseModel):
    farmer_id: str
    message: str
    language: str


@router.post("/initiate-call", dependencies=[Depends(rate_limit_dependency)])
async def initiate_call(
    payload: InitiateCallRequest,
    user=Depends(get_current_user),
):
    verify_role(user, "ADMIN")

    return {
        "status": "call_initiated",
        "farmer_id": payload.farmer_id
    }
