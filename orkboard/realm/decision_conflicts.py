"""The conflicts of a decision (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md E1.1, decisions §254.6): a standing decision the goal's decision goes against, said by the
decision's call as data and kept on `way["decision"]["conflicts"]`. No model, no face.

    decision_conflicts.clean(raw, known)     # [{number, point}] (at most CONFLICTS_MAX): the numbers among `known`, once each, the point one line of CARD_LINE_CHARS at most
    decision_conflicts.kept(decision)        # the conflicts a kept decision carries, [{number, point, answer}]
    decision_conflicts.open_of(decision)     # the conflicts of a decision not yet answered, [{number, point}]
    decision_conflicts.carry(old, new)       # the new call's conflicts, those the person answered already kept answered (a decision worded again never asks the same twice)

A kept conflict is `{number, point, answer}`: `answer` is "" while it waits for the person, else `replace`, `keep` or `other` (`gui/ideas_conflict.py`). A decision with a conflict open is not confirmable.
"""
from __future__ import annotations

from orkboard.realm.idea_words import CARD_LINE_CHARS

CONFLICTS_MAX = 2
ANSWERS = ("replace", "keep", "other")


def _line(value: object, limit: int) -> str:
    return " ".join(value.split())[:limit].rstrip() if isinstance(value, str) else ""


def clean(raw: object, known: object = ()) -> list[dict]:
    """The conflicts an answer says (see the module): an object with a number among `known` and a point; anything else is left out."""
    if not isinstance(raw, list):
        return []
    have = {int(n) for n in known if isinstance(n, int) and not isinstance(n, bool)}
    out: list[dict] = []
    for c in raw:
        n = c.get("number") if isinstance(c, dict) else None
        point = _line(c.get("point"), CARD_LINE_CHARS) if isinstance(c, dict) else ""
        if isinstance(n, int) and not isinstance(n, bool) and n in have and point and all(o["number"] != n for o in out):
            out.append({"number": n, "point": point})
    return out[:CONFLICTS_MAX]


def kept(decision: object) -> list[dict]:
    """See the module."""
    got = decision.get("conflicts") if isinstance(decision, dict) else None
    return [{"number": c["number"], "point": str(c.get("point") or ""), "answer": c.get("answer") if c.get("answer") in ANSWERS else ""}
            for c in got if isinstance(c, dict) and isinstance(c.get("number"), int) and not isinstance(c.get("number"), bool)] if isinstance(got, list) else []


def open_of(decision: object) -> list[dict]:
    """See the module."""
    return [{"number": c["number"], "point": c["point"]} for c in kept(decision) if not c["answer"]]


def carry(old: object, new: list[dict]) -> list[dict]:
    """See the module: `new` as the call said it (`clean`), each given the answer the person already gave that number."""
    answered = {c["number"]: c["answer"] for c in kept(old) if c["answer"]}
    return [{**c, "answer": answered.get(c["number"], "")} for c in new]
