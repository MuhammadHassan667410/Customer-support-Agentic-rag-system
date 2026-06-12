-- B1.3: Create semantic cache table for question-answer vector reuse.
-- Ensure pgcrypto is available for UUID defaults.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.semantic_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    question_embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hit_count INTEGER NOT NULL DEFAULT 0 CHECK (hit_count >= 0)
);

