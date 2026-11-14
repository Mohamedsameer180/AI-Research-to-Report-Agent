# Project Audit: TaskFinisher AI to TP01 Research Paper Intelligence Platform

**Date:** 2026-11-14  
**Audit Target:** `my agent/` Codebase  
**Auditor:** Senior AI Architect & Python Backend Engineer  
**Objective:** Phase 0 comprehensive audit to establish baseline capabilities, identify deficiencies, and formulate an architectural migration roadmap to **TP01: AI Research Paper Intelligence & Discovery Platform**.

---

## 1. Executive Summary

The audited project originated as **TaskFinisher AI**, a prototype built around the concept of an auditable task-completion agent for the GA-02 hackathon. While the project exhibits clean UI design tokens, structured logging principles, and an 8-stage state machine philosophy, its internal implementation relies heavily on **procedural simulation, pre-baked strings, and placeholder heuristics** rather than actual document parsing, semantic vector search, or dynamic Google ADK reasoning loops.

### Primary Audit Findings:
1. **Simulated Agent Reasoning:** The Google ADK `Agent` instances declared in `taskfinisher_orchestrator.py` (`PlannerAgent`, `DocumentAgent`, `ResearchAgent`, `VerificationAgent`, etc.) are instantiated as metadata wrappers but never invoked via the ADK runner or Gemini completion API. Steps execute via deterministic procedural Python functions with fixed output strings.
2. **Absence of a Vector RAG Pipeline:** There is currently **zero semantic retrieval infrastructure**. No vector database (ChromaDB), no embedding model (`BAAI/bge-small-en-v1.5`), no BM25 lexical index, and no cross-encoder reranker (`ms-marco-MiniLM-L-6-v2`) are installed or implemented.
3. **Naive Document Ingestion:** PDF handling in `tools/file_processor_tool.py` utilizes basic `pypdf`/`PyPDF2` text extraction without column sorting, header/footer removal, hyphenation joining, ligature cleaning, scanned page detection (`needs_ocr`), table extraction, or section classification.
4. **Relational Database Model Gaps:** The SQLite schema in `database/db_manager.py` only models `tasks`, `task_steps`, `execution_history`, and `app_settings` via raw SQLite connections. Core relational entities needed for multi-paper intelligence (`documents`, `document_pages`, `document_chunks`, `paper_records`, `citations`, `comparisons`, `contradictions`, `research_gaps`, `conversations`, `messages`, `agent_runs`) do not exist. SQLAlchemy and Alembic are not yet integrated.
5. **Lack of User & Workspace Scoping:** Multi-tenant isolation is missing. SQL queries operate globally without filtering by `user_id` or `workspace_id`.
6. **No Scientific Extraction & Verification Engine:** There is no entity extraction for paper objectives, methodology, evaluation, or results, no cross-paper comparison logic, no contradiction analysis, and no page-verifiable citation validation algorithm.

---

## 2. Subsystem-by-Subsystem Audit

### 2.1 Architecture & Directory Structure
- **Current State:** The repository was recently organized into a 2-tier full-stack layout with `frontend/` (React + Vite + Tailwind) and `backend/` (FastAPI + SQLite). Root proxies (`main.py`, `taskfinisher_orchestrator.py`) forward calls into `backend/`.
- **Deficiencies:** Core backend logic resides in two monoliths: `backend/main.py` (1,130 lines) and `backend/taskfinisher_orchestrator.py` (1,303 lines). Domain concerns (routing, schemas, database operations, RAG, agent workflows) are conflated in these two files rather than partitioned into modular packages (`app/`, `ingestion/`, `rag/`, `extraction/`, `verification/`, `services/`, `eval/`).

### 2.2 Google ADK Agents & Agent Coordination
- **Current State:** 8 agents are configured in `TaskFinisherOrchestrator._initialize_agents()` using `google.adk.agents.Agent`.
- **Deficiencies:**
  - The agents are never passed user prompts or executed via `google.adk.runtime.Runner`.
  - The orchestrator procedurally mutates an in-memory dictionary of `StepResult` objects.
  - Agent coordination is a rigid sequential loop (`S1` through `S8`), with `S6` hardcoded to pause on a synthetic "market-size conflict" and `S8` computing an arithmetic status based on previous steps.
  - TP01 requires consolidating this architecture into **exactly 4 agents** (`Root/Planner`, `Ingestion+Extraction`, `Synthesis`, `Report`) with sequential/parallel execution and explicit schemas.

