-- B1.5: Create HNSW indexes for vector similarity search performance.
-- HNSW is supported for <= 2000-dim vectors (1536 is OK).

-- HNSW index for document retrieval vectors.
CREATE INDEX IF NOT EXISTS documents_embedding_hnsw_idx
ON public.documents
USING hnsw (embedding vector_cosine_ops);

-- HNSW index for semantic cache question vectors.
CREATE INDEX IF NOT EXISTS semantic_cache_question_embedding_hnsw_idx
ON public.semantic_cache
USING hnsw (question_embedding vector_cosine_ops);

