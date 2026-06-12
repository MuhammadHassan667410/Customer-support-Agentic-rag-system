# Execution Tasks - Granular Build Checklist

This file decomposes the AGENTS.md phases into small, dependency-safe execution tasks for easier build, debugging, and handoff.

## Usage rules

1. Execute tasks in order.
2. Do not start a task if its dependencies are not complete.
3. Mark task status in `PROGRESS.md` after each completed phase.
4. Do not move to the next phase without explicit confirmation.

Status legend:
- `[ ]` pending
- `[~]` in progress
- `[x]` done
- `[!]` blocked

---

## Group A - Foundation

### A1. Repository and structure bootstrap (Phase 1)
- [x] A1.1 Create folder tree exactly as defined in AGENTS.md.
- [x] A1.2 Initialize git repository.
- [x] A1.3 Create `.gitignore` (`.env`, `.venv`, `__pycache__`, Python artifacts).
- [x] A1.4 Create `.venv` and activate.
- [x] A1.5 Create pinned `requirements.txt` from latest stable compatible releases.
- [x] A1.6 Install dependencies.
- [x] A1.7 Create `.env.example` with required variables only.
- [x] A1.8 Create `PROGRESS.md` and set Phase 1 state.
- [x] A1.9 Run import smoke test command.

Dependencies: none

### A2. Configuration source of truth (Phase 2)
- [x] A2.1 Implement `src/config.py` with `load_dotenv()`.
- [x] A2.2 Add required env var validation helper.
- [x] A2.3 Expose grouped constants (Azure, Supabase, LangSmith, app tuning).
- [x] A2.4 Add type hints, docstrings, logging where relevant.
- [x] A2.5 Test config import and non-secret value loading.

Dependencies: A1

### A3. Supabase client singleton (Phase 3)
- [x] A3.1 Implement `src/database/supabase_client.py`.
- [x] A3.2 Create one module-level `supabase` client from config values.
- [x] A3.3 Add clear exception path for invalid credentials.
- [x] A3.4 Run authenticated query smoke check.

Dependencies: A2

---

## Group B - Data layer and ingestion

### B1. Database schema + pgvector + RPC (Phase 4)
- [x] B1.1 Enable `vector` extension.
- [x] B1.2 Create `documents` table with embedding column.
- [x] B1.3 Create `semantic_cache` table with question embedding + hit_count.
- [x] B1.4 Create `long_term_memory` table.
- [x] B1.5 Create HNSW indexes for embedding columns.
- [x] B1.6 Create similarity RPC function(s) needed by retrieval/cache.
- [x] B1.7 Validate by inserting test rows.

Dependencies: A3

### B2. Embedding model module (Phase 5)
- [x] B2.1 Implement `src/embeddings/azure_embeddings.py`.
- [x] B2.2 Export singleton embeddings object.
- [x] B2.3 Run single-sentence embedding test and verify dimension.

Dependencies: A2

### B3. KB consistency normalization pass (pre-Phase 6 quality gate)
- [x] B3.1 Review all six KB files for factual conflicts (pricing limits, support terms, plan constraints).
- [x] B3.2 Normalize conflicting statements to a single canonical policy.
- [x] B3.3 Preserve realistic enterprise tone and retrieval-rich detail.
- [x] B3.4 Re-check for internal consistency across all documents.

Dependencies: A2

### B4. Document loader and chunker (Phase 6)
- [x] B4.1 Implement `src/knowledge_base/document_loader.py`.
- [x] B4.2 Load all `.txt` docs via `DirectoryLoader` + `TextLoader`.
- [x] B4.3 Apply `RecursiveCharacterTextSplitter` with configured size/overlap.
- [x] B4.4 Add metadata (`source`, `title`, `chunk_index`).
- [x] B4.5 Print and inspect sample chunk outputs.

Dependencies: B3, B2

### B5. Ingestion pipeline (Phase 7)
- [x] B5.1 Implement `src/knowledge_base/ingest.py`.
- [x] B5.2 Implement `scripts/run_ingest.py`.
- [x] B5.3 Add batch processing and progress logging.
- [x] B5.4 Define idempotent ingestion strategy (clear/reingest or upsert policy).
- [x] B5.5 Execute ingestion and verify Supabase rows.

Dependencies: B1, B2, B4

---

## Group C - Retrieval, cache, and memory

### C1. RAG retriever tool (Phase 8)
- [ ] C1.1 Implement `src/retriever/rag_retriever.py`.
- [ ] C1.2 Initialize SupabaseVectorStore retriever with configurable top-K.
- [ ] C1.3 Build precise tool name + high-quality description.
- [ ] C1.4 Format retrieved docs for LLM-readable context.
- [ ] C1.5 Direct-call test with policy question.

