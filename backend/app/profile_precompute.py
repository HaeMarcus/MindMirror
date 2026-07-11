"""Debounced, hidden Big Five precomputation for uploaded user data."""

import json
import threading
import traceback

from app.database import get_memory, get_profile_seed_chunks, set_memory
from app.llm import generate_profile_from_evidence
from app.memory import get_user_profile, save_user_profile

PENDING_PROFILE_KEY = "_pending_user_profile"
DEFAULT_DEBOUNCE_SECONDS = 30

_lock = threading.RLock()
_timers: dict[str, threading.Timer] = {}
_events: dict[str, threading.Event] = {}
_running: dict[str, int] = {}
_versions: dict[str, int] = {}
_activate_when_ready: set[str] = set()


def _pending_profile(user_id: str) -> dict:
    raw = get_memory(PENDING_PROFILE_KEY, user_id=user_id)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _build_evidence(user_id: str) -> str:
    chunks = get_profile_seed_chunks(user_id=user_id, per_source_limit=8)
    sections = []
    for index, chunk in enumerate(chunks, start=1):
        content = chunk["content"]
        if len(content) > 600:
            content = content[:600] + "..."
        sections.append(
            f"[{index}] 来源={chunk['source_type']} 文件={chunk['source_name']}\n{content}"
        )
    return "\n\n".join(sections)


def _run_precompute(user_id: str, version: int, event: threading.Event) -> None:
    try:
        evidence = _build_evidence(user_id)
        if not evidence:
            return
        profile = generate_profile_from_evidence(
            evidence=evidence,
            old_profile=get_user_profile(user_id=user_id),
        )
        if not profile.get("big_five"):
            return

        with _lock:
            if version != _versions.get(user_id, version):
                return
            activate_now = user_id in _activate_when_ready

        if activate_now:
            save_user_profile(profile, user_id=user_id)
            set_memory(PENDING_PROFILE_KEY, "", user_id=user_id)
            with _lock:
                _activate_when_ready.discard(user_id)
            print(f"[profile] Precomputed profile activated for {user_id}")
        else:
            set_memory(
                PENDING_PROFILE_KEY,
                json.dumps(profile, ensure_ascii=False),
                user_id=user_id,
            )
            print(f"[profile] Hidden profile precomputed for {user_id}")
    except Exception as exc:
        print(f"[profile] Precompute failed for {user_id}: {exc}")
        traceback.print_exc()
    finally:
        with _lock:
            if _running.get(user_id) == version:
                _running.pop(user_id, None)
        event.set()


def _launch(user_id: str, version: int, event: threading.Event) -> None:
    with _lock:
        if version != _versions.get(user_id):
            event.set()
            return
        running_version = _running.get(user_id)
        if running_version is not None:
            if running_version == version:
                return
            retry = threading.Timer(2, _launch, args=(user_id, version, event))
            retry.daemon = True
            _timers[user_id] = retry
            retry.start()
            return
        _running[user_id] = version
        _timers.pop(user_id, None)
    _run_precompute(user_id, version, event)


def schedule_profile_precompute(
    user_id: str,
    delay_seconds: int = DEFAULT_DEBOUNCE_SECONDS,
) -> None:
    """Debounce repeated uploads so a batch normally costs one model call."""
    with _lock:
        version = _versions.get(user_id, 0) + 1
        _versions[user_id] = version
        _activate_when_ready.discard(user_id)
        old_timer = _timers.pop(user_id, None)
        if old_timer:
            old_timer.cancel()
        event = threading.Event()
        _events[user_id] = event
        timer = threading.Timer(delay_seconds, _launch, args=(user_id, version, event))
        timer.daemon = True
        _timers[user_id] = timer
        timer.start()


def start_scheduled_precompute_now(user_id: str) -> threading.Event | None:
    """Start pending or legacy-data analysis in parallel with the first answer."""
    pending = _pending_profile(user_id)
    if pending:
        ready = threading.Event()
        ready.set()
        return ready

    with _lock:
        timer = _timers.pop(user_id, None)
        if timer:
            timer.cancel()
        elif user_id not in _running:
            # Users who uploaded before this feature was deployed have no
            # scheduled timer. Bootstrap them on their next first conversation.
            if get_user_profile(user_id=user_id).get("big_five"):
                return None
            if not get_profile_seed_chunks(user_id=user_id, per_source_limit=1):
                return None
            _versions[user_id] = _versions.get(user_id, 0) + 1

        event = _events.get(user_id) or threading.Event()
        _events[user_id] = event
        version = _versions.get(user_id, 0)
        running_version = _running.get(user_id)
        if running_version is not None:
            if running_version != version:
                retry = threading.Timer(0.2, _launch, args=(user_id, version, event))
                retry.daemon = True
                _timers[user_id] = retry
                retry.start()
            return event
        _running[user_id] = version

    worker = threading.Thread(
        target=_run_precompute,
        args=(user_id, version, event),
        daemon=True,
    )
    worker.start()
    return event


def activate_precomputed_profile(
    user_id: str,
    event: threading.Event | None,
    wait_seconds: float = 4,
) -> bool:
    """Reveal the hidden profile after the first complete model answer."""
    with _lock:
        _activate_when_ready.add(user_id)

    if event and not event.is_set():
        event.wait(wait_seconds)

    pending = _pending_profile(user_id)
    if pending.get("big_five"):
        save_user_profile(pending, user_id=user_id)
        set_memory(PENDING_PROFILE_KEY, "", user_id=user_id)
        with _lock:
            _activate_when_ready.discard(user_id)
        return True

    return bool(get_user_profile(user_id=user_id).get("big_five"))
