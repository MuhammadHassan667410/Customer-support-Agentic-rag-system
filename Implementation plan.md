# Implementation Plan - NovaTech Agentic RAG Support System

## 1) Project understanding (from AGENTS.md + current repository)

This project is a production-grade customer support chatbot for **NovaTech Solutions** using:
- LangGraph for agentic control flow and tool routing.
- LangChain for loaders, splitters, embeddings, tools, and vector store integration.
- Azure AI Foundry (Azure OpenAI-compatible) for chat + embeddings.
- Supabase (Postgres + pgvector) for document retrieval, long-term memory, and semantic cache.
- LangSmith for observability/traces.
- Gradio for demo/testing UI.

Target behavior:
1. Check semantic cache first.
2. If miss, run LangGraph agent.
3. Load user memory.
4. Let LLM decide direct answer vs RAG tool call.
5. If tool called, retrieve top-K chunks and continue reasoning loop.
6. Return final answer.
7. Persist memory + cache.

## 2) Current baseline status (actual repo state)

Repository currently contains:
- `AGENTS.md` (full build specification and constraints).
- `knowledge_base/` with six source docs:
  - `company_overview.txt`
  - `product_features.txt`
  - `pricing_plans.txt`
  - `faq.txt`
  - `refund_policy.txt`
  - `onboarding_guide.txt`

Not yet present:
- `src/`, `scripts/`, `.env.example`, `requirements.txt`, `.gitignore`, `PROGRESS.md`, and all runtime modules.

## 3) Knowledge-base readiness analysis

### What is good already
- All six required files exist.
- Content is rich and retrieval-friendly (long-form, realistic, domain-specific).
- Coverage includes company, features, pricing, FAQ, onboarding, refund policy.

### Issues to resolve before ingestion
There are cross-document fact mismatches that will hurt retrieval consistency (example: Professional plan user limits and related billing details differ between files).  
Plan includes a **KB consistency normalization pass** before chunking/embedding.

## 4) Non-negotiable implementation constraints (must follow AGENTS.md)

1. Work phase-by-phase, no skipping, no combining.
2. One small step at a time inside each phase.
3. Stop for confirmation before moving to the next phase.
4. Check official docs for each library before coding that phase.
5. Keep `PROGRESS.md` updated after each phase.
6. Use logging, type hints, docstrings, centralized config, and no magic values.
7. Use explicit phase tests and do not mark complete until passing.

## 5) End-to-end build strategy (macro breakdown)

### Part A - Foundation and environment control
Phases: 1-3  
Goal: deterministic local environment + configuration + Supabase client singleton.

### Part B - Data plane setup
Phases: 4-7  
Goal: pgvector schema + embedding setup + document loader + ingestion pipeline.

### Part C - Retrieval and optimization layers
Phases: 8-10  
Goal: RAG tool + semantic cache + long-term memory modules.

### Part D - Agent brain
Phases: 11-13  
Goal: state schema, node logic, conditional graph routing, invoke function.

### Part E - Observability and interface
Phases: 14-15  
Goal: validate tracing + ship Gradio app with cache-first execution path.

### Part F - Hardening and portfolio packaging
Phases: 16-17  
Goal: full scenario testing, tuning, cost analysis, and recruiter-grade README.

## 6) Detailed phase plan with gates (build + debug checkpoints)

### Phase 1 - Project setup and environment
**Deliverables**
- Full folder scaffold from AGENTS.md.
- Virtual environment.
- Pinned `requirements.txt`.
- `.env.example`, `.gitignore`, `PROGRESS.md` (Phase 1 in progress/done states).

**Debug gate**
- Import smoke test for core libraries.

---

### Phase 2 - Config module (`src/config.py`)
**Deliverables**
- `.env` loading, required-variable validation, grouped constants.

**Debug gate**
- Import + print non-secret config values.

---

### Phase 3 - Supabase client (`src/database/supabase_client.py`)
**Deliverables**
- Single exported Supabase client object (singleton pattern).

**Debug gate**
- Lightweight authenticated query check.

---

### Phase 4 - Database schema and RPCs (Supabase SQL editor)
**Deliverables**
- `vector` extension.
- Tables: `documents`, `semantic_cache`, `long_term_memory`.
- HNSW indexes.
- Similarity RPC functions for documents and cache queries.

**Debug gate**
- Manual insert test per table.

---

