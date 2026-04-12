"""
RAG V2 Migration Script - AgriAssist
=====================================
Migrates the agriculture schemes dataset into Pinecone namespace 'tn_agri_v2'.

Usage:
    cd Backend/Chat
    python migrate_rag_v2.py

Features:
    - Loads data/rag_documents/agriSchemes_Data.txt
    - Parses structured JSON scheme data (handles messy PDF-extracted formatting)
    - Enriches each scheme with metadata (soil_type, season, land_size_range, scheme_category)
    - Generates embeddings via Gemini Embedding API
    - Upserts into Pinecone namespace 'tn_agri_v2'
    - Validates with a test query
    - Idempotent: safe to re-run (overwrites same vector IDs)

Production Safety:
    - Old data in default namespace remains untouched (rollback available)
    - No downtime -- new namespace is independent
"""

import asyncio
import os
import sys
import re
import json
import time
import logging

# Fix Windows console encoding for unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from app.services.rag.ingestion_service import IngestionService
from app.services.rag.embedding_service import EmbeddingService
from app.integrations.pinecone.pinecone_store import PineconeStore

# -- Logging Setup --
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("migrate_rag_v2.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("migrate_rag_v2")

# -- Configuration --
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data", "rag_documents")
NAMESPACE = settings.PINECONE_NAMESPACE  # "tn_agri_v2"


def clean_and_parse_schemes(file_path: str):
    """
    Robust JSON parser for the agriSchemes_Data.txt format.
    Handles:
      - Multiline JSON string values (newlines inside "value" pairs)
      - Stray page numbers embedded within JSON values
      - Trailing whitespace / BOM characters
    Returns a list of parsed scheme dicts.
    """
    with open(file_path, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    # Step 1: Remove lines that are ONLY digits (stray PDF page numbers)
    # These appear as standalone lines like "1", "2", "2 3", "4", etc.
    cleaned = re.sub(r'\n\s*\d+(?:\s+\d+)*\s*\n', '\n', raw)

    # Step 2: Join continuation lines that break JSON string values.
    # In valid JSON, a string value spans exactly one line.
    # Here, values are split across lines inside quotes.
    # Strategy: if a line doesn't start a new key/structural token, join it to the previous line.
    lines = cleaned.split('\n')
    joined_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Check if this line starts a JSON structural element or key
        if re.match(r'^[\[\]{},]', stripped) or re.match(r'^"[a-z_]+":', stripped):
            joined_lines.append(stripped)
        else:
            # Continuation of a previous value -- join to previous line
            if joined_lines:
                joined_lines[-1] = joined_lines[-1].rstrip() + ' ' + stripped
            else:
                joined_lines.append(stripped)

    fixed_json = '\n'.join(joined_lines)

    # Step 3: Fix common JSON issues
    # Remove trailing commas before closing braces/brackets
    fixed_json = re.sub(r',\s*}', '}', fixed_json)
    fixed_json = re.sub(r',\s*]', ']', fixed_json)

    # Step 4: Parse
    try:
        schemes = json.loads(fixed_json)
        if isinstance(schemes, list):
            logger.info(f"Successfully parsed {len(schemes)} schemes from {file_path}")
            return schemes
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed even after cleaning: {e}")
        # Try one more approach: extract individual objects with regex
        return _extract_schemes_regex(raw)

    return []


def _extract_schemes_regex(raw_text: str):
    """
    Fallback regex-based extraction of scheme objects from messy JSON.
    Extracts each {...} block and parses individually.
    """
    # Remove standalone page numbers
    cleaned = re.sub(r'\n\s*\d+(?:\s+\d+)*\s*\n', '\n', raw_text)

    schemes = []
    # Find each { ... } block
    brace_depth = 0
    current_obj = ""
    for char in cleaned:
        if char == '{':
            brace_depth += 1
            current_obj += char
        elif char == '}':
            brace_depth -= 1
            current_obj += char
            if brace_depth == 0 and current_obj.strip():
                # Try to parse this object
                try:
                    # Clean up multiline strings
                    obj_text = re.sub(r'\n\s*', ' ', current_obj)
                    obj = json.loads(obj_text)
                    schemes.append(obj)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse object: {current_obj[:80]}...")
                current_obj = ""
        elif brace_depth > 0:
            current_obj += char

    logger.info(f"Regex extraction found {len(schemes)} schemes")
    return schemes


async def run_migration():
    """
    Full migration pipeline:
    1. Parse and validate the dataset
    2. Clear target namespace (idempotent)
    3. Ingest all schemes with enriched metadata
    4. Validate with namespace stats
    5. Run a test query
    """
    start_time = time.time()

    print("=" * 60)
    print("  AgriAssist RAG V2 Migration")
    print(f"  Namespace: {NAMESPACE}")
    print(f"  Data folder: {DATA_FOLDER}")
    print(f"  Pinecone index: {settings.PINECONE_INDEX_NAME}")
    print(f"  Embedding model: {settings.GEMINI_EMBEDDING_MODEL}")
    print(f"  LLM model: {settings.GEMINI_MODEL}")
    print("=" * 60)

    # Validate data folder exists
    if not os.path.exists(DATA_FOLDER):
        logger.error(f"Data folder not found: {DATA_FOLDER}")
        print(f"\n[ERROR] Data folder not found: {DATA_FOLDER}")
        return

    # -- Step 0: Pre-parse the dataset --
    print("\n[Step 0] Pre-parsing dataset with robust JSON cleaner...")
    data_file = os.path.join(DATA_FOLDER, "agriSchemes_Data.txt")
    schemes = clean_and_parse_schemes(data_file)

    if not schemes:
        print("[ERROR] Could not parse any schemes from dataset!")
        return

    print(f"  [OK] Parsed {len(schemes)} schemes")
    for i, s in enumerate(schemes[:5]):
        print(f"    {i+1}. {s.get('scheme_name', 'Unknown')}")
    if len(schemes) > 5:
        print(f"    ... and {len(schemes) - 5} more")

    # -- Step 1: Clear namespace --
    print("\n[Step 1] Clearing target namespace...")
    ingestion = IngestionService(namespace=NAMESPACE)

    try:
        await ingestion.clear_index(namespace=NAMESPACE)
        print("  [OK] Namespace cleared")
    except Exception as e:
        logger.warning(f"Could not clear namespace (may not exist yet): {e}")
        print(f"  [WARN] Could not clear namespace (may be empty): {e}")

    await asyncio.sleep(2)

    # -- Step 2: Ingest structured schemes with enriched metadata --
    print("\n[Step 2] Ingesting schemes with enriched metadata...")
    await ingestion.ingest_structured_schemes(schemes, "agriSchemes_Data.txt")

    ingestion._print_stats()

    # -- Step 3: Validate namespace stats --
    print("\n[Step 3] Validating namespace...")
    await asyncio.sleep(5)

    store = PineconeStore(namespace=NAMESPACE)
    try:
        stats = await store.get_namespace_stats()
        print(f"  Index stats: {stats}")
        ns_count = stats.get("namespaces", {}).get(NAMESPACE, 0)
        print(f"  Vectors in '{NAMESPACE}': {ns_count}")
        logger.info(f"Namespace '{NAMESPACE}' has {ns_count} vectors")
    except Exception as e:
        logger.warning(f"Could not fetch namespace stats: {e}")
        print(f"  [WARN] Could not fetch stats: {e}")

    # -- Step 4: Test query --
    print("\n[Step 4] Running test query...")
    try:
        embedding_service = EmbeddingService()
        test_query = "agriculture subsidies and crop insurance for small farmers growing paddy in Tamil Nadu"
        test_embedding = await embedding_service.embed_text(test_query)

        results = await store.query_schemes(
            embedding=test_embedding,
            top_k=5,
        )

        print(f"  Test query returned {len(results)} results:")
        for i, r in enumerate(results):
            title = r.get("title", "Unknown")
            score = r.get("similarity", 0)
            category = r.get("scheme_category", "N/A")
            region = r.get("region", "N/A")
            print(f"    {i+1}. {title} (score: {score:.4f}, cat: {category}, region: {region})")

        if len(results) > 0:
            print("\n  [OK] Test query successful -- RAG V2 is operational!")
        else:
            print("\n  [WARN] Test query returned no results -- review ingestion")

    except Exception as e:
        logger.error(f"Test query failed: {e}")
        print(f"  [ERROR] Test query failed: {e}")

    # -- Summary --
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"  Migration completed in {elapsed:.1f}s")
    print(f"  Namespace: {NAMESPACE}")
    print(f"  Rollback: Old data remains in default namespace")
    print(f"{'=' * 60}")


async def run_rollback():
    """
    Utility: Switch back to using the default namespace.
    Does NOT delete any data -- just prints instructions.
    """
    print("=" * 60)
    print("  Rollback Instructions")
    print("=" * 60)
    print(f"  To rollback, set PINECONE_NAMESPACE='' in .env")
    print(f"  This will make the system query the default namespace (old data)")
    print(f"  The '{NAMESPACE}' namespace will remain intact for future use")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        asyncio.run(run_rollback())
    else:
        asyncio.run(run_migration())
