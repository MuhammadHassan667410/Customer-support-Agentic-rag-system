# AGENTS.md — Agentic RAG Customer Support Chatbot
## Master Instruction File for Vibe Coding Agent

---

> **READ THIS ENTIRE FILE BEFORE WRITING A SINGLE LINE OF CODE.**
> This is not optional. Every decision made in this project — every library, every design pattern, every database table, every function — is explained here with full reasoning. You are expected to follow this file exactly, phase by phase, step by step. Do not skip ahead. Do not combine phases. Do not assume. Ask when uncertain.

---

## SECTION 0 — WHO THIS IS FOR AND HOW TO READ THIS FILE

This project is being built by Hassan, an AI Engineer and freelance developer. Hassan uses vibe coding — meaning he guides an AI coding agent to build the system while learning every detail of what is being built. This file is written assuming Hassan has solid conceptual understanding of AI systems but wants every single line of code explained clearly, as if reading a textbook, not just a tutorial.

**You, the coding agent, have the following non-negotiable responsibilities:**

1. You will NEVER write a large block of code all at once. Every phase is broken into small steps. Write one step at a time, stop, explain it, and wait for confirmation before moving to the next.

2. You will ALWAYS check the official documentation of every library before writing any code for it. The documentation URLs are listed per phase. Do not rely on your training data alone — library APIs change, methods get deprecated, new patterns emerge. Fetch the docs. Use the current API.

3. You will explain EVERY line of code you write. Not just what it does — why it exists, what problem it solves, what would happen if it was removed, and what alternative approaches exist for doing the same thing. Write these explanations as comments above each line or block, like a teacher annotating code for a student.

4. You will NEVER move to the next phase until the current phase is tested, confirmed working, and Hassan has explicitly said "move on."

5. You will maintain a `PROGRESS.md` file in the root of the project that tracks which phases are complete, which are in progress, and which are pending. Update it after every phase.

6. When a phase is complete, you will write a short summary of what was built, what decisions were made and why, and what the next phase will do.

---

## SECTION 1 — PROJECT OVERVIEW

### What Are We Building?

We are building a production-grade **Agentic RAG Customer Support Chatbot**. This is not a simple question-answering bot. It is a full autonomous agent system that:

- Maintains its own reasoning loop using LangGraph
- Decides on its own when to search a knowledge base vs. when to answer from its general intelligence
- Retrieves relevant company documents using semantic search (RAG — Retrieval Augmented Generation)
- Remembers previous conversations with users across sessions using long-term memory stored in Supabase
- Caches semantically similar questions so that repeated queries do not burn tokens or make API calls
- Is fully observable — every thought, every tool call, every retrieval step is tracked in LangSmith
- Uses a real enterprise LLM deployed on Microsoft Azure AI Foundry
- Exposes a Gradio chat interface for testing and demonstration

### Why Is This Architecture Production-Grade?

Most beginner RAG projects look like this: take a user question → embed it → search a vector database → stuff the retrieved text into a prompt → ask the LLM. That is a pipeline, not an agent. It has no memory. It has no cost optimization. It has no ability to decide whether retrieval is even needed.

Our system is different because:

- **The agent decides** — using LangGraph's conditional graph routing, the LLM decides at runtime whether to call the RAG tool, answer directly, or check memory first. This is agentic behavior.
- **Memory is persistent** — user conversation history is stored in Supabase and retrieved per-user at the start of each session. The agent knows what it talked about before.
- **Cache is semantic** — we do not do exact string matching for cache hits. We embed the new question and compare it to cached question embeddings. If they are similar enough, we return the cached answer without calling the LLM at all.
- **Observability is built-in** — LangSmith traces every agent step automatically. You can see exactly what the agent was thinking, which tools it called, how long each step took, and what it retrieved.

### Who Will Use This?

In the portfolio context, this represents an AI system built for a fictional company called **"NovaTech Solutions"** — a B2B SaaS company that sells project management and team collaboration software. The knowledge base will contain realistic documents: an FAQ document, a company overview, a pricing document, a refund policy, an onboarding guide, and a product feature list. These documents are fictional but professionally written.

---

## SECTION 2 — COMPLETE TECH STACK

Every technology choice is explained with reasoning. Do not substitute any of these without explicit discussion.

### Language
**Python 3.11+**
Python is the dominant language for AI/ML systems. All the libraries we use — LangChain, LangGraph, Supabase client, Gradio — are Python-native. We use 3.11 specifically because it has better performance than 3.10 and better compatibility than 3.12 with current AI libraries.

### LLM Provider
**Microsoft Azure AI Foundry**
Hassan has models deployed on Azure AI Foundry. We will use one of his deployed models through the Azure OpenAI-compatible API. Azure AI Foundry provides enterprise-grade LLM hosting with SLAs, rate limits, and cost controls. The API is compatible with the OpenAI Python SDK and LangChain's `AzureChatOpenAI` integration, so integration is straightforward. The specific model to be used will be configured via environment variable — we will not hardcode model names. This allows switching models without touching code.

### Orchestration Framework
**LangGraph (part of the LangChain ecosystem)**
LangGraph is a library for building stateful, multi-step agent workflows as directed graphs. Unlike a simple LangChain chain (which is linear: step 1 → step 2 → step 3), LangGraph lets us define nodes (steps) and edges (transitions) that can loop, branch, and make conditional decisions. This is the heart of our agent.

Official Documentation: https://langchain-ai.github.io/langgraph/

### RAG Framework
**LangChain**
LangChain provides the document loading, text splitting, embedding, and retriever components we need for the RAG system. It integrates natively with LangGraph and Supabase.

Official Documentation: https://python.langchain.com/docs/introduction/

