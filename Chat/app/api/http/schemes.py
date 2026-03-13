from fastapi import APIRouter, Depends, Query, HTTPException, Header
from typing import Optional

from app.services.rag.rag_service import RagService
from app.core.security import get_current_user

router = APIRouter(prefix="/schemes", tags=["Schemes"])

rag_service = RagService()


@router.get("/recommend")
async def recommend_schemes(
    crop: str = Query("", description="Crop name (e.g. Cotton, Paddy)"),
    soil_type: str = Query("", description="Soil type (e.g. Black, Red, Alluvial)"),
    area_acres: float = Query(0, description="Farm area in acres"),
    state: str = Query("", description="State name"),
    district: str = Query("", description="District name"),
    top_k: int = Query(8, ge=1, le=20),
    authorization: str = Header(...),
):
    """
    Context-aware scheme recommendation using RAG.
    Accepts farm context parameters directly instead of relying on User ORM model.
    """
    # Validate token (just to ensure authenticated access)
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    get_current_user(token)

    try:
        # Build farm context dict from query params
        farm_context = {
            "crop": crop.strip(),
            "soil_type": soil_type.strip(),
            "area_acres": area_acres,
            "state": state.strip(),
            "district": district.strip(),
        }

        # Build a natural-language query from the farm context
        query_parts = []
        if crop:
            query_parts.append(f"farming {crop}")
        if soil_type:
            query_parts.append(f"{soil_type} soil")
        if state:
            query_parts.append(f"in {state}")
        if area_acres > 0:
            query_parts.append(f"{area_acres} acres")
        
        query = " ".join(query_parts) if query_parts else "agricultural schemes for Indian farmers"

        recommendations = await rag_service.recommend_schemes(
            query=query,
            farm_context=farm_context,
            top_k=top_k,
        )

        return {
            "status": "success",
            "count": len(recommendations.get("source_documents", [])),
            "data": recommendations,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))