# Implementation Plan & Migration Roadmap: TP01 Upgrade

**Project:** TP01: AI Research Paper Intelligence & Discovery Platform  
**Audit Stage:** Phase 0 Completion  
**Target Branch:** `tp01-upgrade`  
**Date:** 2026-11-14  

---

## 1. Module Disposition Table

Every existing and planned file in the repository is mapped to an explicit action (**KEEP**, **REFACTOR**, **REMOVE**, or **REPLACE**) with a direct justification based on the TP01 specification:

| Module / File Path | Action | One-Line Reason Mapped to TP01 |
|---|---|---|
| `backend/main.py` | **REFACTOR** | Decompose monolithic routes into modular routers (`app/api/`) and adapt to TP01 REST endpoints. |
| `backend/taskfinisher_orchestrator.py` | **REFACTOR** | Consolidate 8 simulated steps into the 4 functional Google ADK agent roles. |
| `backend/tools/file_processor_tool.py` | **REPLACE** | Replace pypdf with PyMuPDF two-column sorting, section detection, and parent-child chunking. |
| `backend/tools/web_search_tool.py` | **KEEP** | Retain as an optional secondary tool, but remove as the primary source for paper fact retrieval. |
| `backend/tools/web_scraper_tool.py` | **KEEP** | Retain for potential external URL/DOI resolution; isolate from core local RAG flow. |
| `backend/tools/create_important_points_docx.py`| **REFACTOR** | Adapt into `backend/services/report_service.py` for cited multi-format report generation. |
| `backend/database/db_manager.py` | **REPLACE** | Replace raw sqlite3 scripts with SQLAlchemy 2.0 ORM models and Alembic migrations. |
| `backend/database/document_integrity.py` | **REFACTOR** | Migrate SHA-256 calculation and deduplication logic into `backend/ingestion/dedup.py` backed by SQL. |
| `backend/database/firebase_service.py` | **KEEP** | Preserve optional cloud mirroring stub without blocking local SQLite operations. |
| `backend/agents/__init__.py` | **REFACTOR** | Populate with Root, Ingestion, Synthesis, and Report agent definitions. |
| `backend/ingestion/pdf_extractor.py` | **NEW** | Implement PyMuPDF two-column extraction, header/footer cleaning, and ligature/hyphen fixing. |
| `backend/ingestion/section_detector.py` | **NEW** | Implement heuristic academic section classification. |
| `backend/ingestion/chunker.py` | **NEW** | Implement section-aware parent-child chunking preserving page, section, and char spans. |
| `backend/ingestion/metadata.py` | **NEW** | Extract title, authors, year, abstract, DOI, and raw reference strings. |
| `backend/ingestion/dedup.py` | **NEW** | Detect duplicate uploads via SHA-256 and manage versioning. |
| `backend/rag/embeddings.py` | **NEW** | Encapsulate `sentence-transformers` with configurable `BAAI/bge-small-en-v1.5`. |
| `backend/rag/vector_store.py` | **NEW** | Manage ChromaDB persistent collections partitioned by workspace. |
| `backend/rag/bm25_index.py` | **NEW** | Implement BM25 index creation, persistence, query, and deletion. |
| `backend/rag/retrieval.py` | **NEW** | Hybrid dense + BM25 retrieval combining ranks via Reciprocal Rank Fusion (RRF). |
| `backend/rag/reranker.py` | **NEW** | Implement cross-encoder reranker (`ms-marco-MiniLM-L-6-v2`) filtering top-30 to top-8. |
| `backend/rag/query_planner.py` | **NEW** | Gemini structured query classifier, query rewriter, and sub-query decomposer. |
| `backend/extraction/paper_schema.py` | **NEW** | Define Pydantic `PaperRecord` and `Evidence` data structures. |
| `backend/extraction/paper_extractor.py` | **NEW** | Section-by-section extraction using Gemini structured output with verbatim quote guarantees. |
| `backend/verification/citation_verifier.py` | **NEW** | Programmatic rapidfuzz verbatim quote matching across exact, fuzzy (≥90%), and ±1 page bounds. |
| `backend/verification/completion_check.py` | **NEW** | Code-level validation ensuring structural output completeness and honest status reporting. |
| `backend/services/qa_service.py` | **NEW** | Research Q&A service producing structured claims with chunk citations and honest refusals. |
| `backend/services/comparison.py` | **NEW** | Pairwise and collection matrix comparison across methodologies, datasets, and metrics. |
| `backend/services/contradictions.py` | **NEW** | Contradiction detector flagging conflicting outcomes on comparable evaluation settings. |
| `backend/services/gaps.py` | **NEW** | Research gap discovery engine (stated limitations, coverage gaps, inferred opportunities). |
| `backend/services/report_service.py` | **NEW** | Multi-document comprehensive report builder outputting Markdown, PDF, and DOCX. |
| `backend/eval/build_eval_set.py` | **NEW** | Generate gold synthetic question-chunk benchmark pairs using Gemini. |
| `backend/eval/run_eval.py` | **NEW** | Execute evaluation harness computing Recall@K, MRR, nDCG, and Faithfulness. |
| `frontend/` (All views & components) | **KEEP** | Maintain existing React 18 UI; wire to upgraded TP01 endpoints in subsequent phases. |
| `test_basic.py` | **KEEP** | Maintain as the lightweight file-structure smoke test. |
| `tests/test_comprehensive.py` | **REFACTOR** | Expand to test Phase 1 through Phase 9 implementations. |

