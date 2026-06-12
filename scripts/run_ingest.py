#!/usr/bin/env python3
"""One-time script to load, chunk, embed, and ingest the knowledge base into Supabase.

Run this once after setting up Supabase to populate the documents table:
    python scripts/run_ingest.py

This script does NOT need to be run again unless you delete the documents table
or want to re-ingest with new documents or different chunk settings.
"""

# Standard library for logging output and configuration.
import logging
import sys
from pathlib import Path

# Project root is 2 directories up from scripts/ folder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables before any project imports.
from dotenv import load_dotenv

load_dotenv()

# Import the two key functions: load the knowledge base, then ingest it.
from src.knowledge_base import load_documents
from src.knowledge_base.ingest import ingest_documents

# Configure logging to show all info-level messages with timestamps.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Orchestrate the full knowledge base ingestion pipeline."""
    try:
        # Step 1: Load all .txt files from knowledge_base/ and chunk them.
        # This returns a list of LangChain Document objects, each with content and metadata.
        LOGGER.info("=" * 70)
        LOGGER.info("Loading knowledge base documents from knowledge_base/")
        LOGGER.info("=" * 70)
        chunks = load_documents()

        if not chunks:
            LOGGER.error("No documents found. Check knowledge_base/ folder exists.")
            sys.exit(1)

        LOGGER.info(f"Loaded and chunked {len(chunks)} document chunks.")

        # Step 2: Embed and upload chunks to Supabase pgvector.
        # SupabaseVectorStore.from_documents() handles batching and rate limits.
        LOGGER.info("=" * 70)
        LOGGER.info("Embedding and uploading to Supabase...")
        LOGGER.info("=" * 70)
        ingest_documents(chunks)

        LOGGER.info("=" * 70)
        LOGGER.info("✓ Ingestion complete! Navigate to Supabase > documents table to verify.")
        LOGGER.info("=" * 70)

    except KeyboardInterrupt:
        # User pressed Ctrl+C; exit gracefully without stack trace.
        LOGGER.warning("Ingestion interrupted by user.")
        sys.exit(130)

    except Exception as e:
        # Catch any error (Supabase, Azure, file I/O) and log with full traceback.
        LOGGER.exception(
            "Ingestion failed with error: %s. Check config and Supabase connectivity.",
            str(e),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
