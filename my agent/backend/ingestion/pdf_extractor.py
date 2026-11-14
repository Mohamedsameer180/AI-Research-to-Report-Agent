import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pymupdf  # PyMuPDF

logger = logging.getLogger("tp01.ingestion.pdf")

LIGATURE_MAP = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
}


def clean_ligatures(text: str) -> str:
    """Replace common typography ligatures with plain ASCII equivalents."""
    for lig, rep in LIGATURE_MAP.items():
        text = text.replace(lig, rep)
    return text


def fix_hyphenation(text: str) -> str:
    """Join hyphenated words broken across line wraps (e.g., 'evalu- \\n ation' -> 'evaluation')."""
    return re.sub(r"(\b[A-Za-z]+)-\s*\n\s*([a-z]+)", r"\1\2\n", text)


def sort_blocks_two_column(blocks: List[Any], page_width: float) -> List[Any]:
    """
    Sort text blocks for academic PDFs:
    If content spans multiple columns, sort the left column top-to-bottom,
    then the right column top-to-bottom.
    Full-width blocks (like titles or abstracts) are placed in reading order.
    """
    if not blocks:
        return []

    mid_x = page_width / 2.0
    full_width_threshold = page_width * 0.70

    # Separate blocks into header/full-width, left column, right column
    full_width_blocks = []
    left_col = []
    right_col = []

    for b in blocks:
        # Block structure: (x0, y0, x1, y1, text, block_no, block_type)
        if len(b) < 5 or b[4].strip() == "":
            continue
        x0, y0, x1, y1 = b[0], b[1], b[2], b[3]
        width = x1 - x0

        if width >= full_width_threshold:
            full_width_blocks.append(b)
        elif x0 < mid_x and x1 <= (mid_x + 35):
            left_col.append(b)
        elif x0 >= (mid_x - 35):
            right_col.append(b)
        else:
            # Spans midpoint moderately
            full_width_blocks.append(b)

    # Sort each group top-to-bottom
    full_width_blocks.sort(key=lambda b: b[1])
    left_col.sort(key=lambda b: b[1])
    right_col.sort(key=lambda b: b[1])

    # Interleave full width based on vertical bounds
    # For standard academic two-column papers:
    # Full-width top (title, authors, abstract) -> Left col -> Right col -> Full width bottom
    ordered = []
    # Blocks above columns
    top_y = min((b[1] for b in (left_col + right_col)), default=float("inf"))
    for b in full_width_blocks:
        if b[3] <= top_y + 10:
            ordered.append(b)

    ordered.extend(left_col)
    ordered.extend(right_col)

    # Bottom full width (e.g. footnotes or wide figures)
    bottom_y = max((b[3] for b in (left_col + right_col)), default=0)
    for b in full_width_blocks:
        if b not in ordered:
            ordered.append(b)

    ordered.sort(key=lambda b: (0 if b in ordered[:len(full_width_blocks)] and b[3] <= top_y else 1, b[0] > mid_x, b[1]))
    return ordered if ordered else sorted(blocks, key=lambda b: (b[1], b[0]))


class ExtractedPage:
    def __init__(
        self,
        pdf_page_index: int,
        printed_page_label: Optional[str],
        text: str,
        is_scanned: bool,
        char_count: int,
        tables_text: List[str],
    ):
        self.pdf_page_index = pdf_page_index
        self.printed_page_label = printed_page_label or str(pdf_page_index + 1)
        self.text = text
        self.is_scanned = is_scanned
        self.char_count = char_count
        self.tables_text = tables_text


