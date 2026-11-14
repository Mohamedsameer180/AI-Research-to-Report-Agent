"""Research API endpoints for TP01 Research Platform.

Provides structured per-paper extraction, objective & methodology analysis,
empirical findings breakdown, and citation-verified groundings.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import Document, PaperRecord
from backend.extraction.paper_extractor import PaperExtractor
from backend.extraction.paper_schema import PaperRecordSchema

logger = logging.getLogger("taskfinisher.api.research")

router = APIRouter(prefix="/research", tags=["research"])


class AnalyzePaperRequest(BaseModel):
    document_id: str = Field(..., description="Document ID to analyze and extract")
    workspace_id: Optional[str] = Field("default_workspace", description="Workspace isolation scope")
    force_refresh: bool = Field(False, description="Bypass cache and force re-extraction")


@router.post("/analyze", response_model=PaperRecordSchema)
@router.post("/analyze/", response_model=PaperRecordSchema)
def analyze_paper(
    req: AnalyzePaperRequest,
    db: Session = Depends(get_db),
):
    """
    Analyzes a document section-by-section, extracting objectives, methodology,
    empirical results, and limitations, binding all claims to verbatim quotes.
    """
    # Verify document exists in workspace
    doc = db.query(Document).filter(
        Document.document_id == req.document_id,
        Document.workspace_id == req.workspace_id,
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {req.document_id} not found in workspace {req.workspace_id}.",
        )

    try:
        extractor = PaperExtractor()
        record = extractor.extract_from_document(
            document_id=req.document_id,
            workspace_id=req.workspace_id,
            force_refresh=req.force_refresh,
        )
        return record
    except Exception as exc:
        logger.error("Paper extraction failed for doc %s: %s", req.document_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failure: {str(exc)}",
        )

