import json

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from app.parsers.flomo_parser import parse_flomo_html
from app.parsers.md_parser import parse_markdown
from app.parsers.csv_parser import parse_ledger_csv
from app.database import insert_document, insert_chunks, delete_document, get_all_documents, get_chunk_count_by_doc
from app.embedding import encode_batch, add_vectors

router = APIRouter()

BATCH_SIZE = 16


@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """Upload and process a file with SSE progress."""
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

    def generate():
        total = len(chunks)
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'parse', 'message': f'解析完成，共 {total} 个片段', 'current': 0, 'total': total})}\n\n"

        # Remove old data if re-uploading same doc
        delete_document(doc["doc_id"])

        # Generate embeddings in batches with progress
        import numpy as np
        texts = [c["content"] for c in chunks]
        all_embeddings = []
        for i in range(0, total, BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            emb = encode_batch(batch)
            all_embeddings.append(emb)
            done = min(i + BATCH_SIZE, total)
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'embed', 'message': f'数据向量化处理中', 'current': done, 'total': total})}\n\n"

        embeddings = np.vstack(all_embeddings)
        faiss_ids = add_vectors(embeddings)

        for chunk, fid in zip(chunks, faiss_ids):
            chunk["faiss_id"] = fid

        insert_document(**doc)
        insert_chunks(chunks)

        yield f"data: {json.dumps({'type': 'done', 'doc_id': doc['doc_id'], 'source_type': doc['source_type'], 'source_name': doc['source_name'], 'chunk_count': total, 'time_range_start': doc.get('time_range_start'), 'time_range_end': doc.get('time_range_end')})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/documents")
async def list_documents():
    """List all imported documents with chunk counts."""
    docs = get_all_documents()
    result = []
    for doc in docs:
        doc["chunk_count"] = get_chunk_count_by_doc(doc["doc_id"])
        result.append(doc)
    return {"documents": result}