### Phase 5 - Embeddings module (`src/embeddings/azure_embeddings.py`)
**Deliverables**
- Azure embedding object exported for global reuse.

**Debug gate**
- Embed test sentence; confirm vector length matches DB dimension.

---

### Phase 6 - Loader/chunker (`src/knowledge_base/document_loader.py`)
**Deliverables**
- Directory load + recursive chunking + metadata enrichment.

**Debug gate**
- Print loaded docs/chunk count/sample chunk + metadata.

---

### Phase 7 - Ingestion pipeline (`src/knowledge_base/ingest.py`, `scripts/run_ingest.py`)
**Deliverables**
- Batch ingestion into Supabase vector table.
- Idempotent ingestion strategy documented and implemented.

**Debug gate**
- Run ingestion script and verify populated rows in `documents`.

---

### Phase 8 - RAG retriever tool (`src/retriever/rag_retriever.py`)
**Deliverables**
- Properly named/described LangChain tool for KB retrieval.

**Debug gate**
- Direct tool call returns relevant refund-policy context.

---

### Phase 9 - Semantic cache (`src/cache/semantic_cache.py`)
**Deliverables**
- `check_cache` + `write_to_cache` with thresholded semantic match.
- `hit_count` increment and duplicate suppression.

**Debug gate**
- Paraphrase query triggers cache hit.

---

### Phase 10 - Long-term memory (`src/memory/long_term_memory.py`)
**Deliverables**
- `get_user_memory` + `save_to_memory` with user scoping and formatting.

**Debug gate**
- Multi-entry retrieval for test user.

---

### Phase 11 - Agent state (`src/agent/state.py`)
**Deliverables**
- Typed state schema supporting loop + tool messaging.

**Debug gate**
- Construct and inspect full sample state object.

---

### Phase 12 - Agent nodes (`src/agent/nodes.py`)
**Deliverables**
- Memory-read, reasoning, tool execution, memory-write, cache-write nodes.

**Debug gate**
- Unit-style function calls for each node with expected updates.

---

### Phase 13 - Graph construction (`src/agent/graph.py`)
**Deliverables**
- Conditional loop graph, compiled runnable, invoke wrapper.
- Loop guard/max-iteration configuration.

**Debug gate**
- `invoke_agent("What is the refund policy?", "test_user_001")` succeeds and routes correctly.

---

### Phase 14 - LangSmith verification
**Deliverables**
- Tracing variables validated.
- Traces inspected for node-level visibility.

**Debug gate**
- Three test prompts produce three traces; at least one includes RAG tool call.

---

### Phase 15 - Gradio interface (`src/interface/gradio_app.py`)
**Deliverables**
- Chat UI with cache-first callback and agent fallback.
- Friendly error handling.

**Debug gate**
- Five required scenario tests from AGENTS.md.

---

### Phase 16 - End-to-end refinement
**Deliverables**
- Structured test matrix execution.
- Bugs/fixes documented in `PROGRESS.md`.
- Cache hit-rate + latency + token observations recorded.

**Debug gate**
- All six E2E scenarios pass.

---

### Phase 17 - README and portfolio docs
**Deliverables**
- Recruiter/client-ready README including architecture, setup, SQL, tracing, design choices, and cost analysis.

**Debug gate**
- README complete against all mandatory sections from AGENTS.md.

## 7) Cross-cutting debugging and reliability plan

1. Add module-level logging in every `src/` component.
2. Use deterministic config constants (no hidden defaults for critical settings).
3. Add narrow exception handling at I/O boundaries (Azure/Supabase/Gradio).
4. Keep data contracts explicit:
   - embedding dimension
   - table names
   - RPC signatures
   - agent state keys
5. Validate each integration in isolation before wiring graph-level behavior.

## 8) Dependency map (high-level)

- Phase 1 -> required by all.
- Phase 2 -> required by 3, 5, 8, 9, 10, 12, 13, 15.
- Phase 3 + 4 + 5 -> required by 7, 8, 9, 10.
- Phase 6 -> required by 7.
- Phases 8, 9, 10 -> required by 12/13/15.
- Phases 11 + 12 -> required by 13.
- Phase 13 -> required by 14/15/16.
- Phase 16 -> informs 17.

## 9) Immediate next action

Start with **Phase 1** exactly as defined in AGENTS.md, and initialize `PROGRESS.md` as the single source of truth.

