#!/usr/bin/env python3
"""
Firebase persistence layer for TaskFinisher AI.

This module intentionally sits outside the Google ADK agent. It persists real
task responses, events, steps, evidence, human decisions, and generated document
metadata produced by the existing backend/orchestrator flow.
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from database.document_integrity import build_metadata, sha256_file

logger = logging.getLogger(__name__)


TERMINAL_STATUSES = {"COMPLETED", "PARTIALLY_COMPLETED", "FAILED", "WAITING_FOR_HUMAN"}


def _load_dotenv_file() -> None:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        logger.warning("Could not read .env file for Firebase configuration.", exc_info=True)


def _now() -> str:
    return datetime.utcnow().isoformat()


def _status_value(value: Any) -> str:
    return getattr(value, "value", value) if value is not None else ""


def _safe_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", ""))
    except ValueError:
        return None


def _duration_ms(started_at: Any, completed_at: Any) -> Optional[int]:
    start = _safe_datetime(started_at)
    end = _safe_datetime(completed_at)
    if not start or not end:
        return None
    return max(0, int((end - start).total_seconds() * 1000))


def _stable_id(*parts: Any) -> str:
    text = "|".join(str(part or "") for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, Path):
        return str(value)
    return value


class FirebaseService:
    """Reusable Firebase Admin wrapper with SQLite-compatible fallbacks."""

    def __init__(self) -> None:
        self.enabled = False
        self.db = None
        self.bucket = None
        self._firebase_admin = None
        self._init_error: Optional[str] = None
        self._initialize()

    def _initialize(self) -> None:
        _load_dotenv_file()
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore, storage
        except ImportError as exc:
            self._init_error = str(exc)
            logger.info("Firebase Admin SDK is not installed; using local persistence only.")
            return

        project_id = os.getenv("FIREBASE_PROJECT_ID")
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
        private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE")
        service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")

        if not (service_account_path or service_account_json or (project_id and client_email and private_key)):
            logger.info("Firebase credentials are not configured; using local persistence only.")
            return

        try:
            if firebase_admin._apps:
                app = firebase_admin.get_app()
            else:
                if service_account_path:
                    cred = credentials.Certificate(service_account_path)
                elif service_account_json:
                    cred = credentials.Certificate(json.loads(service_account_json))
                else:
                    cred = credentials.Certificate({
                        "type": "service_account",
                        "project_id": project_id,
                        "private_key": private_key.replace("\\n", "\n"),
                        "client_email": client_email,
                        "token_uri": "https://oauth2.googleapis.com/token",
                    })
                options = {"storageBucket": storage_bucket} if storage_bucket else None
                app = firebase_admin.initialize_app(cred, options)

            self._firebase_admin = firebase_admin
            self.db = firestore.client(app)
            self.bucket = storage.bucket(app) if storage_bucket else None
            self.enabled = True
            logger.info("Firebase persistence initialized.")
        except Exception as exc:
            self._init_error = str(exc)
            logger.exception("Firebase initialization failed; using local persistence only.")

    def verify_user_token(self, authorization: Optional[str]) -> Optional[str]:
        if not self.enabled or not self._firebase_admin or not authorization:
            return None
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        try:
            decoded = self._firebase_admin.auth.verify_id_token(token)
            return decoded.get("uid")
        except Exception:
            logger.warning("Firebase auth token verification failed.", exc_info=True)
            return None

    def user_id_from_request(self, authorization: Optional[str] = None) -> str:
        uid = self.verify_user_token(authorization)
        return uid or os.getenv("TASKFINISHER_DEFAULT_USER_ID", "local_user")

    def _task_ref(self, task_id: str):
        return self.db.collection("tasks").document(task_id)

    def _settings_ref(self, user_id: str, key: str):
        return self.db.collection("users").document(user_id).collection("settings").document(key)

    def _write_with_retries(self, operation, *, label: str) -> bool:
        if not self.enabled:
            return False
        for attempt in range(3):
            try:
                operation()
                return True
            except Exception:
                logger.warning("Firebase write failed for %s on attempt %s.", label, attempt + 1, exc_info=True)
                time.sleep(0.2 * (2 ** attempt))
        return False

    def save_task(self, task_state: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        if not self.enabled:
            return False

        task = _json_safe(task_state)
        task_id = task["task_id"]
        owner = user_id or task.get("user_id") or os.getenv("TASKFINISHER_DEFAULT_USER_ID", "local_user")
        execution_id = task.get("execution_id") or f"exec_{task_id}"
        now = _now()

        steps = task.get("steps") or {}
        events = task.get("events") or []
        evidence = task.get("evidence") or []
        artifacts = task.get("artifacts") or {}

        completed_steps = sum(1 for step in steps.values() if _status_value(step.get("status")) == "COMPLETED")
        failed_steps = sum(1 for step in steps.values() if _status_value(step.get("status")) == "FAILED")
        retry_count = sum(max(int(step.get("attempts") or 0) - 1, 0) for step in steps.values())
        recovery_count = sum(1 for event in events if "RECOVERY" in str(event.get("event") or event.get("type") or ""))
        human_count = sum(1 for event in events if "HUMAN" in str(event.get("event") or event.get("type") or ""))
        completed_at = task.get("updated_at") if task.get("status") in TERMINAL_STATUSES else None
        started_at = task.get("created_at")
        document_id = f"doc_{task_id}" if artifacts else None

        title = task.get("title") or (task.get("user_request") or "")[:80]
        task_doc = {
            "task_id": task_id,
            "user_id": owner,
            "title": title,
            "title_search": str(title).lower(),
            "description": task.get("description") or task.get("user_request") or "",
            "task_type": task.get("scenario") or task.get("task_type"),
            "status": task.get("status"),
            "verdict": task.get("verdict"),
            "created_at": task.get("created_at") or now,
            "updated_at": task.get("updated_at") or now,
            "started_at": started_at,
            "completed_at": completed_at,
            "execution_id": execution_id,
            "output_format": task.get("output_format") or "docx",
            "progress": task.get("completion_percentage", 0),
            "total_steps": task.get("total_steps", len(steps)),
            "completed_steps": task.get("completed_steps", completed_steps),
            "failed_steps": failed_steps,
            "retry_count": retry_count,
            "recovery_count": recovery_count,
            "human_intervention_count": human_count,
            "evidence_count": len(evidence),
            "document_id": document_id,
            "archived": bool(task.get("archived", False)),
        }

        execution_doc = {
            "execution_id": execution_id,
            "task_id": task_id,
            "user_id": owner,
            "started_at": started_at,
            "completed_at": completed_at,
            "status": task.get("status"),
            "verdict": task.get("verdict"),
            "duration_ms": _duration_ms(started_at, completed_at),
            "total_steps": task_doc["total_steps"],
            "completed_steps": task_doc["completed_steps"],
            "failed_steps": failed_steps,
            "retry_count": retry_count,
            "recovery_count": recovery_count,
            "human_intervention_count": human_count,
        }

        def write_all() -> None:
            task_ref = self._task_ref(task_id)
            batch = self.db.batch()
            batch.set(task_ref, task_doc, merge=True)
            batch.set(task_ref.collection("executions").document(execution_id), execution_doc, merge=True)

            for index, event in enumerate(events):
                event_id = event.get("event_id") or _stable_id(task_id, execution_id, index, event.get("timestamp"), event.get("event"))
                event_doc = dict(event)
                event_doc.update({
                    "event_id": event_id,
                    "execution_id": execution_id,
                    "task_id": task_id,
                    "user_id": owner,
                    "type": str(event.get("type") or event.get("event") or "event").lower(),
                    "timestamp": event.get("timestamp") or now,
                })
                batch.set(task_ref.collection("events").document(event_id), event_doc, merge=True)

            for step_id, step in steps.items():
                started = step.get("started_at")
                completed = step.get("completed_at")
                step_doc = dict(step)
                step_doc.update({
                    "step_id": step_id,
                    "name": step.get("description") or step_id,
                    "status": _status_value(step.get("status")),
                    "agent_name": step.get("agent"),
                    "duration_ms": _duration_ms(started, completed),
                    "evidence_count": len(step.get("evidence") or []),
                    "execution_id": execution_id,
                    "task_id": task_id,
                    "user_id": owner,
                })
                batch.set(task_ref.collection("steps").document(step_id), step_doc, merge=True)

            for item in evidence:
                evidence_id = item.get("id") or item.get("evidence_id") or _stable_id(task_id, item.get("source"), item.get("content"))
                metadata = item.get("metadata") or {}
                evidence_doc = dict(item)
                evidence_doc.update({
                    "evidence_id": evidence_id,
                    "execution_id": execution_id,
                    "task_id": task_id,
                    "user_id": owner,
                    "step_id": metadata.get("step_id") or item.get("step_id"),
                    "title": metadata.get("title") or item.get("source"),
                    "reference": metadata.get("url") or item.get("source"),
                    "verification_status": metadata.get("status") or "RECORDED",
                    "created_at": item.get("timestamp") or now,
                })
                batch.set(task_ref.collection("evidence").document(evidence_id), evidence_doc, merge=True)

            if task.get("requires_human_approval") or task.get("human_decision_point"):
                action_id = _stable_id(task_id, execution_id, task.get("human_decision_point"))
                human_doc = {
                    "action_id": action_id,
                    "task_id": task_id,
                    "user_id": owner,
                    "execution_id": execution_id,
                    "question": task.get("human_decision_point"),
                    "options": task.get("human_options", []),
                    "selected_option": task.get("selected_option"),
                    "status": "WAITING" if task.get("requires_human_approval") else "RESOLVED",
                    "created_at": now,
                    "resolved_at": None if task.get("requires_human_approval") else now,
                }
                batch.set(task_ref.collection("human_actions").document(action_id), human_doc, merge=True)

            batch.commit()

            for key, artifact in artifacts.items():
                self.save_document_metadata(task_id, execution_id, owner, key, artifact)
            if artifacts:
                preferred = artifacts.get("preferred_report") or artifacts.get("report.docx") or artifacts.get("report.md")
                self.save_document_metadata(task_id, execution_id, owner, "preferred_report", preferred, document_id=document_id)

        return self._write_with_retries(write_all, label=f"task {task_id}")

    def save_setting(self, key: str, value: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        if not self.enabled:
            return False
        owner = user_id or os.getenv("TASKFINISHER_DEFAULT_USER_ID", "local_user")
        setting = _json_safe(value)
        setting.update({
            "key": key,
            "user_id": owner,
            "updated_at": _now(),
        })

        def write_setting() -> None:
            self._settings_ref(owner, key).set(setting, merge=True)

        return self._write_with_retries(write_setting, label=f"setting {key}")

    def get_setting(self, key: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        owner = user_id or os.getenv("TASKFINISHER_DEFAULT_USER_ID", "local_user")
        try:
            doc = self._settings_ref(owner, key).get()
            return doc.to_dict() if doc.exists else None
        except Exception:
            logger.warning("Failed to read Firebase setting %s.", key, exc_info=True)
            return None

    def save_document_metadata(
        self,
        task_id: str,
        execution_id: str,
        user_id: str,
        artifact_key: str,
        artifact_path: str,
        document_id: Optional[str] = None,
    ) -> bool:
        if not self.enabled or not artifact_path:
            return False

        path = Path(artifact_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        document_id = document_id or _stable_id(task_id, artifact_key, artifact_path)
        storage_path = f"users/{user_id}/tasks/{task_id}/documents/{document_id}/{path.name}"

        def write_doc() -> None:
            existing = self._task_ref(task_id).collection("documents").document(document_id).get()
            previous = existing.to_dict() if existing.exists else {}
            version = int(previous.get("version") or 0) + 1 if previous and previous.get("sha256") else 1
            doc = build_metadata(
                document_id=document_id,
                path=path,
                user_id=user_id,
                task_id=task_id,
                execution_id=execution_id,
                storage_path=storage_path if self.bucket else str(path),
                version=version,
            )
            doc["artifact_key"] = artifact_key

            if self.bucket and path.exists():
                blob = self.bucket.blob(storage_path)
                blob.upload_from_filename(str(path))
                blob.reload()
                doc["status"] = "VERIFIED" if int(blob.size or 0) == doc["size_bytes"] else "FILE_INTEGRITY_ERROR"

            self._task_ref(task_id).collection("documents").document(document_id).set(doc, merge=True)
            self._task_ref(task_id).collection("documents").document(document_id).collection("versions").document(str(doc["version"])).set(doc, merge=True)
            self.db.collection("documents").document(document_id).set(doc, merge=True)
            self._task_ref(task_id).collection("events").document(_stable_id(document_id, "FILE_INTEGRITY_VERIFIED", doc["sha256"])).set({
                "event": "FILE_INTEGRITY_VERIFIED",
                "type": "file_integrity_verified",
                "document_id": document_id,
                "algorithm": "SHA-256",
                "sha256": doc["sha256"],
                "timestamp": _now(),
                "user_id": user_id,
                "task_id": task_id,
                "execution_id": execution_id,
            }, merge=True)

        return self._write_with_retries(write_doc, label=f"document {document_id}")

    def save_uploaded_document(self, metadata: Dict[str, Any], local_path: Path) -> bool:
        if not self.enabled:
            return False
        document_id = metadata["document_id"]
        storage_path = metadata["storage_path"]

        def write_doc() -> None:
            stored = dict(metadata)
            if self.bucket and local_path.exists():
                blob = self.bucket.blob(storage_path)
                blob.upload_from_filename(str(local_path))
                blob.reload()
                stored["status"] = "VERIFIED" if int(blob.size or 0) == stored["size_bytes"] else "FILE_INTEGRITY_ERROR"
            self.db.collection("documents").document(document_id).set(stored, merge=True)
            task_id = stored.get("task_id")
            if task_id:
                task_ref = self._task_ref(task_id)
                task_ref.collection("documents").document(document_id).set(stored, merge=True)
                task_ref.collection("events").document(_stable_id(document_id, "FILE_UPLOADED", stored["sha256"])).set({
                    "event": "FILE_UPLOADED",
                    "type": "file_uploaded",
                    "document_id": document_id,
                    "algorithm": "SHA-256",
                    "sha256": stored["sha256"],
                    "timestamp": _now(),
                    "user_id": stored.get("user_id"),
                    "task_id": task_id,
                    "execution_id": stored.get("execution_id"),
                }, merge=True)

        return self._write_with_retries(write_doc, label=f"uploaded document {document_id}")

    def list_tasks(
        self,
        user_id: str,
        limit: int = 25,
        cursor: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {"tasks": [], "next_cursor": None}

        query = self.db.collection("tasks").where("user_id", "==", user_id).where("archived", "==", False)
        if status:
            query = query.where("status", "==", status)
        if task_type:
            query = query.where("task_type", "==", task_type)
        if date_from:
            query = query.where("created_at", ">=", date_from)
        if date_to:
            query = query.where("created_at", "<=", date_to)
        if search:
            needle = search.lower()
            query = query.where("title_search", ">=", needle).where("title_search", "<=", f"{needle}\uf8ff")
            query = query.order_by("title_search").order_by("created_at", direction="DESCENDING")
        else:
            query = query.order_by("created_at", direction="DESCENDING")
        if cursor:
            cursor_doc = self.db.collection("tasks").document(cursor).get()
            if cursor_doc.exists:
                query = query.start_after(cursor_doc)
        docs = list(query.limit(max(1, min(limit, 100))).stream())
        tasks = [doc.to_dict() for doc in docs]
        next_cursor = docs[-1].id if len(docs) == limit else None
        return {"tasks": tasks, "next_cursor": next_cursor}

    def get_task(self, task_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        doc = self._task_ref(task_id).get()
        if not doc.exists:
            return None
        task = doc.to_dict()
        if user_id and task.get("user_id") != user_id:
            return None
        return task

    def list_subcollection(self, task_id: str, collection: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        task = self.get_task(task_id, user_id)
        if not task:
            return []
        docs = self._task_ref(task_id).collection(collection).stream()
        return [doc.to_dict() for doc in docs]

    def get_execution_details(self, task_id: str, execution_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        task = self.get_task(task_id, user_id)
        if not task:
            return None
        execution_doc = self._task_ref(task_id).collection("executions").document(execution_id).get()
        if not execution_doc.exists:
            return None

        def for_execution(collection: str) -> List[Dict[str, Any]]:
            return [
                item for item in self.list_subcollection(task_id, collection, user_id)
                if item.get("execution_id") == execution_id
            ]

        events = for_execution("events")
        adk_events = [event for event in events if event.get("event") == "ADK_AGENT_USED"]
        return {
            "task": task,
            "execution": execution_doc.to_dict(),
            "steps": for_execution("steps"),
            "events": events,
            "agents": adk_events,
            "tools": [
                event for event in events
                if "TOOL" in str(event.get("event") or event.get("type") or "").upper()
            ],
            "verification": [
                event for event in events
                if "VERIFICATION" in str(event.get("event") or event.get("type") or "").upper()
            ],
            "recovery": [
                event for event in events
                if "RECOVERY" in str(event.get("event") or event.get("type") or "").upper()
                or "RETRY" in str(event.get("event") or event.get("type") or "").upper()
            ],
            "evidence": for_execution("evidence"),
            "human_actions": for_execution("human_actions"),
            "documents": for_execution("documents"),
            "final_result": {
                "status": task.get("status"),
                "verdict": task.get("verdict"),
                "document_id": task.get("document_id"),
                "completed_at": task.get("completed_at"),
            },
        }

    def archive_task(self, task_id: str, user_id: str) -> bool:
        if not self.enabled:
            return False
        task = self.get_task(task_id, user_id)
        if not task:
            return False
        return self._write_with_retries(
            lambda: self._task_ref(task_id).set({"archived": True, "updated_at": _now()}, merge=True),
            label=f"archive task {task_id}",
        )

    def get_analytics(self, user_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {}
        tasks = self.list_tasks(user_id, limit=100).get("tasks", [])
        status_counts: Dict[str, int] = {}
        durations = []
        total_recoveries = 0
        total_human = 0
        total_evidence = 0
        documents = 0
        for task in tasks:
            status = task.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
            if task.get("completed_at") and task.get("started_at"):
                duration = _duration_ms(task.get("started_at"), task.get("completed_at"))
                if duration is not None:
                    durations.append(duration / 1000)
            total_recoveries += int(task.get("recovery_count") or 0)
            total_human += int(task.get("human_intervention_count") or 0)
            total_evidence += int(task.get("evidence_count") or 0)
            documents += 1 if task.get("document_id") else 0
        return {
            "total_tasks": len(tasks),
            "completed_tasks": status_counts.get("COMPLETED", 0),
            "partially_completed_tasks": status_counts.get("PARTIALLY_COMPLETED", 0),
            "failed_tasks": status_counts.get("FAILED", 0),
            "average_execution_time": sum(durations) / len(durations) if durations else 0,
            "total_recoveries": total_recoveries,
            "total_human_interventions": total_human,
            "total_evidence_items": total_evidence,
            "documents_generated": documents,
        }

    def signed_document_url(self, task_id: str, document_id: str, user_id: str) -> Optional[str]:
        if not self.enabled or not self.bucket:
            return None
        task = self.get_task(task_id, user_id)
        if not task:
            return None
        document = self._task_ref(task_id).collection("documents").document(document_id).get()
        if not document.exists:
            return None
        metadata = document.to_dict()
        storage_path = metadata.get("storage_path")
        if not storage_path:
            return None
        blob = self.bucket.blob(storage_path)
        return blob.generate_signed_url(expiration=timedelta(minutes=15), method="GET")

    def find_document(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        direct_doc = self.db.collection("documents").document(document_id).get()
        if direct_doc.exists:
            metadata = direct_doc.to_dict()
            if metadata.get("user_id") == user_id:
                return metadata
        task_id = document_id[4:] if document_id.startswith("doc_") else None
        candidate_tasks = [task_id] if task_id else [task["task_id"] for task in self.list_tasks(user_id, limit=100).get("tasks", [])]
        for candidate_task_id in candidate_tasks:
            if not candidate_task_id:
                continue
            task = self.get_task(candidate_task_id, user_id)
            if not task:
                continue
            doc = self._task_ref(candidate_task_id).collection("documents").document(document_id).get()
            if doc.exists:
                metadata = doc.to_dict()
                metadata["task_id"] = candidate_task_id
                return metadata
        return None

    def verify_document_integrity(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        metadata = self.find_document(document_id, user_id)
        if not metadata:
            return None
        expected = metadata.get("sha256")
        actual = None
        integrity = "FILE_NOT_FOUND"
        try:
            if self.bucket and metadata.get("storage_path", "").startswith("users/"):
                import tempfile

                blob = self.bucket.blob(metadata["storage_path"])
                if not blob.exists():
                    integrity = "FILE_NOT_FOUND"
                else:
                    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                        blob.download_to_filename(temp_file.name)
                        actual = sha256_file(Path(temp_file.name))
                    integrity = "VERIFIED" if actual == expected else "INTEGRITY_FAILED"
            else:
                path = Path(metadata.get("local_path") or metadata.get("storage_path") or "")
                if path.exists():
                    actual = sha256_file(path)
                    integrity = "VERIFIED" if actual == expected else "INTEGRITY_FAILED"
        except Exception:
            logger.warning("Firebase document integrity verification failed.", exc_info=True)
            integrity = "VERIFICATION_ERROR"

        result = {
            "document_id": document_id,
            "filename": metadata.get("filename"),
            "algorithm": "SHA-256",
            "expected_hash": expected,
            "actual_hash": actual,
            "integrity": integrity,
            "verified_at": _now(),
        }
        if metadata.get("task_id"):
            self._write_with_retries(
                lambda: self._task_ref(metadata["task_id"]).collection("events").document(_stable_id(document_id, "FILE_INTEGRITY_CHECKED", result["verified_at"])).set({
                    "event": "FILE_INTEGRITY_CHECKED",
                    "type": "file_integrity_checked",
                    "document_id": document_id,
                    "algorithm": "SHA-256",
                    "expected_hash": expected,
                    "actual_hash": actual,
                    "integrity": integrity,
                    "timestamp": result["verified_at"],
                    "user_id": user_id,
                    "task_id": metadata.get("task_id"),
                    "execution_id": metadata.get("execution_id"),
                }, merge=True),
                label=f"document verification event {document_id}",
            )
        return result


firebase_service = FirebaseService()
