import json

from app.database import get_recent_messages, get_memory, set_memory, get_message_count
from app.config import SHORT_MEMORY_ROUNDS, ROLLING_SUMMARY_INTERVAL


def get_short_memory() -> list[dict]:
    """Get recent N rounds of conversation (each round = user + assistant)."""
    return get_recent_messages(limit=SHORT_MEMORY_ROUNDS * 2)


def get_rolling_summary() -> str:
    """Get the current rolling summary."""
    return get_memory("rolling_summary") or ""


def get_user_profile() -> dict:
    """Get the long-term user profile."""
    raw = get_memory("user_profile")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def should_update_summary() -> bool:
    """Check if rolling summary needs updating (every N rounds)."""
    count = get_message_count()
    # Update every ROLLING_SUMMARY_INTERVAL rounds (each round = 2 messages)
    return count > 0 and (count // 2) % ROLLING_SUMMARY_INTERVAL == 0


def save_rolling_summary(summary: str):
    set_memory("rolling_summary", summary)


def save_user_profile(profile: dict):
    set_memory("user_profile", json.dumps(profile, ensure_ascii=False))
