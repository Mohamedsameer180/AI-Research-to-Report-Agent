"""
Deduplication and versioning engine for TP01 documents.
Calculates SHA-256 digests and manages workspace version increments.
"""
import hashlib
from pathlib import Path
from typing import Union, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.db.models import Document

CHUNK_SIZE = 1024 * 1024  # 1 MB


def compute_sha256(input_data: Union[Path, str, bytes, bytearray]) -> str:
    """Compute the SHA-256 hash of a file path or raw bytes."""
    hasher = hashlib.sha256()
    if isinstance(input_data, (bytes, bytearray)):
        hasher.update(input_data)
    elif isinstance(input_data, (str, Path)):
        p = Path(input_data)
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                hasher.update(chunk)
    else:
        hasher.update(bytes(input_data))
    return hasher.hexdigest()


def check_duplicate_and_version(
    db: Session,
    file_hash: str,
    filename: str,
    workspace_id: str,
) -> int:
    """
    Checks if a document with this hash or filename already exists in the workspace.
    Returns next version integer (1 for new, 2+ for update).
    """
    same_name_doc = (
        db.query(Document)
        .filter(Document.workspace_id == workspace_id, Document.filename == filename)
        .order_by(Document.version.desc())
        .first()
    )
    if same_name_doc:
        return same_name_doc.version + 1
    return 1
