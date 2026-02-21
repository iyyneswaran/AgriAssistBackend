import os
import re
import json
import asyncio
from typing import List, Dict
import google.generativeai as genai
from app.core.config import settings
from app.services.rag.embedding_service import EmbeddingService
from app.integrations.pinecone.pinecone_store import PineconeStore


class IngestionService:
    """
    Handles scheme document ingestion into vector DB (Pinecone).
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = PineconeStore()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def ingest_documents_from_folder(self, folder_path: str):
        """
        Reads all .txt files from folder_path, chunks them, and stores them.
        """
        print(f"Starting ingestion from {folder_path}...")
        if not os.path.exists(folder_path):
            print(f"Folder not found: {folder_path}")
            return

        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(folder_path, filename)
                print(f"Processing {filename}...")
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # We no longer need to pass global placeholders here, 
                # as each chunk will have its own extracted metadata.
                await self.ingest_scheme(
                    filename=filename,
                    description=content
                )
        print("Ingestion complete.")

    async def ingest_scheme(
        self,
        filename: str,
        description: str,
    ):
        """
        Split description → extract metadata in batches → embed → store.
        """
        chunks = self._chunk_text(description)
        print(f"Ingesting {len(chunks)} chunks for {filename}...")

        # Process in batches of 8 to stay under API limits
        batch_size = 8
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1} ({len(batch)} chunks)...")
            
            try:
                # Extract metadata for the whole batch
                batch_metadata = await self._extract_metadata_batch(batch)
                
                for j, chunk in enumerate(batch):
                    idx = i + j
                    chunk_meta = batch_metadata[j] if j < len(batch_metadata) else {}
                    
                    title = chunk_meta.get("title", filename)
                    embedding = await self.embedding_service.embed_text(chunk)

                    # Generate a unique ID for the vector
                    vector_id = f"{filename.replace('.txt', '')}_{idx}"

                    await self.vector_store.upsert_scheme(
                        vector_id=vector_id,
                        title=f"{title} (Part {idx+1})",
                        description=chunk,
                        eligibility=chunk_meta.get("eligibility", "Not mentioned"),
                        region=chunk_meta.get("region", "Not mentioned"),
                        crop_type=chunk_meta.get("crop_type", "Not mentioned"),
                        embedding=embedding,
                    )
            except Exception as e:
                print(f"Failed to process batch ending at {i + batch_size}: {e}")
            
            # Additional small delay to be safe for RPM
            await asyncio.sleep(10)

    async def _extract_metadata_batch(self, chunks: List[str]) -> List[Dict[str, str]]:
        """
        Uses Gemini to extract structured metadata from a batch of chunks.
        """
        chunks_text = ""
        for idx, chunk in enumerate(chunks):
            chunks_text += f"\n--- CHUNK {idx} ---\n{chunk}\n"

        prompt = f"""
        Extract metadata for each of these {len(chunks)} agricultural scheme text chunks.
        For each chunk, identify: title, eligibility, region, crop_type.
        If a field is not mentioned, return "Not mentioned".
        Return a JSON list of objects, one for each chunk in order.

        TEXTS:
        {chunks_text}

        JSON List:
        """
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                clean_json = re.sub(r'```json\n|\n```', '', response.text).strip()
                return json.loads(clean_json)
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 30
                    print(f"Rate limited. Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    continue
                print(f"Batch metadata extraction failed: {e}")
                return [{"title": "Unknown", "eligibility": "Not mentioned", "region": "Not mentioned", "crop_type": "Not mentioned"}] * len(chunks)

    def _chunk_text(self, text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        A slightly better chunker that tries to split by paragraphs/double newlines,
        and falls back to sentences or words if a block is too large.
        """
        # Clean up excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            if len(current_chunk) + len(para) + 2 <= max_chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If a single paragraph is larger than max_chunk_size, we just force split it
                if len(para) > max_chunk_size:
                    # Very crude split for huge paragraphs
                    for i in range(0, len(para), max_chunk_size - overlap):
                        chunks.append(para[i:i + max_chunk_size - overlap])
                    current_chunk = ""
                else:
                    current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    async def clear_index(self):
        """
        Clears all data from the vector store.
        """
        print("Clearing vector store index...")
        await self.vector_store.delete_all()
        print("Index cleared.")