---

## 2. Target Directory Structure Mapping

To cleanly adopt the target layout while preserving existing functionality:

```
my agent/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Clean FastAPI entrypoint with CORS & exception handlers
│   │   ├── config.py                # Pydantic Settings loading from .env
│   │   ├── api/                     # Modular route controllers
│   │   │   ├── documents.py         # /api/documents/* (upload, batch, process, status)
│   │   │   ├── rag.py               # /api/rag/* (retrieve, query, eval)
│   │   │   ├── research.py          # /api/research/* (analyze, chat, compare, contradictions, gaps)
│   │   │   ├── reports.py           # /api/reports/* (generate, list, download)
│   │   │   └── agents.py            # /api/agents/* (execute, status)
│   │   ├── schemas/                 # Pydantic models for request/response and LLM outputs
│   │   │   ├── document.py
│   │   │   ├── rag.py
│   │   │   ├── paper.py
│   │   │   ├── research.py
│   │   │   └── report.py
│   │   └── db/                      # SQLAlchemy 2.0 ORM & Alembic
│   │       ├── database.py          # Engine, SessionLocal, session dependency
│   │       ├── models.py            # Consolidated ORM models
│   │       └── migrations/          # Alembic version files
│   │
│   ├── agents/                      # Exactly 4 Google ADK Agents
│   │   ├── root_agent.py            # Coordinator & planner
│   │   ├── ingestion_agent.py       # Ingestion & extraction executor
│   │   ├── synthesis_agent.py       # Comparison, contradiction & gap discoverer
│   │   └── report_agent.py          # Comprehensive report compiler
│   │
│   ├── ingestion/                   # Document parsing & chunking
│   │   ├── pdf_extractor.py         # PyMuPDF two-column, headers/footers, hyphenation
│   │   ├── section_detector.py      # Heuristic heading classification
│   │   ├── chunker.py               # Parent-child chunking preserving page & char spans
│   │   ├── metadata.py              # Title, authors, abstract, DOI extraction
│   │   └── dedup.py                 # File hash calculation & versioning
│   │
│   ├── rag/                         # Hybrid vector + lexical retrieval
│   │   ├── embeddings.py            # SentenceTransformers wrapper (BAAI/bge-small-en-v1.5)
│   │   ├── vector_store.py          # ChromaDB collection manager
│   │   ├── bm25_index.py            # BM25 index builder & searcher
│   │   ├── retrieval.py             # Hybrid RRF rank fusion
│   │   ├── reranker.py              # Cross-encoder reranker (ms-marco-MiniLM-L-6-v2)
│   │   └── query_planner.py         # Query decomposition & router
│   │
│   ├── extraction/                  # Information extraction
│   │   ├── paper_schema.py          # PaperRecord & Evidence definitions
│   │   └── paper_extractor.py       # Section-by-section Gemini extractor
│   │
│   ├── verification/                # Programmatic truthfulness verification
│   │   ├── citation_verifier.py     # Rapidfuzz verbatim quote validator (±1 page)
│   │   └── completion_check.py      # Structural completion & gap audit
│   │
│   ├── services/                    # High-level domain services
│   │   ├── qa_service.py            # Grounded Q&A with inline citations
│   │   ├── comparison.py            # Multi-paper matrix comparison
│   │   ├── contradictions.py        # Conflicting results analysis
│   │   ├── gaps.py                  # Research gap hypothesis generator
│   │   └── report_service.py        # Multi-format report builder
│   │
│   ├── eval/                        # Evaluation & benchmarking
│   │   ├── build_eval_set.py        # Gold question-chunk generator
│   │   ├── run_eval.py              # Precision, Recall, MRR, Faithfulness evaluation
│   │   └── finetune_embeddings.py   # Optional embedding fine-tuning script
│   │
│   └── tests/                       # Pytest unit & integration tests per phase
│
├── frontend/                        # Existing React 18 + Vite SPA
├── docs/                            # Architectural documentation
├── package.json                     # Monorepo runner
├── run_system.bat                   # Parallel system launcher
└── README.md                        # Master project documentation
```

