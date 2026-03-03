import hashlib
import re
from bs4 import BeautifulSoup


def parse_flomo_html(content: str, source_name: str) -> dict:
    """Parse Flomo exported HTML, return document + chunks."""
    soup = BeautifulSoup(content, "html.parser")
    memos = soup.select("div.memo")

    doc_id = _hash_id("flomo_html", source_name, content[:200])
    chunks = []
    times = []

    for i, memo in enumerate(memos):
        time_el = memo.select_one(".time")
        content_el = memo.select_one(".content")

        time_str = time_el.get_text(strip=True) if time_el else ""
        if time_str:
            times.append(time_str)

        text = content_el.get_text("\n", strip=True) if content_el else ""
        if not text:
            continue

        tags = re.findall(r"#(\S+)", text)

        # Split long memos
        text_chunks = _split_if_long(text, max_len=1200, min_len=600)

        for j, chunk_text in enumerate(text_chunks):
            chunk_id = f"{doc_id}_memo_{i}_{j}"
            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "chunk_type": "memo",
                "content": chunk_text,
                "metadata": {
                    "source_type": "flomo_html",
                    "source_name": source_name,
                    "date": time_str,
                    "tags": tags,
                },
            })

    time_range_start = min(times) if times else None
    time_range_end = max(times) if times else None

    document = {
        "doc_id": doc_id,
        "source_type": "flomo_html",
        "source_name": source_name,
        "time_range_start": time_range_start,
        "time_range_end": time_range_end,
        "metadata": {"memo_count": len(memos), "chunk_count": len(chunks)},
    }

    return {"document": document, "chunks": chunks}


def _split_if_long(text: str, max_len: int = 1200, min_len: int = 600) -> list[str]:
    if len(text) <= max_len:
        return [text]
    paragraphs = text.split("\n")
    result = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 1 > max_len and len(current) >= min_len:
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