### Vector Database and General Storage
**Supabase**
Supabase is an open-source Firebase alternative built on top of PostgreSQL. We use it for three purposes:
1. **pgvector** — Supabase has a built-in PostgreSQL extension called `pgvector` that turns it into a vector database. We store document embeddings here and perform semantic similarity search.
2. **Long-term memory storage** — A regular Supabase table stores conversation summaries per user, keyed by user ID.
3. **Semantic cache storage** — A separate table stores cached question-answer pairs as embeddings for fast lookup.

Official Documentation: https://supabase.com/docs and https://python.langchain.com/docs/integrations/vectorstores/supabase/

### Observability
**LangSmith**
LangSmith is LangChain's observability platform for LLM applications. When enabled, it automatically intercepts every LangChain and LangGraph call and logs it — the input, the output, the token count, the latency, the tool calls, and the reasoning steps. We access this data through a web dashboard at smith.langchain.com. Setup requires only environment variables — no code changes. LangSmith wraps everything automatically once configured.

Official Documentation: https://docs.smith.langchain.com/

### Semantic Cache
**Custom implementation using Supabase pgvector**
LangChain provides caching utilities, but we will build a custom semantic cache backed by our Supabase pgvector table. This means: when a question comes in, we embed it, compare it to previously cached question embeddings using pgvector similarity search, and if similarity is above a configurable threshold, we return the stored answer without any LLM call. This approach gives us full control and keeps everything in one database.

### Testing Interface
**Gradio**
Gradio is a Python library for building web-based ML demos quickly. We use it because it requires zero frontend code, provides a `ChatInterface` component that looks and works like a real chat application, and can be shared via a temporary public URL using `share=True`. Gradio is our testing and demo interface, not the production interface.

Official Documentation: https://www.gradio.app/docs/

### Embeddings
**Azure OpenAI Embeddings via LangChain**
We use the same Azure AI Foundry deployment for embeddings as we do for chat completion. Azure provides text embedding models (e.g., `text-embedding-ada-002` or `text-embedding-3-small`) which we use for embedding documents, user queries, memory entries, and cache lookups.

### Environment Management
**python-dotenv**
All secrets (API keys, database URLs, model deployment names) are stored in a `.env` file and loaded at runtime. Nothing is ever hardcoded. The `.env` file is always listed in `.gitignore`.

### Dependency Management
**pip with a pinned requirements.txt file**
Simple and universally understood. We list every dependency with a pinned version to ensure reproducibility across different machines.

---

## SECTION 3 — SYSTEM ARCHITECTURE (DETAILED DATA FLOW)

Read this section carefully before writing any code. Understanding the full data flow will help you understand why each piece of code exists.

### How a User Message Flows Through the System

**Step 1: User sends a message via Gradio**
The user types a message in the Gradio chat interface. The Gradio callback function captures the message and the full conversation history of the current session.

**Step 2: Semantic Cache Check**
Before anything else, we embed the user's message and compare it to all cached question embeddings in the `semantic_cache` table in Supabase. If a match is found with similarity above our threshold (e.g., 0.95), we immediately return the cached answer. No LLM is called. No tokens are burned. This is the most cost-saving step in the entire system.

**Step 3: LangGraph Agent Entry**
If there is no cache hit, the user's message enters the LangGraph agent. The agent state is initialized with the user's message, their user ID, their conversation history loaded from long-term memory, and an empty message list for this reasoning cycle.

**Step 4: Memory Retrieval Node**
The first node in the graph retrieves the user's past conversation summaries from Supabase using their user ID. This summary is added to the agent's system context so the LLM knows what was discussed in previous sessions.

**Step 5: LLM Reasoning Node with Tool Access**
The LLM receives the user's message, the conversation history, and access to one tool: the RAG Retrieval Tool. The LLM decides on its own: if the question is general (e.g., "What time is it?"), it answers directly. If the question is about the company, products, policies, or anything in the knowledge base, it calls the RAG Retrieval Tool.

**Step 6: RAG Tool Execution (if called)**
The RAG Retrieval Tool receives the user's question as input, embeds it, searches the `documents` table in Supabase using pgvector similarity search, retrieves the top-K most relevant document chunks, and returns them as formatted text. The LLM then reads these chunks and formulates its answer.

**Step 7: Final Answer Generation**
The LLM generates the final answer using either its general knowledge or the retrieved document chunks. The graph routes to the output node.

**Step 8: Memory Write Node**
After generating the answer, the agent writes a summary of the conversation turn (user message and agent answer) to the `long_term_memory` table in Supabase, keyed by user ID.

**Step 9: Cache Write**
The original question and the final answer are written to the semantic cache so that future similar questions can be answered without LLM calls.

**Step 10: Return to Gradio**
The final answer is returned to the Gradio interface and displayed to the user.

---

## SECTION 4 — SUPABASE DATABASE SCHEMA

We need exactly three tables in Supabase. Understand each one thoroughly before the database setup phase.

### Table 1: `documents`
This stores the chunked knowledge base documents as vector embeddings.

- `id` — UUID, primary key, auto-generated by Supabase
- `content` — TEXT, the raw text of the document chunk
- `metadata` — JSONB, stores information like source filename, chunk index, document title
- `embedding` — vector(1536), the embedding of the content (dimension must match the Azure embedding model used)

This table uses pgvector's HNSW or IVFFlat index for fast approximate nearest-neighbor similarity search.

### Table 2: `long_term_memory`
This stores per-user conversation memory.

- `id` — UUID, primary key, auto-generated
- `user_id` — TEXT, identifies the user (can be a username, email, or session ID)
- `summary` — TEXT, a short summary of one conversation turn
- `created_at` — TIMESTAMP WITH TIME ZONE, auto-generated, used to retrieve the most recent N memories
- `session_id` — TEXT, optional, identifies which session the memory came from

### Table 3: `semantic_cache`
This stores cached question-answer pairs with embeddings for fast semantic lookup.

