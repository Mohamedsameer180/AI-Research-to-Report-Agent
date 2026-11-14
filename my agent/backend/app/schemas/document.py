"""
Pydantic schemas for Document operations in TP01.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    filename: str
    workspace_id: str = "default_workspace"
    user_id: str = "local_user"


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    workspace_id: str
    file_size_bytes: int
    file_hash: str
    version: int
    processing_status: str
    message: str


class DocumentBatchUploadResponse(BaseModel):
    uploaded: List[DocumentUploadResponse]
    failed: List[Dict[str, str]]
    total_uploaded: int
    total_failed: int


class DocumentStatusResponse(BaseModel):
    id: str
    filename: str
    processing_status: str
    error_message: Optional[str] = None
    page_count: int = 0
    chunk_count: int = 0
    needs_ocr: bool = False
    title: Optional[str] = None
    publication_year: Optional[int] = None
    doi: Optional[str] = None


class PaperMetadataSchema(BaseModel):
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    publication_year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    primary_domain: Optional[str] = None
    keywords: Optional[List[str]] = None


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    filename: str
    file_size_bytes: int
    file_hash: str
    version: int
    page_count: int
    processing_status: str
    error_message: Optional[str] = None
    needs_ocr: bool = False
    title: Optional[str] = None
    metadata_extracted: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    workspace_id: str

