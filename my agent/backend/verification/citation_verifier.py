"""Programmatic Citation Verifier (Plain Python).

Verifies factual quotes against the underlying document text:
1. Normalizes ligatures, whitespace, and hyphenated line-wraps.
2. Checks exact substring match on the claimed page.
3. Performs RapidFuzz fuzzy matching (>= 90 threshold).
4. Tests adjacent pages (+-1) to detect and correct page-offset discrepancies.
5. Flags or purges ungrounded citations to ensure zero hallucination.
"""

import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import fuzz

from backend.extraction.paper_schema import (
    EvidenceItem,
    PaperRecordSchema,
    ResultFinding,
)

logger = logging.getLogger("taskfinisher.verification.citation")

# Standard ligatures and typography replacements
LIGATURE_MAP = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "\u00a0": " ",
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
}


def normalize_text(text: Optional[str]) -> str:
    """Normalizes whitespace, ligatures, Unicode artifacts, and hyphenation."""
    if not text:
        return ""

    s = unicodedata.normalize("NFKD", text)
    for lig, repl in LIGATURE_MAP.items():
        s = s.replace(lig, repl)

    # Rejoin hyphenated line wraps (e.g. "method- \nology" -> "methodology")
    s = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", s)

    # Collapse multiple whitespaces and newlines
    s = re.sub(r"\s+", " ", s).strip()
    return s


@dataclass
class CitationVerificationResult:
    status: str  # "verified", "corrected_page", "unverified"
    matched_page: Optional[int]
    matched_span: Optional[str]
    fuzzy_score: float
    is_valid: bool