- `id` — UUID, primary key, auto-generated
- `question` — TEXT, the original question that was cached
- `answer` — TEXT, the answer that was cached
- `question_embedding` — vector(1536), the embedding of the question used for similarity lookup
- `created_at` — TIMESTAMP WITH TIME ZONE, auto-generated
- `hit_count` — INTEGER, tracks how many times this cache entry has been returned (useful for analytics)

---

## SECTION 5 — KNOWLEDGE BASE DOCUMENTS

Before building any code, we need realistic company documents. The fictional company is **NovaTech Solutions**, a B2B SaaS company that sells project management and team collaboration software. The coding agent must create the following documents as plain `.txt` files inside a `knowledge_base/` folder in the project root. Each document should be realistic, detailed, and at least 400-600 words long so that chunking and retrieval are non-trivial challenges.

**Documents to create:**

1. **`company_overview.txt`** — Company history, mission, what the product does, founding story, team size, office locations, and core values.

2. **`product_features.txt`** — Detailed breakdown of every feature: task management, team chat, file sharing, time tracking, reporting dashboards, integrations (Slack, GitHub, Jira), API access, and mobile app.

3. **`pricing_plans.txt`** — Starter plan (free, up to 5 users), Professional plan ($29/month, up to 50 users), Enterprise plan (custom pricing), detailed feature comparison per plan, annual vs. monthly billing discounts.

4. **`faq.txt`** — At least 20 frequently asked questions with detailed answers covering account setup, password reset, billing, cancellation, data export, team permissions, GDPR compliance, API rate limits, and support response times.

5. **`refund_policy.txt`** — Full refund policy: 30-day money-back guarantee, how to request a refund, what is refundable vs. non-refundable, timeline for processing, exceptions.

6. **`onboarding_guide.txt`** — Step-by-step guide for new customers: creating an account, inviting team members, setting up first project, connecting integrations, and accessing support.

---

## SECTION 6 — PROJECT FOLDER STRUCTURE

The coding agent must set up this exact folder structure at the beginning of Phase 1. Every folder and file serves a specific purpose.

```
novatech-support-agent/
│
├── .env                          # All secrets and config — NEVER commit this
├── .env.example                  # Empty template safe to commit to GitHub
├── .gitignore                    # Must include .env, __pycache__, .venv
├── requirements.txt              # All Python dependencies with pinned versions
├── AGENTS.md                     # This file
├── PROGRESS.md                   # Phase tracking file — agent maintains this
│
├── knowledge_base/               # Raw company documents (plain text)
│   ├── company_overview.txt
│   ├── product_features.txt
│   ├── pricing_plans.txt
│   ├── faq.txt
│   ├── refund_policy.txt
│   └── onboarding_guide.txt
│
├── src/                          # All application source code lives here
│   ├── __init__.py
│   │
│   ├── config.py                 # Loads .env, defines all configuration constants
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── supabase_client.py    # Supabase connection singleton
│   │
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── azure_embeddings.py   # Azure embedding model setup and export
│   │
│   ├── knowledge_base/
│   │   ├── __init__.py
│   │   ├── document_loader.py    # Loads and chunks all .txt documents
│   │   └── ingest.py             # Embeds and uploads chunks to Supabase
│   │
│   ├── retriever/
│   │   ├── __init__.py
│   │   └── rag_retriever.py      # LangChain Tool wrapping the vector search
│   │
│   ├── cache/
│   │   ├── __init__.py
│   │   └── semantic_cache.py     # Semantic cache read and write functions
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   └── long_term_memory.py   # Per-user memory read and write functions
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py              # LangGraph AgentState TypedDict definition
│   │   ├── nodes.py              # All graph node functions
│   │   ├── tools.py              # LangChain Tool definitions
│   │   └── graph.py              # LangGraph graph construction and compilation
│   │
│   └── interface/
│       ├── __init__.py
│       └── gradio_app.py         # Gradio chat interface for testing and demo
│
└── scripts/
    └── run_ingest.py             # One-time script to ingest knowledge base docs
```

---

## SECTION 7 — ENVIRONMENT VARIABLES

The `.env` file must contain the following variables. The coding agent must create a `.env.example` file (with empty values) that is safe to commit to GitHub, and a real `.env` file that is listed in `.gitignore`.

```
# Azure AI Foundry Configuration
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_VERSION=
AZURE_CHAT_DEPLOYMENT_NAME=
AZURE_EMBEDDING_DEPLOYMENT_NAME=

# Supabase Configuration
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# LangSmith Observability (credentials from smith.langchain.com)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=novatech-support-agent

# Application Tuning Configuration
SIMILARITY_THRESHOLD=0.95
TOP_K_RETRIEVAL=5
MAX_MEMORY_ENTRIES=10
CACHE_TABLE_NAME=semantic_cache
DOCUMENTS_TABLE_NAME=documents
MEMORY_TABLE_NAME=long_term_memory
```

---

## SECTION 8 — PHASE-BY-PHASE BUILD PLAN

This is the complete breakdown of every phase. Each phase is a self-contained milestone. Completing a phase means: code is written, explained line-by-line, tested with a simple test script, and confirmed working by Hassan before anything else continues.

---

### PHASE 1 — Project Setup and Environment

**Goal:** Create the project folder structure, initialize Git, set up the Python virtual environment, create the requirements.txt, create the .env files, and verify that all dependencies install correctly with no errors.

**Steps in order:**
1. Create the full folder structure exactly as defined in Section 6
2. Initialize a Git repository with `git init`
3. Create `.gitignore` with standard Python entries plus `.env` and `.venv`
4. Create the Python virtual environment using `python -m venv .venv`
5. Create `requirements.txt` with all libraries (agent must check PyPI for latest stable versions at build time)
6. Install all requirements and confirm zero errors
7. Create `.env.example` with all variable names but empty values
8. Create `PROGRESS.md` and mark Phase 1 as In Progress