---

## 3. Phase-by-Phase Execution Schedule

### **Phase 1: Ingestion, Page-Aware Chunking, Data Model**
- **Goal:** Ingest multiple research PDFs, extract high-fidelity text with page awareness, split into section-bounded parent-child chunks, and persist in SQLite + ChromaDB + BM25.
- **Tasks:**
  1. Add dependencies: `pymupdf`, `sqlalchemy`, `alembic`, `chromadb`, `sentence-transformers`, `rank-bm25`.
  2. Implement `ingestion/pdf_extractor.py` (PyMuPDF 2-column block sorting, header/footer strip, ligature fix, scanned page flag, printed vs. PDF page tracking).
  3. Implement `ingestion/section_detector.py` and `ingestion/chunker.py`.
  4. Implement `app/db/models.py` with SQLAlchemy 2.0 (13 tables) and configure Alembic.
  5. Implement `rag/embeddings.py`, `rag/vector_store.py`, and `rag/bm25_index.py`.
  6. Implement endpoints: `POST /api/documents/upload`, `POST /api/documents/batch-upload`, `GET /api/documents`, `GET /api/documents/{id}`, `DELETE /api/documents/{id}`, `POST /api/documents/{id}/process`.
  7. Write and pass unit tests for extraction, deduplication, chunking, and workspace isolation.

### **Phase 2: Advanced RAG Retrieval**
- **Goal:** Hybrid dense + lexical retrieval with Reciprocal Rank Fusion, query planning, per-paper balance, and cross-encoder reranking.
- **Tasks:**
  1. Implement `rag/retrieval.py` (RRF rank combination).
  2. Implement `rag/reranker.py` with `ms-marco-MiniLM-L-6-v2` (top-30 -> top-8).
  3. Implement `rag/query_planner.py` using Gemini structured output.
  4. Implement per-paper balanced allocation and section-aware boosting.
  5. Expose `POST /api/rag/retrieve` and `POST /api/rag/query`.
  6. Benchmark hybrid vs. dense vs. BM25 on test queries.

### **Phase 3: Structured Per-Paper Extraction**
- **Goal:** Extract structured scientific representations (`PaperRecord`) with verbatim quotes and page numbers.
- **Tasks:**
  1. Define `extraction/paper_schema.py` (`PaperRecord` with `Evidence` spans).
  2. Implement `extraction/paper_extractor.py` performing section-by-section Gemini extraction.
  3. Implement caching by SHA-256 hash.
  4. Expose `POST /api/research/analyze` and `GET /api/documents/{id}/record`.
  5. Write tests verifying null-on-missing behavior (zero hallucination).

### **Phase 4: Programmatic Citation Verification**
- **Goal:** Plain Python verifier guaranteeing quotes exist on cited pages.
- **Tasks:**
  1. Implement `verification/citation_verifier.py` (exact -> rapidfuzz ≥90% -> adjacent page ±1).
  2. Implement `verification/completion_check.py` for structural and factual completeness checks.
  3. Write comprehensive unit tests for exact, hyphenated, offset, and fabricated citations.

