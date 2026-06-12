-- B1.4: Create long-term memory table for per-user conversation summaries.
-- Ensure pgcrypto is available for UUID defaults.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.long_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_id TEXT
);

