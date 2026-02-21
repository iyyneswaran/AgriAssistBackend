import asyncio
import os
import sys
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

load_dotenv(os.path.join(current_dir, ".env"))

# Import base first to satisfy SQLAlchemy class registries and prevent circular import
import app.db.base

from app.services.rag.ag_service import RagService
from app.db.models.user import User

async def main():
    service = RagService()
    
    # Mock a User objects
    mock_user = User(
        id="test-id-123",
        name="Test Farmer",
        phone_number="+919876543210",
        region="Pan India",
        crop_type="Various",
        land_size=4.0
    )
    
    query = "What are the benefits of the Seed Multiplication Scheme?"
    
    print(f"Querying: '{query}'...")
    
    # We pass None for db since the RAG service currently does not actively use the db session for retrieval
    # It relies on the Supabase client created natively in Retriever instead
    result = await service.recommend_schemes(
        query=query, 
        user=mock_user, 
        db=None, 
        top_k=3
    )
    
    print("\n--- Final Answer From LLM ---\n")
    print(result.get("answer"))
    
    print("\n--- Source Documents Retrieved ---\n")
    for doc in result.get("source_documents", []):
        print(f"Title: {doc.get('title')}, Score: {doc.get('final_score')}")

if __name__ == "__main__":
    asyncio.run(main())
