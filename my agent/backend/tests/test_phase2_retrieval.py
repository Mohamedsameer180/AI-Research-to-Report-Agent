"""
Phase 2 Test Suite: Hybrid Retrieval & Cross-Encoder Reranker.
Verifies query expansion, Reciprocal Rank Fusion, Cross-Encoder reranking,
section filtering, parent chunk expansion, workspace isolation, and the API search endpoint.
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend and project root are in sys.path
_TEST_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _TEST_DIR.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
for p in [str(_BACKEND_DIR), str(_PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import app
from backend.app.db.database import SessionLocal, init_db
from backend.app.db.models import Document, DocumentChunk
from backend.rag.query_expansion import generate_multi_queries, expand_acronyms, generate_keyword_query
from backend.rag.reranker import get_cross_encoder_reranker
from backend.rag.retriever import get_hybrid_retriever, compute_rrf_fusion
from backend.rag.embeddings import get_embedding_service
from backend.rag.vector_store import get_vector_store
from backend.rag.bm25_index import get_bm25_manager


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()


# --- TEST 1: Query Expansion ---
def test_query_expansion():
    # Acronym expansion
    acronym_query = "What are the limitations of RAG and LLMs in healthcare?"
    expanded = expand_acronyms(acronym_query)
    assert "retrieval augmented generation" in expanded
    assert "large language models" in expanded

    # Keyword extraction
    keyword_q = generate_keyword_query("What are the empirical results in this study?")
    assert "empirical results" in keyword_q
    assert "What are the" not in keyword_q

    # Multi-query variations
    variations = generate_multi_queries("How does attention scaling affect memory?")
    assert len(variations) >= 2
    assert variations[0] == "How does attention scaling affect memory?"


# --- TEST 2: Reciprocal Rank Fusion (RRF) ---
def test_rrf_fusion():
    list_a = [
        {"chunk_id": "c1", "text": "Chunk 1"},
        {"chunk_id": "c2", "text": "Chunk 2"},
    ]
    list_b = [
        {"chunk_id": "c2", "text": "Chunk 2"},
        {"chunk_id": "c3", "text": "Chunk 3"},
    ]

    fused = compute_rrf_fusion([list_a, list_b], k=60)
    # c2 appears in both lists, so its combined RRF score must be highest
    assert fused[0]["chunk_id"] == "c2"
    assert fused[0]["rrf_score"] > fused[1]["rrf_score"]


# --- TEST 3: Cross-Encoder Reranker ---
def test_cross_encoder_reranker():
    reranker = get_cross_encoder_reranker()
    query = "transformer self-attention mechanism"
    candidates = [
        {"chunk_id": "c_irrelevant", "text": "The university library opens at 9 AM and serves coffee."},
        {"chunk_id": "c_relevant", "text": "The transformer self-attention mechanism computes pairwise token affinities using query, key, and value matrices."},
    ]

    reranked = reranker.rerank(query=query, candidates=candidates, top_k=2)
    assert len(reranked) == 2
    # The relevant document must be ranked #1 with a higher score
    assert reranked[0]["chunk_id"] == "c_relevant"
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]


# --- TEST 4: Hybrid Retriever Pipeline & Dual Retrieval ---
def test_hybrid_retriever_pipeline():
    ws = "test_workspace_hybrid_p2"
    vs = get_vector_store()
    bm25_mgr = get_bm25_manager()
    embedder = get_embedding_service()

    chunks = [
        {
            "chunk_id": "h_c1",
            "document_id": "doc_h1",
            "filename": "deep_learning.pdf",
            "title": "Deep Learning Principles",
            "pdf_page": 2,
            "printed_page": "2",
            "section": "methodology",
            "text": "Gradient descent optimizes neural network parameters via backpropagation.",
            "char_start": 0,
            "char_end": 75,
            "is_parent": False,
            "is_table": False,
        },
        {
            "chunk_id": "h_c2",
            "document_id": "doc_h2",
            "filename": "vision.pdf",
            "title": "Computer Vision",
            "pdf_page": 5,
            "printed_page": "5",
            "section": "results",
            "text": "ResNet-50 achieves 76.5% top-1 accuracy on ImageNet classification.",
            "char_start": 0,
            "char_end": 70,
            "is_parent": False,
            "is_table": False,
        },
    ]

    # Index into ChromaDB
    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_texts(texts)
    vs.add_chunks(ws, chunks, embeddings)

    # Index into BM25
    bm25_idx = bm25_mgr.get_index(ws)
    bm25_idx.add_chunks(chunks)

    retriever = get_hybrid_retriever()
    results = retriever.search(
        query="backpropagation gradient descent neural network",
        workspace_id=ws,
        top_k=2,
    )

    assert len(results) >= 1
    top_result = results[0]
    assert top_result["chunk_id"] == "h_c1"
    assert "rrf_score" in top_result
    assert "rerank_score" in top_result

    # Cleanup
    vs.delete_document(ws, "doc_h1")
    vs.delete_document(ws, "doc_h2")


# --- TEST 5: Section Filtering ---
def test_section_filtering():
    ws = "test_workspace_section_filter"
    vs = get_vector_store()
    bm25_mgr = get_bm25_manager()
    embedder = get_embedding_service()

    chunks = [
        {
            "chunk_id": "sec_intro",
            "document_id": "doc_sec",
            "filename": "paper.pdf",
            "title": "A Study",
            "pdf_page": 1,
            "printed_page": "1",
            "section": "introduction",
            "text": "Introduction to neural network architectures and history.",
            "char_start": 0,
            "char_end": 60,
            "is_parent": False,
            "is_table": False,
        },
        {
            "chunk_id": "sec_meth",
            "document_id": "doc_sec",
            "filename": "paper.pdf",
            "title": "A Study",
            "pdf_page": 3,
            "printed_page": "3",
            "section": "methodology",
            "text": "Methodology detailing neural network architectures and layer sizes.",
            "char_start": 0,
            "char_end": 70,
            "is_parent": False,
            "is_table": False,
        },
    ]

    embeddings = embedder.embed_texts([c["text"] for c in chunks])
    vs.add_chunks(ws, chunks, embeddings)
    bm25_mgr.get_index(ws).add_chunks(chunks)

    retriever = get_hybrid_retriever()
    # Filter strictly for "methodology"
    results = retriever.search(
        query="neural network architectures",
        workspace_id=ws,
        sections=["methodology"],
        top_k=5,
    )

    assert len(results) >= 1
    for r in results:
        assert r["metadata"]["section"] == "methodology"

    # Cleanup
    vs.delete_document(ws, "doc_sec")


# --- TEST 6: Parent Chunk Expansion ---
def test_parent_chunk_expansion():
    db = SessionLocal()
    ws = "test_workspace_parent_exp"

    # Insert parent chunk and child chunk in SQLite
    doc_id = "doc_parent_test"
    parent_id = "parent_chunk_001"
    child_id = "child_chunk_001"

    # Ensure document row exists for FK integrity
    existing_doc = db.query(Document).filter(Document.document_id == doc_id).first()
    if not existing_doc:
        doc = Document(
            document_id=doc_id,
            workspace_id=ws,
            user_id="test_user",
            filename="parent_test.pdf",
            file_path="/dummy/path",
            file_hash="dummy_hash_parent",
        )
        db.add(doc)
        db.commit()

    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()

    parent_chunk = DocumentChunk(
        chunk_id=parent_id,
        parent_id=None,
        document_id=doc_id,
        workspace_id=ws,
        pdf_page=4,
        printed_page="4",
        section="methodology",
        text="Full section text containing extensive methodological context and equations.",
        is_parent=True,
    )
    child_chunk = DocumentChunk(
        chunk_id=child_id,
        parent_id=parent_id,
        document_id=doc_id,
        workspace_id=ws,
        pdf_page=4,
        printed_page="4",
        section="methodology",
        text="Child chunk with specific equation reference.",
        is_parent=False,
    )
    db.add(parent_chunk)
    db.add(child_chunk)
    db.commit()

    # Index child chunk into ChromaDB and BM25
    vs = get_vector_store()
    embedder = get_embedding_service()
    bm25_mgr = get_bm25_manager()

    child_dict = {
        "chunk_id": child_id,
        "parent_id": parent_id,
        "document_id": doc_id,
        "filename": "parent_test.pdf",
        "title": "Parent Test Paper",
        "pdf_page": 4,
        "printed_page": "4",
        "section": "methodology",
        "text": child_chunk.text,
        "char_start": 0,
        "char_end": len(child_chunk.text),
        "is_parent": False,
        "is_table": False,
    }
    vec = embedder.embed_texts([child_chunk.text])
    vs.add_chunks(ws, [child_dict], vec)
    bm25_mgr.get_index(ws).add_chunks([child_dict])

    retriever = get_hybrid_retriever()
    results = retriever.search(
        query="equation reference",
        workspace_id=ws,
        top_k=1,
        expand_parent=True,
        db=db,
    )

    assert len(results) == 1
    res = results[0]
    assert res["chunk_id"] == child_id
    # Parent text must be expanded
    assert "Full section text containing extensive methodological context" in res["parent_text"]

    # Cleanup
    vs.delete_document(ws, doc_id)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
    db.query(Document).filter(Document.document_id == doc_id).delete()
    db.commit()
    db.close()


# --- TEST 7: Workspace Scoping (Isolation) ---
def test_workspace_retrieval_isolation():
    ws_1 = "test_workspace_isolation_1"
    ws_2 = "test_workspace_isolation_2"

    vs = get_vector_store()
    embedder = get_embedding_service()
    bm25_mgr = get_bm25_manager()

    chunk_1 = {
        "chunk_id": "iso_c1",
        "parent_id": None,
        "document_id": "doc_iso_1",
        "filename": "iso1.pdf",
        "title": "Secret Project 1",
        "pdf_page": 1,
        "printed_page": "1",
        "section": "introduction",
        "text": "Quantum cryptographic key distribution secret protocol.",
        "char_start": 0,
        "char_end": 50,
        "is_parent": False,
        "is_table": False,
    }

    vec = embedder.embed_texts([chunk_1["text"]])
    vs.add_chunks(ws_1, [chunk_1], vec)
    bm25_mgr.get_index(ws_1).add_chunks([chunk_1])

    retriever = get_hybrid_retriever()

    # Query in Workspace 1 -> finds result
    res_1 = retriever.search("quantum cryptographic", workspace_id=ws_1, top_k=5)
    assert len(res_1) >= 1

    # Query in Workspace 2 -> MUST return 0 results
    res_2 = retriever.search("quantum cryptographic", workspace_id=ws_2, top_k=5)
    assert len(res_2) == 0

    # Cleanup
    vs.delete_document(ws_1, "doc_iso_1")


# --- TEST 8: Full API Search Endpoint ---
def test_api_search_endpoint():
    client = TestClient(app)
    ws = "test_workspace_api_search"

    # Pre-index a chunk
    vs = get_vector_store()
    embedder = get_embedding_service()
    bm25_mgr = get_bm25_manager()

    chunk = {
        "chunk_id": "api_search_chunk",
        "parent_id": None,
        "document_id": "doc_api_search",
        "filename": "api_paper.pdf",
        "title": "API Search Paper",
        "pdf_page": 10,
        "printed_page": "10",
        "section": "results",
        "text": "Our model achieved 98.4% precision on standard entity resolution.",
        "char_start": 0,
        "char_end": 65,
        "is_parent": False,
        "is_table": False,
    }

    vec = embedder.embed_texts([chunk["text"]])
    vs.add_chunks(ws, [chunk], vec)
    bm25_mgr.get_index(ws).add_chunks([chunk])

    response = client.post(
        "/api/retrieval/search",
        json={
            "query": "entity resolution precision",
            "workspace_id": ws,
            "top_k": 3,
            "expand_parent": False,
            "use_reranker": True,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["query"] == "entity resolution precision"
    assert data["workspace_id"] == ws
    assert data["total_found"] >= 1

    match = data["results"][0]
    assert match["chunk_id"] == "api_search_chunk"
    assert match["pdf_page"] == 10
    assert match["section"] == "results"
    assert match["rerank_score"] is not None

    # Cleanup
    vs.delete_document(ws, "doc_api_search")
