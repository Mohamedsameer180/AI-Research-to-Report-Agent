# Phase 1 Completion Report: Ingestion, Page-Aware Chunking, and Unified Data Model

**Date:** 2026-11-14  
**Branch:** `tp01-upgrade`  
**Phase:** Phase 1 of TP01 Upgrade  
**Status:** COMPLETE (8/8 Phase 1 Tests Passed, 8/8 Legacy Tests Passed)

---

## 1. Objectives & Scope Delivered

Phase 1 established the foundation for **TP01: AI Research Paper Intelligence & Discovery Platform**:
1. **PyMuPDF Document Extractor (`backend/ingestion/pdf_extractor.py`)**:
   - Two-column academic layout reading order preservation (`sort_blocks_two_column`).
   - Dynamic header and footer stripping for journals, conferences, and running headers.
   - Printed page label detection (e.g. Roman numerals or printed folio numbers) mapped alongside 1-based physical `pdf_page_number`.
   - Ligature normalization (`clean_ligatures`: ﬁ -> fi, ﬂ -> fl, etc.) and line-wrap hyphenation unwrapping (`fix_hyphenation`).
   - Scanned document / image-only page detection (`needs_ocr=True`) without crashing.
   - Best-effort table parsing via PyMuPDF `find_tables()`.

2. **Section Classifier & Metadata Extraction (`backend/ingestion/section_detector.py`, `backend/ingestion/metadata.py`)**:
   - Canonical academic section classification (`abstract`, `introduction`, `related_work`, `methodology`, `experiments`, `results`, `discussion`, `limitations`, `conclusion`, `references`).
   - Strictly zero-hallucination metadata parsing: extracts title, publication year, author keywords, research domain, and reference count.
   - DOI extraction strictly matching regex pattern `10.\d{4,9}/[-._;()/:A-Za-z0-9]+` with guaranteed `None` when absent.

3. **Page-Bounded Parent-Child Chunker (`backend/ingestion/chunker.py`)**:
   - Parent chunks created per page/section boundary (~800–1200 tokens).
   - Child chunks created via sliding window (~300–400 tokens, 15% overlap) strictly contained within individual PDF pages so citations can never cite incorrect pages.
   - Exact `char_start` and `char_end` tracking mapping directly into source page text.
   - Table chunks preserved as distinct semantic units with tabular CSV representations.

4. **Multi-Tenant Dual Indexing Engine (`backend/rag/`)**:
   - **ChromaDB (`backend/rag/vector_store.py`)**: Persistent workspace-isolated collections (`papers_{workspace_id}`) using `BAAI/bge-small-en-v1.5` embeddings (384-dim, normalized).
   - **BM25 Index (`backend/rag/bm25_index.py`)**: Workspace-scoped BM25 indices powered by `rank_bm25.BM25Plus` for robust keyword matching on academic terminology without small-corpus zero-IDF degradation.
   - Fully scoped by `workspace_id` and `user_id` across queries and vector searches.

5. **SQLAlchemy 2.0 Unified Data Model (`backend/app/db/models.py`)**:
   - 13 consolidated relational tables initialized in SQLite (`research_platform.db`):
     - `documents`
     - `document_pages`
     - `document_chunks`
     - `paper_records`
     - `citations`
     - `comparisons`
     - `contradictions`
     - `research_gaps`
     - `conversations`
     - `messages`
     - `agent_runs`
     - `reports`
     - `eval_results`

6. **FastAPI Document Management Router (`backend/app/api/documents.py`)**:
   - `POST /api/documents/upload`: Single PDF upload, SHA-256 deduplication, versioning, automated extraction, chunking, and dual indexing.
   - `POST /api/documents/batch-upload`: Concurrent multi-PDF upload with workspace quota enforcement.
   - `GET /api/documents`: List workspace papers.
   - `GET /api/documents/{id}`: Detailed paper inspection.
   - `GET /api/documents/{id}/status`: Fast status polling (`queued`, `processing`, `completed`, `failed`).
   - `POST /api/documents/{id}/process`: Re-trigger processing pipeline.
   - `DELETE /api/documents/{id}`: Complete cascaded deletion across SQLite, ChromaDB, BM25 index, and physical disk storage.

---

## 2. Test Verification Summary

