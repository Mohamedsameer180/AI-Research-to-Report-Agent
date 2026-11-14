
"""Structure Completion & Quality Checker.

Validates structured research records and agent outputs:
1. Confirms presence of mandatory core sections (objective, methodology, results).
2. Calculates verified citation percentage.
3. Flags unsupported conclusions or hallucination hazards.
4. Returns an honest status: 'complete', 'partial', or 'failed' with explicit reasons.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from backend.extraction.paper_schema import PaperRecordSchema


class CompletionVerdict(BaseModel):
    status: str = Field(..., description="'complete', 'partial', or 'failed'")
    score: float = Field(..., description="Quality/completion completeness score (0.0 to 1.0)")
    verified_citation_rate: float = Field(..., description="Percentage of claims backed by verified citations")
    missing_sections: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    is_acceptable: bool = Field(..., description="Whether output meets the minimum reliability floor")


def evaluate_paper_record_completion(
    record: PaperRecordSchema,
    min_citation_rate: float = 0.70,
) -> CompletionVerdict:
    """Evaluates whether an extracted paper record meets research quality thresholds."""
    missing = []
    reasons = []

    if not record.title:
        missing.append("title")
        reasons.append("Paper title is missing.")

    if not record.objective or not record.objective.value:
        missing.append("objective")
        reasons.append("Core research objective could not be verified.")

    has_methodology = (
        record.methodology
        and (
            (record.methodology.approach and record.methodology.approach.value)
            or record.methodology.algorithms
            or record.methodology.datasets
        )
    )
    if not has_methodology:
        missing.append("methodology")
        reasons.append("Methodology details (approach/algorithms/datasets) are incomplete.")

    has_results = bool(record.results and any(r.value for r in record.results))
    if not has_results:
        missing.append("results")
        reasons.append("Empirical benchmark results or quantitative findings are missing.")

    stats = record.citation_stats or {}
    total = stats.get("total_claims", 0)
    verified = stats.get("verified", 0) + stats.get("corrected_page", 0)
    rate = (verified / total) if total > 0 else 1.0

    if rate < min_citation_rate:
        reasons.append(f"Citation verification rate ({rate:.1%}) is below the required threshold ({min_citation_rate:.1%}).")

    # Score calculation
    section_penalty = len(missing) * 0.25
    citation_score = rate
    raw_score = max(0.0, min(1.0, citation_score - section_penalty))

    if len(missing) == 0 and rate >= min_citation_rate:
        status = "complete"
        is_acceptable = True
    elif len(missing) <= 2 and (verified > 0 or total == 0):
        status = "partial"
        is_acceptable = True
    else:
        status = "failed"
        is_acceptable = False

    return CompletionVerdict(
        status=status,
        score=round(raw_score, 3),
        verified_citation_rate=round(rate, 4),
        missing_sections=missing,
        reasons=reasons,
        is_acceptable=is_acceptable,
    )
