import hashlib

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path

from app.config import EMBEDDING_MODEL, EMBEDDING_DIM, FAISS_INDEX_DIR

_model: SentenceTransformer | None = None

# Per-user index cache: user_id -> (index, next_id)
_indexes: dict[str, faiss.IndexFlatIP] = {}
_next_ids: dict[str, int] = {}


def _index_path(user_id: str) -> Path:
    """Get the FAISS index file path for a user (hash nickname for safe filenames)."""
    safe_name = hashlib.sha256(user_id.encode()).hexdigest()[:16]
    return FAISS_INDEX_DIR / f"{safe_name}.faiss"


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def encode(texts: list[str]) -> np.ndarray:
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return np.array(embeddings, dtype=np.float32)


def encode_batch(texts: list[str]) -> np.ndarray:
    """Encode a small batch — same as encode but named for clarity in progress tracking."""
    return encode(texts)


def get_index(user_id: str) -> faiss.IndexFlatIP:
    """Get or load the FAISS index for a specific user."""
    if user_id not in _indexes:
        path = _index_path(user_id)
        if path.exists():
            _indexes[user_id] = faiss.read_index(str(path))
            _next_ids[user_id] = _indexes[user_id].ntotal
        else:
            _indexes[user_id] = faiss.IndexFlatIP(EMBEDDING_DIM)
            _next_ids[user_id] = 0
    return _indexes[user_id]


def add_vectors(embeddings: np.ndarray, user_id: str) -> list[int]:
    """Add vectors to a user's FAISS index, return assigned IDs."""
    index = get_index(user_id)
    start_id = _next_ids[user_id]
    index.add(embeddings)
    ids = list(range(start_id, start_id + len(embeddings)))
    _next_ids[user_id] = start_id + len(embeddings)
    save_index(user_id)
    return ids


def search(query_embedding: np.ndarray, user_id: str, top_k: int = 12) -> list[tuple[int, float]]:
    """Search a user's FAISS index, return list of (faiss_id, score)."""
    index = get_index(user_id)
    if index.ntotal == 0:
        return []
    scores, indices = index.search(query_embedding.reshape(1, -1), min(top_k, index.ntotal))
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0:
            results.append((int(idx), float(score)))
    return results


def save_index(user_id: str):
    """Persist a user's FAISS index to disk."""
    index = get_index(user_id)
    faiss.write_index(index, str(_index_path(user_id)))


def rebuild_index(all_embeddings: np.ndarray, user_id: str):
    """Rebuild a user's FAISS index from scratch."""
    _indexes[user_id] = faiss.IndexFlatIP(EMBEDDING_DIM)
    if len(all_embeddings) > 0:
        _indexes[user_id].add(all_embeddings)
    _next_ids[user_id] = len(all_embeddings)
    save_index(user_id)


def delete_user_index(user_id: str):
    """Delete a user's FAISS index from disk and cache."""
    _indexes.pop(user_id, None)
    _next_ids.pop(user_id, None)
    path = _index_path(user_id)
    if path.exists():
        path.unlink()
