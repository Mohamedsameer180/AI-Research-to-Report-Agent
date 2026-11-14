"""
Retrieval API endpoint for TP01 Research Platform.
Provides hybrid semantic-lexical search with cross-encoder reranking.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.retrieval import SearchRequest, SearchResponse, RetrievedChunk
from backend.rag.retriever import get_hybrid_retriever

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=SearchResponse)
def hybrid_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
):
    """
    Perform hybrid retrieval (ChromaDB dense + BM25 sparse + Cross-Encoder rerank)
    strictly scoped to the specified workspace.
    """
    retriever = get_hybrid_retriever()

    results = retriever.search(
        query=request.query,
        workspace_id=request.workspace_id,
        top_k=request.top_k,
        candidate_k=request.candidate_k,
        sections=request.sections,
        document_ids=request.document_ids,
        expand_parent=request.expand_parent,
        use_reranker=request.use_reranker,
        db=db,
    )

    formatted_results = []
    for r in results:
        meta = r.get("metadata", {})
        formatted_results.append(
            RetrievedChunk(
                chunk_id=r.get("chunk_id", ""),
                document_id=meta.get("document_id", ""),
                filename=meta.get("filename", ""),
                title=meta.get("title", ""),
                pdf_page=int(meta.get("pdf_page", 1)),
                printed_page=str(meta.get("printed_page", "1")),
                section=meta.get("section", "body"),
                text=r.get("text", ""),
                parent_text=r.get("parent_text"),
                char_start=int(meta.get("char_start", 0)),
                char_end=int(meta.get("char_end", 0)),
                score=float(r.get("score", 0.0)),
                rerank_score=r.get("rerank_score"),
                rrf_score=r.get("rrf_score"),
            )
        )

    return SearchResponse(
        query=request.query,
        workspace_id=request.workspace_id,
        total_found=len(formatted_results),
        results=formatted_results,
    )
