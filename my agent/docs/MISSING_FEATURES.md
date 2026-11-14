# Missing Features & Gap Analysis: TP01 vs. Current Codebase

**Target Specification:** TP01: AI Research Paper Intelligence & Discovery Platform  
**Baseline Project:** TaskFinisher AI (Google ADK Document Agent)  
**Date:** 2026-11-14  

---

## 1. Executive Gap Matrix

The table below contrasts the target capabilities defined in the TP01 specification against the current codebase:

| Capability | TP01 Requirement | Current Codebase Status | Gap Severity |
|---|---|---|---|
| **PDF Extraction** | PyMuPDF with 2-column sorting, header/footer strip, hyphenation/ligature fix, `needs_ocr` detection, printed vs. physical page tracking | Basic `pypdf` sequential text extraction; columns are interleaved; headers/footers preserved | **CRITICAL** |
| **Section Detection** | Deterministic heading parser classifying Abstract, Intro, Methodology, Results, Limitations, Conclusion, References | None; full document is treated as a flat string | **CRITICAL** |
| **Chunking Engine** | Section-aware parent-child chunking (~300–500 tokens, 15% overlap), keeping chunk_id, parent_id, page, section, char_span | No chunking; documents treated as monolithic text blobs | **CRITICAL** |
| **Data Modeling** | Consolidated tables via SQLAlchemy + Alembic (`documents`, `document_pages`, `document_chunks`, `paper_records`, `citations`, etc.) | Raw SQLite queries on `tasks`, `task_steps`, `execution_history`; no Alembic | **HIGH** |
| **Vector Indexing** | ChromaDB collections scoped per workspace/user, using `BAAI/bge-small-en-v1.5` | ChromaDB not installed or configured | **CRITICAL** |
| **Lexical Search** | BM25 index (`rank_bm25`) synchronized with document lifecycle | BM25 not installed or implemented | **HIGH** |
| **Hybrid Retrieval** | Dense + BM25 combined via Reciprocal Rank Fusion (RRF) | None; only DuckDuckGo external web search is available | **CRITICAL** |
| **Reranking** | Cross-encoder reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`) filtering top-30 to top-8 | Not installed or implemented | **HIGH** |
| **Query Planning** | Gemini query planner classifying intent, rewriting, decomposing into sub-queries, per-paper balancing | None | **HIGH** |
| **Paper Extraction** | Structured `PaperRecord` with verbatim `Evidence` spans (≤300 chars, page, section) | None; models do not extract paper metadata or scientific structures | **CRITICAL** |
| **Citation Verifier** | Programmatic rapidfuzz verification (exact -> fuzzy ≥90% -> adjacent page ±1) | None; verification is a procedural check of step execution booleans | **CRITICAL** |
| **Cited Chatbot** | POST `/api/research/chat` returning answers with grounded inline `[Paper, p.X]` citations and refusal when absent | None | **HIGH** |
| **Cross-Paper Matrix** | POST `/api/research/compare` comparing algorithms, datasets, metrics, limitations with citations in each cell | None | **HIGH** |
| **Contradictions** | POST `/api/research/contradictions` analyzing conflicting numbers on same dataset/task with comparability flag | Simulated demo string in S6 | **HIGH** |
| **Research Gaps** | POST `/api/research/gap-discovery` inferring stated limitations, collection coverage gaps, and opportunities | None | **HIGH** |
| **ADK Orchestration** | Exactly 4 agents (Root/Planner, Ingestion+Extraction, Synthesis, Report) with execution logging in `agent_runs` | 8 declarative agents listed in code but never invoked via runtime | **HIGH** |
| **Evaluation Suite** | Synthetic gold benchmark generation (`build_eval_set.py`) and metric runner (`run_eval.py` measuring Recall, MRR, Faithfulness) | None; only basic smoke tests exist | **HIGH** |
| **Reporting Engine** | POST `/api/reports/generate` producing cited Markdown, PDF, and DOCX documents | Simple procedural DOCX generator with fixed strings | **MEDIUM** |

---

## 2. Phase-by-Phase Detailed Requirements Gap

### Phase 1: Ingestion, Page-Aware Chunking, Data Model
- [ ] **PyMuPDF Ingestion:** Replace `pypdf` with `fitz` (PyMuPDF). Implement block-level reading sorted by vertical/horizontal coordinates to correctly parse two-column academic layouts.
- [ ] **Text Cleaning:** Clean hyphenated line breaks (`hy- \n phenation` -> `hyphenation`), decode ligatures (fi, fl, ffi), and strip recurring running headers and page numbers.
- [ ] **Page Coordinate Tracking:** Extract and store both `pdf_page_index` (0-based physical page) and `printed_page_label` (e.g., page 142 from pagination text).
- [ ] **Scanned Document Detection:** Detect pages with <50 characters of extractable text and mark document with `needs_ocr=True` without crashing.
- [ ] **Academic Section Detector:** Implement regex heuristic detector for sections: `abstract`, `introduction`, `related_work`, `methodology`, `experiments`, `results`, `discussion`, `limitations`, `conclusion`, `references`.
- [ ] **Parent-Child Chunker:** Create small child chunks (300-500 tokens, 15% overlap) for vector indexing that link to full parent section text for context expansion.
- [ ] **SQLAlchemy 2.0 & Alembic:** Create formal declarative models for `Document`, `DocumentPage`, `DocumentChunk`, `PaperRecord`, `Citation`, `Comparison`, `Contradiction`, `ResearchGap`, `Conversation`, `Message`, `AgentRun`, `Report`, `EvalResult`.
- [ ] **Dual Vector/Lexical Indexing:** Initialize ChromaDB persistent client per workspace; build and persist `rank_bm25` index files.

### Phase 2: Advanced RAG Retrieval
- [ ] **Hybrid RRF Algorithm:** Implement Reciprocal Rank Fusion:
  $$RRF(d) = \sum_{m \in \{dense, bm25\}} \frac{1}{60 + \text{rank}_m(d)}$$
- [ ] **Cross-Encoder Reranker:** Add `cross-encoder/ms-marco-MiniLM-L-6-v2` taking top-30 candidates from RRF and scoring down to top-8.
- [ ] **Gemini Query Planner:** Structured output prompt classifying queries (`single_paper_fact`, `multi_paper_comparison`, `aggregate`, `gap_analysis`, `methodology`), generating query rewrites and sub-queries.
- [ ] **Per-Paper Balanced Retrieval:** For comparison and aggregate questions, partition retrieval to guarantee top-$k$ representation per uploaded paper.
- [ ] **Section Boosting & Context Compression:** Boost limitation/discussion sections when queries target limitations or future work. Compress returned chunks within an explicit token budget.

### Phase 3: Structured Per-Paper Extraction
- [ ] **Pydantic `PaperRecord` Schema:** Models for research domain, objectives, methodology (approach, algorithms, datasets, preprocessing), evaluation (metrics, baselines, setup), experimental results (metric, value, dataset, conditions), strengths, limitations, future work, conclusions.
- [ ] **`Evidence` Data Contract:** Every field must wrap an `Evidence` object:
  ```python
  class Evidence(BaseModel):
      value: Any
      quote: Optional[str] = Field(None, max_length=300)
      pdf_page: int
      printed_page: Optional[str]
      section: str
  ```
- [ ] **Section-by-Section Gemini Extraction:** Extract data iteratively per section rather than passing the entire paper in a single prompt.
- [ ] **Idempotent Caching:** Cache extraction results by document SHA-256 hash in SQL to prevent re-extraction costs.

### Phase 4: Programmatic Citation Verification
- [ ] **Exact & Fuzzy Matcher:** Implement plain Python citation verifier:
  1. Normalize whitespace, hyphens, and ligatures in both quote and page text.
  2. Search for exact substring match on target page.
  3. If missing, compute `rapidfuzz.fuzz.partial_ratio(quote, page_text)` (threshold ≥90%).
  4. If missing, repeat on adjacent pages (`page - 1`, `page + 1`) to account for page offset errors.
- [ ] **Citation Status Tagging:** Output tagged as `verified`, `corrected_page`, or `unverified`. Unverified citations must be scrubbed from final user outputs.
- [ ] **`completion_check.py`:** Standalone code validating completeness of required sections, identifying missing citations, and emitting honest status verdicts.

### Phase 5: Cited Research Chatbot
- [ ] **POST `/api/research/chat` Endpoint:** Accept `query`, optional `document_ids`, and `conversation_id`.
- [ ] **Structured Claim Generation:** Gemini prompt returning claims with supporting chunk IDs:
  ```json
  [{"claim": "...", "supports": [{"chunk_id": "...", "quote": "..."}]}]
  ```
- [ ] **Inline Citation Renderer:** Format verified citations as `[Author/Title, p.X]`.
- [ ] **Refusal & Honest Fallback:** Explicit fallback response when retrieved chunks do not contain sufficient evidence:
  > *"Information not found in the uploaded papers. Searched sections: Methodology, Results."*

### Phase 6: Cross-Paper Synthesis (Comparison, Contradictions, Gaps)
- [ ] **Matrix Comparison (POST `/api/research/compare`):** Tabulate methodologies, datasets, benchmarks, and results across all papers in the workspace, with citations in every cell.
- [ ] **Contradiction Detection (POST `/api/research/contradictions`):** Identify pairs of papers with conflicting metrics or opposing conclusions on comparable datasets/tasks. Flag comparability criteria.
- [ ] **Research Gap Discovery (POST `/api/research/gap-discovery`):** Extract and cluster limitations across the corpus to identify under-explored methodology × dataset intersections. Classify into:
  1. `stated_limitation`
  2. `collection_coverage_gap`
  3. `inferred_opportunity`
- [ ] **Fixed Disclaimer Banner:** Include mandatory disclaimer that gaps are collection-specific hypotheses.

### Phase 7: Google ADK Orchestration
- [ ] **4-Agent Consolidation:**
  1. `RootPlannerAgent`
  2. `IngestionExtractionAgent`
  3. `SynthesisAgent`
  4. `ReportAgent`
- [ ] **Tool Conversion:** Convert retrieval, verification, and extraction pipelines into typed Google ADK tools.
- [ ] **Execution Logging:** Record every step run, agent name, latency, tool calls, and inputs/outputs to `agent_runs` table in SQLite.

### Phase 8: Evaluation & Benchmark Suite
- [ ] **Synthetic Dataset Generator (`build_eval_set.py`):** Generate 30–50 factual, multi-paper, and unanswerable question-chunk pairs from ingested papers into JSON.
- [ ] **Evaluation Harness (`run_eval.py`):** Calculate Precision@k, Recall@5/@10, MRR, nDCG, answer faithfulness (LLM judge), and citation validity rate across dense, BM25, and hybrid pipelines.
- [ ] **GET `/api/rag/evaluation` Endpoint:** Expose latest evaluation metrics.

### Phase 9: Reports & Comprehensive Documentation
- [ ] **Report Generator (POST `/api/reports/generate`):** Generate comprehensive research reports in Markdown, PDF, and DOCX formats with verified citations and statistics.
- [ ] **Documentation Suite:** System architecture, API documentation, RAG specification, agent workflow diagram, and testing report.

---

## 3. Dependency Deficit (Packages to Add)

The following packages must be added to `backend/requirements.txt`:
```text
# Document Extraction & Cleaning
pymupdf>=1.24.0
rapidfuzz>=3.8.0

# Database & ORM
sqlalchemy>=2.0.25
alembic>=1.13.1

# Vector Search & RAG
chromadb>=0.4.22
sentence-transformers>=2.3.1
rank-bm25>=0.2.2
langchain-text-splitters>=0.0.1

# PDF Report Generation
reportlab>=4.1.0
```

