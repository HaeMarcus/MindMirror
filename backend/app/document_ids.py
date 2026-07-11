"""Stable, user-scoped identifiers for parsed documents and chunks."""

import hashlib


def namespace_parsed_result(result: dict, user_id: str) -> dict:
    """Scope parser-generated IDs to a user without mutating source content.

    Parsers intentionally produce content-stable IDs. The database, however,
    stores documents from every user in the same tables, so the user namespace
    must be part of the persisted IDs to prevent identical uploads from
    replacing another user's records.
    """
    normalized_user = user_id.strip()
    if not normalized_user:
        raise ValueError("user_id is required")

    document = result["document"]
    old_doc_id = document["doc_id"]
    digest = hashlib.sha256(f"{normalized_user}|{old_doc_id}".encode()).hexdigest()[:24]
    new_doc_id = f"doc_{digest}"
    document["doc_id"] = new_doc_id

    for chunk in result["chunks"]:
        old_chunk_id = chunk["chunk_id"]
        chunk_digest = hashlib.sha256(
            f"{normalized_user}|{old_chunk_id}".encode()
        ).hexdigest()[:24]
        chunk["doc_id"] = new_doc_id
        chunk["chunk_id"] = f"chunk_{chunk_digest}"

    return result
