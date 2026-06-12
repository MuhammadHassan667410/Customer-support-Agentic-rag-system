"""Azure embeddings singleton used across retrieval, cache, and ingestion.

This module centralizes Azure OpenAI embedding client construction so every
component shares one consistent embeddings configuration.
"""

from __future__ import annotations

import logging
from typing import Final

from langchain_openai import AzureOpenAIEmbeddings

from src.config import (
    AZURE_EMBEDDING_DEPLOYMENT_NAME,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
)


logger = logging.getLogger(__name__)


def create_embeddings() -> AzureOpenAIEmbeddings:
    """Create and return the Azure OpenAI embeddings client.

    Returns:
        A configured `AzureOpenAIEmbeddings` instance.
    """
    logger.info("Initializing Azure OpenAI embeddings client singleton.")
    return AzureOpenAIEmbeddings(
        # The deployment name is the Azure resource we actually call.
        azure_deployment=AZURE_EMBEDDING_DEPLOYMENT_NAME,
        # LangChain expects model metadata for request shaping/token handling.
        model=AZURE_EMBEDDING_DEPLOYMENT_NAME,
        # Explicit credentials/config from centralized config module.
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


# Module-level singleton for app-wide reuse.
embeddings: Final[AzureOpenAIEmbeddings] = create_embeddings()


__all__ = ["embeddings", "create_embeddings"]

