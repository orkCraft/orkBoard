"""A leader's answer in Talk, taken strictly (docs/specs/99-a-goals-way.md §5; decisions §121.2, §153.3, §153.5, §158.1): the model's answer is untrusted, so what a
round or a bug's diagnosis keeps is what these functions let through. Pure code, no model, no face; `core/idea_talk.py` calls them.

    clean_round(answer, party, leader, rnd, first, known)     # {stance, for, against, cards: [(card, blocks, key)], more}, or None; the second round has no stance
    pick_three(pool)                                          # the Orkmaster's rule for the three of all the leaders' cards: (chosen, closed)
    clean_diagnosis(answer, party, leader, root, first, known, again=False)    # a bug's {cause, where: [path], cards}, or None
    touched(root, text, limit) / failure_lines(text)          # the files a report names; its failure's lines
    fact_text(q, answer) / said_lines(rec)                    # a project question kept as a fact; a round's questions with their answers, for the second round
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from orkboard.hooks.warder import is_secret
from orkboard.realm import idea_questions, project_facts

MAX_CARDS = 3                      # a round's questions: the goal's three, the leaders' and the project's together (§121.2, §153.3)
MAX_GOAL = 3                       # a leader's questions about the goal, at most
MAX_PROJECT = 2                    # … and about the project, at most (a bug's Tech: one it cannot do without)
LINE = 200                         # a stance, a for, an against
CAUSE_CHARS = 300
WHERE = 5                          # the paths a cause names
FAILURE_LINES, FAILURE_CHARS = 12, 1500
FACT_ROOM = 20                     # the least of a question kept with its answer as a fact
_KEY = re.compile(r"[a-z0-9_]{1,40}")
_FAIL = re.compile(r"Traceback \(most recent call last\)|^\s*at\s+\S.*:\d+|\bFAILED\b|\b\w*Error:|File \".*\", line \d+", re.M)
_PATH = re.compile(r"(?<![\w.-])(/?(?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]{1,8})(?::\d+)?")


def _line(value: object, limit: int = LINE) -> str:
    return " ".join(value.split())[:limit] if isinstance(value, str) else ""


def total(step: str, measures: list[dict]) -> dict:
    """The calls' measures as one (`step`, their prompts' characters, their tokens key by key, their cost): the goal's `measure`."""
    tokens: dict[str, float] = {}
    for m in measures:
        for k, v in (m.get("tokens") or {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                tokens[k] = tokens.get(k, 0) + v
    costs = [m["cost"] for m in measures if isinstance(m.get("cost"), (int, float)) and not isinstance(m.get("cost"), bool)]
    return {"step": step, "prompt_chars": sum(int(m.get("prompt_chars") or 0) for m in measures), "tokens": tokens or None,
            "cost": round(sum(costs), 4) if costs else None}


# -- a leader's answer, strictly -------------------------------------------------------------------------------------------------------

def _cards(raw: object, party: str, leader: str, prefix: str, limit: int, project: bool = False, known: set[str] | None = None) -> list[tuple[dict, bool, str]]:
    """`(card, blocks, key)` of the questions in a list of the model's answer, strictly: those that are cards (`idea_questions.card`), the same question once,
    `blocks` when the leader says the work cannot start without it; a project question has a key (`[a-z0-9_]{1,40}`) that is not answered yet."""
    out: list[tuple[dict, bool, str]] = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict) or len(out) >= limit:
            continue
        key = ""
        if project:
            key = str(item.get("key") or "").strip().lower()
            if not _KEY.fullmatch(key) or key in (known or set()) or any(k == key for _c, _b, k in out):
                continue
        c = idea_questions.card(item, id=f"p-{party}-{key}" if project else f"{prefix}-{len(out) + 1}", by=party, leader=leader, project=project)
        if c is None or any(o["q"].lower() == c["q"].lower() for o, _b, _k in out):
            continue
        out.append((c, item.get("blocks") is True, key))
    return out


def clean_round(answer: object, party: str, leader: str, rnd: int, first: bool, known: set[str]) -> dict | None:
    """One leader's answer to a round, strictly: `{stance, for, against, cards: [(card, blocks, key)], more}`; None when it is no object, or says no stance in the
    first round. The second round has no stance and no question about the project; `more` is the leader asking for a second round (the first round's)."""
    if not isinstance(answer, dict):
        return None
    out: dict[str, Any] = {"stance": "", "for": "", "against": "", "more": rnd == 1 and answer.get("second_round") is True}
    if rnd == 1:
        out.update({"stance": _line(answer.get("stance")), "for": _line(answer.get("for")), "against": _line(answer.get("against"))})
        if not out["stance"]:
            return None
    cards = _cards(answer.get("questions"), party, leader, f"r{rnd}-{party}", MAX_GOAL)
    if rnd == 1 and first:
        cards += _cards(answer.get("project_questions"), party, leader, "", MAX_PROJECT, True, known)
    out["cards"] = cards
    return out


def pick_three(pool: list[tuple[dict, bool, str]], limit: int = MAX_CARDS) -> tuple[list[tuple[dict, bool, str]], list[tuple[dict, bool, str]]]:
    """The Orkmaster's rule for the three (§121.2, §153.3) of all the leaders' cards, given in the route's order: those the work cannot start without first, then by
    the route's order; `(chosen, closed)`, the chosen again in the route's order (as they are asked), the closed ones left to their leaders' picks."""
    order = sorted(range(len(pool)), key=lambda n: (not pool[n][1], n))[:limit]
    return [pool[n] for n in sorted(order)], [pool[n] for n in range(len(pool)) if n not in order]


def clean_diagnosis(answer: object, party: str, leader: str, root: Path, first: bool, known: set[str], again: bool = False) -> dict | None:
    """Tech's answer to the diagnosis, strictly: `{cause, where: [path], cards}`; None when it is no object or names no cause. The questions are the cases' (at most
    three) and, at its party's first goal, the one about the project it cannot do without (`blocks`); a second guess (`again`) asks nothing. `where`: files that exist."""
    if not isinstance(answer, dict):
        return None
    cause = _line(answer.get("cause"), CAUSE_CHARS)
    if not cause:
        return None
    where: list[str] = []
    for w in answer.get("where") if isinstance(answer.get("where"), list) else []:
        p = _relative(root, w)
        if p and p not in where and len(where) < WHERE:
            where.append(p)
    cards: list[tuple[dict, bool, str]] = []
    if not again:
        cards = _cards(answer.get("questions"), party, leader, "case", MAX_GOAL)
        if first:
            cards += [x for x in _cards(answer.get("project_questions"), party, leader, "", MAX_PROJECT, True, known) if x[1]][:1]
    return {"cause": cause, "where": where, "cards": cards}


def _relative(root: Path, value: object) -> str:
    """A file of the project the text names, as a path inside it ("" for none: not a file, outside the project, a link, a secret)."""
    p = str(value or "").strip()
    if not p or len(p) > 300:
        return ""
    try:
        f = Path(p)
        if f.is_absolute():
            f = f.resolve().relative_to(root.resolve())
        rel = f.as_posix()                                   # a leading "./" is gone already; a leading dot of a name (".github") stays
        if not rel or rel == "." or ".." in rel.split("/") or is_secret(rel):
            return ""
        full = root / rel
        return rel if full.is_file() and not full.is_symlink() else ""
    except (OSError, ValueError):
        return ""


def touched(root: Path, text: str, limit: int) -> list[str]:
    """The files of the project a report names, by code, in the order it names them (at most `limit`)."""
    found: list[str] = []
    for m in _PATH.finditer(text or ""):
        p = _relative(root, m.group(1))
        if p and p not in found:
            found.append(p)
        if len(found) >= limit:
            break
    return found


def failure_lines(text: str) -> str:
    """The lines of a report that are a failure's (a `Traceback`, an `at …(…:n)`, `FAILED`, an `Error:`), by code."""
    return "\n".join([ln.rstrip() for ln in (text or "").splitlines() if _FAIL.search(ln)][:FAILURE_LINES])[:FAILURE_CHARS]


def fact_text(q: str, answer: str) -> str:
    """A project question and its answer as the one fact kept (`project_facts.FACT_CHARS`): the question first, cut before the answer is."""
    room = project_facts.FACT_CHARS - len(answer) - 3
    if room < FACT_ROOM:
        return answer[:project_facts.FACT_CHARS]
    return f"{q if room >= len(q) else q[:room - 1].rstrip() + '…'} — {answer}"


def said_lines(rec: dict) -> str:
    """The round's questions with their answers (and the picks that closed the rest), for the second round's prompt: the round's own answers, nothing more."""
    rows = [f"- {a['q']} — {a['answer']}" for a in rec.get("answers") or []]
    rows += [f"- {d['q']} — {d['answer']} (left to {d.get('by') or 'its leader'}'s pick)" for d in rec.get("defaults") or []]
    return "\n".join(rows)

