"""A leader's answer in Talk, taken strictly (docs/specs/99-a-goals-way.md §5; decisions §121.2, §153.3, §153.5, §158.1): the model's answer is untrusted, so what a
round or a bug's diagnosis keeps is what these functions let through. Pure code, no model, no face; `core/idea_talk.py` calls them.

    clean_round(answer, party, leader, rnd, first, known, line, craft="", again=False)     # {stance, for, against, verdict, why, instead, after, priority, risk, assumes, cards: [(card, blocks, key)], more, rejudged}, or None; the second round has no stance, verdict or assumes (unless `again`)
    clean_judgement(answer, craft, line)                      # a verdict alone, after the answers or from Product weighing a goal: {verdict, why, instead, after, priority, risk}, or None (spec 120 §3)
    clean_assumes(value)                                      # what a leader assumes about a goal: {text, signal} (a line each, 200 characters) or {} (spec 116 §3)
    pick_three(pool)                                          # the Orkmaster's rule for the three of all the leaders' cards: (chosen, closed)
    clean_diagnosis(answer, party, leader, root, first, known, again=False)    # a bug's {cause, where: [path], cards}, or None
    touched(root, text, limit) / failure_lines(text)          # the files a report names; its failure's lines
    fact_text(q, answer) / said_lines(rec)                    # a project question kept as a fact; a round's questions with their answers, for the second round
"""
from __future__ import annotations

from orkboard.realm.seat_talk_limits_rules import LINE, MAX_GOAL, MAX_PROJECT

import re
from pathlib import Path
from typing import Any, Iterable

from orkboard.hooks.warder import is_secret
from orkboard.realm import idea_questions, project_facts

MAX_CARDS = 3                      # a round's questions: the goal's three, the leaders' and the project's together (§121.2, §153.3)
PRIORITIES = ("high", "normal", "low")       # Product's word on how the goal stands against the goals in line (spec 120 §3.1)
RISKS = ("low", "medium", "high")            # Tech's word on what the change may break
PRODUCT, TECH = "product", "tech"            # the crafts (`goal_team.craft_of`) whose leaders give a priority and a risk
CAUSE_CHARS = 500
CHECK_CHARS = 200                  # what a doubt says to look up (spec 155 D.2)
WHERE = 5                          # the paths a cause names
FAILURE_LINES, FAILURE_CHARS = 12, 1500
FACT_ROOM = 20                     # the least of a question kept with its answer as a fact
_KEY = re.compile(r"[a-z0-9_]{1,40}")
_FAIL = re.compile(r"Traceback \(most recent call last\)|^\s*at\s+\S.*:\d+|\bFAILED\b|\b\w*Error:|File \".*\", line \d+", re.M)
_PATH = re.compile(r"(?<![\w.-])(/?(?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]{1,8})(?::\d+)?")


def _line(value: object, limit: int = LINE) -> str:
    """One line of the model's words: cut at a word with `…` when it is too long (as `idea_questions._plain` does), never mid-word."""
    text = " ".join(value.split()) if isinstance(value, str) else ""
    if len(text) <= limit:
        return text
    head = text[:limit - 1]
    return (head.rsplit(" ", 1)[0] if " " in head else head).rstrip(",;:") + "…"


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


def clean_verdict(answer: dict, line: Iterable[str] = ()) -> dict:
    """A leader's verdict on the goal (spec 108 §4.1), strictly: `{verdict: go|doubt|no, why, instead, after}`. A `doubt` or a `no` needs its `why` (one line): without it the
    leader said nothing against the goal and the verdict reads as `go`. `instead` (a smaller or other goal that would serve) is kept with a doubt or a no; `after`, the goal in `line`
    (the slugs the leader was given) a `no` says should come first, with a `no` only and only one of those. `check` (spec 155 D.2): what reading the code would look up to settle a
    `doubt` (at most `CHECK_CHARS` characters), kept with a doubt only."""
    verdict = str(answer.get("verdict") or "").strip().lower() if isinstance(answer.get("verdict"), str) else ""
    why = _line(answer.get("why"))
    if verdict not in ("doubt", "no") or not why:
        return {"verdict": "go", "why": "", "instead": "", "after": "", "check": ""}
    after = answer.get("after").strip() if isinstance(answer.get("after"), str) else ""
    return {"verdict": verdict, "why": why, "instead": _line(answer.get("instead")), "after": after if verdict == "no" and after in set(line) else "",
            "check": _line(answer.get("check"), CHECK_CHARS) if verdict == "doubt" else ""}


