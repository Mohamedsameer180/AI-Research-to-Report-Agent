"""
Section-aware, page-bounded parent-child chunking for academic research papers.
Maintains exact character spans and page references for zero-hallucination citations.
"""
import uuid
from typing import List, Dict, Any, Optional
import tiktoken
from backend.ingestion.section_detector import classify_text_section

# Tokenizer initialization with safe fallback
try:
    _ENC = tiktoken.get_encoding("cl100k_base")
except Exception:
    _ENC = None


def count_tokens(text: str) -> int:
    """Return token count using tiktoken or whitespace fallback."""
    if _ENC is not None:
        return len(_ENC.encode(text, disallowed_special=()))
    return max(1, len(text.split()))


def chunk_text_sliding_window(
    text: str,
    target_tokens: int = 400,
    overlap_tokens: int = 60,
) -> List[Dict[str, Any]]:
    """
    Split text into sliding window slices bounded by tokens and paragraphs.
    Preserves character offsets (char_start, char_end).
    """
    if not text.strip():
        return []

    # If small enough, return as single chunk
    total_tokens = count_tokens(text)
    if total_tokens <= target_tokens + 50:
        return [{
            "text": text,
            "token_count": total_tokens,
            "char_start": 0,
            "char_end": len(text),
        }]

    # Split into paragraphs/sentences while tracking char offsets
    paragraphs = []
    start = 0
    raw_paras = text.split("\n\n")
    for p in raw_paras:
        p_len = len(p)
        if p.strip():
            paragraphs.append({
                "text": p,
                "start": start,
                "end": start + p_len,
                "tokens": count_tokens(p),
            })
        start += p_len + 2  # account for \n\n

    chunks = []
    current_tokens = 0
    curr_paras = []

    for p in paragraphs:
        if current_tokens + p["tokens"] > target_tokens and curr_paras:
            # Emit current slice
            chunk_text = text[curr_paras[0]["start"]: curr_paras[-1]["end"]]
            chunks.append({
                "text": chunk_text,
                "token_count": count_tokens(chunk_text),
                "char_start": curr_paras[0]["start"],
                "char_end": curr_paras[-1]["end"],
            })
            # Overlap: keep the last paragraph if possible
            if len(curr_paras) > 1 and curr_paras[-1]["tokens"] <= overlap_tokens * 1.5:
                curr_paras = [curr_paras[-1]]
                current_tokens = curr_paras[0]["tokens"]
            else:
                curr_paras = []
                current_tokens = 0

        curr_paras.append(p)
        current_tokens += p["tokens"]

    if curr_paras:
        chunk_text = text[curr_paras[0]["start"]: curr_paras[-1]["end"]]
        chunks.append({
            "text": chunk_text,
            "token_count": count_tokens(chunk_text),
            "char_start": curr_paras[0]["start"],
            "char_end": curr_paras[-1]["end"],
        })

    return chunks


def create_page_chunks(
    document_id: str,
    filename: str,
    title: str,
    pages_data: List[Dict[str, Any]],
    target_tokens: int = 400,
    overlap_tokens: int = 60,
) -> List[Dict[str, Any]]:
    """
    Produce page-bounded, section-aware parent and child chunks.
    Guarantees that child chunks do NOT span multiple PDF pages,
    enabling strictly accurate page-level citations.
    """
    all_chunks = []
    current_section = "introduction"

    for p in pages_data:
        pdf_page = p.get("page_number", 1)
        printed_page = p.get("printed_page_label", str(pdf_page))
        page_text = p.get("text", "")
        if not page_text.strip():
            continue

        # Check section transition on this page
        current_section = classify_text_section(page_text, current_section)

        # 1. Create Parent Chunk for the page/section
        parent_id = f"{document_id}_p{pdf_page}_parent"
        parent_token_count = count_tokens(page_text)
        parent_chunk = {
            "chunk_id": parent_id,
            "parent_id": None,
            "document_id": document_id,
            "filename": filename,
            "title": title,
            "pdf_page": pdf_page,
            "printed_page": printed_page,
            "section": current_section,
            "text": page_text,
            "token_count": parent_token_count,
            "char_start": 0,
            "char_end": len(page_text),
            "is_parent": True,
            "is_table": False,
        }
        all_chunks.append(parent_chunk)

        # 2. Create Child Chunks via sliding window within the page
        slices = chunk_text_sliding_window(page_text, target_tokens=target_tokens, overlap_tokens=overlap_tokens)
        for idx, s in enumerate(slices):
            child_id = f"{document_id}_p{pdf_page}_c{idx+1}"
            child_chunk = {
                "chunk_id": child_id,
                "parent_id": parent_id,
                "document_id": document_id,
                "filename": filename,
                "title": title,
                "pdf_page": pdf_page,
                "printed_page": printed_page,
                "section": current_section,
                "text": s["text"],
                "token_count": s["token_count"],
                "char_start": s["char_start"],
                "char_end": s["char_end"],
                "is_parent": False,
                "is_table": False,
            }
            all_chunks.append(child_chunk)

        # 3. Add any extracted tables as specialized chunks
        tables = p.get("tables", [])
        for t_idx, tbl in enumerate(tables):
            csv_repr = tbl.get("csv", "")
            if csv_repr.strip():
                table_id = f"{document_id}_p{pdf_page}_tbl{t_idx+1}"
                table_chunk = {
                    "chunk_id": table_id,
                    "parent_id": parent_id,
                    "document_id": document_id,
                    "filename": filename,
                    "title": title,
                    "pdf_page": pdf_page,
                    "printed_page": printed_page,
                    "section": current_section,
                    "text": f"Table on page {printed_page}:\n{csv_repr}",
                    "token_count": count_tokens(csv_repr),
                    "char_start": 0,
                    "char_end": len(csv_repr),
                    "is_parent": False,
                    "is_table": True,
                }
                all_chunks.append(table_chunk)

    return all_chunks

