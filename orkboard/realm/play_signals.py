"""What a play's probe saw that is wrong, by code (docs/specs/115-the-live-product-under-each-leaders-eyes.md §4; decisions §193): the hints of a running product, as the maps' hints of code are
(`realm/map_signals.py`), shown in the lens of the craft whose aspect they ground (`realm/lens_rubrics.py`). A hint is not a verdict (the leader judges it). No model, no face, nothing written; the
host keeps one `Ring` a play and drops it when Play stops.

    play_signals.Ring()                              # the last RING_SIZE events of one play, thread-safe: add(event), events() -> a list oldest first, clear(); len(ring)
    play_signals.hints(events, path, slow_ms=1000)   # [{kind, on: {selector, rect} | None, words, at}], newest first, MAX_HINTS at most, one a kind and element (the newest)
    play_signals.CRAFT                               # {kind: craft}: tech for error, failed, slow; design for dead_press, again

An event is a dict with `kind` (`type` is taken too) and `at` (milliseconds, the probe's clock), by §2.2 of the spec:
- `error`: `{message, stack, path, at}`, `path` the page's path it happened on;
- `request`: `{method, path, status, ms, at}`, `path` the request's own, without its query (a request carries no page path);
- `press`: `{selector, rect, changed, pressable, at, path}`, `path` the page's; `changed` is whether within 1 s the DOM, the path or a request changed; `pressable` is the probe's: true when the element
  is a button, a link, an input or has a role, else false or missing (a press on a bare area is no dead press).
An event of another shape is skipped. With a `path`, the hints of `error` and `press` events are of that page's path alone; requests are the play's (they carry none). By kind:
- `error`: an uncaught error or rejection or a `console.error`; the element is its message. `on` is None.
- `failed`: a request answered 5xx, or 4xx but 401 (a sign-in is asked for) and a 404 of a path asked once in the ring (a probe for a file); the element is the method and path. `on` is None.
- `slow`: a request over `slow_ms`; the element is the method and path. `on` is None.
- `dead_press`: a press on something pressable with `changed` false; the element is its selector.
- `again`: THIS_MANY presses or more within WINDOW_MS on one element; the element is its selector, its `at` the last press of the newest such run.
"""
from __future__ import annotations

import threading
from collections import deque

RING_SIZE = 2000                    # the events a play keeps
MAX_HINTS = 20                      # hints at most
SLOW_MS = 1000                      # a request over this is slow (`preview_slow_ms` in the checks file)
WINDOW_MS = 1000                    # presses this close are "again and again"
THIS_MANY = 3                       # presses within WINDOW_MS that make `again`
WORDS_MAX = 160                     # an error's message in the words, at most
CRAFT = {"error": "tech", "failed": "tech", "slow": "tech", "dead_press": "design", "again": "design"}


class Ring:
    """The last RING_SIZE events of one play; safe to add to from the probe's thread and to read from another."""

    def __init__(self, size: int = RING_SIZE):
        self._events: deque = deque(maxlen=size)
        self._lock = threading.Lock()

    def add(self, event: dict) -> None:
        if isinstance(event, dict):
            with self._lock:
                self._events.append(dict(event))

    def events(self) -> list[dict]:
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)


def _num(v, default: float = 0.0) -> float:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else default


def _text(v) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def _kind(e) -> str:
    return (e.get("kind") or e.get("type") or "") if isinstance(e, dict) else ""


def _on(e: dict) -> dict | None:
    sel = _text(e.get("selector"))
    return {"selector": sel, "rect": e.get("rect") if isinstance(e.get("rect"), dict) else None} if sel else None


def hints(events, path: str = "", slow_ms: float = SLOW_MS) -> list[dict]:
    """The hints of one play's `events` (see the module), newest first, one a kind and element, MAX_HINTS at most. `path` keeps the page's own errors and presses to it ("" for all)."""
    evs = [(i, e) for i, e in enumerate(events or ()) if _kind(e) in ("error", "request", "press") and isinstance(e.get("at"), (int, float))]
    asked: dict[str, int] = {}
    for _, e in evs:
        if _kind(e) == "request":
            asked[_text(e.get("path"))] = asked.get(_text(e.get("path")), 0) + 1
    found: dict[tuple, tuple] = {}         # (kind, element) -> (at, order, hint): the newest of each

    def keep(kind: str, element: str, order: int, hint: dict) -> None:
        old = found.get((kind, element))
        if old is None or (hint["at"], order) >= old[:2]:
            found[(kind, element)] = (hint["at"], order, hint)

    presses: dict[str, list[tuple]] = {}
    for i, e in evs:
        kind, at = _kind(e), _num(e.get("at"))
        if kind in ("error", "press") and path and e.get("path") != path:
            continue
        if kind == "error":
            msg = _text(e.get("message")) or "unknown"
            msg = msg if len(msg) <= WORDS_MAX else msg[:WORDS_MAX - 1] + "…"
            keep("error", msg, i, {"kind": "error", "on": None, "words": f"An error here: {msg}", "at": at})
        elif kind == "request":
            method, p, status = (_text(e.get("method")) or "GET").upper(), _text(e.get("path")) or "/", _num(e.get("status"))
            call = f"{method} {p}"
            if status >= 500 or (400 <= status < 500 and status != 401 and not (status == 404 and asked.get(_text(e.get("path")), 0) < 2)):
                keep("failed", call, i, {"kind": "failed", "on": None, "words": f"A request failed: {call} {int(status)}", "at": at})
            if _num(e.get("ms")) > slow_ms:
                keep("slow", call, i, {"kind": "slow", "on": None, "words": f"Slow: {call} {round(_num(e.get('ms')))} ms", "at": at})
        elif kind == "press" and _text(e.get("selector")):
            sel = _text(e.get("selector"))
            presses.setdefault(sel, []).append((at, i, e))
            if e.get("pressable") is True and e.get("changed") is False:
                keep("dead_press", sel, i, {"kind": "dead_press", "on": _on(e), "words": "A press did nothing", "at": at})
    for sel, rows in presses.items():
        rows.sort(key=lambda r: r[:2])
        for n in range(len(rows) - THIS_MANY + 1):        # the newest run of THIS_MANY within the window wins
            if rows[n + THIS_MANY - 1][0] - rows[n][0] <= WINDOW_MS:
                last = rows[n + THIS_MANY - 1]
                keep("again", sel, last[1], {"kind": "again", "on": _on(last[2]), "words": "Pressed again and again", "at": last[0]})
    ordered = sorted(found.values(), key=lambda r: r[:2], reverse=True)
    return [r[2] for r in ordered[:MAX_HINTS]]
