from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship, synonym
from backend.app.db.database import Base


def _now():
    return datetime.utcnow()


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(64), primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    size_bytes = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(64), nullable=False, default="application/pdf")
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="queued")  # queued, processing, ready, failed
    error_message = Column(Text, nullable=True)
    doc_metadata = Column(Text, nullable=True)  # JSON: title, authors, year, abstract, doi, domain
    needs_ocr = Column(Boolean, nullable=False, default=False)
    page_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    id = synonym("document_id")
    file_size_bytes = synonym("size_bytes")
    processing_status = synonym("status")

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    paper_records = relationship("PaperRecord", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_doc_ws_hash", "workspace_id", "file_hash"),
        Index("ix_doc_ws_status", "workspace_id", "status"),
    )

    @property
    def title(self) -> Optional[str]:
        if self.doc_metadata:
            try:
                data = json.loads(self.doc_metadata) if isinstance(self.doc_metadata, str) else self.doc_metadata
                return data.get("title")
            except Exception:
                pass
        return self.filename

    @title.setter
    def title(self, val: str):
        try:
            data = json.loads(self.doc_metadata) if self.doc_metadata else {}
        except Exception:
            data = {}
        data["title"] = val
        self.doc_metadata = json.dumps(data)

    @property
    def metadata_extracted(self) -> Dict[str, Any]:
        if self.doc_metadata:
            try:
                return json.loads(self.doc_metadata) if isinstance(self.doc_metadata, str) else self.doc_metadata
            except Exception:
                pass
        return {}

    @metadata_extracted.setter
    def metadata_extracted(self, val: Any):
        self.doc_metadata = json.dumps(val) if isinstance(val, dict) else val

    def get_metadata(self) -> Dict[str, Any]:
        return json.loads(self.doc_metadata) if self.doc_metadata else {}

    def set_metadata(self, data: Dict[str, Any]):
        self.doc_metadata = json.dumps(data)


class DocumentPage(Base):
    __tablename__ = "document_pages"

    page_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    document_id = Column(String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(64), nullable=True, index=True)
    pdf_page_index = Column(Integer, nullable=False, default=0)  # 0-based physical page
    printed_page_label = Column(String(32), nullable=True)  # e.g., "142" or "ii"
    raw_text = Column(Text, nullable=False, default="")
    is_scanned = Column(Boolean, nullable=False, default=False)
    char_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_now, nullable=False)

    id = synonym("page_id")
    page_number = synonym("pdf_page_index")

    document = relationship("Document", back_populates="pages")

    __table_args__ = (
        Index("ix_page_doc_idx", "document_id", "pdf_page_index"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    parent_id = Column(String(64), nullable=True, index=True)  # Parent section chunk ID
    document_id = Column(String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(64), nullable=True, index=True)
    pdf_page = Column(Integer, nullable=False, default=1)
    printed_page = Column(String(32), nullable=True)
    section = Column(String(64), nullable=False, default="body")
    text = Column(Text, nullable=False, default="")
    token_count = Column(Integer, nullable=False, default=0)
    char_start = Column(Integer, nullable=False, default=0)
    char_end = Column(Integer, nullable=False, default=0)
    is_parent = Column(Boolean, nullable=False, default=False)
    is_table = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=_now, nullable=False)

    id = synonym("chunk_id")
    parent_chunk_id = synonym("parent_id")
    pdf_page_number = synonym("pdf_page")
    printed_page_label = synonym("printed_page")
    section_name = synonym("section")
    chunk_text = synonym("text")
    char_start_offset = synonym("char_start")
    char_end_offset = synonym("char_end")

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunk_ws_doc", "workspace_id", "document_id"),
        Index("ix_chunk_section", "section"),
    )


