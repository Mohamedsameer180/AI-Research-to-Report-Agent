"""
Hybrid Retriever for TP01 Research Platform.
Combines Dense Semantic Search (ChromaDB) + Sparse Lexical Search (BM25Plus),
fused with Reciprocal Rank Fusion (RRF), reranked by Cross-Encoder,
with optional Parent Chunk Expansion for full context.
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db.models import DocumentChunk
from backend.rag.embeddings import get_embedding_service
from backend.rag.vector_store import get_vector_store
from backend.rag.bm25_index import get_bm25_manager
from backend.rag.query_expansion import generate_multi_queries
from backend.rag.reranker import get_cross_encoder_reranker

logger = logging.getLogger("tp01.rag.retriever")

RRF_K = 60  # Standard RRF constant


def compute_rrf_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    weights: Optional[List[float]] = None,
    k: int = RRF_K,
) -> List[Dict[str, Any]]:
    """
    Computes Reciprocal Rank Fusion over multiple ranked result sets.
    RRF score = sum_{list} weight * (1 / (k + rank))
    """
    if not ranked_lists:
        return []

    if weights is None:
        weights = [1.0] * len(ranked_lists)

    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    for l_idx, ranked in enumerate(ranked_lists):
        w = weights[l_idx]
        for rank, item in enumerate(ranked):
            cid = item["chunk_id"]
            rrf_delta = w / (k + (rank + 1))
            scores[cid] = scores.get(cid, 0.0) + rrf_delta

            if cid not in doc_map:
                doc_map[cid] = item.copy()

    # Re-score documents with aggregated RRF score
    merged = []
    for cid, total_score in scores.items():
        doc = doc_map[cid]
        doc["rrf_score"] = total_score
        merged.append(doc)

    merged.sort(key=lambda x: x["rrf_score"], reverse=True)
    return merged


class HybridRetriever:
    def __init__(
        self,
        embedder=None,
        vector_store=None,
        bm25_manager=None,
        reranker=None,
    ):
        self.embedder = embedder or get_embedding_service()
        self.vector_store = vector_store or get_vector_store()
        self.bm25_manager = bm25_manager or get_bm25_manager()
        self.reranker = reranker or get_cross_encoder_reranker()

    def search(
        self,
        query: str,
        workspace_id: str,
        top_k: int = 5,
        candidate_k: int = 20,
        sections: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
        expand_parent: bool = False,
        use_reranker: bool = True,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes complete hybrid retrieval pipeline:
        1. Multi-query expansion
        2. Dual retrieval (Dense ChromaDB + Sparse BM25Plus)
        3. Reciprocal Rank Fusion
        4. Cross-Encoder reranking
        5. Parent chunk context expansion
        """
        if not query.strip() or not workspace_id:
            return []

        # Build metadata filter if specified
        where_filter = None
        if document_ids and len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}

        # 1. Multi-query generation
        queries = generate_multi_queries(query, max_variations=3)

        # 2. Retrieve candidates across each query variation
        ranked_lists = []
        weights = []

        bm25_idx = self.bm25_manager.get_index(workspace_id)

        for q_idx, q_text in enumerate(queries):
            # Primary query receives higher weight than expansions
            weight = 1.0 if q_idx == 0 else 0.7

            # Dense retrieval
            q_emb = self.embedder.embed_query(q_text)
            dense_results = self.vector_store.query(
                workspace_id=workspace_id,
                query_embedding=q_emb,
                n_results=candidate_k,
                where_filter=where_filter,
            )
            if dense_results:
                ranked_lists.append(dense_results)
                weights.append(weight * 1.0)

            # Sparse lexical retrieval
            sparse_results = bm25_idx.search(
                query=q_text,
                top_k=candidate_k,
                where_filter=where_filter,
            )
            if sparse_results:
                ranked_lists.append(sparse_results)
                weights.append(weight * 0.8)

        if not ranked_lists:
            return []

        # 3. Reciprocal Rank Fusion (RRF)
        fused = compute_rrf_fusion(ranked_lists, weights=weights, k=RRF_K)

        # Apply in-memory section and multi-document filtering if specified
        filtered = []
        for item in fused:
            meta = item.get("metadata", {})
            if sections and meta.get("section") not in sections:
                continue
            if document_ids and meta.get("document_id") not in document_ids:
                continue
            filtered.append(item)

        candidates = filtered[:candidate_k]
        if not candidates:
            return []

        # 4. Cross-Encoder Reranking
        if use_reranker and candidates:
            reranked = self.reranker.rerank(query=query, candidates=candidates, top_k=top_k)
        else:
            reranked = candidates[:top_k]

        # 5. Parent Chunk Expansion
        if expand_parent and db is not None:
            for item in reranked:
                meta = item.get("metadata", {})
                parent_id = meta.get("parent_id")
                if parent_id:
                    parent = db.query(DocumentChunk).filter(DocumentChunk.chunk_id == parent_id).first()
                    if parent:
                        item["parent_text"] = parent.text
                    else:
                        item["parent_text"] = item.get("text", "")
                else:
                    item["parent_text"] = item.get("text", "")

        return reranked


_HYBRID_RETRIEVER_INSTANCE = None


def get_hybrid_retriever() -> HybridRetriever:
    global _HYBRID_RETRIEVER_INSTANCE
    if _HYBRID_RETRIEVER_INSTANCE is None:
        _HYBRID_RETRIEVER_INSTANCE = HybridRetriever()
    return _HYBRID_RETRIEVER_INSTANCE
