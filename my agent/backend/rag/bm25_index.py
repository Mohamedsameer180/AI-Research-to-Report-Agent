"""
BM25 sparse index for keyword and exact-term retrieval.
Maintains persistent index per workspace using rank_bm25.BM25Plus.
"""
import os
import re
import pickle
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Plus
from backend.app.config import settings

_BM25_LOCK = threading.Lock()


def tokenize_bm25(text: str) -> List[str]:
    """Tokenize text for BM25 matching, capturing words, acronyms, and hyphenated terms."""
    cleaned = re.sub(r"[^\w\s\-]", " ", text.lower())
    words = cleaned.split()
    tokens = []
    for w in words:
        w_clean = w.strip("-_.")
        if len(w_clean) >= 2:
            tokens.append(w_clean)
            if "-" in w_clean:
                parts = [p for p in w_clean.split("-") if len(p) >= 2]
                tokens.extend(parts)
    return tokens


class BM25WorkspaceIndex:
    def __init__(self, workspace_id: str, index_dir: Optional[Path] = None):
        self.workspace_id = workspace_id
        self.index_dir = index_dir or settings.BM25_INDEX_DIR
        self.file_path = self.index_dir / f"bm25_{workspace_id}.pkl"
        self.records: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Plus] = None
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "rb") as f:
                    data = pickle.load(f)
                    self.records = data.get("records", [])
                    if self.records:
                        corpus = [r["tokens"] for r in self.records]
                        self.bm25 = BM25Plus(corpus)
            except Exception:
                self.records = []
                self.bm25 = None

    def _save(self):
        with open(self.file_path, "wb") as f:
            pickle.dump({"records": self.records}, f)

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add new chunks and rebuild BM25 index."""
        if not chunks:
            return

        for c in chunks:
            existing = [r for r in self.records if r["chunk_id"] == c["chunk_id"]]
            if not existing:
                tokens = tokenize_bm25(c["text"])
                self.records.append({
                    "chunk_id": c["chunk_id"],
                    "document_id": c.get("document_id"),
                    "text": c["text"],
                    "tokens": tokens,
                    "metadata": {
                        "document_id": c.get("document_id"),
                        "parent_id": c.get("parent_id"),
                        "filename": c.get("filename"),
                        "title": c.get("title"),
                        "pdf_page": c.get("pdf_page"),
                        "printed_page": c.get("printed_page"),
                        "section": c.get("section"),
                        "is_parent": c.get("is_parent", False),
                        "is_table": c.get("is_table", False),
                        "char_start": c.get("char_start", 0),
                        "char_end": c.get("char_end", 0),
                    }
                })

        corpus = [r["tokens"] for r in self.records]
        if corpus:
            self.bm25 = BM25Plus(corpus)
        self._save()

    def delete_document(self, document_id: str) -> int:
        """Remove chunks for document and rebuild."""
        initial_len = len(self.records)
        self.records = [r for r in self.records if r["document_id"] != document_id]
        deleted_count = initial_len - len(self.records)

        if deleted_count > 0:
            if self.records:
                corpus = [r["tokens"] for r in self.records]
                self.bm25 = BM25Plus(corpus)
            else:
                self.bm25 = None
            self._save()

        return deleted_count

    def search(
        self,
        query: str,
        top_k: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run BM25 search with optional metadata filtering."""
        if not self.bm25 or not self.records:
            return []

        tokens = tokenize_bm25(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        scored_records = []

        query_set = set(tokens)
        for idx, score in enumerate(scores):
            rec = self.records[idx]
            # Verify at least one token matches
            doc_tokens = set(rec["tokens"])
            matches = len(query_set.intersection(doc_tokens))
            if matches == 0 and score <= 0.0:
                continue

            # Apply where_filter if provided
            if where_filter:
                match = True
                meta = rec.get("metadata", {})
                for k, v in where_filter.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            scored_records.append({
                "chunk_id": rec["chunk_id"],
                "text": rec["text"],
                "metadata": rec["metadata"],
                "score": float(score),
            })

        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def count(self) -> int:
        return len(self.records)


class BM25IndexManager:
    def __init__(self):
        self._indices: Dict[str, BM25WorkspaceIndex] = {}

    def get_index(self, workspace_id: str) -> BM25WorkspaceIndex:
        with _BM25_LOCK:
            if workspace_id not in self._indices:
                self._indices[workspace_id] = BM25WorkspaceIndex(workspace_id)
            return self._indices[workspace_id]


_BM25_MANAGER = None


def get_bm25_manager() -> BM25IndexManager:
    global _BM25_MANAGER
    if _BM25_MANAGER is None:
        _BM25_MANAGER = BM25IndexManager()
    return _BM25_MANAGER
