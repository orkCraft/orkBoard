"""The bus: how the core tells a face what changed. A service never shows anything itself, it
publishes. Each face subscribes and decides how to show it: a toast, a redrawn road, a refreshed
hall. Payloads are plain data (strings, numbers, lists, dicts), so a daemon can later carry them
over a socket unchanged.

    bus.subscribe(TOAST, lambda e: show(e.data["message"]))
    bus.publish(TOAST, message="🛤 Pit → Lake", title="Roads")
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

ANY = "*"            # a subscriber to every topic (a log, a socket)

TOAST = "toast"      # message, title, severity ("information" | "warning" | "error"), timeout (s or None)
SIGN_IN = "sign_in"  # harness, tool, state, by, auto, why, command, waiting: a tool's sign-in changed (core/sign_ins.py, spec 45 §4)
SIGNED_IN = "signed_in"  # harness: a tool is signed in again; what was held for it goes on (spec 45 §6)
TOOL_MOVED = "tool_moved"  # from, to, until: the tool the work goes to changed (the Main tool ran dry, or is back): once a change (realm/tool_now.py, spec 105 §2.5)
MAIN_CHECK = "main.check"  # idea, checks: a step of the checks on a goal's way into main ([{name, state, words}], gui/ideas_gate.py, spec 111 §4.2); the face reads the snapshot's `main_checks`
MOVE_PLAYED = "move.played"  # idea, kind, origin: a one-press move of the hand was played and its Undo kept (core/idea_undo.py, spec 171 D)
MOVE_UNDONE = "move.undone"  # idea, kind: that move was put back


@dataclass(frozen=True)
class Event:
    topic: str
    data: dict[str, Any] = field(default_factory=dict)


class Bus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Callable[[Event], Any]]] = defaultdict(list)

    def subscribe(self, topic: str, fn: Callable[[Event], Any]) -> Callable[[], None]:
        """`fn(event)` on every event of `topic` (ANY: of every topic). Returns the unsubscribe."""
        self._subs[topic].append(fn)

        def off() -> None:
            if fn in self._subs[topic]:
                self._subs[topic].remove(fn)
        return off

    def publish(self, topic: str, **data: Any) -> Event:
        """Synchronous, on the caller's thread: a face that draws on one thread hops itself."""
        event = Event(topic, data)
        for fn in list(self._subs.get(topic, ())) + list(self._subs.get(ANY, ())):
            fn(event)
        return event
