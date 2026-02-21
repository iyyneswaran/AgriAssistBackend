import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the root project directory to Python path if necessary
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Load environment variables
load_dotenv(os.path.join(current_dir, ".env"))

from app.services.rag.ingestion_service import IngestionService

async def main():
    service = IngestionService()
    
    # Define the folder where text documents are stored
    folder_path = os.path.join(current_dir, "data", "rag_documents")
    
    print("Starting automated ingestion process...")
    await service.clear_index()
    await service.ingest_documents_from_folder(folder_path)
    print("Ingestion process finished.")

if __name__ == "__main__":
    asyncio.run(main())
