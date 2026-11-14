"""
Ingestion package for TP01 Research Platform.
"""
from backend.ingestion.dedup import compute_sha256, check_duplicate_and_version
from backend.ingestion.pdf_extractor import extract_pdf_data
from backend.ingestion.section_detector import detect_section_heading, classify_text_section
from backend.ingestion.metadata import extract_paper_metadata
from backend.ingestion.chunker import create_page_chunks, count_tokens

__all__ = [
    "compute_sha256",
    "check_duplicate_and_version",
    "extract_pdf_data",
    "detect_section_heading",
    "classify_text_section",
    "extract_paper_metadata",
    "create_page_chunks",
    "count_tokens",
]
