"""Load and chunk knowledge base documents for downstream embedding and retrieval."""

# Use postponed evaluation for type annotations to avoid runtime import cycles.
from __future__ import annotations

# Standard library imports for logging, file system paths, and typing.
import logging
from pathlib import Path
from typing import Dict, List

# LangChain document type used throughout the ingestion pipeline.
from langchain_core.documents import Document

# DirectoryLoader and TextLoader handle bulk loading of .txt files.
from langchain_community.document_loaders import DirectoryLoader, TextLoader

# RecursiveCharacterTextSplitter chunks documents into retrieval-friendly pieces.
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Centralized configuration keeps chunk sizes and file patterns consistent.
from src.config import CHUNK_OVERLAP, CHUNK_SIZE, KNOWLEDGE_BASE_GLOB


# Module-level logger keeps output consistent across the codebase.
LOGGER = logging.getLogger(__name__)

# The knowledge base folder lives two levels above this module (project root).
PROJECT_ROOT_DEPTH = 2

# Metadata keys are centralized to avoid typos and enable consistent retrieval.
METADATA_SOURCE_KEY = "source"
METADATA_TITLE_KEY = "title"
METADATA_CHUNK_INDEX_KEY = "chunk_index"


def _derive_title(source_path: str) -> str:
    """Derive a human-readable document title from a file path.

    Args:
        source_path: File path pointing to the source document.

    Returns:
        A title based on the file name with underscores replaced by spaces.
    """
    # Keep only the file name without extension for a clean title.
    file_stem = Path(source_path).stem
    return file_stem.replace("_", " ").strip()


def _enrich_chunk_metadata(chunks: List[Document]) -> List[Document]:
    """Add source, title, and chunk index metadata to each chunk.

    Args:
        chunks: Chunked documents to be enriched.

    Returns:
        Chunked documents with consistent metadata fields populated.
    """
    # Track chunk counters per source file to ensure stable indices.
    counters_by_source: Dict[str, int] = {}

    for chunk in chunks:
        # Default to an empty dict if no metadata exists yet.
        metadata = dict(chunk.metadata or {})

        # Resolve a stable source identifier from the loader metadata if present.
        source_path = str(metadata.get("source", "unknown"))

        # Initialize and increment the per-source chunk counter.
        current_index = counters_by_source.get(source_path, 0)
        counters_by_source[source_path] = current_index + 1

        # Populate normalized metadata fields expected by downstream retrieval.
        metadata[METADATA_SOURCE_KEY] = source_path
        metadata[METADATA_TITLE_KEY] = _derive_title(source_path)
        metadata[METADATA_CHUNK_INDEX_KEY] = current_index

        # Re-attach enriched metadata to the chunk.
        chunk.metadata = metadata

    return chunks


def load_documents() -> List[Document]:
    """Load knowledge base documents from disk.

    Returns:
        A list of LangChain Document objects from the knowledge base folder.
    """
    # Resolve the project root without relying on external configuration.
    project_root = Path(__file__).resolve().parents[PROJECT_ROOT_DEPTH]

    # Build the path to the knowledge_base directory.
    knowledge_base_dir = project_root / "knowledge_base"

    # Stop early with a clear log if the folder is missing.
    if not knowledge_base_dir.exists():
        LOGGER.error(
            "Knowledge base folder not found at %s. Expected .txt files inside it.",
            knowledge_base_dir,
        )
        return []

    # Configure a directory loader that only reads .txt files.
    loader = DirectoryLoader(
        path=str(knowledge_base_dir),
        glob=KNOWLEDGE_BASE_GLOB,
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        recursive=True,
        show_progress=False,
    )

    # Load the documents while logging any loader failures.
    try:
        documents = loader.load()
    except Exception:
        LOGGER.exception(
            "Failed to load knowledge base documents from %s.", knowledge_base_dir
        )
        return []

    # Warn if the directory is empty to prevent silent ingestion.
    if not documents:
        LOGGER.warning("No documents found in knowledge base at %s.", knowledge_base_dir)

    # Build a splitter that respects configured chunk size and overlap.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    # Split the documents into overlapping chunks for retrieval.
    try:
        chunks = splitter.split_documents(documents)
    except Exception:
        LOGGER.exception(
            "Failed to split knowledge base documents from %s.", knowledge_base_dir
        )
        return []

    # Warn if splitting produced no chunks to avoid silent failures.
    if not chunks:
        LOGGER.warning(
            "Document splitting produced zero chunks from %s.", knowledge_base_dir
        )
        return []

    # Enrich chunk metadata with source, title, and chunk indices.
    return _enrich_chunk_metadata(chunks)