def extract_pdf_pages(file_path: Path) -> Tuple[List[ExtractedPage], bool]:
    """
    Extracts text from PDF using PyMuPDF:
    - Sorts blocks for two-column academic layouts
    - Strips repeated headers/footers
    - Cleans hyphenation & ligatures
    - Flags scanned pages (needs_ocr=True) without crashing
    - Best-effort table extraction
    """
    doc = pymupdf.open(str(file_path))
    raw_pages_blocks = []
    scanned_detected = False

    # First pass: collect raw blocks and text per page
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        rect = page.rect
        blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
        text_blocks = [b for b in blocks if len(b) >= 5 and b[4].strip() and b[6] == 0]

        # Best effort table extraction
        tables_text = []
        try:
            tabs = page.find_tables()
            for tab in tabs:
                df_text = tab.extract()
                if df_text:
                    table_str = "\n".join(["\t".join([str(c or "") for c in row]) for row in df_text])
                    tables_text.append(table_str)
        except Exception as e:
            logger.debug(f"Table extraction skipped for page {page_idx}: {e}")

        # Printed page number heuristic from page labels
        label = page.get_label() or None

        raw_pages_blocks.append({
            "page_idx": page_idx,
            "rect": rect,
            "blocks": text_blocks,
            "label": label,
            "tables": tables_text,
        })

    # Second pass: detect and strip recurring running headers/footers across pages
    header_candidates = {}
    footer_candidates = {}
    total_pages = len(raw_pages_blocks)

    if total_pages >= 3:
        for p in raw_pages_blocks:
            page_h = p["rect"].height
            for b in p["blocks"]:
                txt = b[4].strip()
                if not txt or len(txt) > 100:
                    continue
                # Top 7% of page = header
                if b[1] <= page_h * 0.08:
                    header_candidates[txt] = header_candidates.get(txt, 0) + 1
                # Bottom 7% of page = footer
                elif b[3] >= page_h * 0.92:
                    footer_candidates[txt] = footer_candidates.get(txt, 0) + 1

    recurring_headers = {txt for txt, count in header_candidates.items() if count >= max(2, total_pages * 0.5)}
    recurring_footers = {txt for txt, count in footer_candidates.items() if count >= max(2, total_pages * 0.5)}

    results: List[ExtractedPage] = []

    JOURNAL_HEADER_RE = re.compile(
        r"\b(ieee|acm|transactions|proceedings|journal|vol\.|conference|arxiv|published|issn|isbn)\b",
        re.IGNORECASE,
    )
    PAGE_NUM_RE = re.compile(r"^(?:page\s+)?(\d+)$", re.IGNORECASE)

    for p in raw_pages_blocks:
        page_idx = p["page_idx"]
        page_w = p["rect"].width
        page_h = p["rect"].height
        filtered_blocks = []

        for b in p["blocks"]:
            txt = b[4].strip()
            if not txt:
                continue

            # Strip recurring headers or standard publication banners in top 8%
            if b[1] <= page_h * 0.08:
                if txt in recurring_headers or JOURNAL_HEADER_RE.search(txt):
                    continue

            # Strip recurring footers or page numbers in bottom 8%
            if b[3] >= page_h * 0.92:
                pn_match = PAGE_NUM_RE.match(txt)
                if pn_match:
                    if not p["label"]:
                        p["label"] = pn_match.group(1)
                    continue
                if txt in recurring_footers:
                    continue

            filtered_blocks.append(b)

        # Sort two-column layouts
        sorted_blocks = sort_blocks_two_column(filtered_blocks, page_w)
        page_text = "\n\n".join(b[4].strip() for b in sorted_blocks if b[4].strip())

        # Clean ligatures and hyphenations
        page_text = clean_ligatures(page_text)
        page_text = fix_hyphenation(page_text)

        char_count = len(page_text.strip())
        is_scanned = char_count < 50
        if is_scanned:
            scanned_detected = True

        results.append(
            ExtractedPage(
                pdf_page_index=page_idx,
                printed_page_label=p["label"],
                text=page_text,
                is_scanned=is_scanned,
                char_count=char_count,
                tables_text=p["tables"],
            )
        )

    doc.close()
    return results, scanned_detected


def extract_pdf_data(file_path: Path) -> Dict[str, Any]:
    """High-level extractor returning dictionary structure for ingestion pipeline."""
    pages, scanned_detected = extract_pdf_pages(file_path)
    pages_list = []
    for p in pages:
        pages_list.append({
            "page_number": p.pdf_page_index + 1,
            "printed_page_label": p.printed_page_label,
            "text": p.text,
            "is_scanned": p.is_scanned,
            "char_count": p.char_count,
            "tables": [{"csv": t} for t in p.tables_text] if p.tables_text else [],
            "figures": [],
            "blocks": [],
        })
    return {
        "page_count": len(pages),
        "needs_ocr": scanned_detected,
        "pages": pages_list,
    }
