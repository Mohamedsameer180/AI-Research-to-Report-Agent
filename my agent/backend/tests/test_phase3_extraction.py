"""Phase 3 Test Suite: Structured Per-Paper Extraction & Grounded Citations.

Validates:
1. PaperRecordSchema and EvidenceItem Pydantic schema validation.
2. Programmatic Citation Verification:
   - Exact substring match on claimed page -> verified
   - Whitespace, ligature, and hyphenation normalization
   - Adjacent page offset detection (+-1) -> corrected_page
   - Fabricated quote detection -> unverified, purged to null (no hallucination)
3. Completion and quality checking (complete, partial, failed).
4. Section-by-section extraction pipeline and distinct ModelAnalysis.
5. Idempotent caching by file_hash.
6. API routes:
   - POST /api/research/analyze
   - GET /api/documents/{id}/record
   - Workspace multi-tenant isolation
"""

import os
import sys
import uuid
import pytest
from pathlib import Path

# Ensure backend and project root are in sys.path
_TEST_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _TEST_DIR.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
for p in [str(_BACKEND_DIR), str(_PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient

from backend.main import app
from backend.app.db.database import get_db_context, init_db
from backend.app.db.models import Document, DocumentChunk, DocumentPage, PaperRecord, Citation
from backend.extraction.paper_schema import (
    EvidenceItem,
    MethodologyDetails,
    EvaluationDetails,
    ResultFinding,
    ModelAnalysis,
    PaperRecordSchema,
)
from backend.verification.citation_verifier import (
    CitationVerifier,
    normalize_text,
)
from backend.verification.completion_check import (
    evaluate_paper_record_completion,
)
from backend.extraction.paper_extractor import PaperExtractor


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()


def test_schema_validity():
    """Validates Pydantic schema construction, type safety, and serialization."""
    ev = EvidenceItem[str](
        value="Self-Attention Mechanism",
        quote="The transformer relies entirely on an attention mechanism.",
        pdf_page=3,
        printed_page="145",
        section="methodology",
        status="verified",
        fuzzy_score=100.0,
    )
    assert ev.value == "Self-Attention Mechanism"
    assert ev.pdf_page == 3
    assert ev.status == "verified"

    record = PaperRecordSchema(
        record_id="rec_test_001",
        document_id="doc_test_001",
        workspace_id="ws_test",
        title="Attention Is All You Need",
        methodology=MethodologyDetails(
            approach=ev,
            algorithms=[ev],
        ),
        results=[
            ResultFinding(
                metric="BLEU",
                value="28.4 BLEU",
                quote="On the WMT 2014 English-to-German task, the model establishes a new SOTA of 28.4 BLEU.",
                pdf_page=7,
                section="results",
                status="verified",
            )
        ],
        model_analysis=ModelAnalysis(
            contributions=["Introduces Transformer architecture without recurrence."],
            strengths=["High parallelizability."],
            weaknesses=["Quadratic memory complexity with sequence length."],
        ),
    )

    dumped = record.model_dump()
    assert dumped["title"] == "Attention Is All You Need"
    assert dumped["results"][0]["metric"] == "BLEU"
    assert len(dumped["model_analysis"]["contributions"]) == 1


def test_citation_verifier_exact_and_normalization():
    """Tests exact match, ligatures, hyphenated line-wraps, and whitespace normalization."""
    verifier = CitationVerifier(fuzzy_threshold=90.0)

    # Document page with typographic ligatures and hyphenation
    page_text = (
        "In this work, we introduce the trans-\nformer architecture, which achieves "
        "a scientific break-through on machine translation with ﬁne-grained attention."
    )
    pages_dict = {1: page_text}

    # Quote with standard ASCII letters ('fi' instead of 'ﬁ', joined hyphenation)
    clean_quote = "we introduce the transformer architecture, which achieves a scientific breakthrough"

    result = verifier.verify_quote(
        quote=clean_quote,
        claimed_page=1,
        pages_dict=pages_dict,
    )

    assert result.is_valid is True
    assert result.status == "verified"
    assert result.matched_page == 1
    assert result.fuzzy_score >= 90.0


def test_citation_verifier_adjacent_page_correction():
    """Tests that a quote on an adjacent page (+-1) is detected and page corrected."""
    verifier = CitationVerifier(fuzzy_threshold=90.0)

    pages_dict = {
        1: "Title: Deep Learning Survey. Introduction to neural networks and gradient descent.",
        2: "Our methodology employs a dual-encoder transformer fine-tuned on MS-MARCO passages.",
        3: "Conclusions and future research opportunities.",
    }

    # Claimed page is incorrectly 1, but text is on page 2
    quote = "methodology employs a dual-encoder transformer fine-tuned on MS-MARCO"

    result = verifier.verify_quote(
        quote=quote,
        claimed_page=1,
        pages_dict=pages_dict,
    )

    assert result.is_valid is True
    assert result.status == "corrected_page"
    assert result.matched_page == 2
    assert result.fuzzy_score >= 90.0


def test_citation_verifier_fabricated_quote_purged_to_null():
    """Tests that a hallucinated/fabricated quote is marked unverified and purged to null."""
    verifier = CitationVerifier(fuzzy_threshold=90.0)

    pages_dict = {
        1: "The model was trained for 10 epochs using AdamW optimizer with a learning rate of 1e-4.",
    }

    # Fabricated claim not in the text
    fake_quote = "Our breakthrough quantum algorithm solved NP-hard protein folding in 3 milliseconds."

    result = verifier.verify_quote(
        quote=fake_quote,
        claimed_page=1,
        pages_dict=pages_dict,
    )

    assert result.is_valid is False
    assert result.status == "unverified"
    assert result.fuzzy_score < 70.0

    # Test purging via verify_evidence_item
    item = EvidenceItem[str](
        value="Quantum Protein Folding",
        quote=fake_quote,
        pdf_page=1,
    )
    verified_item = verifier.verify_evidence_item(item, pages_dict, purge_unverified=True)

    assert verified_item.status == "unverified"
    assert verified_item.value is None  # Zero hallucination guarantee: null instead of invention


def test_completion_check_verdict():
    """Tests completion quality check for complete, partial, and failed states."""
    # Complete record
    good_record = PaperRecordSchema(
        record_id="rec_comp_001",
        document_id="doc_001",
        workspace_id="ws_test",
        title="Neural Architecture Search",
        objective=EvidenceItem(value="Automate network design", quote="automate network design", pdf_page=1, status="verified"),
        methodology=MethodologyDetails(
            approach=EvidenceItem(value="Reinforcement Learning controller", quote="RL controller", pdf_page=2, status="verified"),
        ),
        results=[
            ResultFinding(metric="Accuracy", value="97.4%", quote="achieves 97.4% top-1 accuracy", pdf_page=4, status="verified")
        ],
        citation_stats={"total_claims": 3, "verified": 3, "corrected_page": 0, "unverified": 0},
    )

    verdict_complete = evaluate_paper_record_completion(good_record, min_citation_rate=0.7)
    assert verdict_complete.status == "complete"
    assert verdict_complete.is_acceptable is True
    assert len(verdict_complete.missing_sections) == 0

    # Incomplete record (missing methodology and results)
    bad_record = PaperRecordSchema(
        record_id="rec_comp_002",
        document_id="doc_002",
        workspace_id="ws_test",
        title=None,
        objective=None,
        citation_stats={"total_claims": 1, "verified": 0, "corrected_page": 0, "unverified": 1},
    )

    verdict_failed = evaluate_paper_record_completion(bad_record, min_citation_rate=0.7)
    assert verdict_failed.status == "failed"
    assert verdict_failed.is_acceptable is False
    assert "objective" in verdict_failed.missing_sections


def test_extractor_pipeline_and_idempotent_cache():
    """Tests end-to-end extraction from database document, verification, and caching."""
    ws_id = f"test_ws_extract_{uuid.uuid4().hex[:8]}"
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    file_hash = f"hash_{uuid.uuid4().hex[:16]}"

    with get_db_context() as db:
        doc = Document(
            document_id=doc_id,
            workspace_id=ws_id,
            user_id="test_user",
            filename="empirical_transformer_eval.pdf",
            file_path="dummy_path.pdf",
            file_hash=file_hash,
            page_count=3,
            status="ready",
        )
        db.add(doc)

        # Add pages with verbatim factual spans
        p1 = DocumentPage(
            page_id=f"{doc_id}_p1",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page_index=0,
            printed_page_label="1",
            raw_text=(
                "Empirical Evaluation of Transformer Architectures. "
                "In this paper, we propose a cross-attention transformer framework "
                "to address the problem of quadratic memory bottleneck in deep learning."
            ),
        )
        p2 = DocumentPage(
            page_id=f"{doc_id}_p2",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page_index=1,
            printed_page_label="2",
            raw_text=(
                "Our methodology incorporates an efficient attention mechanism. "
                "The algorithm relies on Adam optimizer with cosine learning rate decay. "
                "We benchmarked our model on the ImageNet dataset."
            ),
        )
        p3 = DocumentPage(
            page_id=f"{doc_id}_p3",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page_index=2,
            printed_page_label="3",
            raw_text=(
                "Experimental Results: The model achieved 88.5% top-1 accuracy on ImageNet. "
                "A notable limitation of our approach is the sensitivity to hyperparameter initialization. "
                "In conclusion, our method demonstrates competitive efficiency."
            ),
        )
        db.add_all([p1, p2, p3])

        # Add document chunks mapped to sections
        c1 = DocumentChunk(
            chunk_id=f"chk_{doc_id}_1",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page=1,
            printed_page="1",
            section="introduction",
            text=p1.raw_text,
        )
        c2 = DocumentChunk(
            chunk_id=f"chk_{doc_id}_2",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page=2,
            printed_page="2",
            section="methodology",
            text=p2.raw_text,
        )
        c3 = DocumentChunk(
            chunk_id=f"chk_{doc_id}_3",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page=3,
            printed_page="3",
            section="results",
            text=p3.raw_text,
        )
        db.add_all([c1, c2, c3])
        db.commit()

    extractor = PaperExtractor()

    # First run: performs extraction & DB persistence
    record1 = extractor.extract_from_document(doc_id, ws_id, force_refresh=True)

    assert record1.document_id == doc_id
    assert record1.objective is not None
    assert record1.objective.value is not None
    assert record1.objective.status in {"verified", "corrected_page"}
    assert record1.model_analysis is not None
    assert len(record1.model_analysis.contributions) >= 1
    assert record1.citation_stats["verified"] >= 1

    # Check that citations were persisted in citations table
    with get_db_context() as db:
        cits = db.query(Citation).filter(
            Citation.document_id == doc_id,
            Citation.workspace_id == ws_id,
        ).all()
        assert len(cits) >= 1
        assert any(c.status in {"verified", "corrected_page"} for c in cits)

    # Second run without force_refresh: should hit cache idempotently
    record2 = extractor.extract_from_document(doc_id, ws_id, force_refresh=False)
    assert record2.file_hash == file_hash
    assert record2.citation_stats.get("cached") is True


def test_api_analyze_and_record_endpoints():
    """Tests POST /api/research/analyze and GET /api/documents/{id}/record."""
    client = TestClient(app)
    ws_id = f"test_api_extract_{uuid.uuid4().hex[:8]}"
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

    with get_db_context() as db:
        doc = Document(
            document_id=doc_id,
            workspace_id=ws_id,
            user_id="local_user",
            filename="api_test_paper.pdf",
            file_path="dummy.pdf",
            file_hash=f"hash_{uuid.uuid4().hex[:12]}",
            page_count=2,
            status="ready",
        )
        db.add(doc)

        p1 = DocumentPage(
            page_id=f"{doc_id}_p1",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page_index=0,
            printed_page_label="1",
            raw_text="In this paper, we propose a graph neural network for molecular discovery.",
        )
        p2 = DocumentPage(
            page_id=f"{doc_id}_p2",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page_index=1,
            printed_page_label="2",
            raw_text="The model achieved an ROC-AUC of 0.92 on the Tox21 dataset.",
        )
        db.add_all([p1, p2])

        c1 = DocumentChunk(
            chunk_id=f"chk_{doc_id}_1",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page=1,
            section="introduction",
            text=p1.raw_text,
        )
        c2 = DocumentChunk(
            chunk_id=f"chk_{doc_id}_2",
            document_id=doc_id,
            workspace_id=ws_id,
            pdf_page=2,
            section="results",
            text=p2.raw_text,
        )
        db.add_all([c1, c2])
        db.commit()

    # 1. POST /api/research/analyze
    res = client.post(
        "/api/research/analyze",
        json={
            "document_id": doc_id,
            "workspace_id": ws_id,
            "force_refresh": True,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["document_id"] == doc_id
    assert data["workspace_id"] == ws_id
    assert data["objective"]["value"] is not None

    # 2. GET /api/documents/{id}/record
    res_get = client.get(
        f"/api/documents/{doc_id}/record",
        params={"workspace_id": ws_id},
    )
    assert res_get.status_code == 200, res_get.text
    record_data = res_get.json()
    assert record_data["document_id"] == doc_id

    # 3. Multi-tenant isolation test: accessing from different workspace returns 404
    res_iso = client.get(
        f"/api/documents/{doc_id}/record",
        params={"workspace_id": "isolated_other_workspace"},
    )
    assert res_iso.status_code == 404
