import os
import re
import json
import asyncio
import logging
from typing import List, Dict
from google import genai
from app.core.config import settings
from app.services.rag.embedding_service import EmbeddingService
from app.integrations.pinecone.pinecone_store import PineconeStore

logger = logging.getLogger(__name__)


# ── Domain Constants ─────────────────────────────────────────────────────

CROP_KEYWORDS = {
    "rice", "paddy", "wheat", "cotton", "sugarcane", "millets", "maize",
    "pulses", "oilseeds", "soybean", "groundnut", "mustard", "sunflower",
    "vegetables", "fruits", "horticulture", "bamboo", "coconut", "banana",
    "tomato", "onion", "potato", "spices", "cereals", "fish", "aquaculture",
}

SCHEME_CATEGORIES = {
    "insurance": ["insurance", "bima", "premium", "crop loss", "fasal bima"],
    "subsidy": ["subsidy", "subsidized", "subvention", "grant"],
    "credit": ["credit", "loan", "kisan credit", "kcc", "interest"],
    "pension": ["pension", "retirement", "maan-dhan"],
    "price_support": ["msp", "price support", "procurement", "price-deficiency"],
    "training": ["training", "extension", "kvk", "education", "workshop"],
    "infrastructure": ["infrastructure", "storage", "godown", "warehouse", "cold chain"],
    "irrigation": ["irrigation", "sinchai", "micro-irrigation", "drip", "sprinkler", "solar pump"],
    "organic": ["organic", "natural farming", "paramparagat"],
    "market_access": ["e-nam", "mandi", "market", "trading platform"],
    "income_support": ["income support", "₹6,000", "₹5,000 per acre", "financial assistance"],
}

SEASON_KEYWORDS = {
    "kharif": ["kharif", "monsoon", "june", "july", "rainy"],
    "rabi": ["rabi", "winter", "october", "november", "wheat season"],
    "zaid": ["zaid", "summer", "march", "april"],
}


