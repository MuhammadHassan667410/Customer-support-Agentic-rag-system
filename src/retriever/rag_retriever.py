"""RAG retriever tool backed by Supabase pgvector RPC calls.

This module provides semantic search functionality for the NovaTech knowledge base:
- search_company_knowledge_base: The @tool-wrapped version for use by the LangGraph agent.
- _search_knowledge_base_internal: The underlying function for direct testing (not wrapped).
"""

# Standard library imports for logging and typing.
import logging
from typing import List

# LangChain document type used when formatting retrieved chunks.
from langchain_core.documents import Document

# LangChain Tool wrapper for making a function usable by agents.
from langchain_core.tools import tool

# Our embeddings and database clients are singletons.
from src.embeddings import embeddings
from src.database import supabase

# Configuration for retrieval parameters.
from src.config import TOP_K_RETRIEVAL

LOGGER = logging.getLogger(__name__)

# RPC name defined in the Supabase SQL scripts (scripts/sql/b1_6_create_similarity_rpc_functions.sql).
_MATCH_DOCUMENTS_RPC_NAME = "match_documents"


def _format_documents_for_llm(documents: List[Document]) -> str:
    """Format retrieved Document objects into readable text for the LLM.

    Each document includes its source and title in metadata. This function
    creates a clear, readable block of text that the LLM can understand.

    Args:
        documents: List of LangChain Document objects with content and metadata.

    Returns:
        A formatted string with all documents, clearly labeled with source.
    """
    if not documents:
        return "No relevant documents found."

    # Build a readable string for each document with metadata context.
    formatted_parts: List[str] = []
    for idx, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "Unknown Source")
        title = doc.metadata.get("title", "Untitled")
        content = doc.page_content

        formatted_parts.append(
            f"[Document {idx}] {title} (from {source})\n{content}"
        )

    # Join all documents with clear separation.
    return "\n\n".join(formatted_parts)


def _build_documents_from_rpc_rows(rows: List[dict]) -> List[Document]:
    """Convert Supabase RPC response rows into LangChain Document objects.

    Args:
        rows: List of rows returned by the match_documents RPC function.

    Returns:
        A list of Document objects ready for formatting and LLM consumption.
    """
    documents: List[Document] = []

    for row in rows:
        # Metadata can be null in the database, so ensure we always have a dict.
        metadata = row.get("metadata") or {}
        # Preserve similarity scores for debugging or future ranking tweaks.
        if "similarity" in row:
            metadata["similarity"] = row["similarity"]

        documents.append(
            Document(
                page_content=row.get("content", ""),
                metadata=metadata,
            )
        )

    return documents


def _search_knowledge_base_internal(query: str) -> str:
    """Internal helper for knowledge base search (testable without @tool wrapper).

    This is the core search logic that does the actual work.
    It is separated from the @tool version so you can call it directly for testing.

    Args:
        query: A natural language question about NovaTech or its products.

    Returns:
        Formatted text containing the top-K most relevant document chunks,
        or a message if no relevant documents are found.
    """
    # Embed the query using the Azure OpenAI embeddings model.
    query_embedding = embeddings.embed_query(query)

    # Call the Supabase RPC function to fetch the top-K most similar documents.
    rpc_payload = {
        "query_embedding": query_embedding,
        "match_count": TOP_K_RETRIEVAL,
    }
    response = supabase.rpc(_MATCH_DOCUMENTS_RPC_NAME, rpc_payload).execute()
    rows = response.data or []
    documents = _build_documents_from_rpc_rows(rows)

    # Format the retrieved documents into readable text for the LLM.
    formatted_result = _format_documents_for_llm(documents)

    LOGGER.info(
        "RAG search for query '%s' returned %d documents via RPC.",
        query[:50],  # Log first 50 chars of query for debugging.
        len(documents),
    )

    return formatted_result


@tool
def search_company_knowledge_base(query: str) -> str:
    """Search NovaTech Support's company knowledge base for relevant information.

    This tool searches a semantic vector database of company documents including:
    - Company overview, mission, and history
    - Product features and capabilities
    - Pricing plans and billing details
    - Frequently asked questions
    - Refund and cancellation policies
    - Onboarding guides and setup instructions

    Use this tool when:
    - The user asks about NovaTech products, pricing, or policies
    - The user needs details about company procedures or features
    - The user's question is specific to NovaTech operations
    - The query is about account, billing, or product information

    Do NOT use this tool for:
    - General knowledge questions (e.g., "What is machine learning?")
    - Questions outside NovaTech's scope
    - Polite greetings or meta-questions about the chatbot itself

    The search returns the top {0} most relevant document chunks based on
    semantic similarity to your query. The LLM will use these documents to
    formulate an accurate, grounded answer.

    Args:
        query: A natural language question about NovaTech or its products.

    Returns:
        Formatted text containing the top-K most relevant document chunks,
        or a message if no relevant documents are found.
    """
    # Delegate to the internal helper function (which does the actual work).
    # This indirection allows us to call the logic directly for testing
    # while keeping the @tool wrapper for agent integration.
    return _search_knowledge_base_internal(query)