def clean_weight(answer: dict, craft: str) -> dict:
    """What only two leaders give (spec 120 §3.1), strictly: `{priority, risk}`. Product's leader (`craft` "product") gives a `priority` (high · normal · low), Tech's ("tech") a `risk`
    (low · medium · high); a value out of its set is dropped (""), and every other leader gives neither."""
    def one(key: str, allowed: tuple[str, ...], mine: bool) -> str:
        got = answer.get(key)
        got = got.strip().lower() if isinstance(got, str) else ""
        return got if mine and got in allowed else ""
    return {"priority": one("priority", PRIORITIES, craft == PRODUCT), "risk": one("risk", RISKS, craft == TECH)}


def clean_judgement(answer: object, craft: str = "", line: Iterable[str] = ()) -> dict | None:
    """A leader's verdict alone (spec 120 §3.2, §2.4), strictly: `{verdict, why, instead, after, priority, risk}`, the verdict as `clean_verdict` takes it and the weight as `clean_weight`
    does. None when the answer is no object. A leader that doubted and says nothing against the goal now reads as `go`."""
    if not isinstance(answer, dict):
        return None
    return {**{k: v for k, v in clean_verdict(answer, line).items() if k != "check"}, **clean_weight(answer, craft)}      # a verdict heard again looks nothing up


def clean_weigh(answer: object, craft: str = "", line: Iterable[str] = ()) -> dict | None:
    """What the weigher gives (spec 155 E, decisions §260.7), strictly: a verdict shaped like `clean_judgement`'s but always `go` with no `instead`, its `why` (one line), the `after` (a goal
    in `line` it should wait for) and its `priority`. A doubt or a no it may write opens nothing. None when the answer is no object."""
    if not isinstance(answer, dict):
        return None
    after = answer.get("after").strip() if isinstance(answer.get("after"), str) else ""
    return {"verdict": "go", "why": _line(answer.get("why")), "instead": "", "after": after if after in set(line) else "", **clean_weight(answer, craft)}


def clean_assumes(value: object) -> dict:
    """What a leader says the goal rests on that no one has shown (spec 116 §3), strictly: `{text, signal}`, a line each of `LINE` characters at most, or `{}` when it says none. The
    shape asked for is an object (`text`: the assumption, `signal`: what would show it); a bare line is the text alone (`signal` is ""), as a leader that writes less still has said it."""
    if isinstance(value, str):
        value = {"text": value}
    if not isinstance(value, dict):
        return {}
    text = _line(value.get("text"))
    return {"text": text, "signal": _line(value.get("signal"))} if text else {}


def clean_round(answer: object, party: str, leader: str, rnd: int, first: bool, known: set[str], line: Iterable[str] = (), craft: str = "", again: bool = False) -> dict | None:
    """One leader's answer to a round, strictly: `{stance, for, against, verdict, why, instead, after, priority, risk, assumes, cards: [(card, blocks, key)], more, rejudged}`; None when it is no object, or says no
    stance in the first round. `assumes` is `{text, signal}` or `{}` (`clean_assumes`). The second round has no stance, no verdict and no question about the project, unless it was asked to judge
    again (`again`: its verdict is then taken and `rejudged` is true; spec 120 §3.2); `more` is the leader asking for a second round (the first round's).
    `line`: the slugs of the goals in line the leader was given (a `no` may name one as `after`). `craft`: the leader's party's craft, which says whether it gives a `priority` or a `risk` (`clean_weight`)."""
    if not isinstance(answer, dict):
        return None
    out: dict[str, Any] = {"stance": "", "for": "", "against": "", "verdict": "go", "why": "", "instead": "", "after": "", "priority": "", "risk": "", "assumes": {},
                           "more": rnd == 1 and answer.get("second_round") is True, "rejudged": rnd == 2 and again}
    if rnd == 1:
        out.update({"stance": _line(answer.get("stance")), "for": _line(answer.get("for")), "against": _line(answer.get("against")), **clean_verdict(answer, line),
                    **clean_weight(answer, craft), "assumes": clean_assumes(answer.get("assumes"))})
        if not out["stance"]:
            return None
    elif again:
        out.update({**clean_verdict(answer, line), **clean_weight(answer, craft)})
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
    rows += [f"- {d['q']} — {d['answer']} ({'answered by ' + d['by'] if str(d.get('by')).startswith(('§', 'spec ')) else 'left to ' + (d.get('by') or 'its leader') + chr(39) + 's pick'})" for d in rec.get("defaults") or []]
    return "\n".join(rows)

