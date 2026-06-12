"""Embed and upload knowledge base chunks to Supabase pgvector table."""

# Use postponed evaluation for type annotations to avoid runtime import cycles.
from __future__ import annotations

# Standard library imports for logging and typing.
import logging
from typing import List

# LangChain document type and vector store integration for Supabase.
from langchain_core.documents import Document

# SupabaseVectorStore handles embedding and batch uploading to pgvector.
from langchain_community.vectorstores import SupabaseVectorStore

# Our embeddings and database clients are singletons.
from src.embeddings import embeddings
from src.database import supabase

# Configuration for table names and batch sizes.
from src.config import DELETE_ALL_ROWS_FILTER_ID, DOCUMENTS_TABLE_NAME

# Module-level logger for consistent output and observability.
LOGGER = logging.getLogger(__name__)


def ingest_documents(chunks: List[Document]) -> None:
    """Embed and upload document chunks to Supabase pgvector.

    Args:
        chunks: Pre-chunked and metadata-enriched Document objects to ingest.

    Raises:
        ValueError: If the chunks list is empty or embeddings/database config invalid.
        Exception: Propagates any Supabase or Azure API errors for caller to handle.
    """
    # Guard against silent failures when given empty input.
    if not chunks:
        raise ValueError("Cannot ingest zero document chunks. Load and split KB first.")

    LOGGER.info("Starting ingestion of %d chunks to Supabase.", len(chunks))

    # Ensure idempotency by clearing any existing rows before re-ingesting.
    _clear_documents_table()

    # Create a SupabaseVectorStore that will:
    # 1. Embed each chunk using our Azure embeddings instance.
    # 2. Upload embeddings to the Supabase pgvector table.
    # 3. Handle batching and rate limit protection automatically.
    SupabaseVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        client=supabase,
        table_name=DOCUMENTS_TABLE_NAME,
        # query_name is the RPC function we created in B1.6 for similarity search.
        query_name="match_documents",
    )

    LOGGER.info(
        "Successfully ingested %d chunks. Vector store created at table '%s'.",
        len(chunks),
        DOCUMENTS_TABLE_NAME,
    )


def _clear_documents_table() -> None:
    """Delete all rows from the documents table for idempotent ingestion."""
    LOGGER.info("Clearing existing rows from '%s' before ingestion.", DOCUMENTS_TABLE_NAME)

    try:
        response = (
            supabase.table(DOCUMENTS_TABLE_NAME)
            .delete()
            .neq("id", DELETE_ALL_ROWS_FILTER_ID)
            .execute()
        )
    except Exception as error:
        # Surface Supabase failures clearly while preserving the traceback.
        LOGGER.exception(
            "Failed to clear '%s' before ingestion: %s",
            DOCUMENTS_TABLE_NAME,
            str(error),
        )
        raise

    deleted_count = len(response.data) if response and response.data else 0
    LOGGER.info("Cleared %d existing rows from '%s'.", deleted_count, DOCUMENTS_TABLE_NAME)
