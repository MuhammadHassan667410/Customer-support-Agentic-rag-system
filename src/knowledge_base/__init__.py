"""Knowledge base package for document loading, chunking, and ingestion."""

# Export the main entry point for loading and chunking documents.
from src.knowledge_base.document_loader import load_documents

__all__ = ["load_documents"]
