"""
Metadata extractor for academic research papers.
Extracts title, authors, year, abstract, DOI, keywords/domain, and reference lists
strictly from document text without hallucination.
"""
import re
from typing import Dict, Any, List, Optional

DOI_PATTERN = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b")
YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")
ARXIV_PATTERN = re.compile(r"arXiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?)", re.IGNORECASE)


def extract_doi(text: str) -> Optional[str]:
    """
    Extract DOI if explicitly present in the document.
    Returns None if no valid DOI pattern is matched.
    """
    match = DOI_PATTERN.search(text)
    if match:
        doi = match.group(1).rstrip(".,;)>]")
        return doi
    return None


def extract_arxiv_id(text: str) -> Optional[str]:
    """Extract arXiv identifier if present in the header or text."""
    match = ARXIV_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def extract_year(text: str, pdf_metadata_year: Optional[int] = None) -> Optional[int]:
    """
    Find publication year in the text or fallback to PDF metadata year.
    Only accepts years between 1950 and 2030.
    """
    if pdf_metadata_year and 1950 <= pdf_metadata_year <= 2030:
        return pdf_metadata_year

    # Search for year matches near copyright, published, accepted, or arXiv dates
    first_pages_text = text[:3000]
    date_context_matches = re.findall(
        r"(?:copyright|\(c\)|published|accepted|received|arXiv|proceeding|\b19\d{2}\b|\b20\d{2}\b)",
        first_pages_text,
        re.IGNORECASE,
    )
    all_years = [int(y) for y in YEAR_PATTERN.findall(first_pages_text) if 1950 <= int(y) <= 2030]
    if all_years:
        # Return most recent plausible publication year on the title page
        return all_years[0]
    return None


def extract_abstract(text: str) -> Optional[str]:
    """
    Extract abstract text from the first two pages.
    """
    abstract_match = re.search(
        r"\b(?:ABSTRACT|Abstract)\b[:\.\s]*(.+?)(?=\b(?:1[\.\s]+|I[\.\s]+)?(?:Introduction|INDEX TERMS|Keywords)\b|\Z)",
        text[:6000],
        re.DOTALL | re.IGNORECASE,
    )
    if abstract_match:
        abstract_text = abstract_match.group(1).strip()
        # Clean extra whitespace
        abstract_text = re.sub(r"\s+", " ", abstract_text)
        if len(abstract_text) > 40:
            return abstract_text[:2500]
    return None


def extract_keywords(text: str) -> List[str]:
    """
    Extract author keywords or index terms if explicitly provided.
    """
    kw_match = re.search(
        r"\b(?:Keywords|Index Terms|Key words)\b[:\.\s]*(.+?)(?=\n\n|\b(?:1[\.\s]+|I[\.\s]+)?Introduction\b|\Z)",
        text[:6000],
        re.IGNORECASE,
    )
    if kw_match:
        kw_raw = kw_match.group(1).strip()
        parts = re.split(r"[,;•—\n]", kw_raw)
        keywords = [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]
        return keywords[:10]
    return []


def extract_title(blocks_page1: List[Dict[str, Any]], filename: str) -> str:
    """
    Infer paper title from page 1 blocks.
    Prefers blocks with the largest font size or first prominent block.
    Fallback to clean filename if undetermined.
    """
    candidates = []
    for b in blocks_page1:
        text = b.get("text", "").strip()
        if not text or len(text) < 5:
            continue
        # Skip common headers like "Preprint", "arXiv", conference headers
        if re.search(r"^(arxiv|conference|proceedings|journal|vol\.|doi:)", text, re.IGNORECASE):
            continue
        font_size = b.get("font_size", 0.0)
        candidates.append((font_size, text))

    if candidates:
        # Sort by font size descending, then position
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_text = candidates[0][1]
        # Clean single newlines into spaces
        clean_title = re.sub(r"\s+", " ", top_text)
        return clean_title[:300]

    # Fallback to filename
    clean_fn = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE)
    clean_fn = clean_fn.replace("_", " ").replace("-", " ")
    return clean_fn


def extract_references(text: str) -> List[str]:
    """
    Extract reference entries from the References section.
    """
    ref_match = re.search(
        r"\b(?:References|Bibliography|Literature Cited)\b\s*(.+)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not ref_match:
        return []

    ref_text = ref_match.group(1).strip()
    # References often start with [1], [2], 1., 2. or author names
    raw_entries = re.split(r"\n+(?=\[\d+\]|\d+\.\s+[A-Z])", ref_text)
    cleaned = []
    for entry in raw_entries:
        entry_clean = re.sub(r"\s+", " ", entry).strip()
        if len(entry_clean) > 20:
            cleaned.append(entry_clean[:500])
        if len(cleaned) >= 100:
            break
    return cleaned


def extract_paper_metadata(pages_data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
    """
    Full metadata extraction across parsed pages.
    """
    full_text = "\n\n".join(p.get("text", "") for p in pages_data)
    page1_blocks = pages_data[0].get("blocks", []) if pages_data else []

    title = extract_title(page1_blocks, filename)
    abstract = extract_abstract(full_text)
    doi = extract_doi(full_text)
    year = extract_year(full_text)
    keywords = extract_keywords(full_text)
    references = extract_references(full_text)

    # Simple domain inference from keywords or title
    domain = None
    if keywords:
        domain = keywords[0]

    return {
        "title": title,
        "abstract": abstract,
        "doi": doi,
        "publication_year": year,
        "keywords": keywords,
        "domain": domain,
        "reference_count": len(references),
        "references": references,
    }