### 2.3 Tools & Extensibility
- **Current State:**
  - `web_search_tool.py`: Performs DuckDuckGo searches with fallback to static hardcoded arrays (`CURATED_SOURCES`).
  - `web_scraper_tool.py`: Basic BeautifulSoup scraper extracting text from generic HTML.
  - `file_processor_tool.py`: Naive extractor for text, PDF, DOCX, CSV.
  - `create_important_points_docx.py`: Utility generating `.docx` files using python-docx.
- **Deficiencies:**
  - Tools are designed for generic task execution rather than scientific paper RAG.
  - Tools do not return structured Pydantic representations with page-level bounding spans, character offsets, or section categories.

### 2.4 API Endpoints & Request/Response Flow
- **Current State:** `backend/main.py` exposes 24 endpoints covering task creation, status polling, streaming WebSocket, mock demo runs (`/api/demo/{scenario}`), report downloads, and document verification.
- **Deficiencies:**
  - Endpoints cater to the generic "TaskFinisher" task lifecycle (`/api/tasks`, `/api/demo/*`) rather than scientific document intelligence.
  - Missing all TP01 specification routes: `/api/documents/upload`, `/api/documents/batch-upload`, `/api/documents/{id}/process`, `/api/rag/retrieve`, `/api/rag/query`, `/api/research/analyze`, `/api/research/chat`, `/api/research/compare`, `/api/research/contradictions`, `/api/research/gap-discovery`, `/api/reports/generate`.
  - Pydantic models in `main.py` lack strict field validation, regex formatters for DOIs, and structured evidence contracts.

### 2.5 Database Schema & Persistence
- **Current State:** Direct `sqlite3` cursors without an ORM. Tables: `tasks`, `task_steps`, `execution_history`, `app_settings`. Metadata for file hashes is stored in a separate JSON file `document_integrity_records.json`.
- **Deficiencies:**
  - Dual persistence anti-pattern: task state is saved in SQLite while document SHA-256 metadata is saved in a local JSON file (`document_integrity_records.json`), risking desynchronization.
  - No database migration tool (Alembic) is configured.
  - Complete absence of normalized schema for scientific documents, pages, chunks, vectors, extractions, citations, conversations, or evaluation benchmarks.

### 2.6 Authentication & Multi-Tenant Scoping
- **Current State:** `_extract_user_id` extracts `Authorization` header bearer tokens via a Firebase stub, defaulting to `"local_user"`.
- **Deficiencies:**
  - All database queries (`SELECT * FROM tasks WHERE task_id = ?`) ignore `user_id`. Any user knowing a `task_id` can access or delete any task.
  - File storage in `uploads/` and `outputs/` is flat and unpartitioned by workspace.
  - TP01 requires every database record and vector collection to be strictly partitioned by `user_id` and `workspace_id`.

### 2.7 PDF & Document Ingestion
- **Current State:** `tools/file_processor_tool.py` reads PDFs via `pypdf.PdfReader.extract_text()`.
- **Deficiencies:**
  - Two-column academic papers result in jumbled, interleaved line extraction.
  - Page headers (journal names, running titles) and footers (page numbers, copyright notices) contaminate chunk text.
  - Hyphenated words across line wraps (e.g., `con- \n clusion`) are not joined.
  - Scanned PDFs without embedded text produce empty strings with no OCR fallback warning (`needs_ocr`).
  - Table structures are flattened into illegible strings.
  - No detection of printed page numbers vs. physical PDF page indexes (crucial for accurate citations).

