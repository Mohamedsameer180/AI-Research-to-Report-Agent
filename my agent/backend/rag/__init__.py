"""
RAG package for TP01 Research Platform.
"""
from backend.rag.embeddings import EmbeddingService, get_embedding_service
from backend.rag.vector_store import ChromaVectorStore, get_vector_store
from backend.rag.bm25_index import BM25IndexManager, get_bm25_manager
from backend.rag.query_expansion import generate_multi_queries, expand_acronyms
from backend.rag.reranker import CrossEncoderReranker, get_cross_encoder_reranker
from backend.rag.retriever import HybridRetriever, get_hybrid_retriever, compute_rrf_fusion

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "ChromaVectorStore",
    "get_vector_store",
    "BM25IndexManager",
    "get_bm25_manager",
    "generate_multi_queries",
    "expand_acronyms",
    "CrossEncoderReranker",
    "get_cross_encoder_reranker",
    "HybridRetriever",
    "get_hybrid_retriever",
    "compute_rrf_fusion",
]
