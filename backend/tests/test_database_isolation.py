import os
import sys
import tempfile
import types
import unittest

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="mindmirror-tests-")

# The deploy verification intentionally avoids installing the heavy backend
# dependency stack. database.py only needs load_dotenv to be a harmless no-op.
dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda: None
sys.modules.setdefault("dotenv", dotenv_stub)

from app.database import (  # noqa: E402
    create_user,
    delete_document,
    get_db,
    get_document,
    init_db,
    insert_chunks,
    insert_document,
)


class DatabaseIsolationTests(unittest.TestCase):
    def setUp(self):
        init_db()
        with get_db() as db:
            db.executescript(
                "DELETE FROM chunks; DELETE FROM documents; DELETE FROM users;"
            )
        create_user("owner")
        create_user("other")
        insert_document(
            doc_id="doc-owned",
            source_type="review_md",
            source_name="sample.md",
            user_id="owner",
        )
        insert_chunks(
            [{
                "chunk_id": "chunk-owned",
                "doc_id": "doc-owned",
                "chunk_type": "md_section",
                "content": "fictional content",
            }]
        )

    def test_other_user_cannot_delete_document(self):
        self.assertFalse(delete_document("doc-owned", user_id="other"))
        self.assertIsNotNone(get_document("doc-owned"))

    def test_owner_can_delete_document(self):
        self.assertTrue(delete_document("doc-owned", user_id="owner"))
        self.assertIsNone(get_document("doc-owned"))


if __name__ == "__main__":
    unittest.main()
