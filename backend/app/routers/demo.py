"""Isolated, fully fictional demo-persona setup."""

import secrets
from pathlib import Path

import numpy as np
from fastapi import APIRouter, HTTPException

from app.database import (
    clear_all_data,
    create_user,
    delete_document,
    insert_chunks,
    insert_document,
)
from app.demo_content import DEMO_DISPLAY_NAME, DEMO_PROFILE, DEMO_SUMMARY
from app.document_ids import namespace_parsed_result
from app.embedding import add_vectors, encode_batch
from app.memory import save_rolling_summary, save_user_profile
from app.parsers.csv_parser import parse_ledger_csv
from app.parsers.flomo_parser import parse_flomo_html
from app.parsers.md_parser import parse_markdown

router = APIRouter()
ASSET_DIR = Path(__file__).resolve().parent.parent / "demo_assets"


def _load_results() -> list[dict]:
    flomo = (ASSET_DIR / "xuyao_flomo.html").read_text(encoding="utf-8")
    review = (ASSET_DIR / "xuyao_review.md").read_text(encoding="utf-8")
    ledger = (ASSET_DIR / "xuyao_ledger.csv").read_text(encoding="utf-8")
    return [
        parse_flomo_html(flomo, "许遥的虚构日常记录.html"),
        parse_markdown(review, "许遥的2026上半年复盘.md"),
        parse_ledger_csv(ledger, "许遥的虚构账单.csv"),
    ]


def _persist_demo_result(result: dict, user_id: str) -> None:
    result = namespace_parsed_result(result, user_id)
    document = result["document"]
    chunks = result["chunks"]
    embeddable = [chunk for chunk in chunks if chunk["chunk_type"] != "ledger_row"]

    delete_document(document["doc_id"], user_id=user_id)
    if embeddable:
        embeddings = encode_batch([chunk["content"] for chunk in embeddable])
        ids = add_vectors(np.asarray(embeddings, dtype=np.float32), user_id=user_id)
        for chunk, faiss_id in zip(embeddable, ids):
            chunk["faiss_id"] = faiss_id

    insert_document(**document, user_id=user_id)
    insert_chunks(chunks)


@router.post("/demo/start")
def start_demo():
    """Create a private demo session backed only by original fictional data."""
    user_id = f"demo_{secrets.token_hex(8)}"
    create_user(user_id)
    try:
        for result in _load_results():
            _persist_demo_result(result, user_id)
        save_user_profile(DEMO_PROFILE, user_id=user_id)
        save_rolling_summary(DEMO_SUMMARY, user_id=user_id)
    except Exception as exc:
        clear_all_data(user_id=user_id)
        raise HTTPException(status_code=503, detail="示例数据准备失败，请稍后重试") from exc

    return {
        "status": "ok",
        "nickname": user_id,
        "display_name": DEMO_DISPLAY_NAME,
        "is_demo": True,
    }