**Libraries to include in requirements.txt (agent fetches latest stable versions from PyPI at build time):**
- `langchain`
- `langgraph`
- `langchain-openai` (for AzureChatOpenAI and AzureOpenAIEmbeddings)
- `langchain-community`
- `langchain-core`
- `supabase` (official Supabase Python client)
- `gradio`
- `python-dotenv`
- `tiktoken` (for token counting utilities)
- `langsmith`
- `openai` (Azure uses OpenAI-compatible API under the hood)
- `numpy`
- `pydantic`

**Documentation to consult before writing anything:**
- LangChain installation: https://python.langchain.com/docs/installation/
- LangGraph: https://langchain-ai.github.io/langgraph/
- Supabase Python: https://supabase.com/docs/reference/python/introduction
- Gradio: https://www.gradio.app/docs/

**Test for this phase:** Run `python -c "import langchain; import langgraph; import gradio; import supabase; print('All imports successful')"` and confirm no errors appear.

---

### PHASE 2 — Configuration Module

**Goal:** Build `src/config.py` — the single source of truth for all configuration. Every other module imports from this file. No module should read `.env` directly except this one.

**What this module does:**
- Uses `python-dotenv` to load the `.env` file at startup
- Reads each environment variable and assigns it to a Python constant with a clear name
- Validates required variables — if a required variable is missing, the app raises a clear, descriptive error on startup rather than silently failing later when a function is called
- Groups configuration into logical sections with comments: Azure config, Supabase config, LangSmith config, App config

**Concepts the agent must explain thoroughly when building this module:**
- What is `os.getenv()` and how is it different from `os.environ[]`? What happens when a key is missing with each approach?
- What does `load_dotenv()` do at the OS level? When does it need to be called relative to other imports?
- Why do we centralize configuration in one file instead of reading `.env` in every module that needs it?
- What is a Pydantic `BaseSettings` class and how is it a more advanced alternative to plain constants? Why are we using plain constants here for simplicity?

**Test for this phase:** Import the config module in a test script and print all non-secret values to confirm they load from the `.env` file correctly.

---

### PHASE 3 — Supabase Client Setup

**Goal:** Build `src/database/supabase_client.py` — a module that creates and exports a single Supabase client instance that all other modules import and use.

**What this module does:**
- Imports `create_client` from the official Supabase Python library
- Uses the Supabase URL and service key from the config module (not hardcoded)
- Creates one client instance and exports it as a module-level variable (singleton pattern)
- All other modules that need Supabase access import this single instance

**Concepts the agent must explain thoroughly:**
- What is a client object in the context of a database SDK? What does it represent?
- Why do we use the service key (not the anon key) for a backend server application?
- What is the singleton pattern? Why does creating multiple Supabase client instances cause problems?
- Does the Supabase Python client handle connection pooling automatically?

**Documentation to consult:**
- https://supabase.com/docs/reference/python/initializing

**Test for this phase:** Use the client to perform a simple health check — for example, attempt to select zero rows from any table and confirm no authentication errors are raised.

---

### PHASE 4 — Supabase Database Schema Setup

**Goal:** Create all three tables in Supabase with the correct schema using SQL statements run in the Supabase SQL editor. Enable the pgvector extension. Create the similarity search function.

**What this phase produces:**
- The SQL to enable the `vector` extension (pgvector) in Supabase
- The SQL to create each of the three tables defined in Section 4
- The SQL to create HNSW indexes on the embedding columns for fast similarity search
- A PostgreSQL RPC function that LangChain calls to perform vector similarity search — this is a stored procedure that accepts a query embedding and returns the most similar rows

**Concepts the agent must explain thoroughly:**
- What is pgvector and how does it add vector data types and operators to standard PostgreSQL?
- What is a vector and what does the dimension number (e.g., 1536) represent in practice?
- What is the difference between an HNSW index and an IVFFlat index? Which is recommended for our use case and why?
- What is cosine similarity? Why is it the right distance metric for comparing text embeddings rather than Euclidean distance?
- What is a Supabase RPC function? Why does LangChain's Supabase integration require one to be defined manually rather than doing the search directly?
- What is the `match_threshold` parameter in the RPC function and how does it filter irrelevant results?

**Documentation to consult:**
- https://supabase.com/docs/guides/database/extensions/pgvector
- https://python.langchain.com/docs/integrations/vectorstores/supabase/

**Test for this phase:** Manually insert one fake row into each table from the Supabase Table Editor UI and confirm the table structure accepts the data types correctly.

---

### PHASE 5 — Azure Embeddings Setup

**Goal:** Build `src/embeddings/azure_embeddings.py` — a module that creates a LangChain-compatible embedding object using Azure OpenAI and exports it for use throughout the project.

**What this module does:**
- Uses `AzureOpenAIEmbeddings` from `langchain_openai`
- Configures it with the Azure endpoint, API key, embedding deployment name, and API version from the config module
- Creates and exports a single `embeddings` instance that all other modules import

**Concepts the agent must explain thoroughly:**
- What is an embedding model and what does it output? What is the mathematical structure of an embedding?
- Why is the embedding model separate from the chat completion model? Can the same model be used for both?
- What does the embedding dimension (e.g., 1536 for ada-002, 3072 for text-embedding-3-large) represent and why must it match the `vector()` column size in Supabase exactly?
- What is `AzureOpenAIEmbeddings` and how does it differ from the standard `OpenAIEmbeddings`? What extra parameters does Azure require?

**Documentation to consult:**
- https://python.langchain.com/docs/integrations/text_embedding/azureopenai/

**Test for this phase:** Call the embeddings model on a single test sentence (e.g., "Hello world") and print the first 5 values of the resulting vector and its total length to confirm it produces a list of floats with the expected dimension.

---

### PHASE 6 — Knowledge Base Document Loading and Chunking

