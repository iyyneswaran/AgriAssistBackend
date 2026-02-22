from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.services.rag.rag_service import RagService
from app.db.session import get_db
from app.core.security import get_current_user
from app.db.models.user import User

router = APIRouter(prefix="/schemes", tags=["Schemes"])

rag_service = RagService()


@router.get("/recommend")
async def recommend_schemes(
    query: str = Query(..., description="User query about schemes"),
    top_k: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Context-aware scheme recommendation using RAG.
    """

    try:
        recommendations = await rag_service.recommend_schemes(
            query=query,
            user=current_user,
            db=db,
            top_k=top_k,
        )

        return {
            "status": "success",
            "count": len(recommendations),
            "data": recommendations,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))