Dependencies: B1, B2, B5

### C2. Semantic cache module (Phase 9)
- [ ] C2.1 Implement `src/cache/semantic_cache.py`.
- [ ] C2.2 `check_cache(query)` with embedding + thresholded semantic lookup.
- [ ] C2.3 Increment `hit_count` on successful match.
- [ ] C2.4 `write_to_cache(question, answer)` with near-duplicate suppression.
- [ ] C2.5 Paraphrase hit/miss behavior test.

Dependencies: B1, B2

### C3. Long-term memory module (Phase 10)
- [ ] C3.1 Implement `src/memory/long_term_memory.py`.
- [ ] C3.2 `get_user_memory(user_id)` recent-N retrieval and formatting.
- [ ] C3.3 `save_to_memory(user_id, user_message, agent_answer)` write path.
- [ ] C3.4 Multi-entry retrieval test for isolated test user.

Dependencies: B1

---

## Group D - Agent core

### D1. Agent state schema (Phase 11)
- [ ] D1.1 Implement `src/agent/state.py` TypedDict schema.
- [ ] D1.2 Configure additive list fields for messages where needed.
- [ ] D1.3 Validate sample state object shape.

Dependencies: C1, C2, C3

### D2. Agent nodes (Phase 12)
- [ ] D2.1 Implement `retrieve_memory_node`.
- [ ] D2.2 Implement `agent_reasoning_node` with Azure chat model + bound tools.
- [ ] D2.3 Implement `rag_tool_node` tool-call execution.
- [ ] D2.4 Implement `write_memory_node`.
- [ ] D2.5 Implement `write_cache_node`.
- [ ] D2.6 Node-level isolated tests with mock/sample state.

Dependencies: D1, C1, C2, C3, A2

### D3. Graph assembly and invoke wrapper (Phase 13)
- [ ] D3.1 Implement `src/agent/graph.py` with node registration.
- [ ] D3.2 Add edge flow and conditional routing.
- [ ] D3.3 Add loop guard/max iterations.
- [ ] D3.4 Export `invoke_agent(user_message, user_id)`.
- [ ] D3.5 End-to-end invoke test with refund-policy query.

Dependencies: D2

---

## Group E - Observability and interface

### E1. LangSmith observability validation (Phase 14)
- [ ] E1.1 Verify required tracing env vars are set.
- [ ] E1.2 Run three representative prompts.
- [ ] E1.3 Confirm traces show node/tool-level visibility.
- [ ] E1.4 Capture trace review notes for optimization.

Dependencies: D3

### E2. Gradio chat app (Phase 15)
- [ ] E2.1 Implement `src/interface/gradio_app.py`.
- [ ] E2.2 Add cache-first callback behavior.
- [ ] E2.3 Add fallback to `invoke_agent`.
- [ ] E2.4 Add user-friendly error messages.
- [ ] E2.5 Run the five required functional tests from AGENTS.md.

Dependencies: D3, C2

---

## Group F - Hardening and portfolio packaging

### F1. End-to-end validation and tuning (Phase 16)
- [ ] F1.1 Cache effectiveness scenario (5 paraphrase variants).
- [ ] F1.2 RAG accuracy scenario (10 KB-grounded questions).
- [ ] F1.3 Memory persistence across sessions (same user ID).
- [ ] F1.4 Direct-answer scenarios (no RAG expected).
- [ ] F1.5 Out-of-domain graceful handling scenario.
- [ ] F1.6 Concurrent-user isolation scenario.
- [ ] F1.7 Record bugs, fixes, and metrics in `PROGRESS.md`.

Dependencies: E2, E1

### F2. README and portfolio docs (Phase 17)
- [ ] F2.1 Write project tagline and feature summary.
- [ ] F2.2 Add architecture diagram (Mermaid or ASCII).
- [ ] F2.3 Add setup instructions and Supabase SQL section.
- [ ] F2.4 Add LangSmith usage section.
- [ ] F2.5 Add design decision rationale section.
- [ ] F2.6 Add cost analysis table (cache vs no-cache).
- [ ] F2.7 Add screenshot placeholders and guidance.

Dependencies: F1

---

## Recommended execution order (strict)

`A1 -> A2 -> A3 -> B1 -> B2 -> B3 -> B4 -> B5 -> C1 -> C2 -> C3 -> D1 -> D2 -> D3 -> E1 -> E2 -> F1 -> F2`

## Blocking conditions (stop and resolve before continuing)

- Missing or invalid `.env` values.
- Embedding dimension mismatch vs DB vector columns.
- RPC function signature mismatch with vector store calls.
- Tool-call loop without convergence.
- Cache threshold causing incorrect semantic hits.
- Memory leakage across user IDs.

