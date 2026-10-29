"""Going on paid (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §3; decisions §177.3): when every subscription is out, the Orkmaster asks
whether to go on with a tool billed by its API. A pure read of the Board's state and the tool now, and the one answer kept; no face, no words of the card.

    paid.until(state_dir, at)                          # the reset a yes holds until (epoch seconds), None with none
    paid.answer(state_dir, yes, until, at)             # keeps the yes (`paid_until`) or the wait (`paid_wait`), both ending at the reset
    paid.row(state_dir, machine, got, usd_task, at)    # [] or [{kind: "paid", tool, name, until, usd_task, text, blocks, priority, at}]

`<state_dir>/paid.json` is `{"paid_until": epoch, "paid_wait": epoch}`. **Nothing is run by a tool billed by its API without the yes**: `realm/tool_now.py`
picks one only while `paid_until` is in the future. The row is asked when the tool now is None (every subscription out) and a tool turned on is billed by its API,
and not again before the reset a no was kept for. `usd_task` (about what a task of that tool costs) is the host's to say; None when it is not known.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from orkboard.realm import harnesses, ideas, tool_now

FILE = "paid.json"
TEXT = "Go on paid?"            # the row's `text`, as a stop of an unknown kind is drawn until the face draws this one (spec 100)


def _read(state_dir: Path) -> dict:
    got = ideas._json(Path(state_dir) / FILE)
    return got if isinstance(got, dict) else {}


def _num(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def until(state_dir: Path, at: float) -> float | None:
    """The reset a yes to go on paid holds until, while it holds; else None (it ended with the reset)."""
    got = _num(_read(state_dir).get("paid_until"))
    return got if got is not None and got > at else None


def waiting(state_dir: Path, at: float) -> bool:
    """A no was kept and its reset has not come: the row is not asked again."""
    got = _num(_read(state_dir).get("paid_wait"))
    return got is not None and got > at


def answer(state_dir: Path, yes: bool, ends: float | None, at: float) -> float:
    """Keeps the answer until `ends` (the reset the card named; none known: the five-hour window from now) and returns it. A yes drops a no and the other way round."""
    ends = ends if ends is not None and ends > at else at + tool_now.PAID_HOLD_S
    with ideas.LOCK:
        ideas._write_json(Path(state_dir) / FILE, {"paid_until" if yes else "paid_wait": ends})
    return ends


def row(state_dir: Path, machine, got: dict, usd_task: float | None, at: float) -> list[dict]:
    """The Orkmaster's row `paid` (goal-free, as `board_rows.project_q`): `got` is the tool now's read (`tool_now.now`): it is asked only while every subscription
    is out (`now` None) and a tool billed by its API is turned on; [] while a yes holds (then `now` is that tool), a no waits for its reset, or there is no such tool."""
    tool = tool_now.api_tool(machine)
    if got.get("now") is not None or tool is None or until(state_dir, at) is not None or waiting(state_dir, at):
        return []
    ends = got.get("until")
    return [{"kind": "paid", "tool": tool, "name": harnesses.title(tool), "until": _iso(ends), "usd_task": usd_task, "text": TEXT, "blocks": True,
             "priority": "high", "at": _iso(at)}]


def _iso(epoch: float | None) -> str | None:
    return dt.datetime.fromtimestamp(epoch).isoformat(timespec="minutes") if epoch is not None else None