**Goal:** Build `src/knowledge_base/document_loader.py` — a module that loads all `.txt` files from the `knowledge_base/` folder and splits them into chunks that are appropriately sized for embedding and retrieval.

**What this module does:**
- Uses LangChain's `DirectoryLoader` with `TextLoader` to load all `.txt` files from the `knowledge_base/` directory
- Uses `RecursiveCharacterTextSplitter` to split each document into overlapping chunks
- Enriches the metadata of each chunk with the source filename, a document title derived from the filename, and the chunk index
- Returns a list of LangChain `Document` objects ready for embedding

**Concepts the agent must explain thoroughly:**
- What is chunking and why can we not embed a whole 600-word document as a single unit?
- What is chunk size (measured in characters or tokens) and how do we choose the right value for customer support documents?
- What is chunk overlap and why is it important to include it? What problem does it solve?
- What is `RecursiveCharacterTextSplitter`? Why is it preferred over a simple fixed-character splitter? What hierarchy of separators does it try in order?
- What is a LangChain `Document` object? What are its two main fields?
- What is metadata in this context and why do we store it alongside each chunk?

**Documentation to consult:**
- https://python.langchain.com/docs/how_to/recursive_text_splitter/
- https://python.langchain.com/docs/how_to/document_loader_directory/

**Test for this phase:** Run the loader and print the total number of documents loaded, the total number of chunks produced, the content of the first chunk, and the metadata dictionary of the first chunk.

---

### PHASE 7 — Knowledge Base Ingestion into Supabase

**Goal:** Build `src/knowledge_base/ingest.py` and `scripts/run_ingest.py` — the one-time ingestion pipeline that embeds all document chunks and uploads them to the Supabase `documents` table.

**What this module does:**
- Takes the list of `Document` chunks from the document loader
- Uses LangChain's `SupabaseVectorStore` with the Azure embeddings instance to embed and upload all chunks in one operation
- Handles batching to avoid hitting Azure API rate limits for the embedding model
- Prints progress to the console so the user knows the ingestion is running (e.g., "Uploading batch 3 of 12...")

**Concepts the agent must explain thoroughly:**
- What does `SupabaseVectorStore.from_documents()` do? What is the sequence of operations it performs internally?
- What is batching and why is it necessary when embedding hundreds of document chunks?
- What are API rate limits and what happens if we exceed them? How does batching help avoid this?
- What is idempotency? If we run the ingestion script twice, will we get duplicate rows? Should we clear the table before re-ingesting, and how?
- What is the difference between `from_documents()` (which creates a new store) and `add_documents()` (which adds to an existing one)?

**Documentation to consult:**
- https://python.langchain.com/docs/integrations/vectorstores/supabase/

**Test for this phase:** Run `python scripts/run_ingest.py` and then open the Supabase Table Editor to check the `documents` table. Confirm rows were inserted with non-null content, metadata, and embedding columns.

---

### PHASE 8 — RAG Retriever Tool

**Goal:** Build `src/retriever/rag_retriever.py` — a LangChain `Tool` that the LangGraph agent can call to search the knowledge base when it needs company-specific information.

**What this module does:**
- Creates a `SupabaseVectorStore` instance connected to the `documents` table as a retriever
- Configures the retriever for top-K search with the K value from config
- Wraps the retriever in a LangChain `Tool` object with a carefully written name and description
- The tool function takes a plain text query, runs similarity search, retrieves the top-K chunks, formats them into a readable string, and returns that string to the LLM
- The description field is critical — it must explain clearly and specifically to the LLM what this tool does and when to use it

**Concepts the agent must explain thoroughly:**
- What is a LangChain `Tool` and what is the contract it defines (name, description, function)?
- Why is the `description` field of a Tool so important for agent behavior? What happens if it is vague or poorly written?
- What does "top-K" mean in the retrieval context? What are the tradeoffs of a larger vs. smaller K?
- Should we apply a similarity score threshold to filter out low-quality retrieval results? What are the tradeoffs?
- How do we format the retrieved `Document` objects into a clean string that the LLM can read and use?

**Documentation to consult:**
- https://python.langchain.com/docs/concepts/tools/
- https://python.langchain.com/docs/integrations/vectorstores/supabase/

**Test for this phase:** Call the tool function directly (not through the agent) with a test question such as "What is the refund policy?" and print the returned string. Confirm it contains relevant chunks from the `refund_policy.txt` document.

---

### PHASE 9 — Semantic Cache System

**Goal:** Build `src/cache/semantic_cache.py` — the complete semantic cache with a read function and a write function, both backed by the `semantic_cache` table in Supabase.

**What the read function (`check_cache`) does:**
- Takes the user's query string as input
- Embeds the query using the Azure embedding model
- Calls the Supabase similarity search RPC function on the `semantic_cache` table
- If a result is found with similarity above the threshold defined in config, it returns the cached answer string
- It also increments the `hit_count` of the matched cache entry so we can track how often each entry is used
- If no sufficiently similar result is found, it returns `None` to signal a cache miss

**What the write function (`write_to_cache`) does:**
- Takes the original question string and the generated answer string as inputs
- Embeds the question using the Azure embedding model
- Inserts a new row into the `semantic_cache` table containing the question text, answer text, and question embedding
- Should perform a quick near-duplicate check before writing to avoid polluting the cache with near-identical entries

**Concepts the agent must explain thoroughly:**
- What is semantic caching and how is it fundamentally different from exact-match string caching (like Redis)?
- Why do we embed the question and not the answer when building the cache lookup?
- What is a good starting value for the similarity threshold (e.g., 0.95)? What are the practical consequences of setting it too high vs. too low?
- Should the cache have a time-to-live (TTL)? What happens if we cache an answer that becomes outdated?
- What is the `hit_count` column useful for in terms of analytics and cache management?

