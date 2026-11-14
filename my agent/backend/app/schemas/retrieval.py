"""
Pydantic schemas for Hybrid Retrieval operations.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Search query")
    workspace_id: str = Field("default_workspace", description="Workspace ID for scoping")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")
    candidate_k: int = Field(20, ge=5, le=100, description="Candidates retrieved before reranking")
    sections: Optional[List[str]] = Field(None, description="Optional filter by academic sections")
    document_ids: Optional[List[str]] = Field(None, description="Optional filter by document IDs")
    expand_parent: bool = Field(False, description="Whether to include parent chunk section context")
    use_reranker: bool = Field(True, description="Whether to apply cross-encoder reranker")


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    title: str
    pdf_page: int
    printed_page: str
    section: str
    text: str
    parent_text: Optional[str] = None
    char_start: int = 0
    char_end: int = 0
    score: float = 0.0
    rerank_score: Optional[float] = None
    rrf_score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    workspace_id: str
    total_found: int
    results: List[RetrievedChunk]

