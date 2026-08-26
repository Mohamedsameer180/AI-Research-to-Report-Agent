#!/usr/bin/env python3
"""Document SHA-256 integrity helpers.

SHA-256 is used here only as a one-way file fingerprint for integrity checks.
It does not encrypt, hide, or protect document contents.
"""

import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib

CHUNK_SIZE = 1024 * 1024
REGISTRY_PATH = Path("database") / "document_integrity_records.json"


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_valid_sha256(value: str) -> bool:
    return len(value or "") == 64 and all(char in "0123456789abcdef" for char in value)


def content_type_for(path: Path, fallback: Optional[str] = None) -> str:
    return fallback or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def _load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"documents": {}, "events": []}
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"documents": {}, "events": []}


def _save_registry(registry: Dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def build_metadata(
    *,
    document_id: str,
    path: Path,
    user_id: str,
    task_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    content_type: Optional[str] = None,
    storage_path: Optional[str] = None,
    version: int = 1,
    status: str = "VERIFIED",
) -> Dict[str, Any]:
    resolved = path.resolve()
    file_hash = sha256_file(resolved)
    created_at = now_iso()
    return {
        "document_id": document_id,
        "file_id": document_id,
        "task_id": task_id,
        "execution_id": execution_id,
        "user_id": user_id,
        "filename": resolved.name,
        "content_type": content_type_for(resolved, content_type),
        "format": resolved.suffix.lstrip(".").lower(),
        "size_bytes": resolved.stat().st_size,
        "file_size": resolved.stat().st_size,
        "sha256": file_hash,
        "algorithm": "SHA-256",
        "storage_path": storage_path or str(resolved),
        "local_path": str(resolved),
        "version": version,
        "status": status,
        "integrity": "VERIFIED" if status == "VERIFIED" else status,
        "created_at": created_at,
        "updated_at": created_at,
    }


def record_local_document(metadata: Dict[str, Any]) -> Dict[str, Any]:
    registry = _load_registry()
    document_id = metadata["document_id"]
    previous = registry["documents"].get(document_id)
    if previous and previous.get("sha256") != metadata.get("sha256"):
        metadata["version"] = int(previous.get("version") or 1) + 1
    registry["documents"][document_id] = metadata
    registry["events"].append({
        "event": "FILE_HASH_CREATED",
        "document_id": document_id,
        "algorithm": "SHA-256",
        "sha256": metadata.get("sha256"),
        "timestamp": now_iso(),
        "user_id": metadata.get("user_id"),
        "task_id": metadata.get("task_id"),
    })
    registry["events"].append({
        "event": "FILE_INTEGRITY_VERIFIED",
        "document_id": document_id,
        "algorithm": "SHA-256",
        "sha256": metadata.get("sha256"),
        "timestamp": now_iso(),
        "user_id": metadata.get("user_id"),
        "task_id": metadata.get("task_id"),
    })
    _save_registry(registry)
    return metadata


def get_local_document(document_id: str) -> Optional[Dict[str, Any]]:
    return _load_registry().get("documents", {}).get(document_id)


def verify_local_document(document_id: str) -> Dict[str, Any]:
    metadata = get_local_document(document_id)
    verified_at = now_iso()
    if not metadata:
        return {
            "document_id": document_id,
            "algorithm": "SHA-256",
            "expected_hash": None,
            "actual_hash": None,
            "integrity": "FILE_NOT_FOUND",
            "verified_at": verified_at,
        }

    path = Path(metadata.get("local_path") or metadata.get("storage_path") or "")
    if not path.exists():
        return {
            "document_id": document_id,
            "filename": metadata.get("filename"),
            "algorithm": "SHA-256",
            "expected_hash": metadata.get("sha256"),
            "actual_hash": None,
            "integrity": "FILE_NOT_FOUND",
            "verified_at": verified_at,
        }

    try:
        actual = sha256_file(path)
    except OSError:
        return {
            "document_id": document_id,
            "filename": metadata.get("filename"),
            "algorithm": "SHA-256",
            "expected_hash": metadata.get("sha256"),
            "actual_hash": None,
            "integrity": "VERIFICATION_ERROR",
            "verified_at": verified_at,
        }

    integrity = "VERIFIED" if actual == metadata.get("sha256") else "INTEGRITY_FAILED"
    return {
        "document_id": document_id,
        "filename": metadata.get("filename"),
        "algorithm": "SHA-256",
        "expected_hash": metadata.get("sha256"),
        "actual_hash": actual,
        "integrity": integrity,
        "verified_at": verified_at,
    }


def secure_filename(stem: str, suffix: str, file_hash: str) -> str:
    safe_stem = "".join(char if char.isalnum() or char in "._-" else "_" for char in stem).strip("._") or "file"
    return f"{safe_stem}_{file_hash[:16]}{suffix}"
