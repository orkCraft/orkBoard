"""The night's order (docs/specs/121-the-day-the-morning-and-the-night.md §4.3): the goals *Work at night* held start in the night's window by
**Product's priority** (the `priority` Product's leader gave its stance in Talk, spec 120 §3.1), then their place in line. No face, no model.

    night_order.priority_of(idea_questions.record(state_dir, slug))     # "high" · "normal" · "low": Product's word, "normal" when it gave none
    night_order.key(priority, place)                                    # what the held goals are sorted by: Product's word first, then their place

A record from before spec 120 (no `priority` on any stance), or one with a word out of the three, reads `normal`: a goal is never lost to a
record the night cannot read.
"""
from __future__ import annotations

PRIORITIES = ("high", "normal", "low")
AHEAD = -1                        # a plan *Build it now* started by day goes before every other: ahead of the night's queue (§4.5)


def priority_of(record: object) -> str:
    """Product's priority of a goal from its Talk record: the `priority` of the first stance (or weigher) that has one of the three; only Product's
    leader gives one (spec 120 §3.1). `normal` when there is none."""
    rec = record if isinstance(record, dict) else {}
    rows = [*(rec.get("stances") if isinstance(rec.get("stances"), list) else []), rec.get("weigher")]
    for row in rows:
        word = str(row.get("priority") or "").strip().lower() if isinstance(row, dict) else ""
        if word in PRIORITIES:
            return word
    return "normal"


def index(priority: object) -> int:
    """A priority's place in the order (`high` first); a word out of the three is `normal`'s."""
    word = str(priority or "").strip().lower()
    return PRIORITIES.index(word if word in PRIORITIES else "normal")


def key(priority: object, place: tuple) -> tuple:
    """What the held goals are sorted by: Product's priority, then the goal's place in line (`gui/ideas_board.py` `rank`)."""
    return (index(priority), *place)
