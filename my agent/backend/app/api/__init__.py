"""
API router package.
"""
from backend.app.api.documents import router as documents_router
from backend.app.api.retrieval import router as retrieval_router

__all__ = ["documents_router", "retrieval_router"]
