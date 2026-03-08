import json

from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException
from fastapi.responses import StreamingResponse

from app.parsers.flomo_parser import parse_flomo_html
from app.parsers.md_parser import parse_markdown
from app.parsers.csv_parser import parse_ledger_csv
from app.database import insert_document, insert_chunks, delete_document, get_all_documents, get_chunk_count_by_doc
from app.embedding import encode_batch, add_vectors

router = APIRouter()

BATCH_SIZE = 16


@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...), nickname: str = Form(...)):
    """Upload and process a file with SSE progress."""
    content = (await file.read()).decode("utf-8")
    filename = file.filename or "unknown"
    user_id = nickname.strip()

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

    def generate():
        import numpy as np

        # Separate chunks: only embed summaries, not individual ledger rows
        chunks_to_embed = [c for c in chunks if c["chunk_type"] != "ledger_row"]
        chunks_no_embed = [c for c in chunks if c["chunk_type"] == "ledger_row"]

        embed_total = len(chunks_to_embed)
        store_total = len(chunks)

        yield f"data: {json.dumps({'type': 'progress', 'stage': 'parse', 'message': f'解析完成，共 {store_total} 条数据，{embed_total} 条将进行语义索引', 'current': 0, 'total': embed_total})}\n\n"

        # Remove old data if re-uploading same doc
        delete_document(doc["doc_id"])

        # Embed only the embeddable chunks in batches with progress
        if chunks_to_embed:
            texts = [c["content"] for c in chunks_to_embed]
            all_embeddings = []
            for i in range(0, embed_total, BATCH_SIZE):
                batch = texts[i:i + BATCH_SIZE]
                emb = encode_batch(batch)
                all_embeddings.append(emb)
                done = min(i + BATCH_SIZE, embed_total)
                yield f"data: {json.dumps({'type': 'progress', 'stage': 'embed', 'message': '数据向量化处理中', 'current': done, 'total': embed_total})}\n\n"

            embeddings = np.vstack(all_embeddings)
            faiss_ids = add_vectors(embeddings, user_id=user_id)

            for chunk, fid in zip(chunks_to_embed, faiss_ids):
                chunk["faiss_id"] = fid

        # Non-embedded chunks keep faiss_id=None (already the default)

        insert_document(**doc, user_id=user_id)
        insert_chunks(chunks)

        yield f"data: {json.dumps({'type': 'done', 'doc_id': doc['doc_id'], 'source_type': doc['source_type'], 'source_name': doc['source_name'], 'chunk_count': store_total, 'embedded_count': embed_total, 'time_range_start': doc.get('time_range_start'), 'time_range_end': doc.get('time_range_end')})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/documents")
async def list_documents(nickname: str = Query(...)):
    """List all imported documents with chunk counts for a user."""
    docs = get_all_documents(user_id=nickname.strip())
    result = []
    for doc in docs:
        doc["chunk_count"] = get_chunk_count_by_doc(doc["doc_id"])
        result.append(doc)
    return {"documents": result}