class CitationVerifier:
    """Core verification engine running deterministic Python checks."""

    def __init__(self, fuzzy_threshold: float = 90.0):
        self.fuzzy_threshold = float(fuzzy_threshold)

    def verify_quote(
        self,
        quote: str,
        claimed_page: Optional[int],
        pages_dict: Dict[int, str],
        threshold: Optional[float] = None,
    ) -> CitationVerificationResult:
        """
        Verifies a quote against a dictionary of {pdf_page_number: page_text}.
        Page numbers in pages_dict should be 1-based integers.
        """
        thresh = self.fuzzy_threshold if threshold is None else float(threshold)

        if not quote or not quote.strip():
            return CitationVerificationResult(
                status="unverified",
                matched_page=None,
                matched_span=None,
                fuzzy_score=0.0,
                is_valid=False,
            )

        norm_quote = normalize_text(quote).lower()
        if not norm_quote:
            return CitationVerificationResult(
                status="unverified",
                matched_page=None,
                matched_span=None,
                fuzzy_score=0.0,
                is_valid=False,
            )

        if not pages_dict:
            return CitationVerificationResult(
                status="unverified",
                matched_page=claimed_page,
                matched_span=None,
                fuzzy_score=0.0,
                is_valid=False,
            )

        target_pages: List[int] = []
        if claimed_page and claimed_page in pages_dict:
            target_pages.append(claimed_page)

        # 1. Exact match on claimed page
        for p in target_pages:
            norm_page = normalize_text(pages_dict[p]).lower()
            if norm_quote in norm_page:
                idx = norm_page.find(norm_quote)
                span = pages_dict[p][max(0, idx - 5) : min(len(pages_dict[p]), idx + len(norm_quote) + 15)]
                return CitationVerificationResult(
                    status="verified",
                    matched_page=p,
                    matched_span=span or quote,
                    fuzzy_score=100.0,
                    is_valid=True,
                )

        # 2. Fuzzy match on claimed page
        for p in target_pages:
            norm_page = normalize_text(pages_dict[p]).lower()
            score = fuzz.partial_ratio(norm_quote, norm_page)
            if score >= thresh:
                return CitationVerificationResult(
                    status="verified",
                    matched_page=p,
                    matched_span=quote,
                    fuzzy_score=float(score),
                    is_valid=True,
                )

        # 3. Check adjacent pages (claimed_page - 1 and claimed_page + 1)
        adjacent_pages: List[int] = []
        if claimed_page:
            for offset in (-1, 1):
                adj = claimed_page + offset
                if adj in pages_dict and adj not in target_pages:
                    adjacent_pages.append(adj)

        for p in adjacent_pages:
            norm_page = normalize_text(pages_dict[p]).lower()
            if norm_quote in norm_page:
                idx = norm_page.find(norm_quote)
                span = pages_dict[p][max(0, idx - 5) : min(len(pages_dict[p]), idx + len(norm_quote) + 15)]
                return CitationVerificationResult(
                    status="corrected_page",
                    matched_page=p,
                    matched_span=span or quote,
                    fuzzy_score=100.0,
                    is_valid=True,
                )
            score = fuzz.partial_ratio(norm_quote, norm_page)
            if score >= thresh:
                return CitationVerificationResult(
                    status="corrected_page",
                    matched_page=p,
                    matched_span=quote,
                    fuzzy_score=float(score),
                    is_valid=True,
                )

        # 4. Search any other pages in the document to locate offsets
        best_page = None
        best_score = 0.0
        for p, page_text in pages_dict.items():
            if p in target_pages or p in adjacent_pages:
                continue
            norm_page = normalize_text(page_text).lower()
            if norm_quote in norm_page:
                return CitationVerificationResult(
                    status="corrected_page",
                    matched_page=p,
                    matched_span=quote,
                    fuzzy_score=100.0,
                    is_valid=True,
                )
            score = fuzz.partial_ratio(norm_quote, norm_page)
            if score > best_score:
                best_score = score
                best_page = p

        if best_score >= thresh and best_page:
            return CitationVerificationResult(
                status="corrected_page",
                matched_page=best_page,
                matched_span=quote,
                fuzzy_score=float(best_score),
                is_valid=True,
            )

        # Quote could not be validated
        return CitationVerificationResult(
            status="unverified",
            matched_page=claimed_page,
            matched_span=None,
            fuzzy_score=float(best_score),
            is_valid=False,
        )

    def verify_evidence_item(
        self,
        item: Optional[EvidenceItem[Any]],
        pages_dict: Dict[int, str],
        purge_unverified: bool = True,
    ) -> Optional[EvidenceItem[Any]]:
        """Verifies a single EvidenceItem and updates its audit metadata."""
        if item is None:
            return None

        if not item.quote:
            item.status = "unverified"
            item.fuzzy_score = 0.0
            if purge_unverified:
                item.value = None
            return item

        res = self.verify_quote(
            quote=item.quote,
            claimed_page=item.pdf_page,
            pages_dict=pages_dict,
        )

        item.status = res.status
        item.fuzzy_score = res.fuzzy_score
        item.matched_span = res.matched_span

        if res.status == "corrected_page" and res.matched_page:
            item.pdf_page = res.matched_page

        if not res.is_valid and purge_unverified:
            item.value = None

        return item

    def verify_result_item(
        self,
        item: ResultFinding,
        pages_dict: Dict[int, str],
        purge_unverified: bool = True,
    ) -> ResultFinding:
        """Verifies an empirical ResultFinding."""
        if not item.quote:
            item.status = "unverified"
            item.fuzzy_score = 0.0
            if purge_unverified:
                item.value = None
            return item

        res = self.verify_quote(
            quote=item.quote,
            claimed_page=item.pdf_page,
            pages_dict=pages_dict,
        )

        item.status = res.status
        item.fuzzy_score = res.fuzzy_score
        item.matched_span = res.matched_span
        if res.status == "corrected_page" and res.matched_page:
            item.pdf_page = res.matched_page

        if not res.is_valid and purge_unverified:
            item.value = None

        return item

    def verify_record(
        self,
        record: PaperRecordSchema,
        pages_dict: Dict[int, str],
        purge_unverified: bool = True,
    ) -> Tuple[PaperRecordSchema, Dict[str, Any]]:
        """
        Runs exhaustive verification across all factual sections of PaperRecordSchema.
        Returns the updated record and complete verification statistics.
        """
        stats = {
            "total_claims": 0,
            "verified": 0,
            "corrected_page": 0,
            "unverified": 0,
            "verification_rate": 0.0,
        }

        def _audit_evidence(item: Optional[EvidenceItem[Any]]):
            if item is None:
                return
            stats["total_claims"] += 1
            self.verify_evidence_item(item, pages_dict, purge_unverified=purge_unverified)
            if item.status == "verified":
                stats["verified"] += 1
            elif item.status == "corrected_page":
                stats["corrected_page"] += 1
            else:
                stats["unverified"] += 1

        # Check top-level evidence fields
        _audit_evidence(record.research_domain)
        _audit_evidence(record.objective)
        _audit_evidence(record.problem_statement)
        _audit_evidence(record.strengths)
        _audit_evidence(record.conclusion)

        # Check methodology
        if record.methodology:
            _audit_evidence(record.methodology.approach)
            _audit_evidence(record.methodology.preprocessing)
            for alg in record.methodology.algorithms:
                _audit_evidence(alg)
            for tech in record.methodology.technologies:
                _audit_evidence(tech)
            for ds in record.methodology.datasets:
                _audit_evidence(ds)

        # Check evaluation
        if record.evaluation:
            _audit_evidence(record.evaluation.experimental_setup)
            for met in record.evaluation.metrics:
                _audit_evidence(met)
            for base in record.evaluation.baselines:
                _audit_evidence(base)

        # Check results
        for res_item in record.results:
            stats["total_claims"] += 1
            self.verify_result_item(res_item, pages_dict, purge_unverified=purge_unverified)
            if res_item.status == "verified":
                stats["verified"] += 1
            elif res_item.status == "corrected_page":
                stats["corrected_page"] += 1
            else:
                stats["unverified"] += 1

        # Check limitations & future work
        for lim in record.limitations:
            _audit_evidence(lim)
        for fw in record.future_work:
            _audit_evidence(fw)

        total = stats["total_claims"]
        valid_count = stats["verified"] + stats["corrected_page"]
        stats["verification_rate"] = round(valid_count / total, 4) if total > 0 else 1.0
        record.citation_stats = stats

        return record, stats

