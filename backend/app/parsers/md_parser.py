import hashlib
import re
from pathlib import Path


def parse_markdown(content: str, source_name: str) -> dict:
    """Parse a markdown file, return document + chunks."""
    doc_id = _hash_id("review_md", source_name, content[:200])

    # Time inference
    time_range = _infer_time_range(content, source_name)

    # Split into sections
    sections = _split_by_headings(content)
    chunks = []

    for i, section in enumerate(sections):
        text = section["text"].strip()
        if not text or len(text) < 10:
            continue
        # Further split long sections
        sub_chunks = _split_if_long(text)
        for j, chunk_text in enumerate(sub_chunks):
            chunk_id = f"{doc_id}_sec_{i}_{j}"
            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "chunk_type": "md_section",
                "content": chunk_text,
                "metadata": {
                    "source_type": "review_md",
                    "source_name": source_name,
                    "heading_path": section.get("heading", ""),
                    "time_range": time_range.get("value"),
                    "time_confidence": time_range.get("confidence"),
                },
            })

    document = {
        "doc_id": doc_id,
        "source_type": "review_md",
        "source_name": source_name,
        "time_range_start": time_range.get("value"),
        "time_range_end": time_range.get("value"),
        "metadata": {
            "section_count": len(sections),
            "chunk_count": len(chunks),
            "time_confidence": time_range.get("confidence"),
        },
    }

    return {"document": document, "chunks": chunks}


def _split_by_headings(content: str) -> list[dict]:
    lines = content.split("\n")
    sections = []
    current_heading = ""
    current_lines = []

    for line in lines:
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            if current_lines:
                sections.append({
                    "heading": current_heading,
                    "text": "\n".join(current_lines),
                })
            current_heading = heading_match.group(2).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "heading": current_heading,
            "text": "\n".join(current_lines),
        })

    # If no headings found, split by paragraphs
    if len(sections) <= 1 and len(content) > 500:
        return _split_by_paragraphs(content)

    return sections


def _split_by_paragraphs(content: str) -> list[dict]:
    paragraphs = re.split(r"\n\s*\n", content)
    sections = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) > 500 and current:
            sections.append({"heading": "", "text": current.strip()})
            current = p
        else:
            current = current + "\n\n" + p if current else p
    if current.strip():
        sections.append({"heading": "", "text": current.strip()})
    return sections


def _infer_time_range(content: str, source_name: str) -> dict:
    """Infer time range from frontmatter, filename, or content."""
    # 1. Try frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        date_match = re.search(r"date:\s*(\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?)", fm)
        if date_match:
            return {"value": date_match.group(1), "confidence": "high"}

    # 2. Try filename
    fn_year = re.search(r"(20\d{2})", source_name)
    fn_month = re.search(r"(\d{1,2})月", source_name)
    if fn_year:
        val = fn_year.group(1)
        if fn_month:
            val += f"-{int(fn_month.group(1)):02d}"
        return {"value": val, "confidence": "medium"}

    # 3. Try content
    content_date = re.search(r"(20\d{2})[\-年/](\d{1,2})月?", content)
    if content_date:
        val = f"{content_date.group(1)}-{int(content_date.group(2)):02d}"
        return {"value": val, "confidence": "low"}

    year_only = re.search(r"(20\d{2})", content[:500])
    if year_only:
        return {"value": year_only.group(1), "confidence": "low"}

    return {"value": None, "confidence": None}


def _split_if_long(text: str, max_len: int = 500) -> list[str]:
    """Split text that exceeds embedding model's effective window (~512 tokens ≈ 300-400 Chinese chars)."""
    if len(text) <= max_len:
        return [text]
    paragraphs = text.split("\n")
    result = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 1 > max_len and current:
            result.append(current.strip())
            current = p
        else:
            current = current + "\n" + p if current else p
    if current.strip():
        result.append(current.strip())
    return result if result else [text]


def _hash_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
