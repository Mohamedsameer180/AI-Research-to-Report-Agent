"""
Document API endpoints for TP01 Research Platform.
Provides multi-PDF upload, batch upload, status tracking, metadata extraction,
and deletion cascading across SQLite, ChromaDB, and BM25 index.
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status, Query
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db.database import get_db
from backend.app.db.models import Document, DocumentPage, DocumentChunk, PaperRecord
from backend.app.schemas.document import (
    DocumentUploadResponse,
    DocumentBatchUploadResponse,
    DocumentStatusResponse,
    DocumentResponse,
    DocumentListResponse,
)
from backend.ingestion.dedup import compute_sha256, check_duplicate_and_version
from backend.ingestion.pdf_extractor import extract_pdf_data
from backend.ingestion.metadata import extract_paper_metadata
from backend.ingestion.chunker import create_page_chunks
from backend.rag.embeddings import get_embedding_service
from backend.rag.vector_store import get_vector_store
from backend.rag.bm25_index import get_bm25_manager
from backend.extraction.paper_extractor import PaperExtractor
from backend.extraction.paper_schema import PaperRecordSchema

router = APIRouter(prefix="/documents", tags=["documents"])


def run_document_processing_pipeline(document_id: str, db: Session):
    """
    Synchronous / background pipeline that processes a PDF:
    Extracts text, metadata, generates page-bounded chunks,
    and indexes into both ChromaDB and BM25.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return

    doc.processing_status = "processing"
    db.commit()

    try:
        pdf_path = Path(doc.file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"File not found: {doc.file_path}")

        # 1. Extract PDF pages and structure
        extracted = extract_pdf_data(pdf_path)
        pages_data = extracted.get("pages", [])
        page_count = extracted.get("page_count", len(pages_data))
        needs_ocr = extracted.get("needs_ocr", False)

        doc.page_count = page_count
        doc.needs_ocr = needs_ocr

        # Delete any existing pages/chunks for re-processing
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        db.query(DocumentPage).filter(DocumentPage.document_id == document_id).delete()

        # 2. Insert DocumentPage rows
        for p in pages_data:
            doc_page = DocumentPage(
                page_id=f"{document_id}_p{p.get('page_number', 1)}",
                document_id=document_id,
                workspace_id=doc.workspace_id,
                pdf_page_index=p.get("page_number", 1) - 1,
                printed_page_label=p.get("printed_page_label", str(p.get("page_number", 1))),
                raw_text=p.get("text", ""),
                is_scanned=p.get("is_scanned", False),
                char_count=p.get("char_count", 0),
            )
            db.add(doc_page)

        # 3. Extract Metadata
        meta = extract_paper_metadata(pages_data, doc.filename)
        doc.title = meta.get("title") or doc.filename
        doc.metadata_extracted = meta

        # Upsert PaperRecord
        paper_rec = db.query(PaperRecord).filter(PaperRecord.document_id == document_id).first()
        if not paper_rec:
            paper_rec = PaperRecord(
                record_id=f"rec_{document_id}",
                document_id=document_id,
                workspace_id=doc.workspace_id,
                user_id=doc.user_id,
                file_hash=doc.file_hash,
                title=doc.title,
                abstract=meta.get("abstract"),
                publication_year=meta.get("publication_year"),
                doi=meta.get("doi"),
                research_domain=meta.get("domain"),
            )
            db.add(paper_rec)
        else:
            paper_rec.title = doc.title
            paper_rec.abstract = meta.get("abstract")
            paper_rec.publication_year = meta.get("publication_year")
            paper_rec.doi = meta.get("doi")
            paper_rec.research_domain = meta.get("domain")

        # 4. Chunking (page-bounded, section-aware)
        chunks = create_page_chunks(
            document_id=document_id,
            filename=doc.filename,
            title=doc.title,
            pages_data=pages_data,
            target_tokens=settings.CHUNK_SIZE_TOKENS,
            overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
        )

        for c in chunks:
            db_chunk = DocumentChunk(
                chunk_id=c["chunk_id"],
                parent_id=c.get("parent_id"),
                document_id=document_id,
                workspace_id=doc.workspace_id,
                pdf_page=c["pdf_page"],
                printed_page=c["printed_page"],
                section=c["section"],
                text=c["text"],
                token_count=c["token_count"],
                char_start=c["char_start"],
                char_end=c["char_end"],
                is_parent=c["is_parent"],
                is_table=c["is_table"],
            )
            db.add(db_chunk)

        db.commit()

        # 5. Dual Indexing (ChromaDB + BM25)
        # We index non-parent chunks (or all chunks if no child chunks)
        indexable_chunks = [c for c in chunks if not c["is_parent"]]
        if not indexable_chunks:
            indexable_chunks = chunks

        if indexable_chunks:
            # Embeddings
            embedder = get_embedding_service()
            texts = [c["text"] for c in indexable_chunks]
            embeddings = embedder.embed_texts(texts)

            # ChromaDB
            vector_store = get_vector_store()
            vector_store.add_chunks(doc.workspace_id, indexable_chunks, embeddings)

            # BM25
            bm25_manager = get_bm25_manager()
            bm25_idx = bm25_manager.get_index(doc.workspace_id)
            bm25_idx.add_chunks(indexable_chunks)

        doc.processing_status = "completed"
        doc.error_message = None
        db.commit()

    except Exception as exc:
        db.rollback()
        doc.processing_status = "failed"
        doc.error_message = str(exc)
        db.commit()


