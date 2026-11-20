"""KH: remembers the address (BASE_URL) Kochheft was last reached at, so a move to another domain is noticed (D85).
Shortcuts and home-screen icons contain the address, so everyone has to set them up again after a change."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from mealie.core.root_logger import get_logger

logger = get_logger()

NOTICE_DAYS = 60  # how long the system check keeps warning about a change


@dataclass(frozen=True)
class AddressState:
    """What address.json holds: the address now, the one before a change, when it changed, whether all were told."""

    current: str
    previous: str | None = None
    changed_at: str | None = None  # ISO time of the change, None while the address never changed
    notified: bool = False  # the push message and the card for the change are out


def is_placeholder(url: str) -> bool:
    """True for Mealie's default BASE_URL and Kochheft's localhost one: no real address is set yet."""
    return (urlsplit(url).hostname or "") in {"localhost", "127.0.0.1", "::1"}


def next_state(stored: AddressState | None, base_url: str, now: datetime) -> AddressState | None:
    """The state after seeing BASE_URL at start: the first real address is just stored, a different one becomes a
    change. A placeholder address (or the same one) leaves the state as it was."""
    current = base_url.rstrip("/")
    if is_placeholder(current) or (stored and stored.current == current):
        return stored
    if stored is None:
        return AddressState(current=current)
    return AddressState(current=current, previous=stored.current, changed_at=now.isoformat())


def recent_change(state: AddressState | None, now: datetime) -> bool:
    """True while a change is less than NOTICE_DAYS old."""
    if state is None or not state.changed_at:
        return False
    return now - datetime.fromisoformat(state.changed_at) < timedelta(days=NOTICE_DAYS)


def _file(data_dir: Path) -> Path:
    return data_dir / "kh" / "address.json"


def read_state(data_dir: Path) -> AddressState | None:
    """The stored state; a missing or broken file counts as nothing stored (the next start writes it again)."""
    try:
        return AddressState(**json.loads(_file(data_dir).read_text(encoding="utf-8")))
    except OSError, ValueError, TypeError:
        return None


def write_state(data_dir: Path, state: AddressState) -> None:
    path = _file(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state)), encoding="utf-8")


def refresh(data_dir: Path, base_url: str) -> AddressState | None:
    """Compares BASE_URL with the stored address, stores a new state and logs a change; returns the state."""
    stored = read_state(data_dir)
    state = next_state(stored, base_url, datetime.now(UTC))
    if state != stored and state is not None:
        write_state(data_dir, state)
        if state.previous:
            logger.warning("Kochheft's address changed from %s to %s", state.previous, state.current)
    return state