class IngestionService:
    """
    Handles scheme document ingestion into vector DB (Pinecone).
    Supports structured JSON scheme files with enriched metadata extraction.
    Uses namespace-based versioning for safe rollback.
    """

    def __init__(self, namespace: str = None):
        self.embedding_service = EmbeddingService()
        self.namespace = namespace or settings.PINECONE_NAMESPACE
        self.vector_store = PineconeStore(namespace=self.namespace)
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

        # Ingestion statistics
        self.stats = {
            "documents_processed": 0,
            "schemes_parsed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "upserts_completed": 0,
            "errors": 0,
        }

    async def ingest_documents_from_folder(self, folder_path: str):
        """
        Reads all .txt files from folder_path.
        If a file contains structured JSON (array of scheme objects), use structured ingestion.
        Otherwise, fall back to chunk-based ingestion.
        """
        logger.info(f"[START] Starting ingestion from {folder_path} -> namespace '{self.namespace}'")
        print(f"[START] Starting ingestion from {folder_path} -> namespace '{self.namespace}'")

        if not os.path.exists(folder_path):
            logger.error(f"Folder not found: {folder_path}")
            print(f"✗ Folder not found: {folder_path}")
            return

        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(folder_path, filename)
                logger.info(f"Processing {filename}...")
                print(f"  Processing {filename}...")
                self.stats["documents_processed"] += 1

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Fallback for files with different encoding
                    with open(file_path, "r", encoding="utf-8-sig") as f:
                        content = f.read()

                if not content.strip():
                    logger.warning(f"Skipping empty file: {filename}")
                    print(f"  [WARN] Skipping empty file: {filename}")
                    continue

                # Try structured JSON ingestion first
                schemes = self._try_parse_structured_json(content)
                if schemes:
                    logger.info(f"Detected structured JSON with {len(schemes)} schemes in {filename}")
                    print(f"  [OK] Detected structured JSON with {len(schemes)} schemes")
                    self.stats["schemes_parsed"] += len(schemes)
                    await self.ingest_structured_schemes(schemes, filename)
                else:
                    logger.info(f"Using chunk-based ingestion for {filename}")
                    print(f"  --> Using chunk-based ingestion for {filename}")
                    await self.ingest_scheme(
                        filename=filename,
                        description=content,
                    )

        self._print_stats()
        logger.info("[DONE] Ingestion complete.")
        print("[DONE] Ingestion complete.")

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

    def _extract_enriched_metadata(self, scheme: Dict) -> Dict[str, str]:
        """
        Extracts enriched metadata from a scheme object for Pinecone filtering.
        Returns: soil_type, season, land_size_range, scheme_category
        """
        description = (scheme.get("description", "") + " " + scheme.get("eligibility", "")).lower()
        applicable_crops = scheme.get("applicable_crops", "").lower()

        # Soil type inference
        soil_type = "all"
        if "soil health" in description or "soil" in description:
            soil_type = "soil_specific"

        # Season inference
        season = "all"
        for s, keywords in SEASON_KEYWORDS.items():
            if any(kw in description or kw in applicable_crops for kw in keywords):
                season = s
                break

        # Land size range inference
        land_size_range = "all"
        eligibility = scheme.get("eligibility", "").lower()
        if "small" in eligibility or "marginal" in eligibility or "≤2 ha" in eligibility:
            land_size_range = "small_marginal"
        elif "all farmer" in eligibility:
            land_size_range = "all"

        # Scheme category classification
        scheme_category = "general"
        desc_lower = description
        for category, keywords in SCHEME_CATEGORIES.items():
            if any(kw in desc_lower for kw in keywords):
                scheme_category = category
                break

        return {
            "soil_type": soil_type,
            "season": season,
            "land_size_range": land_size_range,
            "scheme_category": scheme_category,
        }

    def _normalize_region(self, region: str) -> str:
        """
        Normalizes region string for consistent metadata filtering.
        """
        region = region.strip().lower()
        if "pan-india" in region or "pan india" in region:
            return "pan-india"
        # Extract specific state/region names
        return region

    def _normalize_crops(self, crop_text: str) -> str:
        """
        Normalizes crop text for metadata, keeping it lowercase and trimmed.
        """
        crop_text = crop_text.strip().lower()
        if "all" in crop_text:
            return "all"
        return crop_text

    async def ingest_structured_schemes(self, schemes: List[Dict], source_filename: str):
        """
        Ingest structured JSON scheme data — one vector per scheme.
        Each scheme gets rich metadata stored alongside its embedding.
        Uses batch upserts for efficiency.
        """
        logger.info(f"Ingesting {len(schemes)} structured schemes from {source_filename}...")
        print(f"  Ingesting {len(schemes)} structured schemes...")

        batch_vectors = []
        batch_size = 10  # Process embeddings in groups of 10

        for i, scheme in enumerate(schemes):
            scheme_name = scheme.get("scheme_name", f"Unknown Scheme {i+1}")
            description = scheme.get("description", "")
            eligibility = scheme.get("eligibility", "")
            applicable_crops = scheme.get("applicable_crops", "")
            region = scheme.get("region", "").strip()
            benefit_amount = scheme.get("benefit_amount", "")
            scheme_id = scheme.get("scheme_id", f"SCHEME_{i}")

            # Extract enriched metadata
            enriched = self._extract_enriched_metadata(scheme)

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
                self.stats["embeddings_generated"] += 1

                vector_id = f"{source_filename.replace('.txt', '')}_{scheme_id}"

                metadata = {
                    "title": scheme_name,
                    "description": description[:950] if len(description) > 950 else description,
                    "eligibility": eligibility,
                    "region": self._normalize_region(region),
                    "crop_type": self._normalize_crops(applicable_crops),
                    "benefit_amount": benefit_amount,
                    "scheme_id": scheme_id,
                    "soil_type": enriched["soil_type"],
                    "season": enriched["season"],
                    "land_size_range": enriched["land_size_range"],
                    "scheme_category": enriched["scheme_category"],
                }

                batch_vectors.append((vector_id, embedding, metadata))
                self.stats["chunks_created"] += 1

                logger.info(f"  ✓ Prepared: {scheme_name} [{enriched['scheme_category']}]")
                print(f"    ✓ [{i+1}/{len(schemes)}] {scheme_name} → {enriched['scheme_category']}")

            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"  ✗ Failed to process {scheme_name}: {e}")
                print(f"    ✗ Failed: {scheme_name}: {e}")

            # Rate-limit embedding API calls
            await asyncio.sleep(1.5)

            # Batch upsert when batch is full
            if len(batch_vectors) >= batch_size:
                await self._flush_batch(batch_vectors)
                batch_vectors = []

        # Flush remaining vectors
        if batch_vectors:
            await self._flush_batch(batch_vectors)

        logger.info(f"Structured ingestion complete for {source_filename}.")
        print(f"  ▶ Structured ingestion complete for {source_filename}.")

    async def _flush_batch(self, batch_vectors: List[tuple]):
        """
        Flushes a batch of vectors to Pinecone.
        """
        try:
            await self.vector_store.upsert_batch(batch_vectors)
            self.stats["upserts_completed"] += len(batch_vectors)
            logger.info(f"  Flushed batch of {len(batch_vectors)} vectors")
        except Exception as e:
            self.stats["errors"] += len(batch_vectors)
            logger.error(f"  Batch upsert failed: {e}")
            print(f"    ✗ Batch upsert failed: {e}")

    async def ingest_scheme(
        self,
        filename: str,
        description: str,
    ):
        """
        Fallback: Split description → extract metadata in batches → embed → store.
        """
        chunks = self._chunk_text(description)
        logger.info(f"Ingesting {len(chunks)} chunks for {filename}...")
        print(f"  Ingesting {len(chunks)} chunks for {filename}...")

        batch_size = 8
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} chunks)...")
            print(f"    Processing batch {i//batch_size + 1} ({len(batch)} chunks)...")

            try:
                batch_metadata = await self._extract_metadata_batch(batch)

                for j, chunk in enumerate(batch):
                    idx = i + j
                    chunk_meta = batch_metadata[j] if j < len(batch_metadata) else {}

                    title = chunk_meta.get("title", filename)
                    embedding = await self.embedding_service.embed_text(chunk)
                    self.stats["embeddings_generated"] += 1

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
                    self.stats["chunks_created"] += 1
                    self.stats["upserts_completed"] += 1
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Failed to process batch ending at {i + batch_size}: {e}")
                print(f"    ✗ Failed to process batch ending at {i + batch_size}: {e}")

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
                    contents=prompt,
                )
                clean_json = re.sub(r'```json\n|\n```', '', response.text).strip()
                return json.loads(clean_json)
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 30
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                    print(f"    ⚠ Rate limited. Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"Batch metadata extraction failed: {e}")
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

    async def clear_index(self, namespace: str = None):
        """
        Clears all data from the specified namespace in the vector store.
        """
        ns = namespace or self.namespace
        logger.info(f"Clearing vector store namespace '{ns}'...")
        print(f"  Clearing namespace '{ns}'...")
        await self.vector_store.delete_all(namespace=ns)
        logger.info(f"Namespace '{ns}' cleared.")
        print(f"  ✓ Namespace '{ns}' cleared.")

    def _print_stats(self):
        """
        Prints ingestion statistics.
        """
        print("\n  ── Ingestion Statistics ──")
        for key, value in self.stats.items():
            print(f"    {key}: {value}")
        print("  ─────────────────────────\n")
        logger.info(f"Ingestion stats: {self.stats}")