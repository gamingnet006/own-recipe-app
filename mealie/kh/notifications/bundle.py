"""KH: bundles pushes that come in quick succession (D75): the first message of a key goes out at once, what follows
within the window waits and goes out as one message when the window has passed. State lives in memory, so a restart
only loses a few waiting items."""

import threading
import time
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Slot:
    sent_at: float
    context: object
    waiting: list[Any] = field(default_factory=list)


class Bundler:
    """Per key: at most one message per window. `add` says whether to send now, `due` hands out the waiting ones."""

    def __init__(self, window_seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._window = window_seconds
        self._clock = clock
        self._slots: dict[Hashable, _Slot] = {}
        self._lock = threading.Lock()

    def add(self, key: Hashable, context: object, items: list[Any]) -> bool:
        """True when the items go out now (nothing was sent for KEY within the window); else they wait."""
        now = self._clock()
        with self._lock:
            slot = self._slots.get(key)
            if slot is None or now - slot.sent_at >= self._window and not slot.waiting:
                self._slots[key] = _Slot(sent_at=now, context=context)
                return True
            slot.waiting.extend(items)
            return False

    def due(self) -> list[tuple[object, list[Any]]]:
        """The waiting items of every key whose window has passed, as (context, items); their window starts anew.
        Keys with nothing waiting and an old window are forgotten."""
        now = self._clock()
        out: list[tuple[object, list[Any]]] = []
        with self._lock:
            for key, slot in list(self._slots.items()):
                if now - slot.sent_at < self._window:
                    continue
                if slot.waiting:
                    out.append((slot.context, slot.waiting))
                    slot.waiting, slot.sent_at = [], now
                else:
                    del self._slots[key]
        return out
