import copy
import unittest

from app.document_ids import namespace_parsed_result


SAMPLE_RESULT = {
    "document": {"doc_id": "same-content-id"},
    "chunks": [
        {"chunk_id": "same-content-id_part_0", "doc_id": "same-content-id"},
        {"chunk_id": "same-content-id_part_1", "doc_id": "same-content-id"},
    ],
}


class DocumentNamespaceTests(unittest.TestCase):
    def test_same_upload_is_stable_for_same_user(self):
        first = namespace_parsed_result(copy.deepcopy(SAMPLE_RESULT), "user-a")
        second = namespace_parsed_result(copy.deepcopy(SAMPLE_RESULT), "user-a")
        self.assertEqual(first, second)

    def test_same_upload_is_isolated_between_users(self):
        first = namespace_parsed_result(copy.deepcopy(SAMPLE_RESULT), "user-a")
        second = namespace_parsed_result(copy.deepcopy(SAMPLE_RESULT), "user-b")
        self.assertNotEqual(first["document"]["doc_id"], second["document"]["doc_id"])
        self.assertNotEqual(first["chunks"][0]["chunk_id"], second["chunks"][0]["chunk_id"])

    def test_blank_user_is_rejected(self):
        with self.assertRaises(ValueError):
            namespace_parsed_result(copy.deepcopy(SAMPLE_RESULT), "  ")


if __name__ == "__main__":
    unittest.main()
