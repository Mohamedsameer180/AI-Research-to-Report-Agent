"""
Cross-Encoder reranking service for TP01 Research Platform.
Uses cross-encoder/ms-marco-MiniLM-L-6-v2 to perform deep query-document cross-attention scoring.
"""
import logging
import threading
from typing import List, Dict, Any, Optional
from backend.app.config import settings

logger = logging.getLogger("tp01.rag.reranker")

_RERANKER_INSTANCE = None
_RERANKER_LOCK = threading.Lock()


class CrossEncoderReranker:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.CROSS_ENCODER_MODEL_NAME
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            # Runs CPU-optimized, ~80 MB memory footprint
            logger.info("Loading Cross-Encoder model: %s", self.model_name)
            self._model = CrossEncoder(self.model_name, device="cpu", max_length=512)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate chunk dictionaries against the search query.
        Returns the top_k reranked candidates sorted by cross-encoder score.
        """
        if not candidates or not query.strip():
            return []

        self._load_model()

        # Build query-document pairs
        pairs = [[query, c.get("text", "")] for c in candidates]

        # Compute cross-encoder logit scores
        scores = self._model.predict(pairs, show_progress_bar=False)

        # Attach scores to candidates
        for idx, score in enumerate(scores):
            candidates[idx]["rerank_score"] = float(score)

        # Sort descending by rerank_score
        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]


def get_cross_encoder_reranker() -> CrossEncoderReranker:
    """Singleton getter for the Cross-Encoder reranker."""
    global _RERANKER_INSTANCE
    if _RERANKER_INSTANCE is None:
        with _RERANKER_LOCK:
            if _RERANKER_INSTANCE is None:
                _RERANKER_INSTANCE = CrossEncoderReranker()
    return _RERANKER_INSTANCE
