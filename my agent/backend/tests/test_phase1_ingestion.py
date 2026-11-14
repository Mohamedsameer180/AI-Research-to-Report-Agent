"""
Phase 1 Ingestion, Page-Aware Chunking, and Data Model Test Suite.
Verifies PDF extraction (two-column, headers/footers, scanned pages),
zero-hallucination metadata, parent-child chunking, dual indexing (ChromaDB + BM25),
and workspace isolation.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
import pymupdf
from fastapi.testclient import TestClient

# Ensure backend and project root are in sys.path
_TEST_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _TEST_DIR.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
for p in [str(_BACKEND_DIR), str(_PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import app
from backend.app.config import settings
from backend.app.db.database import get_db, SessionLocal, init_db
from backend.app.db.models import Document, DocumentPage, DocumentChunk, PaperRecord
from backend.ingestion.pdf_extractor import (
    extract_pdf_pages,
    extract_pdf_data,
    clean_ligatures,
    fix_hyphenation,
    sort_blocks_two_column,
)
from backend.ingestion.section_detector import detect_section_heading, classify_text_section
from backend.ingestion.metadata import extract_doi, extract_year, extract_paper_metadata
from backend.ingestion.chunker import create_page_chunks, chunk_text_sliding_window, count_tokens
from backend.rag.embeddings import get_embedding_service
from backend.rag.vector_store import get_vector_store
from backend.rag.bm25_index import get_bm25_manager


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database schema is initialized for testing."""
    init_db()


def create_sample_two_column_pdf(output_path: Path) -> Path:
    """Create a synthetic 2-column academic PDF with header, footer, and tables."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)  # Standard Letter size

    # Running header at top
    page.insert_text(pymupdf.Point(50, 30), "IEEE TRANSACTIONS ON COMPUTING, VOL. 42, 2024", fontsize=8)

    # Title & Abstract (spanning full width)
    page.insert_text(pymupdf.Point(50, 70), "Attention Is What We Analyze", fontsize=16)
    page.insert_text(pymupdf.Point(50, 95), "Alice Researcher, Bob Scientist", fontsize=10)
    page.insert_text(
        pymupdf.Point(50, 120),
        "Abstract— Recent progress in neural architectures has revolutionized academic search. "
        "In this work, we propose a novel framework for document understanding with doi: 10.1145/3372278.3390678.",
        fontsize=9,
    )

    # Column 1 (Left column: x0=50, x1=280)
    col1_text = (
        "1. Introduction\n"
        "Modern deep learning has evolved rapidly over recent years.\n"
        "Traditional models suffer from high computa-\n"
        "tional complexity. Our method solves this.\n\n"
        "2. Methodology\n"
        "We introduce a dual-stream encoder for multi-modal text."
    )
    page.insert_textbox(pymupdf.Rect(50, 160, 280, 700), col1_text, fontsize=9)

    # Column 2 (Right column: x0=320, x1=550)
    col2_text = (
        "3. Experimental Results\n"
        "Our experiments demonstrate a 94.2% accuracy on benchmarks.\n"
        "Table 1 shows the performance across diverse datasets.\n\n"
        "4. Conclusion\n"
        "We presented a grounded evaluation framework for scientific literature."
    )
    page.insert_textbox(pymupdf.Rect(320, 160, 550, 700), col2_text, fontsize=9)

    # Running footer with page number
    page.insert_text(pymupdf.Point(300, 770), "15", fontsize=9)

    doc.save(str(output_path))
    doc.close()
    return output_path


def create_scanned_pdf(output_path: Path) -> Path:
    """Create a synthetic PDF with an image rect and zero selectable text."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    # Draw a shape instead of text to simulate scanned image
    shape = page.new_shape()
    shape.draw_rect(pymupdf.Rect(100, 100, 500, 700))
    shape.finish(fill=(0.9, 0.9, 0.9))
    shape.commit()
    doc.save(str(output_path))
    doc.close()
    return output_path