### 2.8 RAG & Retrieval Engine
- **Current State:** Non-existent. Ingestion does not chunk text or create vector representations.
- **Deficiencies:**
  - No vector store (ChromaDB).
  - No embedding pipeline (`sentence-transformers` with `BAAI/bge-small-en-v1.5`).
  - No lexical search (`rank_bm25`).
  - No hybrid rank fusion (RRF) or cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`).
  - Retrieval questions cannot be answered from papers; the system currently falls back to DuckDuckGo web search.

### 2.9 LLM Integration & Generation
- **Current State:** API key configured in `.env` (`GEMINI_API_KEY`). The orchestrator contains model identifiers (`gemini-2.0-flash`, `gemini-2.5-pro`), but no actual runtime client or generation prompt exists.
- **Deficiencies:**
  - No Gemini structured output parsing (`response_mime_type="application/json"` or Pydantic output schemas).
  - No prompt templates for query planning, section extraction, comparison, contradiction detection, or hypothesis generation.
  - No automated retry on JSON validation failure.

### 2.10 Error Handling, Verification & Logging
- **Current State:** Structured logging is configured via standard library `logging`. Task state transitions include `error`, `attempts`, and `recovery_action`.
- **Deficiencies:**
  - "Verification" in `_final_verify` simply inspects boolean flags (`step.status == COMPLETED`) and counts evidence items. It performs no textual citation verification or verification of claimed quotes against source document text.
  - Errors during execution are swallowed in some places or procedurally bypassed to force a "DONE" or "PARTIALLY_DONE" verdict.

### 2.11 Test Suite
- **Current State:** Two test files exist: `test_basic.py` (file existence check) and `tests/test_comprehensive.py` (smoke tests covering imports, Pydantic models, SQLite persistence, and mock scenario flows).
- **Deficiencies:**
  - Zero unit tests for PDF extraction accuracy, two-column parsing, citation verification, retrieval recall, or embedding generation.
  - No integration tests for multi-document comparisons or contradiction detection.

---

## 3. Findings Matrix: What Works vs. What is Missing

| Component | Status | Existing Implementation | Required for TP01 |
|---|---|---|---|
| **FastAPI Skeleton** | WORKS | `backend/main.py` with CORS, WebSocket, error handlers | REFACTOR into modular `app/api` routers |
| **Pydantic Models** | WORKS | Basic task/step models in `taskfinisher_orchestrator.py` | REPLACE with strict schema models (`PaperRecord`, `Evidence`, `Chunk`, etc.) |
| **SQLite Persistence** | WORKS | Raw `sqlite3` in `db_manager.py` with tasks/steps | REPLACE with SQLAlchemy 2.0 + Alembic migrations |
| **PDF Extraction** | STUBBED | Basic `pypdf` reading in `file_processor_tool.py` | REPLACE with PyMuPDF two-column, clean text, printed/physical page tracking |
| **Chunking Engine** | BROKEN/NONE | None (full document string used) | IMPLEMENT section-aware parent-child chunking (300-500 tokens, 15% overlap) |
| **Embedding Generation** | MISSING | None | IMPLEMENT sentence-transformers (`BAAI/bge-small-en-v1.5`) |
| **Vector Storage** | MISSING | None | IMPLEMENT ChromaDB collections scoped by workspace |
| **BM25 Lexical Search** | MISSING | None | IMPLEMENT `rank_bm25` index persisted alongside ChromaDB |
| **Hybrid Reranking** | MISSING | None | IMPLEMENT Reciprocal Rank Fusion (RRF) + Cross-Encoder reranking |
| **Query Planner** | MISSING | None | IMPLEMENT Gemini structured query decomposer and router |
| **Paper Extraction** | MISSING | None | IMPLEMENT section-by-section extraction into `PaperRecord` with quotes |
| **Citation Verification**| MISSING | Procedural status checks | IMPLEMENT rapidfuzz ±1 page programmatic verification (plain Python) |
| **Contradiction Finder** | STUBBED | Hardcoded demo scenario | IMPLEMENT pairwise analysis on comparable (task, dataset, metric) |
| **Research Gap Engine** | MISSING | None | IMPLEMENT hypothesis generator (stated limitations, coverage, inferred) |
| **ADK Orchestration** | STUBBED | 8 declarative agents never invoked | REFACTOR into exactly 4 functional agents (Planner, Ingestion, Synthesis, Report) |
| **Evaluation Suite** | MISSING | None | IMPLEMENT `build_eval_set.py` and `run_eval.py` (Recall@K, MRR, Faithfulness) |

---

## 4. Hardware Resource & Bottleneck Analysis (8 GB Laptop Constraint)

1. **Embedding Model Selection:** `BAAI/bge-small-en-v1.5` requires ~130 MB RAM and ~384-dimensional vectors. This fits well within an 8 GB RAM profile.
2. **Reranker Selection:** `cross-encoder/ms-marco-MiniLM-L-6-v2` requires ~80 MB RAM and processes top-30 candidate pairs in <250 ms on CPU.
3. **LLM Inference:** All generation (extraction, synthesis, Q&A, gap discovery) will be routed to the cloud via Google Gemini API (`gemini-2.0-flash` / `gemini-2.5-pro`), offloading all heavy compute.
4. **ChromaDB In-Memory vs. Persistent:** ChromaDB will run locally using SQLite persistent client (`chromadb.PersistentClient`), consuming <150 MB RAM for 3–10 research papers.
5. **PyMuPDF Memory Safety:** PyMuPDF (`fitz`) operates via lightweight C bindings, reading and freeing page streams individually to prevent memory spikes.