@router.post("/upload", response_model=DocumentUploadResponse)
@router.post("/upload/", response_model=DocumentUploadResponse, include_in_schema=False)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: str = Form(settings.DEFAULT_WORKSPACE_ID),
    user_id: str = Form(settings.DEFAULT_USER_ID),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """Upload a single research paper PDF."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported for academic paper processing.",
        )

    # Enforce maximum documents per workspace
    existing_count = db.query(Document).filter(Document.workspace_id == workspace_id).count()
    if existing_count >= settings.MAX_DOCUMENTS_PER_WORKSPACE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workspace has reached maximum limit of {settings.MAX_DOCUMENTS_PER_WORKSPACE} papers.",
        )

    # Read content and compute hash
    content = await file.read()
    file_size = len(content)
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_BYTES / (1024*1024):.0f} MB.",
        )

    file_hash = compute_sha256(content)
    version = check_duplicate_and_version(db, file_hash, file.filename, workspace_id)

    doc_id = str(uuid.uuid4())
    stored_filename = f"{doc_id}_{file.filename}"
    file_path = settings.UPLOAD_DIR / stored_filename

    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        id=doc_id,
        workspace_id=workspace_id,
        user_id=user_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size_bytes=file_size,
        file_hash=file_hash,
        version=version,
        processing_status="queued",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Process immediately
    run_document_processing_pipeline(doc_id, db)

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        workspace_id=doc.workspace_id,
        file_size_bytes=doc.file_size_bytes,
        file_hash=doc.file_hash,
        version=doc.version,
        processing_status=doc.processing_status,
        message="Document uploaded and processed successfully." if doc.processing_status == "completed" else "Document uploaded and queued.",
    )


@router.post("/batch-upload", response_model=DocumentBatchUploadResponse)
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    workspace_id: str = Form(settings.DEFAULT_WORKSPACE_ID),
    user_id: str = Form(settings.DEFAULT_USER_ID),
    db: Session = Depends(get_db),
):
    """Upload multiple research paper PDFs simultaneously."""
    uploaded = []
    failed = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            failed.append({"filename": file.filename, "reason": "Not a PDF file."})
            continue

        try:
            content = await file.read()
            file_size = len(content)
            if file_size > settings.MAX_FILE_SIZE_BYTES:
                failed.append({"filename": file.filename, "reason": "Exceeds size limit."})
                continue

            file_hash = compute_sha256(content)
            version = check_duplicate_and_version(db, file_hash, file.filename, workspace_id)

            doc_id = str(uuid.uuid4())
            stored_filename = f"{doc_id}_{file.filename}"
            file_path = settings.UPLOAD_DIR / stored_filename

            with open(file_path, "wb") as f:
                f.write(content)

            doc = Document(
                id=doc_id,
                workspace_id=workspace_id,
                user_id=user_id,
                filename=file.filename,
                file_path=str(file_path),
                file_size_bytes=file_size,
                file_hash=file_hash,
                version=version,
                processing_status="queued",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            run_document_processing_pipeline(doc_id, db)

            uploaded.append(
                DocumentUploadResponse(
                    id=doc.id,
                    filename=doc.filename,
                    workspace_id=doc.workspace_id,
                    file_size_bytes=doc.file_size_bytes,
                    file_hash=doc.file_hash,
                    version=doc.version,
                    processing_status=doc.processing_status,
                    message="Processed successfully." if doc.processing_status == "completed" else "Failed processing.",
                )
            )
        except Exception as e:
            failed.append({"filename": file.filename, "reason": str(e)})

    return DocumentBatchUploadResponse(
        uploaded=uploaded,
        failed=failed,
        total_uploaded=len(uploaded),
        total_failed=len(failed),
    )


@router.get("", response_model=DocumentListResponse)
@router.get("/", response_model=DocumentListResponse, include_in_schema=False)
def list_documents(
    workspace_id: str = settings.DEFAULT_WORKSPACE_ID,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List documents scoped by workspace_id and optional user_id."""
    query = db.query(Document).filter(Document.workspace_id == workspace_id)
    if user_id:
        query = query.filter(Document.user_id == user_id)
    docs = query.order_by(Document.created_at.desc()).all()
    return DocumentListResponse(
        documents=docs,
        total=len(docs),
        workspace_id=workspace_id,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_details(
    document_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve complete metadata and status for a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
):
    """Lightweight processing status check."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
    paper = db.query(PaperRecord).filter(PaperRecord.document_id == document_id).first()

    return DocumentStatusResponse(
        id=doc.id,
        filename=doc.filename,
        processing_status=doc.processing_status,
        error_message=doc.error_message,
        page_count=doc.page_count,
        chunk_count=chunk_count,
        needs_ocr=doc.needs_ocr,
        title=doc.title,
        publication_year=paper.publication_year if paper else None,
        doi=paper.doi if paper else None,
    )


@router.post("/{document_id}/process")
def reprocess_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """Trigger manual re-processing of a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    run_document_processing_pipeline(document_id, db)
    return {"status": "ok", "message": f"Document {document_id} re-processed."}


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete document and cascade across SQLite, ChromaDB, and BM25 index.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    workspace_id = doc.workspace_id

    # 1. Delete from ChromaDB
    try:
        vector_store = get_vector_store()
        vector_store.delete_document(workspace_id, document_id)
    except Exception:
        pass

    # 2. Delete from BM25 index
    try:
        bm25_manager = get_bm25_manager()
        bm25_idx = bm25_manager.get_index(workspace_id)
        bm25_idx.delete_document(document_id)
    except Exception:
        pass

    # 3. Delete file from disk
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 4. Delete SQLite records (chunks, pages, paper record, document)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    db.query(DocumentPage).filter(DocumentPage.document_id == document_id).delete()
    db.query(PaperRecord).filter(PaperRecord.document_id == document_id).delete()
    db.delete(doc)
    db.commit()

    return {"status": "ok", "message": f"Document {document_id} deleted successfully."}


@router.get("/{document_id}/record", response_model=PaperRecordSchema)
@router.get("/{document_id}/record/", response_model=PaperRecordSchema)
def get_document_record(
    document_id: str,
    workspace_id: Optional[str] = Query(None, description="Workspace isolation scope"),
    force_refresh: bool = Query(False, description="Force re-extraction"),
    db: Session = Depends(get_db),
):
    """
    Retrieves the structured PaperRecord for a document.
    Extracts on demand if not yet extracted.
    """
    query = db.query(Document).filter(Document.id == document_id)
    if workspace_id:
        query = query.filter(Document.workspace_id == workspace_id)
    doc = query.first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found."
        )

    extractor = PaperExtractor()
    try:
        record = extractor.extract_from_document(
            document_id=doc.document_id,
            workspace_id=doc.workspace_id,
            force_refresh=force_refresh,
        )
        return record
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate structured paper record: {str(exc)}"
        )
