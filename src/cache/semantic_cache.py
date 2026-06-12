"""Semantic cache utilities backed by Supabase pgvector.

This module will provide read/write helpers for the semantic cache table, allowing
the application to reuse answers for semantically similar questions.
"""

from __future__ import annotations

# Standard library imports for logging and typing.
import logging
from typing import List, Optional

# Embeddings and Supabase client singletons used for vector search.
from src.embeddings import embeddings
from src.database import supabase

# Configuration constants for cache behavior and thresholds.
from src.config import CACHE_TABLE_NAME, SIMILARITY_THRESHOLD

# Module-level logger for consistent, centralized output.
LOGGER = logging.getLogger(__name__)

# RPC name for semantic cache similarity lookup (defined in Supabase SQL scripts).
_MATCH_SEMANTIC_CACHE_RPC_NAME = "match_semantic_cache"

# Cache lookup uses a single best-match result to keep responses deterministic.
_CACHE_MATCH_COUNT = 1

# Limit query text in logs to avoid overly verbose output.
_QUERY_LOG_PREVIEW_LENGTH = 50

# Default similarity value used when a response row omits the score.
_DEFAULT_SIMILARITY_SCORE = 0.0


def _find_cache_match(query_embedding: List[float]) -> Optional[dict]:
    """Find the closest semantic cache match for a given query embedding.

    Args:
        query_embedding: The embedding vector for the user query.

    Returns:
        The top matching cache row if found; otherwise None.
    """
    # Build the RPC payload using the configured threshold and match count.
    rpc_payload = {
        "query_embedding": query_embedding,
        "match_count": _CACHE_MATCH_COUNT,
        "match_threshold": SIMILARITY_THRESHOLD,
    }

    # Execute the Supabase RPC for semantic cache lookup.
    try:
        response = supabase.rpc(_MATCH_SEMANTIC_CACHE_RPC_NAME, rpc_payload).execute()
    except Exception as error:
        # Log RPC failures and return a safe cache miss.
        LOGGER.exception(
            "Cache RPC '%s' failed against table '%s': %s",
            _MATCH_SEMANTIC_CACHE_RPC_NAME,
            CACHE_TABLE_NAME,
            str(error),
        )
        return None

    # Supabase returns a list of rows in response.data.
    rows = response.data or []

    # Treat empty results as a cache miss.
    if not rows:
        return None

    # Use the top match row (RPC already orders by similarity).
    return rows[0]


def check_cache(query: str) -> Optional[str]:
    """Return a cached answer if the query matches an existing entry.

    Args:
        query: The user question to check against the semantic cache.

    Returns:
        The cached answer string if a semantic match is found; otherwise None.
    """
    # Normalize the query for consistent embedding and logging.
    cleaned_query = query.strip()

    # Avoid embedding empty or whitespace-only queries.
    if not cleaned_query:
        LOGGER.warning("Cache check skipped because query was empty.")
        return None

    # Create the query embedding using the shared Azure embeddings instance.
    try:
        query_embedding = embeddings.embed_query(cleaned_query)
    except Exception as error:
        # Surface embedding failures clearly to avoid silent cache misses.
        LOGGER.exception("Failed to embed cache query: %s", str(error))
        return None

    # Look up the closest cache match using the precomputed embedding.
    top_row = _find_cache_match(query_embedding)

    # Log explicit cache miss to aid debugging and tuning.
    if not top_row:
        LOGGER.info(
            "Cache miss for query '%s'.",
            cleaned_query[:_QUERY_LOG_PREVIEW_LENGTH],
        )
        return None

    # Extract the cached answer safely.
    answer = top_row.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        LOGGER.warning("Cache row missing valid answer: %s", top_row)
        return None

    # Log the cache hit with similarity score if present.
    similarity_score = top_row.get("similarity", _DEFAULT_SIMILARITY_SCORE)
    LOGGER.info(
        "Cache hit for query '%s' (similarity=%.4f).",
        cleaned_query[:_QUERY_LOG_PREVIEW_LENGTH],
        similarity_score,
    )

    # Best-effort: increment hit_count for analytics without blocking response.
    cache_id = top_row.get("id")
    current_hits = top_row.get("hit_count", 0)
    if cache_id:
        try:
            supabase.table(CACHE_TABLE_NAME).update(
                {"hit_count": int(current_hits) + 1}
            ).eq("id", cache_id).execute()
        except Exception as error:
            LOGGER.exception(
                "Failed to increment hit_count for cache id '%s': %s",
                cache_id,
                str(error),
            )

    return answer


def write_to_cache(question: str, answer: str) -> bool:
    """Insert a new semantic cache entry if no near-duplicate exists.

    Args:
        question: The original user question to cache.
        answer: The final response to store for reuse.

    Returns:
        True if a new cache entry was inserted; False otherwise.
    """
    cleaned_question = question.strip()
    cleaned_answer = answer.strip()

    if not cleaned_question:
        LOGGER.warning("Cache write skipped because question was empty.")
        return False

    if not cleaned_answer:
        LOGGER.warning("Cache write skipped because answer was empty.")
        return False

    # Create the embedding for the question once and reuse it.
    try:
        question_embedding = embeddings.embed_query(cleaned_question)
    except Exception as error:
        LOGGER.exception("Failed to embed cache question: %s", str(error))
        return False

    # Near-duplicate suppression: if a close match exists, do not insert.
    existing_match = _find_cache_match(question_embedding)
    if existing_match:
        similarity_score = existing_match.get("similarity", _DEFAULT_SIMILARITY_SCORE)
        LOGGER.info(
            "Cache insert skipped due to near-duplicate (similarity=%.4f).",
            similarity_score,
        )
        return False

    # Insert the new cache entry into Supabase.
    try:
        supabase.table(CACHE_TABLE_NAME).insert(
            {
                "question": cleaned_question,
                "answer": cleaned_answer,
                "question_embedding": question_embedding,
                "hit_count": 0,
            }
        ).execute()
    except Exception as error:
        LOGGER.exception("Failed to write cache entry: %s", str(error))
        return False

    LOGGER.info("Cache entry stored for question '%s'.", cleaned_question[:_QUERY_LOG_PREVIEW_LENGTH])
    return True


__all__ = ["check_cache", "write_to_cache"]

