-- B1.6: Create RPC functions for vector similarity search.
-- These functions are called by retriever and semantic cache logic.

-- Document similarity matcher for RAG retrieval.
CREATE OR REPLACE FUNCTION public.match_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.0,
    filter JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.content,
        d.metadata,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM public.documents AS d
    WHERE d.metadata @> filter
      AND 1 - (d.embedding <=> query_embedding) >= match_threshold
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Semantic cache similarity matcher for question embeddings.
CREATE OR REPLACE FUNCTION public.match_semantic_cache(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 1,
    match_threshold FLOAT DEFAULT 0.95
)
RETURNS TABLE (
    id UUID,
    question TEXT,
    answer TEXT,
    hit_count INTEGER,
    created_at TIMESTAMPTZ,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.question,
        c.answer,
        c.hit_count,
        c.created_at,
        1 - (c.question_embedding <=> query_embedding) AS similarity
    FROM public.semantic_cache AS c
    WHERE 1 - (c.question_embedding <=> query_embedding) >= match_threshold
    ORDER BY c.question_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