### Phase 1 Pytest Suite (`backend/tests/test_phase1_ingestion.py`):
```text
my agent/backend/tests/test_phase1_ingestion.py::test_two_column_pdf_extraction PASSED [ 12%]
my agent/backend/tests/test_phase1_ingestion.py::test_scanned_pdf_detection PASSED     [ 25%]
my agent/backend/tests/test_phase1_ingestion.py::test_section_detector PASSED         [ 37%]
my agent/backend/tests/test_phase1_ingestion.py::test_metadata_extraction PASSED       [ 50%]
my agent/backend/tests/test_phase1_ingestion.py::test_parent_child_chunking PASSED     [ 62%]
my agent/backend/tests/test_phase1_ingestion.py::test_vector_store_isolation PASSED   [ 75%]
my agent/backend/tests/test_phase1_ingestion.py::test_bm25_index_and_search PASSED     [ 87%]
my agent/backend/tests/test_phase1_ingestion.py::test_document_lifecycle_api PASSED    [100%]

======================= 8 passed in 35.49s =======================
```

### Legacy Comprehensive Test Suite (`tests/test_comprehensive.py`):
```text
✓ PASS test_file_structure
✓ PASS test_python_syntax
✓ PASS test_orchestrator_initialization
✓ PASS test_task_state_models
✓ PASS test_database_manager
✓ PASS test_api_models
✓ PASS test_partial_completion_evidence_summary
✓ PASS test_report_download_endpoint

Overall: 8/8 test groups passed (100% Backward Compatibility Maintained)
```

---

## 3. Architecture & Artifacts Created/Updated

```
my agent/backend/
├── app/
│   ├── config.py                 # Paths, models, embedding config, workspace constraints
│   ├── db/
│   │   ├── database.py           # Engine, SessionLocal, get_db, init_db
│   │   ├── models.py             # 13 consolidated SQLAlchemy 2.0 ORM models & synonyms
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── document.py           # Pydantic models for Document APIs
│   │   └── __init__.py
│   └── api/
│       ├── documents.py          # FastAPI router (/api/documents/*)
│       └── __init__.py
├── ingestion/
│   ├── pdf_extractor.py          # Two-column layout, headers/footers, PyMuPDF tables
│   ├── section_detector.py       # IMRaD section heading classification
│   ├── metadata.py               # Zero-hallucination DOI, title, year, keywords
│   ├── chunker.py                # Page-bounded parent-child chunking
│   ├── dedup.py                  # SHA-256 digest & version bump
│   └── __init__.py
├── rag/
│   ├── embeddings.py             # BAAI/bge-small-en-v1.5 embedding service
│   ├── vector_store.py           # Persistent ChromaDB with workspace-scoped collections
│   ├── bm25_index.py             # BM25Plus sparse index per workspace
│   └── __init__.py
└── tests/
    └── test_phase1_ingestion.py  # 8 comprehensive Phase 1 tests
```

---

## 4. Key Decisions & Non-Negotiables Enforced

1. **Page-Level Grounding**: Chunks never cross physical PDF page boundaries. Citations can reference exact pages with 100% confidence.
2. **Zero Fabrication**: DOIs, dates, and author lists are parsed strictly from document text using validated regex. If unverified, fields default to `None`.
3. **Multi-Tenant Isolation**: Both ChromaDB collections and BM25 index files are strictly partitioned by `workspace_id`. Cross-workspace data leakage is prevented.
4. **Hardware Efficiency (8 GB Laptop Target)**: Embeddings run on CPU with lightweight `bge-small-en-v1.5` (~130MB model), and cloud Gemini inference is reserved for LLM reasoning in subsequent phases.
5. **Cascaded Deletion**: Deleting a paper cleans SQLite records, ChromaDB vector points, BM25 serialized entries, and physical disk artifacts simultaneously.

---

## 5. Phase 1 Status Summary

| Item | Status | Notes |
|---|---|---|
| PDF Extraction & Two-Column Layout | **DONE** | PyMuPDF with block sorting & header/footer filtering |
| Scanned PDF OCR Detection | **DONE** | Flags `needs_ocr=True` without crashing |
| Zero-Hallucination Metadata | **DONE** | Regex DOI, year, title, abstract, keywords |
| Page-Bounded Parent-Child Chunking | **DONE** | Spans tracked, parent-child references maintained |
| ChromaDB Vector Store | **DONE** | Persistent workspace-scoped collections |
| BM25 Keyword Search | **DONE** | BM25Plus keyword index per workspace |
| Document CRUD & Batch API | **DONE** | `/api/documents` endpoints mounted & tested |
| 13 SQLAlchemy Tables | **DONE** | Verified in `research_platform.db` |
| Pytest Test Suite | **DONE** | 8/8 tests passed |
| Legacy Regression Tests | **DONE** | 8/8 test groups passed |

