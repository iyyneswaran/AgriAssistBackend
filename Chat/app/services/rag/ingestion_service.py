import os
import re
import json
import asyncio
from typing import List, Dict
from google import genai
from app.core.config import settings
from app.services.rag.embedding_service import EmbeddingService
from app.integrations.pinecone.pinecone_store import PineconeStore


class IngestionService:
    """
    Handles scheme document ingestion into vector DB (Pinecone).
    Supports both structured JSON scheme files and raw text files.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = PineconeStore()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    async def ingest_documents_from_folder(self, folder_path: str):
        """
        Reads all .txt files from folder_path.
        If a file contains structured JSON (array of scheme objects), use structured ingestion.
        Otherwise, fall back to chunk-based ingestion.
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

                # Try structured JSON ingestion first
                schemes = self._try_parse_structured_json(content)
                if schemes:
                    print(f"Detected structured JSON with {len(schemes)} schemes in {filename}")
                    await self.ingest_structured_schemes(schemes, filename)
                else:
                    print(f"Using chunk-based ingestion for {filename}")
                    await self.ingest_scheme(
                        filename=filename,
                        description=content
                    )
        print("Ingestion complete.")

    def _try_parse_structured_json(self, content: str) -> List[Dict] | None:
        """
        Attempt to parse content as a JSON array of scheme objects.
        Cleans up common formatting issues (multiline strings, stray numbers).
        Returns list of scheme dicts if successful, None otherwise.
        """
        try:
            # Clean up: remove stray standalone numbers (page numbers from PDF extraction)
            cleaned = re.sub(r'\n\s*\d+\s*\n', '\n', content)
            # Fix multiline string values: replace newlines within JSON string values
            # by attempting a direct parse first
            data = json.loads(cleaned)
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                # Verify it looks like scheme data
                if any(key in data[0] for key in ["scheme_name", "description", "region"]):
                    return data
            return None
        except json.JSONDecodeError:
            # Try more aggressive cleaning
            try:
                # Remove standalone numbers (PDF page numbers)
                cleaned = re.sub(r'(?<=\n)\s*\d{1,3}\s*(?=\n)', '', content)
                # Collapse multiline strings within JSON values
                # This handles cases where a value spans multiple lines
                lines = cleaned.split('\n')
                fixed_lines = []
                for line in lines:
                    stripped = line.strip()
                    # Skip empty lines and standalone numbers
                    if not stripped or re.match(r'^\d{1,3}$', stripped):
                        continue
                    fixed_lines.append(line)
                fixed_content = '\n'.join(fixed_lines)
                data = json.loads(fixed_content)
                if isinstance(data, list) and len(data) > 0:
                    return data
            except json.JSONDecodeError:
                pass
            return None

    async def ingest_structured_schemes(self, schemes: List[Dict], source_filename: str):
        """
        Ingest structured JSON scheme data — one vector per scheme.
        Each scheme gets rich metadata stored alongside its embedding.
        """
        print(f"Ingesting {len(schemes)} structured schemes from {source_filename}...")

        for i, scheme in enumerate(schemes):
            scheme_name = scheme.get("scheme_name", f"Unknown Scheme {i+1}")
            description = scheme.get("description", "")
            eligibility = scheme.get("eligibility", "")
            applicable_crops = scheme.get("applicable_crops", "")
            region = scheme.get("region", "").strip()
            benefit_amount = scheme.get("benefit_amount", "")
            scheme_id = scheme.get("scheme_id", f"SCHEME_{i}")

            # Build rich embedding text for semantic search
            embedding_text = f"""
Scheme: {scheme_name}
Description: {description}
Eligible: {eligibility}
Crops: {applicable_crops}
Region: {region}
Benefit: {benefit_amount}
""".strip()

            try:
                embedding = await self.embedding_service.embed_text(embedding_text)

                vector_id = f"{source_filename.replace('.txt', '')}_{scheme_id}"

                await self.vector_store.upsert_scheme(
                    vector_id=vector_id,
                    title=scheme_name,
                    description=description,
                    eligibility=eligibility,
                    region=region,
                    crop_type=applicable_crops,
                    embedding=embedding,
                    benefit_amount=benefit_amount,
                    scheme_id=scheme_id,
                )

                print(f"  ✓ Ingested: {scheme_name}")
            except Exception as e:
                print(f"  ✗ Failed to ingest {scheme_name}: {e}")

            # Small delay to respect API rate limits
            await asyncio.sleep(2)

        print(f"Structured ingestion complete for {source_filename}.")

    async def ingest_scheme(
        self,
        filename: str,
        description: str,
    ):
        """
        Fallback: Split description → extract metadata in batches → embed → store.
        """
        chunks = self._chunk_text(description)
        print(f"Ingesting {len(chunks)} chunks for {filename}...")

        batch_size = 8
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1} ({len(batch)} chunks)...")
            
            try:
                batch_metadata = await self._extract_metadata_batch(batch)
                
                for j, chunk in enumerate(batch):
                    idx = i + j
                    chunk_meta = batch_metadata[j] if j < len(batch_metadata) else {}
                    
                    title = chunk_meta.get("title", filename)
                    embedding = await self.embedding_service.embed_text(chunk)

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
            
            await asyncio.sleep(10)

    async def _extract_metadata_batch(self, chunks: List[str]) -> List[Dict[str, str]]:
        """
        Uses Gemini to extract structured metadata from a batch of chunks.
        """
        chunks_text = ""
        for idx, chunk in enumerate(chunks):
            chunks_text += f"\n--- CHUNK {idx} ---\n{chunk}\n"

        prompt = f"""You are an expert agricultural data extractor. Extract specific metadata from the provided {len(chunks)} text chunks separately. 

You MUST return ONLY a valid JSON list of objects, with EXACTLY one object per chunk, maintaining the same order. Do NOT include Markdown formatting like ```json.

Rules for extraction:
1. "title": The specific scheme name if mentioned. If absent, output "Not mentioned". NEVER guess the filename.
2. "eligibility": Extract EXACT groups mentioned in the text (e.g., "SC/ST", "Farm Women Groups", "Small and Marginal Farmers"). If not stated in the chunk, output "Not mentioned". Do NOT use "Unknown".
3. "region": Extract the precise geographic location (e.g., "Tamil Nadu", "Kancheepuram block"). If not explicitly stated, output "Not mentioned". Do NOT guess "Pan India".
4. "crop_type": Extract specific crops (e.g., "Paddy", "Pulses", "Seeds"). If not stated, output "Not mentioned". Do NOT output "Various" or "All Crops".

TEXT CHUNKS:
{chunks_text}

JSON List FORMAT:
[
  {{
    "title": "extracted title or 'Not mentioned'",
    "eligibility": "extracted groups or 'Not mentioned'",
    "region": "extracted region or 'Not mentioned'",
    "crop_type": "extracted crop or 'Not mentioned'"
  }}
]
"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
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
                if len(para) > max_chunk_size:
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