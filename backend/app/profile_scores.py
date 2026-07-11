"""Guardrails for visible Big Five score progression."""

BIG_FIVE_KEYS = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
)


def _clamp(value: float, low: int = 20, high: int = 88) -> int:
    return max(low, min(high, round(value)))


def stabilize_profile_scores(new_profile: dict, old_profile: dict | None = None) -> dict:
    """Keep initial profiles distinctive and later updates believable.

    Initial scores retain the model's ordering but are expanded when all five
    dimensions cluster too closely. Later updates are limited to 2-6 points
    per changed dimension so movement is visible without looking erratic.
    """
    profile = dict(new_profile)
    scores = dict(profile.get("big_five") or {})
    if not all(isinstance(scores.get(key), (int, float)) for key in BIG_FIVE_KEYS):
        return profile

    old_scores = (old_profile or {}).get("big_five") or {}
    has_old_scores = all(
        isinstance(old_scores.get(key), (int, float)) for key in BIG_FIVE_KEYS
    )

    if has_old_scores:
        stabilized = {}
        for key in BIG_FIVE_KEYS:
            old_value = _clamp(old_scores[key])
            target = _clamp(scores[key])
            delta = target - old_value
            if delta == 0:
                stabilized[key] = old_value
                continue
            direction = 1 if delta > 0 else -1
            magnitude = max(2, min(6, abs(delta)))
            stabilized[key] = _clamp(old_value + direction * magnitude)
        profile["big_five"] = stabilized
        return profile

    initial = {key: _clamp(scores[key]) for key in BIG_FIVE_KEYS}
    values = list(initial.values())
    spread = max(values) - min(values)
    if 0 < spread < 20:
        mean = sum(values) / len(values)
        scale = 20 / spread
        initial = {
            key: _clamp(mean + (value - mean) * scale)
            for key, value in initial.items()
        }
    profile["big_five"] = initial
    return profile
