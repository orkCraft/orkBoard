"""The night's proposals (docs/specs/168-the-window-played-as-a-card-games-table.md H3; decisions §283.32): on the top rung of the night's ladder
(`settings.night_rung` is "proposals") a leader picked for the night makes **one proposal** from its map and its journal, **three a night at most**,
each taken **to a ready spec at most** and **never built without a press**, all **within the night's reserve**. In the morning a proposal lies in the
column's *Specs* marked *proposed*, and a card in the hand offers **Take** or **Drop**. No face, no model: the call is made by the caller (`ask`).

    idea_night.night_key("01:00-07:00", now)                         # "2026-11-10": the night `now` is in, by the day it began; "" outside the window
    idea_night.who_may(state_dir, key, leaders, rung)                # the picked leaders asked tonight: none that has proposed tonight, never past three
    idea_night.within_reserve(limits, settings, wall, share=None)    # the reserve holds: a night that would spend past it stops
    idea_night.prompt(party, map_text, journal, taken)               # what the leader is asked; `read_answer(text)` -> {"title", "spec"} | None
    idea_night.make(state_dir, party, key, title, spec, goal, at)    # the proposal kept, `status: "proposed"`, `stage: "spec"` (never past it)
    idea_night.answer(state_dir, pid, take)                          # Take or Drop; `rows(state_dir)` the morning's proposals still to answer
    idea_night.card(settings, ...)                                   # the night's card: rung, window, leaders, how many tonight

A proposal is a record in `<state_dir>/night/proposals.json`; its goal (laid on hold by the caller, so nothing starts it) is `goal`. `status`: `proposed`
(waits for the person), `taken` (the person pressed Take: the goal goes on as any goal does) or `dropped`.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import threading
from pathlib import Path
from typing import Any

from orkboard import settings as board_settings
from orkboard.realm import idea_risk, idea_target, ideas

PER_NIGHT = 3                        # three proposals a night at most, one a leader (decisions §283.32)
STAGE = "spec"                       # a proposal is taken to a ready spec at most: the stage never moves past it without the person's Take
FILE = "proposals.json"
LOCK = threading.Lock()


def _file(state_dir: Path) -> Path:
    return Path(state_dir) / "night" / FILE


def read(state_dir: Path) -> list[dict]:
    """Every proposal kept, oldest first."""
    got = ideas._json(_file(state_dir))
    rows = got.get("proposals") if isinstance(got, dict) else None
    return [r for r in rows or [] if isinstance(r, dict) and isinstance(r.get("id"), str) and isinstance(r.get("party"), str)]


def _save(state_dir: Path, rows: list[dict]) -> None:
    ideas._write_json(_file(state_dir), {"proposals": rows})


def night_key(spec: str, now: dt.datetime) -> str:
    """The night `now` is in, named by the day it began; "" outside the night's window."""
    began = idea_target.night_start(spec, now)
    return began.strftime("%Y-%m-%d") if began is not None else ""


def tonight(state_dir: Path, key: str) -> list[dict]:
    return [r for r in read(state_dir) if r.get("night") == key]


def who_may(state_dir: Path, key: str, leaders: list[str], rung: str) -> list[str]:
    """The picked leaders (parties' slugs, in the order picked) the night may ask now: only on the top rung, none that has proposed tonight (a
    dropped one counts: one a leader), and no more than are left of the three a night."""
    if not key or not idea_risk.night_allows(rung, "propose"):
        return []
    done = tonight(state_dir, key)
    left = PER_NIGHT - len(done)
    asked = {r["party"] for r in done}
    return [p for p in dict.fromkeys(leaders) if p not in asked][:max(0, left)]


def within_reserve(limits: Any, settings: dict | None, wall: float, share: float | None = None) -> bool:
    """The night's reserve holds: no window of the tool is at or under the night's share (`idea_target.reserve_held`), and a call that would cost `share` of
    the window fits what is above the reserve (`idea_target.room`). With no limits read there is nothing to read it against and the call goes, as every
    call does (`fits_window`)."""
    if idea_target.reserve_held(limits, settings, wall) is not None:
        return False
    room = idea_target.room(limits, settings, wall)
    if room is None:
        return True
    return room > 0 and (share is None or share <= room)


