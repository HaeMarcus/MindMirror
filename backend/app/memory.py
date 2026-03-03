import json

from app.database import get_recent_messages, get_memory, set_memory, get_message_count
from app.config import SHORT_MEMORY_ROUNDS, ROLLING_SUMMARY_INTERVAL


def get_short_memory(user_id: str) -> list[dict]:
    """Get recent N rounds of conversation (each round = user + assistant)."""
    return get_recent_messages(limit=SHORT_MEMORY_ROUNDS * 2, user_id=user_id)


def get_rolling_summary(user_id: str) -> str:
    """Get the current rolling summary."""
    return get_memory("rolling_summary", user_id=user_id) or ""


def get_user_profile(user_id: str) -> dict:
    """Get the long-term user profile."""
    raw = get_memory("user_profile", user_id=user_id)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def should_update_summary(user_id: str) -> bool:
    """Check if rolling summary needs updating (every N rounds)."""
    count = get_message_count(user_id=user_id)
    return count > 0 and (count // 2) % ROLLING_SUMMARY_INTERVAL == 0


def save_rolling_summary(summary: str, user_id: str):
    set_memory("rolling_summary", summary, user_id=user_id)


def save_user_profile(profile: dict, user_id: str):
    set_memory("user_profile", json.dumps(profile, ensure_ascii=False), user_id=user_id)
