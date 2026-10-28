"""The project's questions at the first start (docs/specs/99-a-goals-way.md §8; decisions §153.1–§153.4, §157.1): what is kept of the one call of Product's leader (in a
game Game design's), taken strictly, and what the person's answers keep. Pure code, no model, no face; `core/idea_project_q.py` asks, `gui/ideas_project_q.py`
answers, `realm/board_rows.py` shows the row.

    project_questions.party_of(root)                         # the party that asks: Product's, else Game design's, else "" (the Orkmaster's one card then)
    project_questions.clean(answer, party, leader, known)    # the model's answer → [(card, key, said)], at most three, a key (whom · hurts · leaves out) once
    project_questions.fallback(party="")                     # the Orkmaster's one card *What is this project for?* (a text field: no choices)
    project_questions.take(rec, answers, decide)             # the person's answers → [{id, key, answer, by}], `by` person | read; ValueError in plain words
    project_questions.record(state_dir) / save_record(...)   # <state_dir>/project_q.json: what the row shows and what was asked

The record is `{status: "asking"|"waiting"|"done"|"failed", party, leader, questions: [card], keys: {card id: key}, read: [card id], at, error}`. A card is
`idea_questions.card`'s, `project: true`; `read` are the cards whose pick is the leader's reading of the files (`said`), which the person confirms with one press.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import goal_team, idea_questions, ideas, project_facts

FILE = "project_q.json"
KEYS = project_facts.COMMON_KEYS                 # whom it is for · what hurts them · what it leaves out, in the order they are asked
MAX_CARDS = 3
CRAFTS = ("product", "game-design")             # who asks: Product's leader, in a game Game design's (§153.1)
ORKMASTER = "orkmaster"
WHAT_FOR = "What is this project for?"           # the Orkmaster's one card with neither party: a line is the answer
ORKMASTER_FACT = ORKMASTER                       # the party an answer to the Orkmaster's card is kept under (its key is `for_whom`: the common core)


def party_of(root: Path) -> str:
    """The party whose leader reads the project at the start: a party of Product's craft, else of Game design's; "" with neither."""
    found = {goal_team.craft_of(root, t["slug"]): t["slug"] for t in reversed(ideas.tracks(root, make=False)) if t["slug"] != ideas.GENERAL}
    return next((found[c] for c in CRAFTS if c in found), "")


def clean(answer: object, party: str, leader: str, known: set[str]) -> list[tuple[dict, str, bool]]:
    """The leader's answer, strictly: `[(card, key, said)]` for the keys not answered yet, in the order of `KEYS`, each key once, at most `MAX_CARDS`. A question that is
    no card (`idea_questions.card`: two to four choices, one picked) is not one; `said` is the leader telling the files say it, its pick being the reading."""
    items = answer.get("questions") if isinstance(answer, dict) else None
    got: dict[str, tuple[dict, bool]] = {}
    for item in items if isinstance(items, list) else []:
        key = str(item.get("key") or "").strip().lower() if isinstance(item, dict) else ""
        if key not in KEYS or key in known or key in got:
            continue
        c = idea_questions.card(item, id=f"project-{key}", by=party, leader=leader, project=True)
        if c is not None:
            got[key] = (c, item.get("said") is True)
    return [(got[k][0], k, got[k][1]) for k in KEYS if k in got][:MAX_CARDS]


def fallback() -> dict:
    """The Orkmaster's one card for a project with neither party: no choices (a line is the answer, *a mobile app for…*: spec 75 §0), kept as whom it is for."""
    return {"id": "project-for_whom", "by": ORKMASTER, "leader": ORKMASTER, "q": WHAT_FOR, "choices": [], "pick": None, "why": "", "project": True}


def take(rec: dict, answers: object, decide: bool) -> list[dict]:
    """The answers to the cards waiting, as they are kept: `[{id, key, answer, by}]`, `by` "person" for a pick or the words written (*Other…*: the words win when both are
    given), "read" for a card left to the leader (`decide`: its pick; a card with no pick, the Orkmaster's, is let go, nothing kept). ValueError, in plain words, for an
    answer to a question that is not asked, and for a card left unanswered when the person did not leave it to the leader. Nothing is changed here."""
    waiting = {c["id"]: c for c in rec.get("questions") or [] if isinstance(c, dict) and isinstance(c.get("id"), str)}
    given: dict[str, str] = {}
    for a in answers if isinstance(answers, list) else []:
        c = waiting.get(a.get("id")) if isinstance(a, dict) else None
        if c is None:
            raise ValueError("That question is not asked now")
        if got := idea_questions.answer_of(c, a):
            given[c["id"]] = got[0]
    if len(given) < len(waiting) and not decide:
        raise ValueError("Answer every question, or let the leader decide")
    keys = rec.get("keys") if isinstance(rec.get("keys"), dict) else {}
    out = []
    for c in waiting.values():
        key = keys.get(c["id"]) or ""
        if not key:
            continue
        if c["id"] in given:
            out.append({"id": c["id"], "key": key, "answer": given[c["id"]], "by": "person"})
        elif c.get("choices") and isinstance(c.get("pick"), int):
            out.append({"id": c["id"], "key": key, "answer": idea_questions.default_of(c), "by": "read"})
    return out


def record(state_dir: Path) -> dict:
    """What the first start asked (`project_q.json`), {} before it has begun."""
    got = ideas._json(Path(state_dir) / FILE)
    return got if isinstance(got, dict) else {}


def save_record(state_dir: Path, rec: dict) -> dict:
    """The record replaced whole (a caller that read it first holds `ideas.LOCK` for both)."""
    with ideas.LOCK:
        ideas._write_json(Path(state_dir) / FILE, rec)
    return rec
