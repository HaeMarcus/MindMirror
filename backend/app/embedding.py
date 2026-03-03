import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path

from app.config import EMBEDDING_MODEL, EMBEDDING_DIM, FAISS_INDEX_PATH

_model: SentenceTransformer | None = None
_index: faiss.IndexFlatIP | None = None
_next_id: int = 0


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def encode(texts: list[str]) -> np.ndarray:
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return np.array(embeddings, dtype=np.float32)


def get_index() -> faiss.IndexFlatIP:
    global _index, _next_id
    if _index is None:
        if Path(FAISS_INDEX_PATH).exists():
            _index = faiss.read_index(str(FAISS_INDEX_PATH))
            _next_id = _index.ntotal
        else:
            _index = faiss.IndexFlatIP(EMBEDDING_DIM)
            _next_id = 0
    return _index


def add_vectors(embeddings: np.ndarray) -> list[int]:
    """Add vectors to FAISS index, return assigned IDs."""
    global _next_id
    index = get_index()
    start_id = _next_id
    index.add(embeddings)
    ids = list(range(start_id, start_id + len(embeddings)))
    _next_id = start_id + len(embeddings)
    save_index()
    return ids


def search(query_embedding: np.ndarray, top_k: int = 12) -> list[tuple[int, float]]:
    """Search FAISS index, return list of (faiss_id, score)."""
    index = get_index()
    if index.ntotal == 0:
        return []
    scores, indices = index.search(query_embedding.reshape(1, -1), min(top_k, index.ntotal))
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0:
            results.append((int(idx), float(score)))
    return results


def save_index():
    index = get_index()
    faiss.write_index(index, str(FAISS_INDEX_PATH))


def rebuild_index(all_embeddings: np.ndarray):
    """Rebuild the entire FAISS index from scratch."""
    global _index, _next_id
    _index = faiss.IndexFlatIP(EMBEDDING_DIM)
    if len(all_embeddings) > 0:
        _index.add(all_embeddings)
    _next_id = len(all_embeddings)
    save_index()
