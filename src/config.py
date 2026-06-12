"""Centralized configuration loader for the NovaTech support agent project.

This module is the single source of truth for runtime configuration.
It loads values from `.env`, validates required variables early, and exports
typed constants for use across the codebase.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv


def _require_env_var(name: str) -> str:
    """Return a required environment variable or raise a descriptive error.

    Args:
        name: Environment variable name to read.

    Returns:
        The non-empty environment variable value.

    Raises:
        ValueError: If the variable is missing or empty.
    """
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ValueError(
            f"Missing required environment variable: {name}. "
            f"Set it in the project .env file before starting the app."
        )
    return value.strip()


def _parse_bool_env(name: str, default: bool) -> bool:
    """Parse a boolean environment variable with strict accepted values.

    Args:
        name: Environment variable name to parse.
        default: Fallback boolean value when the variable is missing/empty.

    Returns:
        Parsed boolean value.

    Raises:
        ValueError: If a provided value cannot be parsed as a boolean.
    """
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"Invalid boolean value for {name}: {raw_value!r}. "
        "Use one of: true/false, 1/0, yes/no, on/off."
    )


def _parse_int_env(name: str, default: int) -> int:
    """Parse an integer environment variable with a fallback.

    Args:
        name: Environment variable name to parse.
        default: Fallback integer value when missing/empty.

    Returns:
        Parsed integer value.

    Raises:
        ValueError: If a provided value is not a valid integer.
    """
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        return int(raw_value.strip())
    except ValueError as error:
        raise ValueError(
            f"Invalid integer value for {name}: {raw_value!r}."
        ) from error


def _parse_float_env(name: str, default: float) -> float:
    """Parse a float environment variable with a fallback.

    Args:
        name: Environment variable name to parse.
        default: Fallback float value when missing/empty.

    Returns:
        Parsed float value.

    Raises:
        ValueError: If a provided value is not a valid float.
    """
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        return float(raw_value.strip())
    except ValueError as error:
        raise ValueError(
            f"Invalid float value for {name}: {raw_value!r}."
        ) from error


def _read_str_env(name: str, default: str) -> str:
    """Read a string environment variable with a non-empty fallback.

    Args:
        name: Environment variable name to read.
        default: Fallback string value when missing/empty.

    Returns:
        A non-empty string value.
    """
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return raw_value.strip()


# Load project-local .env before reading any environment variables.
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
ENV_FILE_PATH: Final[Path] = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)


# Azure AI Foundry configuration
AZURE_OPENAI_API_KEY: Final[str] = _require_env_var("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT: Final[str] = _require_env_var("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION: Final[str] = _require_env_var("AZURE_OPENAI_API_VERSION")
AZURE_CHAT_DEPLOYMENT_NAME: Final[str] = _require_env_var("AZURE_CHAT_DEPLOYMENT_NAME")
AZURE_EMBEDDING_DEPLOYMENT_NAME: Final[str] = _require_env_var(
    "AZURE_EMBEDDING_DEPLOYMENT_NAME"
)


# Supabase configuration
SUPABASE_URL: Final[str] = _require_env_var("SUPABASE_URL")
SUPABASE_SERVICE_KEY: Final[str] = _require_env_var("SUPABASE_SERVICE_KEY")


# LangSmith observability configuration
LANGCHAIN_TRACING_V2: Final[bool] = _parse_bool_env("LANGCHAIN_TRACING_V2", default=True)
LANGCHAIN_ENDPOINT: Final[str] = _require_env_var("LANGCHAIN_ENDPOINT")
LANGCHAIN_PROJECT: Final[str] = _require_env_var("LANGCHAIN_PROJECT")
LANGCHAIN_API_KEY: Final[str] = (
    _require_env_var("LANGCHAIN_API_KEY")
    if LANGCHAIN_TRACING_V2
    else _read_str_env("LANGCHAIN_API_KEY", "")
)


# Application tuning configuration
SIMILARITY_THRESHOLD: Final[float] = _parse_float_env("SIMILARITY_THRESHOLD", default=0.95)
TOP_K_RETRIEVAL: Final[int] = _parse_int_env("TOP_K_RETRIEVAL", default=5)
MAX_MEMORY_ENTRIES: Final[int] = _parse_int_env("MAX_MEMORY_ENTRIES", default=10)
GRAPH_RECURSION_LIMIT: Final[int] = _parse_int_env("GRAPH_RECURSION_LIMIT", default=10)
CACHE_TABLE_NAME: Final[str] = _read_str_env("CACHE_TABLE_NAME", default="semantic_cache")
DOCUMENTS_TABLE_NAME: Final[str] = _read_str_env("DOCUMENTS_TABLE_NAME", default="documents")
MEMORY_TABLE_NAME: Final[str] = _read_str_env("MEMORY_TABLE_NAME", default="long_term_memory")
# Sentinel UUID used to safely clear a table via "not equal" filter.
DELETE_ALL_ROWS_FILTER_ID: Final[str] = "00000000-0000-0000-0000-000000000000"
# Knowledge base loader settings are configurable to support different corpora.
KNOWLEDGE_BASE_GLOB: Final[str] = _read_str_env("KNOWLEDGE_BASE_GLOB", default="**/*.txt")
# Chunk size determines how much text each retrieval unit contains.
CHUNK_SIZE: Final[int] = _parse_int_env("CHUNK_SIZE", default=1000)
# Overlap preserves context across chunk boundaries for better recall.
CHUNK_OVERLAP: Final[int] = _parse_int_env("CHUNK_OVERLAP", default=200)


__all__ = [
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_VERSION",
    "AZURE_CHAT_DEPLOYMENT_NAME",
    "AZURE_EMBEDDING_DEPLOYMENT_NAME",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "LANGCHAIN_TRACING_V2",
    "LANGCHAIN_ENDPOINT",
    "LANGCHAIN_API_KEY",
    "LANGCHAIN_PROJECT",
    "SIMILARITY_THRESHOLD",
    "TOP_K_RETRIEVAL",
    "MAX_MEMORY_ENTRIES",
    "GRAPH_RECURSION_LIMIT",
    "CACHE_TABLE_NAME",
    "DOCUMENTS_TABLE_NAME",
    "MEMORY_TABLE_NAME",
    "DELETE_ALL_ROWS_FILTER_ID",
    "KNOWLEDGE_BASE_GLOB",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
]

