import os
import re
import unicodedata
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

from config import settings

# --- TEXT CLEANING ---
class TextCleaner:
    MOJIBAKE_MAP = {
        "\u00e2\u20ac\u2122": "'",
        "\u00e2\u20ac\u02dc": "'",
        "\u00e2\u20ac\u0153": '"',
        "\u00e2\u20ac\u009d": '"',
        "\u00e2\u20ac\u2014": "—",
        "\u00e2\u20ac\u2013": "–",
        "\u00e2\u20ac\u00a6": "...",
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€”": "—",
        "â€“": "–",
        "â€¦": "...",
        "\xa0": " ",
        "\u200b": "",
        "\ufeff": "",
    }

    PAGE_NUM_PATTERNS = [
        re.compile(r"^\s*page\s+\d+(\s+of\s+\d+)?\s*$", re.IGNORECASE),
        re.compile(r"^\s*-\s*\d+\s*-\s*$"),
        re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
        re.compile(r"^\s*\d+\s*$"),
    ]

    @classmethod
    def clean(cls, text: str) -> str:
        if not text:
            return ""
        # 1. Mojibake repair
        for bad, good in cls.MOJIBAKE_MAP.items():
            if bad in text:
                text = text.replace(bad, good)

        # 2. NFKC Unicode normalization
        text = unicodedata.normalize("NFKC", text)

        # 3. Broken hyphenation repair across lines
        text = re.sub(r"([A-Za-z]{3,})-\n\s*([a-z]{3,})", r"\1\2", text)

        # 4. Remove pagination artifacts
        lines = [line.rstrip() for line in text.split("\n")]
        filtered_lines = [l for l in lines if not any(p.match(l.strip()) for p in cls.PAGE_NUM_PATTERNS)]
        text = "\n".join(filtered_lines)

        # 5. Normalize whitespace (max 2 consecutive newlines)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{3,}", "  ", text)
        return text.strip()

    @classmethod
    def strip_recurring_headers_footers(cls, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(pages) < 3:
            return pages
        top_lines, bottom_lines = [], []
        for p in pages:
            lines = [l.strip() for l in p.get("text", "").split("\n") if l.strip()]
            if lines:
                top_lines.append(lines[0])
                if len(lines) > 1:
                    bottom_lines.append(lines[-1])

        threshold = max(2, int(len(pages) * 0.35))
        recurring = {l for l, c in Counter(top_lines).items() if c >= threshold}
        recurring.update({l for l, c in Counter(bottom_lines).items() if c >= threshold})

        for p in pages:
            lines = p.get("text", "").split("\n")
            p["text"] = "\n".join(l for l in lines if l.strip() not in recurring).strip()
        return pages

# --- PARSING & EXTRACTION ---
def format_table_as_markdown(table: List[List[Optional[str]]]) -> str:
    if not table or not table[0]:
        return ""
    cleaned_rows = []
    for row in table:
        cleaned_row = [str(c).strip().replace("\n", " ") if c is not None else "" for c in row]
        if any(cleaned_row):
            cleaned_rows.append(cleaned_row)
    if not cleaned_rows:
        return ""

    headers = cleaned_rows[0]
    md = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in cleaned_rows[1:]:
        if len(row) < len(headers):
            row.extend([""] * (len(headers) - len(row)))
        md.append("| " + " | ".join(row[:len(headers)]) + " |")
    return "\n".join(md)

def parse_pdf(file_path: str, max_pages: int = settings.MAX_PAGES_LIMIT) -> List[Dict[str, Any]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Corrupted or invalid PDF: {e}")

    total_pages = min(len(doc), max_pages)
    if total_pages == 0:
        doc.close()
        raise ValueError("Empty PDF containing 0 pages.")

    pages_out: List[Dict[str, Any]] = []
    plumber_pdf = None

    try:
        for p_idx in range(total_pages):
            page = doc[p_idx]
            page_num = p_idx + 1
            text = page.get_text("text").strip()
            images = page.get_images(full=True)
            drawings = page.get_drawings()
            content_type = "prose"

            table_parts = []
            if len(drawings) > 4 or "|" in text or "\t" in text:
                try:
                    if plumber_pdf is None:
                        plumber_pdf = pdfplumber.open(file_path)
                    if p_idx < len(plumber_pdf.pages):
                        tables = plumber_pdf.pages[p_idx].extract_tables()
                        for tbl in tables:
                            md_tbl = format_table_as_markdown(tbl)
                            if md_tbl:
                                table_parts.append(md_tbl)
                                content_type = "table"
                except Exception:
                    pass

            # OCR fallback for image-dominant pages
            if len(text) < 60 and (images or drawings) and HAS_TESSERACT:
                try:
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_res = pytesseract.image_to_string(img).strip()
                    if len(ocr_res) > 30:
                        text = ocr_res
                        content_type = "scanned_ocr"
                except Exception:
                    pass

            combined_blocks = []
            if text:
                combined_blocks.append(text)
            if table_parts:
                combined_blocks.extend(table_parts)

            full_page_text = "\n\n".join(combined_blocks).strip()
            if full_page_text:
                pages_out.append({
                    "page_number": page_num,
                    "text": full_page_text,
                    "content_type": content_type,
                })
    finally:
        doc.close()
        if plumber_pdf:
            try:
                plumber_pdf.close()
            except Exception:
                pass

    return pages_out

# --- CHUNKING: PARENT-CHILD & DOCUMENT-AWARE ---
HEADING_REGEX = re.compile(
    r"^(?:#{1,6}\s+.*|[0-9]{1,2}(?:\.[0-9]{1,2})*\s+[A-Z][A-Za-z0-9\s]{2,50}|[A-Z\s]{4,40})$",
    re.MULTILINE,
)

def create_parent_child_chunks(
    pages: List[Dict[str, Any]],
    document_id: str,
    filename: str,
    parent_size: int = settings.PARENT_CHUNK_SIZE,
    child_size: int = settings.CHILD_CHUNK_SIZE,
    child_overlap: int = settings.CHILD_CHUNK_OVERLAP,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Creates Document-Aware Parent Sections and smaller Child Chunks.
    Returns: (child_chunks_to_embed, parent_chunks_for_context)
    """
    parents: List[Dict[str, Any]] = []
    children: List[Dict[str, Any]] = []

    current_section = "Overview"
    parent_counter = 0
    child_counter = 0

    for page in pages:
        p_num = page["page_number"]
        raw_text = page["text"]
        base_type = page.get("content_type", "prose")

        # 1. Detect section heading on page
        for line in raw_text.split("\n")[:4]:
            if HEADING_REGEX.match(line.strip()):
                current_section = line.strip().lstrip("#").strip()
                break

        # 2. Split page into Parent Sections (document-aware: paragraphs / headings)
        paragraphs = raw_text.split("\n\n")
        parent_buffer: List[str] = []
        current_len = 0

        page_parents: List[Dict[str, Any]] = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if HEADING_REGEX.match(para):
                current_section = para.lstrip("#").strip()

            if current_len + len(para) + 2 > parent_size and parent_buffer:
                p_text = "\n\n".join(parent_buffer)
                p_id = f"{document_id}_p{p_num}_parent_{parent_counter}"
                parent_counter += 1
                page_parents.append({
                    "parent_id": p_id,
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": p_num,
                    "section_heading": current_section,
                    "content_type": base_type,
                    "text": p_text,
                })
                parent_buffer = [para]
                current_len = len(para)
            else:
                parent_buffer.append(para)
                current_len += len(para) + 2

        if parent_buffer:
            p_text = "\n\n".join(parent_buffer)
            p_id = f"{document_id}_p{p_num}_parent_{parent_counter}"
            parent_counter += 1
            page_parents.append({
                "parent_id": p_id,
                "document_id": document_id,
                "filename": filename,
                "page_number": p_num,
                "section_heading": current_section,
                "content_type": base_type,
                "text": p_text,
            })

        parents.extend(page_parents)

        # 3. For each Parent Section, generate smaller Child Chunks
        for p in page_parents:
            p_text = p["text"]
            p_id = p["parent_id"]

            # Split parent text by sentences for fine-grained child chunking
            sentences = re.split(r"(?<=[.!?])\s+", p_text)
            child_buffer: List[str] = []
            child_len = 0

            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if child_len + len(s) + 1 > child_size and child_buffer:
                    c_text = " ".join(child_buffer)
                    c_id = f"{document_id}_p{p_num}_child_{child_counter}"
                    child_counter += 1
                    children.append({
                        "id": c_id,
                        "text": c_text,
                        "parent_id": p_id,
                        "metadata": {
                            "document_id": document_id,
                            "source_filename": filename,
                            "page_number": p_num,
                            "section_heading": current_section,
                            "content_type": p["content_type"],
                            "parent_id": p_id,
                        },
                    })
                    # Overlap with last sentence
                    child_buffer = [child_buffer[-1], s] if len(child_buffer[-1]) <= child_overlap else [s]
                    child_len = sum(len(x) for x in child_buffer) + len(child_buffer) - 1
                else:
                    child_buffer.append(s)
                    child_len += len(s) + 1

            if child_buffer:
                c_text = " ".join(child_buffer)
                c_id = f"{document_id}_p{p_num}_child_{child_counter}"
                child_counter += 1
                children.append({
                    "id": c_id,
                    "text": c_text,
                    "parent_id": p_id,
                    "metadata": {
                        "document_id": document_id,
                        "source_filename": filename,
                        "page_number": p_num,
                        "section_heading": current_section,
                        "content_type": p["content_type"],
                        "parent_id": p_id,
                    },
                })

    return children, parents