### **Phase 5: Cited Research Chatbot**
- **Goal:** Conversational Q&A restricted exclusively to retrieved paper chunks with inline citations.
- **Tasks:**
  1. Implement `services/qa_service.py` with structured claim generation and verifier pipeline.
  2. Persist conversation history in `conversations` and `messages`.
  3. Expose `POST /api/research/chat`.
  4. Write tests for single-paper, multi-paper, comparison, and out-of-scope queries.

### **Phase 6: Cross-Paper Synthesis**
- **Goal:** Compare findings across papers, detect contradictions on comparable benchmarks, and discover research gaps.
- **Tasks:**
  1. Implement `services/comparison.py` (`POST /api/research/compare`).
  2. Implement `services/contradictions.py` (`POST /api/research/contradictions`).
  3. Implement `services/gaps.py` (`POST /api/research/gap-discovery`) with fixed disclaimer.
  4. Write tests with 3 sample research papers.

### **Phase 7: Google ADK Orchestration**
- **Goal:** Wrap workflows into exactly 4 Google ADK agents with sequential/parallel pipelines.
- **Tasks:**
  1. Implement `RootPlannerAgent`, `IngestionExtractionAgent`, `SynthesisAgent`, and `ReportAgent`.
  2. Wrap services and verifiers as typed Google ADK tools.
  3. Log execution traces to `agent_runs`.
  4. Expose `POST /api/agents/execute` and `GET /api/agents/status/{task_id}`.

### **Phase 8: Evaluation & RAG Improvement**
- **Goal:** Empirical evaluation harness measuring retrieval and generation quality.
- **Tasks:**
  1. Implement `eval/build_eval_set.py` (30–50 gold question-chunk pairs).
  2. Implement `eval/run_eval.py` (Recall@K, MRR, Faithfulness, Citation Validity).
  3. Expose `GET /api/rag/evaluation` and write `docs/RAG_EVAL.md`.

### **Phase 9: Reports & Documentation**
- **Goal:** Multi-format research reports and complete developer documentation.
- **Tasks:**
  1. Implement `services/report_service.py` producing Markdown, PDF (`reportlab`), and DOCX.
  2. Expose `POST /api/reports/generate` and `GET /api/reports/{id}/download`.
  3. Compile documentation: `README.md`, `SYSTEM_ARCHITECTURE.md`, `API_DOCUMENTATION.md`, `RAG_ARCHITECTURE.md`, `AGENT_WORKFLOW.md`, `TESTING_REPORT.md`.

---

## 4. Open Questions for User Approval (Do Not Guess)

The following architectural questions require explicit user guidance before commencing Phase 1:

1. **Workspace & User ID Source:** Currently, the system defaults to `"local_user"`. For multi-tenant and workspace scoping, should we introduce a query/header parameter `X-Workspace-Id` (defaulting to `"default_workspace"`) and `X-User-Id` (defaulting to `"local_user"`), or do you have a specific workspace convention you want to adopt?
2. **Embedding Model Location:** The specification prescribes `BAAI/bge-small-en-v1.5` (~133 MB) running locally via `sentence-transformers` on CPU. Would you like this model downloaded and cached locally on first run in `backend/models/cache/`, or should we allow a Gemini cloud embedding fallback via `.env` (`EMBEDDING_PROVIDER=sentence-transformers` vs `EMBEDDING_PROVIDER=gemini`)?
3. **Database File Location:** Should the new SQLite database continue as `backend/taskfinisher_ai.db`, or be named `backend/research_platform.db` to reflect the TP01 target platform?
4. **Existing Frontend Adaptation:** When we expose the new `/api/documents/upload`, `/api/research/chat`, and `/api/research/compare` endpoints, should we maintain backward-compatibility endpoints for the current frontend (`/api/tasks`, `/api/demo/*`) until the frontend is updated, or can we immediately focus backend routes on the target TP01 API?
5. **Sample Research Papers:** For testing Phases 1 through 6, do you have specific PDF research papers in mind, or should we include 3 public open-access computer science/AI papers (e.g., Attention Is All You Need, LoRA, Toolformer) in `demos/sample_papers/` for repeatable testing?
