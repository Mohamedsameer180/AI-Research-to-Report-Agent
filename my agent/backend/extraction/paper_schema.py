"""Pydantic schemas for Phase 3 structured paper extraction.

Defines PaperRecord and EvidenceItem containers ensuring every factual field
maps to a verifiable verbatim quote (<= 300 chars) with pdf_page and printed_page.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class EvidenceItem(BaseModel, Generic[T]):
    """Atomic factual evidence binding a claim value to a verbatim source quote."""
    value: Optional[T] = Field(
        default=None,
        description="Extracted factual value, or null if unsupported by a verbatim quote."
    )
    quote: Optional[str] = Field(
        default=None,
        description="Verbatim excerpt (<= 300 characters) directly from the paper text."
    )
    pdf_page: Optional[int] = Field(
        default=None,
        description="1-based physical PDF page index where the quote is located."
    )
    printed_page: Optional[str] = Field(
        default=None,
        description="Author's printed page label as it appears in the footer/header (e.g. '142')."
    )
    section: Optional[str] = Field(
        default=None,
        description="Paper section name (e.g., 'abstract', 'methodology', 'results', 'limitations')."
    )
    status: str = Field(
        default="unverified",
        description="Verification state: 'verified', 'corrected_page', or 'unverified'."
    )
    matched_span: Optional[str] = Field(
        default=None,
        description="Exact matched text span identified in the document page."
    )
    fuzzy_score: float = Field(
        default=0.0,
        description="Rapidfuzz similarity ratio (0.0 to 100.0) against actual document text."
    )


class MethodologyDetails(BaseModel):
    """Methodological framework, algorithms, datasets, and preprocessing."""
    approach: Optional[EvidenceItem[str]] = None
    algorithms: List[EvidenceItem[str]] = Field(default_factory=list)
    technologies: List[EvidenceItem[str]] = Field(default_factory=list)
    datasets: List[EvidenceItem[str]] = Field(default_factory=list)
    preprocessing: Optional[EvidenceItem[str]] = None


class EvaluationDetails(BaseModel):
    """Evaluation metrics, comparison baselines, and experimental setup."""
    metrics: List[EvidenceItem[str]] = Field(default_factory=list)
    baselines: List[EvidenceItem[str]] = Field(default_factory=list)
    experimental_setup: Optional[EvidenceItem[str]] = None


class ResultFinding(BaseModel):
    """Specific empirical result or benchmark score reported in the experiments."""
    metric: Optional[str] = None
    value: Optional[str] = None
    dataset: Optional[str] = None
    conditions: Optional[str] = None
    quote: Optional[str] = None
    pdf_page: Optional[int] = None
    printed_page: Optional[str] = None
    section: Optional[str] = None
    status: str = "unverified"
    matched_span: Optional[str] = None
    fuzzy_score: float = 0.0


class ModelAnalysis(BaseModel):
    """Distinct, clearly labeled model synthesis (separate from verbatim extracted facts)."""
    contributions: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class PaperRecordSchema(BaseModel):
    """Consolidated structured record for a research paper in TP01."""
    record_id: str
    document_id: str
    workspace_id: str
    file_hash: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    research_domain: Optional[EvidenceItem[str]] = None
    objective: Optional[EvidenceItem[str]] = None
    problem_statement: Optional[EvidenceItem[str]] = None
    methodology: Optional[MethodologyDetails] = None
    evaluation: Optional[EvaluationDetails] = None
    results: List[ResultFinding] = Field(default_factory=list)
    strengths: Optional[EvidenceItem[str]] = None
    limitations: List[EvidenceItem[str]] = Field(default_factory=list)
    future_work: List[EvidenceItem[str]] = Field(default_factory=list)
    conclusion: Optional[EvidenceItem[str]] = None
    model_analysis: Optional[ModelAnalysis] = None
    citation_stats: Dict[str, Any] = Field(default_factory=dict)