# --- TEST 1: PDF Extraction (Two-column, headers/footers, hyphenation) ---
def test_two_column_pdf_extraction(tmp_path):
    pdf_path = create_sample_two_column_pdf(tmp_path / "academic_sample.pdf")
    data = extract_pdf_data(pdf_path)

    assert data["page_count"] == 1
    assert data["needs_ocr"] is False
    assert len(data["pages"]) == 1

    page = data["pages"][0]
    # Check printed page label detected from footer
    assert page["printed_page_label"] == "15"

    text = page["text"]
    # Check header is stripped or present in metadata
    assert "IEEE TRANSACTIONS ON COMPUTING" not in text

    # Verify two-column reading order: Column 1 text must appear BEFORE Column 2 text
    intro_pos = text.find("1. Introduction")
    results_pos = text.find("3. Experimental Results")
    assert intro_pos != -1
    assert results_pos != -1
    assert intro_pos < results_pos, "Left column must be read before right column"

    # Verify hyphenation unwrapping (computa-\n tional -> computational)
    assert "computational" in text


# --- TEST 2: Scanned Document Detection ---
def test_scanned_pdf_detection(tmp_path):
    scanned_path = create_scanned_pdf(tmp_path / "scanned_doc.pdf")
    data = extract_pdf_data(scanned_path)

    assert data["page_count"] == 1
    assert data["needs_ocr"] is True, "Image-only page must be flagged as needing OCR"


# --- TEST 3: Section Detection ---
def test_section_detector():
    assert detect_section_heading("Abstract") == "abstract"
    assert detect_section_heading("1. INTRODUCTION") == "introduction"
    assert detect_section_heading("II. Related Work") == "related_work"
    assert detect_section_heading("3. Methodology") == "methodology"
    assert detect_section_heading("4. Experimental Results") == "results"
    assert detect_section_heading("5. Discussion") == "discussion"
    assert detect_section_heading("6. Limitations") == "limitations"
    assert detect_section_heading("7. Conclusion") == "conclusion"
    assert detect_section_heading("References") == "references"
    # Ordinary sentences should return None
    assert detect_section_heading("This is a normal paragraph describing our work.") is None


# --- TEST 4: Zero-Hallucination Metadata Extraction ---
def test_metadata_extraction():
    text_with_doi = "Paper published with DOI 10.1145/3372278.3390678 in 2024."
    assert extract_doi(text_with_doi) == "10.1145/3372278.3390678"
    assert extract_year(text_with_doi) == 2024

    # When no DOI is in text, it must strictly return None (NEVER fabricate)
    text_without_doi = "A study of neural networks in 2021 without any external identifier."
    assert extract_doi(text_without_doi) is None


# --- TEST 5: Section-Aware Page-Bounded Parent-Child Chunking ---
def test_parent_child_chunking(tmp_path):
    pdf_path = create_sample_two_column_pdf(tmp_path / "academic_sample.pdf")
    data = extract_pdf_data(pdf_path)
    pages = data["pages"]

    chunks = create_page_chunks(
        document_id="test_doc_001",
        filename="academic_sample.pdf",
        title="Attention Is What We Analyze",
        pages_data=pages,
        target_tokens=100,
        overlap_tokens=20,
    )

    assert len(chunks) >= 2
    # Check parent chunk exists
    parent_chunks = [c for c in chunks if c["is_parent"]]
    child_chunks = [c for c in chunks if not c["is_parent"]]
    assert len(parent_chunks) == 1
    assert len(child_chunks) >= 1

    parent = parent_chunks[0]
    assert parent["chunk_id"] == "test_doc_001_p1_parent"
    assert parent["parent_id"] is None
    assert parent["pdf_page"] == 1
    assert parent["printed_page"] == "15"

    for child in child_chunks:
        assert child["parent_id"] == parent["chunk_id"]
        assert child["pdf_page"] == 1
        assert child["printed_page"] == "15"
        # Check character spans map inside parent text
        span_text = child["text"]
        assert len(span_text) > 0


