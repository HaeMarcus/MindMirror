import sqlite3
import json
from contextlib import contextmanager
from typing import Optional

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    time_range_start TEXT,
    time_range_end TEXT,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    chunk_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    faiss_id INTEGER
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS memory (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
"""


def init_db():
    with get_db() as db:
        db.executescript(SCHEMA)


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---- Document CRUD ----

def insert_document(doc_id: str, source_type: str, source_name: str,
                    time_range_start: Optional[str] = None,
                    time_range_end: Optional[str] = None,
                    metadata: Optional[dict] = None):
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO documents (doc_id, source_type, source_name, time_range_start, time_range_end, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (doc_id, source_type, source_name, time_range_start, time_range_end,
             json.dumps(metadata or {}, ensure_ascii=False))
        )


def get_document(doc_id: str) -> Optional[dict]:
    with get_db() as db:
        row = db.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None


def get_all_documents() -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT doc_id, source_type, source_name, time_range_start, time_range_end, created_at FROM documents ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_chunk_count_by_doc(doc_id: str) -> int:
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) as cnt FROM chunks WHERE doc_id = ?", (doc_id,)).fetchone()
        return row["cnt"]


def delete_document(doc_id: str):
    with get_db() as db:
        db.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))


# ---- Chunk CRUD ----

def insert_chunks(chunks: list[dict]):
    with get_db() as db:
        db.executemany(
            "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, chunk_type, content, metadata, faiss_id) VALUES (?, ?, ?, ?, ?, ?)",
            [(c["chunk_id"], c["doc_id"], c["chunk_type"], c["content"],
              json.dumps(c.get("metadata", {}), ensure_ascii=False), c.get("faiss_id"))
             for c in chunks]
        )


def get_chunks_by_doc(doc_id: str) -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM chunks WHERE doc_id = ?", (doc_id,)).fetchall()
        return [dict(r) for r in rows]


def get_chunks_by_ids(chunk_ids: list[str]) -> list[dict]:
    if not chunk_ids:
        return []
    placeholders = ",".join("?" for _ in chunk_ids)
    with get_db() as db:
        rows = db.execute(f"SELECT * FROM chunks WHERE chunk_id IN ({placeholders})", chunk_ids).fetchall()
        return [dict(r) for r in rows]


def get_chunk_by_faiss_id(faiss_id: int) -> Optional[dict]:
    with get_db() as db:
        row = db.execute("SELECT * FROM chunks WHERE faiss_id = ?", (faiss_id,)).fetchone()
        return dict(row) if row else None


def get_chunks_by_faiss_ids(faiss_ids: list[int]) -> list[dict]:
    if not faiss_ids:
        return []
    placeholders = ",".join("?" for _ in faiss_ids)
    with get_db() as db:
        rows = db.execute(f"SELECT * FROM chunks WHERE faiss_id IN ({placeholders})", faiss_ids).fetchall()
        return [dict(r) for r in rows]


# ---- Messages CRUD ----

def add_message(role: str, content: str):
    with get_db() as db:
        db.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))


def get_recent_messages(limit: int = 30) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT role, content, created_at FROM messages ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


def get_message_count() -> int:
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) as cnt FROM messages").fetchone()
        return row["cnt"]


# ---- Memory CRUD ----

def get_memory(key: str) -> Optional[str]:
    with get_db() as db:
        row = db.execute("SELECT value FROM memory WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def set_memory(key: str, value: str):
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO memory (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (key, value)
        )


def clear_all_data():
    """Clear all user data: messages, memory, documents, chunks."""
    with get_db() as db:
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM memory")
        db.execute("DELETE FROM chunks")
        db.execute("DELETE FROM documents")
