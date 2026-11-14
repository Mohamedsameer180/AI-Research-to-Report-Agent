"""
Embedding service for TP01 Research Platform.
Provides deterministic vector embeddings using sentence-transformers (BAAI/bge-small-en-v1.5 by default).
Ensures zero mixing of embedding models within a workspace index.
"""
from typing import List
import threading
from backend.app.config import settings

_EMBEDDER_INSTANCE = None
_LOCK = threading.Lock()


class EmbeddingService:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._model = None
        self._dimension = 384  # Default dimension for bge-small-en-v1.5

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            # Runs efficiently on CPU on an 8 GB laptop
            self._model = SentenceTransformer(self.model_name, device="cpu")
            if hasattr(self._model, "get_embedding_dimension"):
                self._dimension = self._model.get_embedding_dimension()
            else:
                self._dimension = self._model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Compute embeddings for a list of document chunk texts."""
        if not texts:
            return []
        self._load_model()
        # SentenceTransformer encode returns numpy array; convert to list of floats
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Compute normalized embedding for a search query."""
        self._load_model()
        # For BGE models, a query instruction is sometimes used, but standard query encoding works well
        embedding = self._model.encode(
            query,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embedding.tolist()


def get_embedding_service() -> EmbeddingService:
    """Singleton getter for the embedding service."""
    global _EMBEDDER_INSTANCE
    if _EMBEDDER_INSTANCE is None:
        with _LOCK:
            if _EMBEDDER_INSTANCE is None:
                _EMBEDDER_INSTANCE = EmbeddingService()
    return _EMBEDDER_INSTANCE
