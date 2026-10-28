"""Where a goal lies in the window (docs/specs/98-the-table-and-the-hand.md §2.1; decisions §145.2): in the **deck** (not
started, asking nothing), the **hand** (not at work, and a Needs you row waits for the person), on the **table** (the
Orkmaster reads or plans it, or it is at work) or in the **discard** (done, its result not seen) and the **history** (done
and seen). Pure code on what the Board's row already holds: the faces draw it, nothing here words anything.

    place_of(row, kinds, passed=False, picking=False, seen="")
        -> {"place": "deck" | "hand" | "table" | "discard" | "history",
            "asks_you": bool,                  # on the table and asking: in the hand too, never in two piles
            "waits_as": "reset" | "held" | "line" | ""}      # why a deck goal waits (today's `waits` dict stays beside it)

`board_map.row` calls it, so a node and a Board row never differ. A raw `night` queue (the night is gone: spec 99 §3) is read
as `hold`, which `ideas.queue_of` already does.
"""
from __future__ import annotations

from typing import Iterable

PLACES = ("deck", "hand", "table", "discard", "history")
WAITS_AS = ("reset", "held", "line")

_AT_WORK = ("reading", "planning", "working", "judging")        # the Orkmaster reads, plans or judges it; or its tasks run
_ASKING = ("asks", "failed", "proposed", "judged")               # not at work: the person answers
_WAY = ("talk", "decided", "sections")                           # a goal's way before its work (spec 99 §4–§7): the leaders talk, the decision, the sections
_FINISHED = ("sent", "passed")                                   # a pitch since sent on or passed: nothing more to do with it


def _deck(row: dict, why: str) -> dict:
    """`why`: "reset" | "held" | "" (then "line" while the goal waits for goals it depends on)."""
    return {"place": "deck", "asks_you": False, "waits_as": why or ("line" if row.get("waits_on") else "")}


def place_of(row: dict, kinds: Iterable[str], *, passed: bool = False, picking: bool = False, seen: str = "") -> dict:
    """`row`: the Board's row (`state`, `queue`, `held_until`, `start_at`, `waits_on`); `kinds`: the kinds of its Needs you
    rows; `passed`: its plan was passed; `picking`: a task waits for the person's pick; `seen`: when its result was seen."""
    state, kinds = row["state"], set(kinds)
    asks = bool(kinds or picking)
    if state == "done":
        return {"place": "history" if seen else "discard", "asks_you": False, "waits_as": ""}
    if state in _FINISHED:
        return {"place": "history", "asks_you": False, "waits_as": ""}
    table = {"place": "table", "asks_you": asks, "waits_as": ""}
    hand = {"place": "hand", "asks_you": False, "waits_as": ""}
    if state in ("raw", "ready"):
        if kinds:                                                  # a collision's question on a goal not started
            return hand
        if row.get("held_until"):                                  # the keeper's call waits for the window's reset
            return _deck(row, "reset")
        if state == "raw" and row.get("queue") != "now":           # held by the person (a raw `night` is `hold`: spec 99 §3)
            return _deck(row, "held")
        return table
    if state == "plan":
        if row.get("start_at"):                                    # a plan that starts later waits for the reset
            return hand if kinds - {"plan"} else _deck(row, "reset")
        return table if passed or not kinds else hand
    if state == "routed":                                          # a goal routed waits for the person's Talk; put off with *Later, by itself* it waits in the deck (spec 99 §4)
        return _deck(row, "reset") if row.get("held_until") else hand
    if state in _WAY:                                              # Talk, the decision, the sections: on the table, asking when a row waits
        return table
    if state in _ASKING:
        return hand if kinds else (table if state == "asks" else _deck(row, ""))
    return table if state in _AT_WORK or not kinds else hand
