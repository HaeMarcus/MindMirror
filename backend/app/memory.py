import json

from app.database import get_recent_messages, get_memory, set_memory, get_message_count
from app.config import SHORT_MEMORY_ROUNDS, ROLLING_SUMMARY_INTERVAL, PROFILE_UPDATE_INTERVAL


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


def save_rolling_summary(summary: str, user_id: str):
    set_memory("rolling_summary", summary, user_id=user_id)


def save_user_profile(profile: dict, user_id: str):
    set_memory("user_profile", json.dumps(profile, ensure_ascii=False), user_id=user_id)


# ---- Counter-based trigger logic ----

def _get_current_round(user_id: str) -> int:
    """Get current conversation round count (each round = one user + one assistant message)."""
    return get_message_count(user_id=user_id) // 2


def _get_counter(user_id: str, key: str) -> int:
    raw = get_memory(key, user_id=user_id)
    return int(raw) if raw else 0


def _set_counter(user_id: str, key: str, value: int):
    set_memory(key, str(value), user_id=user_id)


def should_update_summary(user_id: str) -> bool:
    """Check if rolling summary needs updating.
    Triggers on first round (bootstrap) or every ROLLING_SUMMARY_INTERVAL rounds.
    """
    current_round = _get_current_round(user_id)
    last_updated = _get_counter(user_id, "_summary_updated_at_round")
    # First round bootstrap: generate initial summary immediately
    if current_round >= 1 and last_updated == 0:
        return True
    return current_round - last_updated >= ROLLING_SUMMARY_INTERVAL


def mark_summary_updated(user_id: str):
    """Record that rolling summary was just updated at the current round."""
    _set_counter(user_id, "_summary_updated_at_round", _get_current_round(user_id))


def should_update_profile(user_id: str) -> bool:
    """Check if user profile needs updating.
    Triggers on first round (bootstrap) or every PROFILE_UPDATE_INTERVAL rounds.
    """
    current_round = _get_current_round(user_id)
    last_updated = _get_counter(user_id, "_profile_updated_at_round")
    # First round bootstrap: generate initial profile immediately
    if current_round >= 1 and last_updated == 0:
        return True
    return current_round - last_updated >= PROFILE_UPDATE_INTERVAL


def mark_profile_updated(user_id: str):
    """Record that user profile was just updated at the current round."""
    _set_counter(user_id, "_profile_updated_at_round", _get_current_round(user_id))
