from fastapi import APIRouter, UploadFile, File, HTTPException

from app.parsers.flomo_parser import parse_flomo_html
from app.parsers.md_parser import parse_markdown
from app.parsers.csv_parser import parse_ledger_csv
from app.database import insert_document, insert_chunks, delete_document
from app.embedding import encode, add_vectors

router = APIRouter()


@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """Upload and process a file (HTML/MD/CSV). Auto parse + index."""
    content = (await file.read()).decode("utf-8")
    filename = file.filename or "unknown"

    try:
        if filename.endswith(".html") or filename.endswith(".htm"):
            result = parse_flomo_html(content, filename)
        elif filename.endswith(".md"):
            result = parse_markdown(content, filename)
        elif filename.endswith(".csv"):
            result = parse_ledger_csv(content, filename)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {filename}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = result["document"]
    chunks = result["chunks"]

    if not chunks:
        raise HTTPException(status_code=400, detail="文件解析后无有效内容")

    # Remove old data if re-uploading same doc
    delete_document(doc["doc_id"])

    # Generate embeddings
    texts = [c["content"] for c in chunks]
    embeddings = encode(texts)
    faiss_ids = add_vectors(embeddings)

    # Assign faiss_ids to chunks
    for chunk, fid in zip(chunks, faiss_ids):
        chunk["faiss_id"] = fid

    # Store in database
    insert_document(**doc)
    insert_chunks(chunks)

    return {
        "doc_id": doc["doc_id"],
        "source_type": doc["source_type"],
        "source_name": doc["source_name"],
        "chunk_count": len(chunks),
        "time_range_start": doc.get("time_range_start"),
        "time_range_end": doc.get("time_range_end"),
    }
