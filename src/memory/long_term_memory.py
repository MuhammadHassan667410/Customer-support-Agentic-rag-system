"""Long-term memory utilities backed by Supabase.

This module will provide read/write helpers for persistent user memory stored
in the long_term_memory table.
"""

from __future__ import annotations

# Standard library imports for logging and typing.
import logging
import uuid
from typing import List

# Supabase client singleton for database access.
from src.database import supabase

# Configuration constants for memory behavior.
from src.config import MAX_MEMORY_ENTRIES, MEMORY_TABLE_NAME

# Module-level logger for consistent, centralized output.
LOGGER = logging.getLogger(__name__)

# Limit user ID logging to avoid overly verbose output.
_USER_ID_LOG_PREVIEW_LENGTH = 50


def _format_memory_entries(entries: List[str]) -> str:
    """Format memory summaries into a single LLM-friendly string.

    Args:
        entries: A list of memory summary strings ordered most-recent first.

    Returns:
        A formatted string suitable for injecting into a system prompt.
    """
    if not entries:
        return ""

    # Preserve ordering with clear labels so the LLM can interpret chronology.
    formatted_lines = ["Previous conversations (most recent first):"]
    for entry in entries:
        formatted_lines.append(f"- {entry}")

    return "\n".join(formatted_lines)


def get_user_memory(user_id: str) -> str:
    """Retrieve the most recent memory entries for a user.

    Args:
        user_id: Unique identifier for the user whose memory should be loaded.

    Returns:
        A formatted string containing recent memory summaries, or empty string.
    """
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        LOGGER.warning("Memory read skipped because user_id was empty.")
        return ""

    try:
        response = (
            supabase.table(MEMORY_TABLE_NAME)
            .select("summary")
            .eq("user_id", cleaned_user_id)
            .order("created_at", desc=True)
            .limit(MAX_MEMORY_ENTRIES)
            .execute()
        )
    except Exception as error:
        LOGGER.exception(
            "Failed to read memory for user '%s': %s",
            cleaned_user_id[:_USER_ID_LOG_PREVIEW_LENGTH],
            str(error),
        )
        return ""

    rows = response.data or []
    summaries = [row.get("summary", "").strip() for row in rows if row.get("summary")]

    if not summaries:
        LOGGER.info(
            "No memory entries found for user '%s'.",
            cleaned_user_id[:_USER_ID_LOG_PREVIEW_LENGTH],
        )
        return ""

    LOGGER.info(
        "Loaded %d memory entries for user '%s'.",
        len(summaries),
        cleaned_user_id[:_USER_ID_LOG_PREVIEW_LENGTH],
    )

    return _format_memory_entries(summaries)


def save_to_memory(user_id: str, user_message: str, agent_answer: str) -> bool:
    """Persist a summarized conversation turn for a user.

    Args:
        user_id: Unique identifier for the user.
        user_message: The raw user input for this turn.
        agent_answer: The assistant's final response for this turn.

    Returns:
        True if the memory entry was written successfully; False otherwise.
    """
    cleaned_user_id = user_id.strip()
    cleaned_user_message = user_message.strip()
    cleaned_agent_answer = agent_answer.strip()

    if not cleaned_user_id:
        LOGGER.warning("Memory write skipped because user_id was empty.")
        return False

    if not cleaned_user_message:
        LOGGER.warning("Memory write skipped because user_message was empty.")
        return False

    if not cleaned_agent_answer:
        LOGGER.warning("Memory write skipped because agent_answer was empty.")
        return False

    # Use a lightweight, deterministic summary to avoid extra LLM calls.
    summary = f"User asked: {cleaned_user_message} | Agent answered: {cleaned_agent_answer}"

    # Generate a session_id so multiple turns can be grouped later if needed.
    session_id = str(uuid.uuid4())

    try:
        supabase.table(MEMORY_TABLE_NAME).insert(
            {
                "user_id": cleaned_user_id,
                "summary": summary,
                "session_id": session_id,
            }
        ).execute()
    except Exception as error:
        LOGGER.exception(
            "Failed to write memory for user '%s': %s",
            cleaned_user_id[:_USER_ID_LOG_PREVIEW_LENGTH],
            str(error),
        )
        return False

    LOGGER.info(
        "Stored memory entry for user '%s' (session_id=%s).",
        cleaned_user_id[:_USER_ID_LOG_PREVIEW_LENGTH],
        session_id,
    )
    return True


__all__ = ["get_user_memory", "save_to_memory"]