**Test for this phase:** Write one question-answer pair to the cache manually. Then call the read function with a slightly different but semantically equivalent question (e.g., "What is the return policy?" after caching "How do refunds work?") and confirm a cache hit is returned with high similarity.

---

### PHASE 10 — Long-Term Memory System

**Goal:** Build `src/memory/long_term_memory.py` — the per-user memory system with a read function and a write function, both backed by the `long_term_memory` table in Supabase.

**What the read function (`get_user_memory`) does:**
- Takes a `user_id` string as input
- Queries the `long_term_memory` table in Supabase for the most recent N entries for that user (N comes from config, e.g., 10)
- Orders results by `created_at` descending to get the most recent first
- Formats the retrieved entries as a readable string that can be injected into the LLM system prompt (e.g., "Previous conversations: User asked about refund policy. Agent explained the 30-day window...")
- Returns this string, or an empty string if no memory exists yet

**What the write function (`save_to_memory`) does:**
- Takes `user_id`, the user's message, and the agent's response as inputs
- Creates a concise summary of this conversation turn (can use a template rather than calling the LLM, e.g., "User asked: [question]. Agent responded: [brief summary of answer].")
- Inserts a new row into the `long_term_memory` table with the user_id, summary, and a generated session_id

**Concepts the agent must explain thoroughly:**
- What is the conceptual difference between in-context memory (the current chat history in the Gradio window) and long-term memory (the persistent summaries in Supabase that survive across sessions)?
- Why do we store summaries of conversations rather than storing the full verbatim message history?
- What is the tradeoff between storing more memory entries vs. the cost of injecting them into the context window?
- Why do we key memory by `user_id` rather than by session ID alone?
- Should we consider summarizing old memories with the LLM when a user accumulates many entries?

**Test for this phase:** Write three fake memory entries for a test user ID. Then call the read function with that user ID and confirm all three entries are returned in a readable, formatted string.

---

### PHASE 11 — LangGraph Agent State Definition

**Goal:** Build `src/agent/state.py` — the TypedDict that defines the complete shape of the state object that flows through every node in the LangGraph graph.

**What this module defines:**
- An `AgentState` TypedDict (or dataclass) with all fields the agent needs throughout its lifecycle
- Required fields include: the user's current message, the user's ID, the list of messages in the current reasoning cycle, the memory context string loaded from Supabase, any retrieved document text from the RAG tool, the final answer string, and a flag indicating whether a tool was called

**Concepts the agent must explain thoroughly:**
- What is a TypedDict in Python and why is it preferred over a plain dict for LangGraph state?
- What does "state" mean in the graph context — why does every node receive the state and return an updated version of it?
- What is the `Annotated[list, operator.add]` pattern that LangGraph requires for list fields that should be appended to rather than overwritten?
- What is the conceptual difference between state fields that accumulate over graph execution (like the messages list) and fields that get replaced (like the final answer string)?

**Documentation to consult:**
- https://langchain-ai.github.io/langgraph/concepts/low_level/

**Test for this phase:** Create an `AgentState` dictionary with test values for all fields and print it to confirm the structure is correct and all fields are accessible.

---

### PHASE 12 — LangGraph Agent Nodes

**Goal:** Build `src/agent/nodes.py` — every node function in the LangGraph graph. Each node is a Python function that receives the current `AgentState` and returns a dictionary of state fields to update.

**This is the most critical module in the entire project.** Take extreme care here.

**Node 1: `retrieve_memory_node`**
- Input: current AgentState
- Action: calls `get_user_memory(state["user_id"])` from the memory module
- Output: returns `{"memory_context": memory_string}` to update the state

**Node 2: `agent_reasoning_node`**
- Input: current AgentState
- Action: creates the `AzureChatOpenAI` LLM instance bound with the RAG tool using `bind_tools()`. Builds the full prompt with system message (including memory context), conversation history, and the current user message. Calls the LLM. Returns the LLM response object as part of the messages list.
- This node does not decide routing — that is handled by conditional edges defined in graph.py

**Node 3: `rag_tool_node`**
- Input: current AgentState
- Action: inspects the last message in the state (which should be an AIMessage with a tool_call). Extracts the tool input (the search query). Calls the RAG retriever tool function with that query. Returns the result as a ToolMessage added to the messages list.

**Node 4: `write_memory_node`**
- Input: current AgentState
- Action: calls `save_to_memory()` with the user ID, original user message, and the final answer extracted from the last AIMessage
- Output: returns an empty dict (no state change needed, the write is a side effect)

**Node 5: `write_cache_node`**
- Input: current AgentState
- Action: calls `write_to_cache()` with the original user message and the final answer
- Output: returns an empty dict

**Concepts the agent must explain thoroughly:**
- What is a node function in LangGraph? What must it always accept and what must it always return?
- What does returning a partial state dictionary mean? Does a node need to return the entire state?
- What is `AzureChatOpenAI` and what parameters does it require for initialization?
- What does `bind_tools()` do? How does it make the LLM aware that tools exist and when to call them?
- What is a `tool_call` in an AIMessage response? How do we detect whether the LLM wants to use a tool?
- What is a `ToolMessage` and why does LangGraph require us to add it to the messages list rather than just passing the result directly?
- What is the difference between `HumanMessage`, `AIMessage`, `SystemMessage`, and `ToolMessage` in LangChain?

**Documentation to consult:**
- https://langchain-ai.github.io/langgraph/tutorials/introduction/
- https://python.langchain.com/docs/integrations/chat/azure_chat_openai/

**Test for this phase:** Test each node function individually by calling it with a manually constructed `AgentState` dictionary and printing the returned update dictionary. Confirm each node produces the expected output.

---

### PHASE 13 — LangGraph Graph Construction

**Goal:** Build `src/agent/graph.py` — assemble all node functions into a compiled LangGraph `StateGraph` with properly defined edges and conditional routing logic.

