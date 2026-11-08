"""A leader's no in Talk (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §4; decisions §183.1–§183.3): what a round's verdicts leave in the Talk's record, the
Needs you rows a `no` makes, what the decision says of the leaders the person overruled. Pure code, no model, no face; `core/idea_talk.py` keeps the record,
`core/idea_objection.py` answers it, `realm/board_map.py` draws the rows, `core/idea_decide.py` words the overruled.

    made(stances)                 # the `no` of a round as objections, in the route's order: [{party, leader, why, instead, after, answer: ""}]
    pending(rec)                  # the objections no one has answered yet
    open_rows(...)                # the Needs you row of the goal's open hearing (spec 120 §4): one `{kind: "hearing", moment: "talk", heading, sides, ...}` in place of a row a no
    open_hearing(...)             # the hearing itself (`realm/idea_hearing.py`'s sides), None when none is open
    objection_rows(...)           # what each no may be answered with: `{party, leader, why, instead, after, after_title, answers}` (`core/idea_objection.py` checks an answer by them)
    answers_of(o)                 # the answers that apply: drop · smaller (it has an `instead`) · later (it names a goal in line) · go
    lines(rec, name_of)           # (the no overruled, the doubts) as the decision's lines: "Against <Leader>: <why>", "Doubt from <Leader>: <why>"
    lens(craft)                   # what a leader judges a goal against, by its party's craft
    reword(root, slug, text)      # the goal's words become `text` (*Do the smaller one*)

The record (`idea_questions.record`) holds `stances` — each with `verdict`, `why`, `instead`, `after` — and `objections`, one a `no`, whose `answer` stays "" until the person
answers it, then one of `ANSWERS`.
"""
from __future__ import annotations

from orkboard.realm.seat_lens_rules import LENS, lens

from pathlib import Path
from typing import Callable

from orkboard.realm import idea_hearing, ideas, lens_rubrics
from orkboard.realm.idea_words import short_of

ANSWERS = ("drop", "smaller", "later", "go")      # in the order the card offers them
TITLE_CHARS = 80


def made(stances: list[dict]) -> list[dict]:
    """The objections of a round: one for each stance whose verdict is `no`, in the route's order, unanswered. The weigher's stance (`weigher: true`) makes none (spec 155 E)."""
    return [{"party": s["party"], "leader": s["leader"], "why": s.get("why", ""), "instead": s.get("instead", ""), "after": s.get("after", ""), "answer": ""}
            for s in stances if isinstance(s, dict) and not s.get("weigher") and s.get("verdict") == "no" and s.get("why")]


def pending(rec: dict) -> list[dict]:
    """The objections no one has answered: the decision waits while there are any."""
    return [o for o in rec.get("objections") or [] if isinstance(o, dict) and not o.get("answer")]


def answers_of(o: dict) -> list[str]:
    """The answers that apply to an objection: *Drop the goal* and *Go on anyway* always, *Do the smaller one* when the leader named one, *Not now* when the leader's no names a goal in line."""
    return [a for a in ANSWERS if a in ("drop", "go") or (a == "smaller" and o.get("instead")) or (a == "later" and o.get("after"))]


def objection_rows(root: Path, state_dir: Path, slug: str, rec: dict) -> list[dict]:
    """What each leader's no may be answered with, one a leader in the route's order (`rec`: the goal's Talk record): `{kind: "objection", party, leader, why, instead, after,
    after_title, answers, text}`. Not a Needs you row any more (a goal's `hearing` is, `open_rows`): `core/idea_objection.py` checks an answer by them. None for a bug's Talk (it is
    Tech's diagnosis alone) or a Talk that is not begun."""
    if rec.get("mode") != "talk":
        return []
    out = []
    for o in pending(rec):
        page = ideas.idea_page(root, o["after"]) if o.get("after") else None
        after = o["after"] if page is not None and o["after"] != slug else ""
        out.append({"kind": "objection", "party": o["party"], "leader": o["leader"], "why": o["why"], "instead": o.get("instead", ""), "after": after,
                    "after_title": " ".join((page.title if page is not None else "").split())[:TITLE_CHARS] if after else "",
                    "answers": answers_of({**o, "after": after}), "text": o["why"]})
    return out


def open_hearing(root: Path, state_dir: Path, slug: str, rec: dict, name_of: Callable[[str], str] | None = None) -> dict | None:
    """The hearing of a goal's Talk while it is open (`idea_hearing.is_open`), else None (spec 120 §4.1): the sides of `idea_hearing.of_talk` from the stances of `rec`, a `no`'s
    `after` kept only when it names another goal that is in the Wiki (its title said), the leaders named by `name_of` (default: `idea_hearing.namer`)."""
    if not idea_hearing.is_open(rec):
        return None
    stances = []
    for s in rec.get("stances") or []:
        if not isinstance(s, dict):
            continue
        page = ideas.idea_page(root, s["after"]) if s.get("after") else None
        keep = s.get("after") if page is not None and s["after"] != slug else ""
        stances.append({**s, "after": keep, "after_title": " ".join(page.title.split())[:TITLE_CHARS] if keep else ""})
    return idea_hearing.of_talk({**rec, "stances": stances}, name_of or idea_hearing.namer(state_dir))


def open_rows(root: Path, state_dir: Path, slug: str, rec: dict) -> list[dict]:
    """The Needs you row of a goal's open hearing, one a goal (spec 120 §4.4; the decision waits while it is open): `{kind: "hearing", moment: "talk", heading, sides, left_out, own, text}`.
    `heading` is the hearing's title (`title` is the goal's, as on every row); a doubt with neither `instead` nor `after` is a line of `go`'s side. None for a bug's Talk or a Talk not begun."""
    got = open_hearing(root, state_dir, slug, rec)
    if got is None:
        return []
    return [{"kind": "hearing", "moment": "talk", "heading": got["title"], "sides": got["sides"], "left_out": got["left_out"], "own": True, "text": got["title"]}]


def lines(rec: dict, name_of: Callable[[str], str]) -> tuple[list[str], list[str]]:
    """What the decision must say of the leaders: `(overruled, doubts)` — *Against <Leader>: <why>* for each `no` the person went on anyway, *Doubt from <Leader>: <why>* for each doubt.
    `name_of(leader)`: the name the leader is called by."""
    stances = [s for s in rec.get("stances") or [] if isinstance(s, dict)]
    over = {o.get("party") for o in rec.get("objections") or [] if isinstance(o, dict) and o.get("answer") == "go"}
    return ([f"Against {name_of(s['leader'])}: {s['why']}" for s in stances if s.get("verdict") == "no" and s.get("party") in over],
            [f"Doubt from {name_of(s['leader'])}: {s['why']}" for s in stances if s.get("verdict") == "doubt" and s.get("why")])


def reword(root: Path, slug: str, text: str) -> None:
    """*Do the smaller one*: the goal's words (its Gist, and the title and short name made of them as `ideas.add_idea` made them) become `text`."""
    text = " ".join(str(text or "").split())
    if not text:
        raise ValueError("A goal needs a few words")
    with ideas.LOCK:
        page = ideas.idea_page(root, slug)
        if page is None:
            raise ValueError(f"No goal {slug!r}")
        first = ideas.thesis(text) or text
        page.title = first if len(first) <= 80 else first[:77].rsplit(" ", 1)[0] + "…"
        page.set("short", short_of(first))
        page.set_section("Gist", text)
        if page.section("Asked").strip():                  # the person's words are asked first by the decision and the sections: the smaller goal is what they read
            page.set_section("Asked", text)
        ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
        ideas._reindex(root)
