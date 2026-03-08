import sqlite3
import json
from contextlib import contextmanager
from typing import Optional

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    nickname TEXT PRIMARY KEY,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
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
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS memory (
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, key)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    user_id TEXT NOT NULL DEFAULT '',
    rating TEXT NOT NULL,
    app_version TEXT NOT NULL DEFAULT '',
    source_types TEXT NOT NULL DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);
"""


def init_db():
    with get_db() as db:
        db.executescript(SCHEMA)
        _migrate_add_user_id(db)
        _migrate_feedback_columns(db)


def _migrate_add_user_id(db):
    """Add user_id columns to existing tables if missing (migration from single-user)."""
    # Check if documents table has user_id column
    cols = [r["name"] for r in db.execute("PRAGMA table_info(documents)").fetchall()]
    if "user_id" not in cols:
        db.execute("ALTER TABLE documents ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")

    cols = [r["name"] for r in db.execute("PRAGMA table_info(messages)").fetchall()]
    if "user_id" not in cols:
        db.execute("ALTER TABLE messages ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")

    # Memory table: need to check if it has old schema (key as sole PK)
    cols = [r["name"] for r in db.execute("PRAGMA table_info(memory)").fetchall()]
    if "user_id" not in cols:
        # Recreate memory table with composite PK
        db.execute("ALTER TABLE memory RENAME TO memory_old")
        db.execute("""
            CREATE TABLE memory (
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, key)
            )
        """)
        db.execute("INSERT INTO memory (user_id, key, value, updated_at) SELECT 'default', key, value, updated_at FROM memory_old")
        db.execute("DROP TABLE memory_old")


def _migrate_feedback_columns(db):
    """Add user_id, app_version, source_types columns to feedback if missing."""
    cols = [r["name"] for r in db.execute("PRAGMA table_info(feedback)").fetchall()]
    if "user_id" not in cols:
        db.execute("ALTER TABLE feedback ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
    if "app_version" not in cols:
        db.execute("ALTER TABLE feedback ADD COLUMN app_version TEXT NOT NULL DEFAULT ''")
    if "source_types" not in cols:
        db.execute("ALTER TABLE feedback ADD COLUMN source_types TEXT NOT NULL DEFAULT ''")


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---- User CRUD ----

def create_user(nickname: str):
    with get_db() as db:
        db.execute("INSERT INTO users (nickname) VALUES (?)", (nickname,))


def user_exists(nickname: str) -> bool:
    with get_db() as db:
        row = db.execute("SELECT 1 FROM users WHERE nickname = ?", (nickname,)).fetchone()
        return row is not None


# ---- Document CRUD ----

def insert_document(doc_id: str, source_type: str, source_name: str,
                    user_id: str,
                    time_range_start: Optional[str] = None,
                    time_range_end: Optional[str] = None,
                    metadata: Optional[dict] = None):
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO documents (doc_id, user_id, source_type, source_name, time_range_start, time_range_end, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (doc_id, user_id, source_type, source_name, time_range_start, time_range_end,
             json.dumps(metadata or {}, ensure_ascii=False))
        )


def get_document(doc_id: str) -> Optional[dict]:
    with get_db() as db:
        row = db.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None


def get_all_documents(user_id: str) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT doc_id, source_type, source_name, time_range_start, time_range_end, created_at FROM documents WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
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


def get_chunks_by_faiss_ids(faiss_ids: list[int], user_id: str) -> list[dict]:
    if not faiss_ids:
        return []
    placeholders = ",".join("?" for _ in faiss_ids)
    with get_db() as db:
        rows = db.execute(
            f"SELECT c.* FROM chunks c JOIN documents d ON c.doc_id = d.doc_id WHERE c.faiss_id IN ({placeholders}) AND d.user_id = ?",
            [*faiss_ids, user_id]
        ).fetchall()
        return [dict(r) for r in rows]


# ---- Messages CRUD ----

def add_message(role: str, content: str, user_id: str) -> int:
    with get_db() as db:
        cursor = db.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
        return cursor.lastrowid


def get_recent_messages(limit: int = 30, user_id: str = "default") -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT role, content, created_at FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


def get_message_count(user_id: str) -> int:
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) as cnt FROM messages WHERE user_id = ?", (user_id,)).fetchone()
        return row["cnt"]


# ---- Memory CRUD ----

def get_memory(key: str, user_id: str) -> Optional[str]:
    with get_db() as db:
        row = db.execute("SELECT value FROM memory WHERE user_id = ? AND key = ?", (user_id, key)).fetchone()
        return row["value"] if row else None


def set_memory(key: str, value: str, user_id: str):
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO memory (user_id, key, value, updated_at) VALUES (?, ?, ?, datetime('now'))",
            (user_id, key, value)
        )


def add_feedback(message_id: int, rating: str, user_id: str = "",
                 app_version: str = "", source_types: str = ""):
    with get_db() as db:
        db.execute(
            "INSERT INTO feedback (message_id, rating, user_id, app_version, source_types) VALUES (?, ?, ?, ?, ?)",
            (message_id, rating, user_id, app_version, source_types),
        )


def get_feedback_stats() -> dict:
    with get_db() as db:
        rows = db.execute("SELECT rating, COUNT(*) as cnt FROM feedback GROUP BY rating").fetchall()
        return {r["rating"]: r["cnt"] for r in rows}


def get_feedback_analytics(days: int = 30) -> dict:
    """Rich analytics for the developer dashboard."""
    with get_db() as db:
        # Overall stats
        total_row = db.execute("SELECT COUNT(*) as total FROM feedback").fetchone()
        total = total_row["total"]
        accurate_row = db.execute("SELECT COUNT(*) as cnt FROM feedback WHERE rating = 'accurate'").fetchone()
        accurate = accurate_row["cnt"]
        rate = round(accurate / total * 100, 1) if total > 0 else 0

        # Daily trend (last N days)
        daily = db.execute(
            """SELECT date(created_at) as day, rating, COUNT(*) as cnt
               FROM feedback
               WHERE created_at >= datetime('now', ?)
               GROUP BY day, rating
               ORDER BY day""",
            (f"-{days} days",)
        ).fetchall()

        daily_map: dict[str, dict] = {}
        for r in daily:
            d = r["day"]
            if d not in daily_map:
                daily_map[d] = {"date": d, "accurate": 0, "inaccurate": 0}
            daily_map[d][r["rating"]] = r["cnt"]
        trend = list(daily_map.values())

        # Per-version breakdown
        versions = db.execute(
            """SELECT app_version, rating, COUNT(*) as cnt
               FROM feedback
               WHERE app_version != ''
               GROUP BY app_version, rating
               ORDER BY app_version"""
        ).fetchall()

        version_map: dict[str, dict] = {}
        for r in versions:
            v = r["app_version"]
            if v not in version_map:
                version_map[v] = {"version": v, "accurate": 0, "inaccurate": 0}
            version_map[v][r["rating"]] = r["cnt"]
        by_version = list(version_map.values())

        # Per-user stats
        users = db.execute(
            """SELECT user_id, rating, COUNT(*) as cnt
               FROM feedback
               WHERE user_id != ''
               GROUP BY user_id, rating"""
        ).fetchall()

        user_map: dict[str, dict] = {}
        for r in users:
            u = r["user_id"]
            if u not in user_map:
                user_map[u] = {"user": u, "accurate": 0, "inaccurate": 0}
            user_map[u][r["rating"]] = r["cnt"]
        by_user = list(user_map.values())

        # Recent feedback entries
        recent = db.execute(
            """SELECT f.id, f.message_id, f.user_id, f.rating, f.app_version,
                      f.source_types, f.created_at
               FROM feedback f ORDER BY f.created_at DESC LIMIT 50"""
        ).fetchall()

        return {
            "total": total,
            "accurate": accurate,
            "inaccurate": total - accurate,
            "rate": rate,
            "trend": trend,
            "by_version": by_version,
            "by_user": by_user,
            "recent": [dict(r) for r in recent],
        }


def clear_all_data(user_id: str):
    """Clear all data for a specific user, including their FAISS index."""
    from app.embedding import delete_user_index

    with get_db() as db:
        # Get user's doc_ids to delete their chunks
        doc_ids = [r["doc_id"] for r in db.execute("SELECT doc_id FROM documents WHERE user_id = ?", (user_id,)).fetchall()]
        if doc_ids:
            placeholders = ",".join("?" for _ in doc_ids)
            db.execute(f"DELETE FROM chunks WHERE doc_id IN ({placeholders})", doc_ids)
        db.execute("DELETE FROM documents WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM memory WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM feedback WHERE message_id NOT IN (SELECT id FROM messages)")

    # Clean up user's FAISS index (outside DB transaction)
    delete_user_index(user_id)