**What this module does:**
- Creates a `StateGraph` using the `AgentState` type as its state schema
- Adds all five nodes with descriptive names
- Defines all edges using `add_edge` and `add_conditional_edges`
- Implements the routing function that inspects the state after `agent_reasoning_node` and decides whether to go to `rag_tool_node` (if a tool call was made) or to `write_memory_node` (if a final answer is ready)
- Compiles the graph into a runnable object
- Exports an `invoke_agent(user_message, user_id)` convenience function that initializes state, invokes the graph, and returns the final answer string

**The edge structure:**
- `START` → `retrieve_memory_node`
- `retrieve_memory_node` → `agent_reasoning_node`
- `agent_reasoning_node` → conditional routing function
- Conditional function → `rag_tool_node` if last message contains tool_calls
- Conditional function → `write_memory_node` if last message is a final answer
- `rag_tool_node` → `agent_reasoning_node` (loop back so LLM can use the retrieved context)
- `write_memory_node` → `write_cache_node`
- `write_cache_node` → `END`

**Concepts the agent must explain thoroughly:**
- What is a `StateGraph` and how is it fundamentally different from a linear LangChain LCEL chain?
- What is `START` and `END` in LangGraph — what do they represent in the graph lifecycle?
- What does `add_conditional_edges` do? What does the routing function it receives need to return?
- What does it mean to "compile" a graph? What does the compiler check and what object does it return?
- What is the risk of infinite loops in a graph that has a cycle (agent_reasoning → rag_tool → agent_reasoning)? How do we set a maximum iteration limit to prevent infinite looping?
- What is graph visualization and how can we render a PNG of the compiled graph for the README?

**Documentation to consult:**
- https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph

**Test for this phase:** Call `invoke_agent("What is the refund policy?", "test_user_001")` and confirm a correct, relevant answer is returned. Then open LangSmith at smith.langchain.com and confirm the trace appears with all nodes visible as separate steps.

---

### PHASE 14 — LangSmith Observability Verification

**Goal:** Confirm that LangSmith tracing is fully working and that all agent steps are visible and interpretable in the LangSmith dashboard.

**What this phase does:**
- Verify that all four required LangSmith environment variables are set correctly
- Run a test agent invocation and navigate to smith.langchain.com to inspect the resulting trace
- Walk through the trace and confirm visibility of: the initial user message, the memory retrieval step, the LLM reasoning call with its input prompt and token counts, any tool call with its input and output, and the final answer with total latency

**Concepts the agent must explain thoroughly:**
- How does LangSmith automatically instrument LangChain and LangGraph without requiring code changes?
- What is a "trace" in LangSmith? What is the relationship between a trace and the individual steps (runs) within it?
- What does the `LANGCHAIN_PROJECT` variable do and how does it help organize traces when working on multiple projects?
- How can we add custom tags and metadata to specific traces for better filtering in the dashboard?
- What insights can we extract from LangSmith that help us optimize the agent — latency per step, token usage, retrieval quality?

**Documentation to consult:**
- https://docs.smith.langchain.com/observability/how_to_guides/tracing/trace_with_langchain

**Test for this phase:** Run three different queries and confirm all three appear as separate, labeled traces in the LangSmith dashboard. Confirm you can see the RAG tool call and its result in at least one trace.

---

### PHASE 15 — Gradio Chat Interface

**Goal:** Build `src/interface/gradio_app.py` — the Gradio-powered chat interface that serves as both the testing environment and the portfolio demonstration layer.

**What this module does:**
- Creates a `gr.ChatInterface` with a descriptive title, description, and example questions
- The callback function receives the user message and the current conversation history from Gradio
- Extracts a demo user ID (can be session-based or a fixed demo ID for portfolio purposes)
- Calls the semantic cache check first — if a cache hit is found, returns the cached answer immediately
- If no cache hit, calls `invoke_agent()` with the message and user ID
- Returns the final answer string to Gradio which displays it in the chat window
- Sets `share=True` so a temporary public URL is generated for easy demo sharing

**Concepts the agent must explain thoroughly:**
- What is `gr.ChatInterface` and what does Gradio handle automatically that we do not have to build?
- What is the exact function signature that a `gr.ChatInterface` callback must have — what arguments does Gradio pass in and what type must be returned?
- What is `share=True` and what infrastructure does Gradio use to generate the temporary public URL?
- Why does the semantic cache check happen in the Gradio callback before calling the agent, rather than inside the agent graph?
- How should we handle errors gracefully in the callback so the UI displays a friendly message instead of crashing?

**Documentation to consult:**
- https://www.gradio.app/docs/gradio/chatinterface

**Test for this phase:** Launch the Gradio app and conduct the following five tests:
1. Ask "What is the refund policy?" — confirm a correct, detailed answer is returned
2. Ask "How do I get my money back?" — this should trigger a cache hit from the previous question (verify in LangSmith — there should be no LLM trace for this call)
3. Ask "What is 2+2?" — confirm the agent answers directly without calling the RAG tool (verify in LangSmith)
4. Check the `long_term_memory` table in Supabase and confirm new rows were written
5. Check the `semantic_cache` table and confirm rows were written for the first question

---

### PHASE 16 — End-to-End Testing and Refinement

**Goal:** Run a comprehensive test of the full system. Identify gaps, bugs, and opportunities for improvement before finalizing the project.

**Required test scenarios:**

1. **Cache effectiveness test** — Ask 5 variations of the same question (about pricing) and confirm that after the first one, all subsequent ones are served from cache. Track this in LangSmith.

2. **RAG accuracy test** — Ask 10 specific questions drawn from the knowledge base documents. Manually verify that the answers match the source documents. Note any incorrect or incomplete answers.