def prompt(party: str, map_text: str, journal: str, taken: list[str] = ()) -> str:
    """What a leader is asked: one proposal for its party from its map and its journal, as a spec that is ready to read (never built)."""
    avoid = "\n".join(f"- {t}" for t in taken) or "- (none)"
    return (f"You are the leader of the {party} party and it is night. Make ONE proposal for what the project should do next in your party's craft, from your map and your "
            "journal below. Write it as a ready spec, not as code, and do not build anything: the person decides in the morning.\n"
            'Answer with one JSON object only: {"title": "<at most 80 characters>", "spec": "<Why, Done when and Stages, plain text>"}.\n\n'
            f"Goals already on the Board or proposed (do not repeat them):\n{avoid}\n\nYour map:\n{map_text or '(empty)'}\n\n{journal or 'Your journal: (empty)'}\n")


def read_answer(text: object) -> dict | None:
    """`{"title", "spec"}` from a leader's answer (a JSON object, maybe inside a fence or prose); None when it holds no title and spec."""
    raw = str(text or "")
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        got = json.loads(m.group(0)) if m else None
    except ValueError:
        return None
    if not isinstance(got, dict):
        return None
    title, spec = " ".join(str(got.get("title") or "").split())[:80], str(got.get("spec") or "").strip()[:ideas.SECTION_CHARS]
    return {"title": title, "spec": spec} if title and spec else None


def make(state_dir: Path, party: str, key: str, title: str, spec: str, goal: str = "", at: str = "") -> dict | None:
    """The proposal kept as `proposed` at the stage `spec`; None when the party has proposed tonight already or the night has its three (the caps hold
    here too, whoever asks)."""
    with LOCK:
        rows = read(state_dir)
        tonights = [r for r in rows if r.get("night") == key]
        if not key or len(tonights) >= PER_NIGHT or any(r["party"] == party for r in tonights):
            return None
        row = {"id": f"np-{key}-{party}"[:120], "party": party, "night": key, "title": title, "spec": spec, "goal": goal, "stage": STAGE,
               "status": "proposed", "at": at or dt.datetime.now().isoformat(timespec="seconds")}
        _save(state_dir, [*rows, row])
        return row


def rows(state_dir: Path) -> list[dict]:
    """The morning's proposals still to answer."""
    return [r for r in read(state_dir) if r.get("status") == "proposed"]


def of_goal(state_dir: Path, slug: str) -> dict | None:
    """The proposal still waiting that a goal is (its card says *proposed*)."""
    return next((r for r in rows(state_dir) if r.get("goal") == slug), None)


def answer(state_dir: Path, pid: str, take: bool) -> dict:
    """The person's Take (`taken`: the goal goes on as any goal does) or Drop (`dropped`). A proposal not waiting is a ValueError."""
    with LOCK:
        all_ = read(state_dir)
        row = next((r for r in all_ if r["id"] == pid and r.get("status") == "proposed"), None)
        if row is None:
            raise ValueError("That proposal is not waiting")
        row["status"] = "taken" if take else "dropped"
        _save(state_dir, all_)
        return dict(row)


WAYS = (("Take", "take", "The goal goes on as any goal does: Talk, then the spec, then the work, each as you allow"),
        ("Drop", "drop", "The proposal and its goal are gone; the leader is not asked for another tonight"))


def way_row(row: dict, title_of: str = "") -> dict:
    """The proposal as a Needs-you row for the hand's card: `kind` "night_proposal", its ways *Take* and *Drop* with their `kinds` (`realm/way_kinds.py`)."""
    return {"idea": "", "goal": row.get("goal") or "", "kind": "night_proposal", "proposed": True, "id": row["id"], "by": row["party"],
            "title": f"Proposed: {row['title']}", "text": row["spec"][:600], "blocks": False, "at": row.get("at") or "", "night": row.get("night") or "",
            "choices": [{"label": w[0], "way": w[1], "text": w[2]} for w in WAYS], "kinds": [w[1] for w in WAYS]}


def card(settings: dict | None, state_dir: Path, wall: float | None = None) -> dict:
    """The night's card: the rung, the night's window (when it runs), the leaders picked, and how many proposals tonight holds."""
    s = settings or {}
    window = str(s.get("night") or board_settings.IDEAS["night"])
    now = dt.datetime.fromtimestamp(wall) if wall else dt.datetime.now()
    key = night_key(window, now)
    rung = board_settings.night_rung(s)
    return {"rung": rung, "rungs": list(board_settings.NIGHT_RUNGS), "window": window, "open": bool(key), "leaders": board_settings.night_leaders(s),
            "picked": board_settings.clean_night_leaders(s.get("night_leaders")) or [], "tonight": len(tonight(state_dir, key)) if key else 0,
            "most": PER_NIGHT, "waiting": len(rows(state_dir))}
