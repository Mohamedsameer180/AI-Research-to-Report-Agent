"""
Section detector for academic research papers.
Identifies standard IMRaD and related academic sections (Abstract, Introduction,
Related Work, Methodology, Experiments, Results, Discussion, Limitations, Conclusion, References).
"""
import re
from typing import Optional, Tuple

# Canonical section labels
CANONICAL_SECTIONS = [
    "abstract",
    "introduction",
    "related_work",
    "methodology",
    "experiments",
    "results",
    "discussion",
    "limitations",
    "conclusion",
    "references",
    "appendix",
    "other",
]

# Patterns for section headings
SECTION_PATTERNS = [
    (
        r"^(?:\d+[\.\)]?\s*)?(?:abstract)\b",
        "abstract"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:introduction|intro)\b",
        "introduction"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:related\s+work|literature\s+review|background|prior\s+work)\b",
        "related_work"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:methodology|method|methods|proposed\s+method|proposed\s+model|system\s+design|architecture|materials\s+and\s+methods)\b",
        "methodology"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:experimental\s+setup|experiments|experimental\s+evaluation|experimentation|empirical\s+evaluation)\b",
        "experiments"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:results|findings|experimental\s+results|empirical\s+results)\b",
        "results"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:discussion|general\s+discussion|analysis)\b",
        "discussion"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:limitations|threats\s+to\s+validity|ethical\s+considerations)\b",
        "limitations"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:conclusion|conclusions|concluding\s+remarks|summary\s+and\s+conclusion|conclusion\s+and\s+future\s+work|future\s+work)\b",
        "conclusion"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:references|bibliography|literature\s+cited)\b",
        "references"
    ),
    (
        r"^(?:\d+[\.\)]?\s*)?(?:appendix|supplementary|supplemental\s+material)\b",
        "appendix"
    ),
]

_COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), section)
    for pattern, section in SECTION_PATTERNS
]

# Roman numeral prefix pattern, e.g. "I. INTRODUCTION", "IV. RESULTS"
_ROMAN_PREFIX_RE = re.compile(
    r"^(?:[IVXLCDM]+\.|\d+(\.\d+)*\.?)\s+",
    re.IGNORECASE
)


def detect_section_heading(text: str) -> Optional[str]:
    """
    Check if a line or short block looks like a section heading.
    Returns the canonical section name or None.
    """
    cleaned = text.strip()
    if not cleaned or len(cleaned) > 120:
        return None

    # Strip leading roman numerals or decimal section numbering like "1.", "1.1", "II."
    normalized = _ROMAN_PREFIX_RE.sub("", cleaned).strip()

    for regex, section in _COMPILED_PATTERNS:
        if regex.search(normalized) or regex.search(cleaned):
            return section

    return None


def classify_text_section(text: str, current_section: str = "introduction") -> str:
    """
    Given a chunk or paragraph of text, determine whether it begins with
    a section transition. If so, return the new section; otherwise continue current.
    """
    first_lines = text.strip().split("\n")[:3]
    for line in first_lines:
        detected = detect_section_heading(line)
        if detected:
            return detected
    return current_section