3. **Memory persistence test** — Have a conversation in one Gradio session. Close the browser tab. Start a new Gradio session with the same user ID. Ask a follow-up question that only makes sense in context of the previous session. Confirm the agent uses the stored memory.

4. **Direct answer test** — Ask 5 questions that should NOT require RAG (math questions, general knowledge, polite greetings). Confirm in LangSmith that no RAG tool was called for any of them.

5. **Edge case test** — Ask a question about something completely outside the knowledge base (e.g., "Who won the cricket match last night?"). Confirm the agent responds gracefully and honestly that it does not have that information.

6. **Concurrent user test** — Simulate two different user IDs asking questions and confirm their memories are stored and retrieved independently without mixing.

**After all tests pass:**
- Document every issue found, the root cause, and the fix applied in `PROGRESS.md`
- Calculate the approximate cache hit rate from the `hit_count` values in the `semantic_cache` table
- Measure average response time for cache hits vs. full agent invocations
- Record total token usage for the test session from LangSmith

---

### PHASE 17 — README and Portfolio Documentation

**Goal:** Write a professional, detailed `README.md` that makes this project impressive to any recruiter, agency, or client who opens the GitHub repository.

**The README must contain all of the following sections:**

1. **Project title and tagline** — One sentence that clearly states what the project is
2. **Live Demo link** — The Gradio `share=True` URL or a note about how to run locally
3. **Architecture diagram** — A Mermaid diagram or ASCII art showing the complete data flow from user message to final answer, including the cache and memory paths
4. **Feature list** — Bullet points with short explanations for each major feature
5. **Tech stack table** — A markdown table with Technology, Purpose, and Why This Choice columns
6. **Setup instructions** — Step-by-step guide: clone repo, create venv, install requirements, configure `.env`, run ingestion script, launch Gradio
7. **Supabase setup guide** — Exactly which SQL to run in the Supabase SQL editor to create the tables and indexes
8. **How to access LangSmith traces** — Where to go and what to look for
9. **Design decisions** — A dedicated section explaining why LangGraph was chosen over a plain chain, why semantic cache was built custom instead of using a library, why memory is stored as summaries rather than raw messages
10. **Cost analysis** — A short section showing how the semantic cache reduces LLM API costs. Include a table: Without Cache (X API calls, Y tokens, Z estimated cost) vs. With Cache After Warmup (fewer API calls, lower cost)
11. **Screenshots** — Placeholder section with instructions on where to add Gradio UI screenshots and LangSmith trace screenshots

---

## SECTION 9 — NON-NEGOTIABLE CODING STANDARDS

The coding agent must follow these standards without exception for every file in the `src/` directory.

1. **Every function must have a docstring** — what the function does, what each parameter is and its type, and what it returns.

2. **Every file must start with a module-level docstring** — one paragraph explaining the file's purpose and its role within the larger system.

3. **Every non-obvious line must have a comment** — explain the "why" not the "what." Code shows what; comments explain why.

4. **No magic numbers or magic strings** — values like `0.95`, `5`, `10`, `"semantic_cache"` must come from the config module, not be hardcoded inline.

5. **All errors must be caught and handled** — no unhandled exceptions in production code. If a Supabase call fails, catch the exception, log a descriptive error message, and return a sensible fallback value.

6. **Use the `logging` module, not `print()`** — all `src/` modules use Python's standard logging module. The Gradio interface may use print for quick debug output but never in `src/`.

7. **Type hints on every function** — all function arguments and return types must have Python type annotations.

8. **No code duplication** — if the same logic appears in two places, extract it into a shared utility function.

---

## SECTION 10 — ALTERNATIVE APPROACHES (For Explanation Purposes)

When building each component, the coding agent must briefly mention (but not implement) these alternatives so Hassan understands the broader landscape of options available.

- **Instead of LangGraph:** CrewAI, AutoGen, or plain LangChain LCEL chains. LangGraph is chosen because it provides the most granular control over agent state and supports cycles (loops) natively.
- **Instead of Supabase/pgvector:** Pinecone (managed, serverless vector DB), Weaviate, Qdrant, or local ChromaDB. Supabase is chosen because it combines vector storage, relational storage for memory, and a managed PostgreSQL instance in one service with a generous free tier.
- **Instead of Gradio:** Streamlit, a plain FastAPI server with an HTML page, or a full Next.js frontend. Gradio is chosen for maximum speed to a working demo with zero frontend code.
- **Instead of Azure AI Foundry:** OpenAI directly, Anthropic Claude API, Google Gemini, or Ollama for local open-source models. Azure is chosen because Hassan already has paid model deployments there.
- **Instead of LangSmith:** Helicone, Arize Phoenix, Weights and Biases LLM observability, or a custom logging system. LangSmith is chosen because it requires zero code changes to instrument LangChain and LangGraph.
- **For the semantic cache:** Redis with a custom embedding comparison layer, LangChain's built-in `GPTCache` integration, or a dedicated service like Zep. The custom Supabase pgvector approach is chosen to keep all data in one database and enable semantic matching rather than exact-string matching.

---

## SECTION 11 — FINAL DIRECTIVES FOR THE CODING AGENT

- If you are ever unsure about the current API signature of any library, stop immediately, fetch the official documentation URL provided for that phase, read it, and then proceed. Do not guess.
- If Hassan asks you to expand an explanation, give the full explanation without summarizing or referring him back to earlier text.
- Treat every phase as equally important. No phase is "just a quick setup step."
- When a phase is complete, say explicitly: **"Phase [N] is complete. Here is a summary of what was built and every decision made. Ready to begin Phase [N+1] when you confirm."**
- Never delete or modify code that Hassan has confirmed as working without asking for explicit permission first.
- Maintain `PROGRESS.md` religiously. It is the single source of truth for where the project stands.

---

*AGENTS.md — Version 1.0 — NovaTech Support Agent — Hassan's Portfolio Project*
