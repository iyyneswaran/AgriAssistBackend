import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.security import get_current_user, verify_role
from app.core.rate_limiter import rate_limit_dependency
from app.services.rag.ingestion_service import IngestionService

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


@router.post("/ingest-schemes")
async def ingest_schemes():
    """
    Trigger ingestion of scheme documents from the rag_documents folder.
    Clears existing index and re-ingests all documents.
    """
    try:
        ingestion_service = IngestionService()
        
        # Clear existing data
        await ingestion_service.clear_index()
        
        # Ingest from rag_documents folder
        folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "rag_documents")
        await ingestion_service.ingest_documents_from_folder(folder_path)
        
        return {"status": "success", "message": "Scheme data ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