class PaperRecord(Base):
    __tablename__ = "paper_records"

    record_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    document_id = Column(String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, default="local_user")
    file_hash = Column(String(64), nullable=True, index=True)
    research_domain = Column(String(128), nullable=True)
    title = Column(String(512), nullable=True)
    abstract = Column(Text, nullable=True)
    publication_year = Column(Integer, nullable=True)
    doi = Column(String(128), nullable=True)
    objective = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=True)
    methodology_json = Column(Text, nullable=True)
    evaluation_json = Column(Text, nullable=True)
    results_json = Column(Text, nullable=True)
    strengths_json = Column(Text, nullable=True)
    limitations_json = Column(Text, nullable=True)
    future_work_json = Column(Text, nullable=True)
    conclusion_json = Column(Text, nullable=True)
    analysis_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    id = synonym("record_id")
    primary_domain = synonym("research_domain")
    research_domain = Column(String(128), nullable=True)
    title = Column(String(512), nullable=True)
    objective = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=True)
    methodology_json = Column(Text, nullable=True)
    evaluation_json = Column(Text, nullable=True)
    results_json = Column(Text, nullable=True)
    strengths_json = Column(Text, nullable=True)
    limitations_json = Column(Text, nullable=True)
    future_work_json = Column(Text, nullable=True)
    conclusion_json = Column(Text, nullable=True)
    analysis_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    document = relationship("Document", back_populates="paper_records")


class Citation(Base):
    __tablename__ = "citations"

    citation_id = Column(String(64), primary_key=True, index=True)
    document_id = Column(String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    source_type = Column(String(64), nullable=False)  # extraction, chat, comparison, gap, report
    source_id = Column(String(64), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    quote = Column(String(512), nullable=False)
    pdf_page = Column(Integer, nullable=False)
    printed_page = Column(String(32), nullable=True)
    status = Column(String(32), nullable=False)  # verified, corrected_page, unverified
    matched_span = Column(Text, nullable=True)
    fuzzy_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=_now, nullable=False)


class Comparison(Base):
    __tablename__ = "comparisons"

    comparison_id = Column(String(64), primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False)
    document_ids_json = Column(Text, nullable=False)
    matrix_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)


class Contradiction(Base):
    __tablename__ = "contradictions"

    contradiction_id = Column(String(64), primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False)
    doc1_id = Column(String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    doc2_id = Column(String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    task = Column(String(255), nullable=True)
    dataset = Column(String(255), nullable=True)
    metric = Column(String(255), nullable=True)
    finding1_json = Column(Text, nullable=False)
    finding2_json = Column(Text, nullable=False)
    analysis = Column(Text, nullable=False)
    comparable = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_now, nullable=False)


class ResearchGap(Base):
    __tablename__ = "research_gaps"

    gap_id = Column(String(64), primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    gap_type = Column(String(32), nullable=False)  # stated_limitation, collection_coverage_gap, inferred_opportunity
    related_papers_json = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=False)
    potential_direction = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.8)
    disclaimer = Column(Text, nullable=False, default="Hypothesis inferred only from the uploaded collection; not globally exhaustive.")
    created_at = Column(DateTime, default=_now, nullable=False)


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(String(64), primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String(64), primary_key=True, index=True)
    conversation_id = Column(String(64), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    claims_json = Column(Text, nullable=True)
    citations_json = Column(Text, nullable=True)
    citation_stats_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False)
    step_name = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)  # STARTED, COMPLETED, FAILED, RETRYING
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    tool_calls_json = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_now, nullable=False)


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(String(64), primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    format = Column(String(16), nullable=False, default="md")  # md, pdf, docx
    file_path = Column(String(1024), nullable=False)
    content = Column(Text, nullable=False)
    citation_stats_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)


class EvalResult(Base):
    __tablename__ = "eval_results"

    eval_id = Column(String(64), primary_key=True, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    pipeline_name = Column(String(64), nullable=False)  # dense_only, bm25_only, hybrid, hybrid_rerank
    metrics_json = Column(Text, nullable=False)
    sample_size = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_now, nullable=False)