# --- TEST 6: ChromaDB Vector Store & Workspace Isolation ---
def test_vector_store_isolation():
    vs = get_vector_store()
    ws_a = "test_workspace_alpha"
    ws_b = "test_workspace_beta"

    # Sample chunks for workspace A
    chunks_a = [{
        "chunk_id": "chunk_a1",
        "parent_id": None,
        "document_id": "doc_a",
        "filename": "paper_a.pdf",
        "title": "Alpha Research",
        "pdf_page": 1,
        "printed_page": "1",
        "section": "methodology",
        "is_parent": False,
        "is_table": False,
        "char_start": 0,
        "char_end": 50,
        "text": "Alpha uses reinforcement learning with policy gradients.",
    }]

    # Dummy embedding (384 dimensions matching bge-small)
    dummy_vec = [0.05] * 384

    # Add to workspace A
    vs.add_chunks(ws_a, chunks_a, [dummy_vec])
    assert vs.count(ws_a) >= 1

    # Query workspace A -> must find it
    results_a = vs.query(ws_a, dummy_vec, n_results=5)
    assert len(results_a) >= 1
    assert results_a[0]["chunk_id"] == "chunk_a1"

    # Query workspace B -> must return ZERO (Workspace isolation)
    results_b = vs.query(ws_b, dummy_vec, n_results=5)
    assert len(results_b) == 0

    # Cleanup
    vs.delete_document(ws_a, "doc_a")
    assert vs.count(ws_a) == 0


# --- TEST 7: BM25 Indexing & Workspace Isolation ---
def test_bm25_index_and_search():
    bm25_mgr = get_bm25_manager()
    ws = "test_workspace_bm25"
    idx = bm25_mgr.get_index(ws)

    chunks = [
        {
            "chunk_id": "c1",
            "document_id": "doc_x",
            "text": "Transformer architecture relies on self-attention mechanisms.",
            "section": "introduction",
        },
        {
            "chunk_id": "c2",
            "document_id": "doc_y",
            "text": "Convolutional networks are optimized for spatial computer vision.",
            "section": "methodology",
        },
    ]

    idx.add_chunks(chunks)
    assert idx.count() >= 2

    # Keyword search for "self-attention"
    res = idx.search("self-attention", top_k=5)
    assert len(res) >= 1
    assert res[0]["chunk_id"] == "c1"

    # Deletion cascade test
    deleted = idx.delete_document("doc_x")
    assert deleted == 1
    res_after = idx.search("self-attention", top_k=5)
    assert len(res_after) == 0


# --- TEST 8: Full FastAPI Document Lifecycle (Upload, Status, Delete) ---
def test_document_lifecycle_api(tmp_path):
    client = TestClient(app)
    pdf_path = create_sample_two_column_pdf(tmp_path / "lifecycle_test.pdf")

    workspace = "test_workspace_lifecycle"
    user = "test_user_01"

    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("lifecycle_test.pdf", f, "application/pdf")},
            data={"workspace_id": workspace, "user_id": user},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    doc_id = data["id"]
    assert data["processing_status"] in ("completed", "queued")
    assert data["version"] == 1

    # Check status endpoint
    status_resp = client.get(f"/api/documents/{doc_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["processing_status"] == "completed"
    assert status_data["page_count"] == 1
    assert status_data["chunk_count"] > 0
    assert status_data["needs_ocr"] is False

    # Check list documents
    list_resp = client.get(f"/api/documents?workspace_id={workspace}")
    assert list_resp.status_code == 200
    docs = list_resp.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)

    # Check re-uploading the same file creates version 2 (dedup / versioning)
    with open(pdf_path, "rb") as f:
        reupload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("lifecycle_test.pdf", f, "application/pdf")},
            data={"workspace_id": workspace, "user_id": user},
        )
    assert reupload_resp.status_code == 200
    reupload_data = reupload_resp.json()
    assert reupload_data["version"] == 2

    # Delete first document
    del_resp = client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 200

    # Verify deleted
    get_del = client.get(f"/api/documents/{doc_id}")
    assert get_del.status_code == 404
