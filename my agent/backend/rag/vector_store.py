"""
ChromaDB persistent vector store for TP01 Research Platform.
Provides workspace-isolated collections for multi-tenant safety.
"""
import re
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.config import settings


def sanitize_collection_name(workspace_id: str) -> str:
    """Ensure ChromaDB collection name satisfies naming rules (3-63 chars, [a-zA-Z0-9_-])."""
    clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", workspace_id)
    name = f"papers_{clean_id}"
    if len(name) > 63:
        name = name[:63]
    return name


class ChromaVectorStore:
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or str(settings.CHROMA_PERSIST_DIR)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_collection(self, workspace_id: str):
        col_name = sanitize_collection_name(workspace_id)
        metadata = {
            "workspace_id": workspace_id,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
        }
        return self.client.get_or_create_collection(
            name=col_name,
            metadata=metadata,
        )

    def add_chunks(
        self,
        workspace_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        """Add child/parent chunks with precomputed embeddings to workspace collection."""
        if not chunks:
            return 0

        collection = self.get_collection(workspace_id)
        ids = []
        documents = []
        metadatas = []

        for c in chunks:
            ids.append(str(c["chunk_id"]))
            documents.append(str(c["text"]))
            metadatas.append({
                "document_id": str(c.get("document_id", "")),
                "parent_id": str(c.get("parent_id") or ""),
                "filename": str(c.get("filename", "")),
                "title": str(c.get("title", ""))[:200],
                "pdf_page": int(c.get("pdf_page", 1)),
                "printed_page": str(c.get("printed_page", "1")),
                "section": str(c.get("section", "other")),
                "is_parent": bool(c.get("is_parent", False)),
                "is_table": bool(c.get("is_table", False)),
                "char_start": int(c.get("char_start", 0)),
                "char_end": int(c.get("char_end", 0)),
            })

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def delete_document(self, workspace_id: str, document_id: str) -> int:
        """Delete all chunks belonging to a document within a workspace."""
        collection = self.get_collection(workspace_id)
        # Query existing IDs with this document_id
        res = collection.get(where={"document_id": document_id})
        ids_to_del = res.get("ids", [])
        if ids_to_del:
            collection.delete(ids=ids_to_del)
            return len(ids_to_del)
        return 0

    def query(
        self,
        workspace_id: str,
        query_embedding: List[float],
        n_results: int = 10,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Dense similarity search within a workspace."""
        collection = self.get_collection(workspace_id)
        count = collection.count()
        if count == 0:
            return []

        limit = min(n_results, count)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0] if results.get("documents") else []
            metas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []

            for i in range(len(ids)):
                # Chroma uses L2 distance or cosine distance; convert to similarity score
                dist = distances[i] if i < len(distances) else 1.0
                score = 1.0 / (1.0 + dist)
                output.append({
                    "chunk_id": ids[i],
                    "text": docs[i] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                    "score": score,
                    "distance": dist,
                })
        return output

    def count(self, workspace_id: str) -> int:
        return self.get_collection(workspace_id).count()


_VECTOR_STORE_INSTANCE = None


def get_vector_store() -> ChromaVectorStore:
    global _VECTOR_STORE_INSTANCE
    if _VECTOR_STORE_INSTANCE is None:
        _VECTOR_STORE_INSTANCE = ChromaVectorStore()
    return _VECTOR_STORE_INSTANCE

