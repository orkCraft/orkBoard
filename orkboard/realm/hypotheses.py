"""Hypotheses on Product's map (docs/specs/116-hypotheses-on-products-tree.md §2; decisions §194): what the project believes and has not shown, with the signal that would show it, what it rests
on and the goals that test it. Kept by the person and by the leaders (who propose, the person keeps); read by code, no model (the leaders' proposals are `core/idea_hypotheses.py`'s); no face.

    hypotheses.read(state_dir)                         # {items: [item]}; an item {id, text, signal, axis, on, rests, tests, by, party, state, evidence, verdict, at}
    hypotheses.add(state_dir, text, signal, *, axis="", on="", rests=(), by="person", party="") -> item   # a person's is `open`, a leader's `proposed`; ValueError in plain words past the bounds
    hypotheses.edit(state_dir, id, **fields) -> item   # text, signal, axis, on, rests (the id stays); ValueError for any other field
    hypotheses.keep(state_dir, id) -> item / hypotheses.drop(state_dir, id)    # a proposed one becomes open / a hypothesis gone
    hypotheses.attach(state_dir, id, goal="", test="") -> item | None    # `goal` rests on it, `test` tests it (a goal tests one hypothesis at most: it moves); an empty `id` detaches the goal / the test
    hypotheses.evidence(state_dir, id, text, ref="") -> item   # a line of what was found (`ref` a goal's slug, a mark's, or none), at most 12, the newest kept
    hypotheses.judge(state_dir, id, state, why="", decision=0) -> item   # "held" | "refuted" (with the decision's number) | "unsure" (stays open; the why becomes evidence)
    hypotheses.state_of(item, places)                  # the state as shown: "testing" for an open one while a test goal is in line or at work (`places`: {slug: "line"|"work"|"done"})
    hypotheses.due(state_dir, places)                  # the open items with a test, every test done, not judged: what the hand asks *Did it hold?* about
    hypotheses.text(state_dir, places)                 # for a leader's call: the open and testing ones, a line each, ~800 characters at most; "" with none
    hypotheses.parse(answer)                           # a leader's proposal, strictly → [{text, signal, axis, on, rests}] (three at most) or None

`<state_dir>/hypotheses.json` is `{items}`; the file is not trusted (what is not of the shape reads as absent). An item's `id` is its text's slug and stays when its words change; `text` and
`signal` are one line of 200 characters at most (the face puts *We believe* and *We'll know when* before them); `axis` is one of desirable, viable, feasible, usable, or ""; `on` is a job's id or an
outcome's id of the tree, or "" (the tree can change under it: a hypothesis on a job gone is read as on no job); `rests` and `tests` are goals' slugs, twelve at most each; `state` is proposed,
open, held or refuted ("testing" is never kept: `state_of` reads it from the goals' places). Bounds: seven open (or testing) at most, twelve proposed at most, forty in all (the oldest judged
go first); a proposal is refused past the first two as a person's new one is. A goal that is not in `places` (gone from the Board) is not done: a hypothesis tested by it is not due. A hypothesis
judged is judged once. The order is the order kept; nothing here depends on the clock but the `at` it writes.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import ideas

FILE = "hypotheses.json"
AXES = ("desirable", "viable", "feasible", "usable")
BY = ("person", "leader")
STATES = ("proposed", "open", "held", "refuted")
JUDGED = ("held", "refuted")
VERDICTS = ("held", "refuted", "unsure")
MAX_OPEN, MAX_PROPOSED, MAX_ALL = 7, 12, 40
TEXT_CHARS, GOALS, EVIDENCE = 200, 12, 12                    # a hypothesis's text and signal, the goals it rests on / is tested by, the lines of evidence kept
MAX_PROPOSE = 3                                               # a leader's proposal, at most
LIMIT = 800                                                   # the text, at most
CAPS = (TEXT_CHARS, 90, 50, 30)                               # the text's and signal's length in `text`, tried in turn until the lines fit
FIELDS = ("text", "signal", "axis", "on", "rests")
_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
_SLUG = re.compile(r"[a-z0-9-]{1,80}")
_WORDS = re.compile(r"[a-z0-9]+")


def _words(value: object, n: int) -> str:
    return " ".join(value.split())[:n].rstrip() if isinstance(value, str) else ""


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:max(0, n - 1)].rstrip() + "…"


def _file(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def _record(state_dir: Path) -> dict:
    got = ideas._json(_file(state_dir))
    return got if isinstance(got, dict) else {}


def _slugs(value: object) -> list[str] | None:
    """A list of goals' slugs, each once, twelve at most; None when it is not one."""
    if not isinstance(value, (list, tuple)) or not all(isinstance(s, str) and _SLUG.fullmatch(s.strip()) for s in value):
        return None
    out = list(dict.fromkeys(s.strip() for s in value))
    return out if len(out) <= GOALS else None


def _evidence(value: object) -> list[dict]:
    out = []
    for e in value if isinstance(value, list) else []:
        if isinstance(e, dict) and _words(e.get("text"), TEXT_CHARS):
            out.append({"text": _words(e["text"], TEXT_CHARS), "ref": _words(e.get("ref"), 80), "at": str(e.get("at") or "")})
    return out[-EVIDENCE:]


def _verdict(value: object) -> dict:
    if not (isinstance(value, dict) and value.get("state") in JUDGED):
        return {}
    decision = value.get("decision")
    return {"state": value["state"], "why": _words(value.get("why"), TEXT_CHARS), "decision": decision if isinstance(decision, int) and not isinstance(decision, bool) and decision > 0 else 0,
            "at": str(value.get("at") or "")}


# -- the record kept ------------------------------------------------------------------------------------------------------------------

def read(state_dir: Path) -> dict:
    """The record kept, each item checked: whatever is not of the shape reads as absent (the file is not trusted); an item with no text or no signal, a duplicate id or a state that is none is
    left out, forty at most."""
    raw = _record(state_dir).get("items")
    items: list[dict] = []
    seen: set[str] = set()
    for r in raw if isinstance(raw, list) else []:
        if not (isinstance(r, dict) and isinstance(r.get("id"), str) and _ID.fullmatch(r["id"]) and r["id"] not in seen and r.get("state") in STATES):
            continue
        text, signal = _words(r.get("text"), TEXT_CHARS), _words(r.get("signal"), TEXT_CHARS)
        if not (text and signal):
            continue
        seen.add(r["id"])
        on = r.get("on")
        items.append({"id": r["id"], "text": text, "signal": signal, "axis": r["axis"] if r.get("axis") in AXES else "", "on": on if isinstance(on, str) and _ID.fullmatch(on) else "",
                      "rests": [s for s in dict.fromkeys(r["rests"] if isinstance(r.get("rests"), list) else []) if isinstance(s, str) and _SLUG.fullmatch(s)][:GOALS],
                      "tests": [s for s in dict.fromkeys(r["tests"] if isinstance(r.get("tests"), list) else []) if isinstance(s, str) and _SLUG.fullmatch(s)][:GOALS],
                      "by": r["by"] if r.get("by") in BY else "person", "party": _words(r.get("party"), 80) if isinstance(r.get("party"), str) and _SLUG.fullmatch(r["party"]) else "",
                      "state": r["state"], "evidence": _evidence(r.get("evidence")), "verdict": _verdict(r.get("verdict")), "at": str(r.get("at") or "")})
    return {"items": items[:MAX_ALL]}


def _id_of(text: str, taken: set[str]) -> str:
    base = "-".join(_WORDS.findall(text.lower()))[:36].strip("-") or "hypothesis"
    out, n = base, 1
    while out in taken:
        n += 1
        out = f"{base}-{n}"
    return out


def _save(state_dir: Path, items: list[dict]) -> None:
    ideas._write_json(_file(state_dir), {**_record(state_dir), "items": items})


def _find(items: list[dict], id: object) -> dict:
    got = next((i for i in items if i["id"] == id), None)
    if got is None:
        raise ValueError("That hypothesis is gone")
    return got


def _count(items: list[dict], *states: str) -> int:
    return sum(1 for i in items if i["state"] in states)


def _need(value: object, what: str) -> str:
    text = _words(value, TEXT_CHARS)
    if not text:
        raise ValueError(what)
    return text


def _axis(value: object) -> str:
    if value in (None, ""):
        return ""
    if value not in AXES:
        raise ValueError("A hypothesis is about what people want, what pays, what can be built or what is easy to use: " + ", ".join(AXES))
    return value


def _on(value: object) -> str:
    if value in (None, ""):
        return ""
    if not (isinstance(value, str) and _ID.fullmatch(value.strip())):
        raise ValueError("A hypothesis is on a job or an outcome of the tree")
    return value.strip()


def _rests(value: object) -> list[str]:
    got = _slugs(value if value is not None else [])
    if got is None:
        raise ValueError(f"A hypothesis rests on {GOALS} goals at most, each a goal's name")
    return got


def _room(items: list[dict], state: str) -> None:
    """ValueError in plain words when one more item of this state does not fit (the total is made room for by `_make_room`)."""
    if state == "open" and _count(items, "open") >= MAX_OPEN:
        raise ValueError(f"{MAX_OPEN} hypotheses are open or being tested: judge or drop one first")
    if state == "proposed" and _count(items, "open") >= MAX_OPEN:
        raise ValueError(f"{MAX_OPEN} hypotheses are open or being tested already: judge or drop one before another is proposed")
    if state == "proposed" and _count(items, "proposed") >= MAX_PROPOSED:
        raise ValueError(f"{MAX_PROPOSED} hypotheses are waiting to be kept: keep or drop some first")


def _make_room(items: list[dict]) -> list[dict]:
    """The items with one place free in the forty: the oldest judged one goes first. ValueError when none is judged."""
    while len(items) >= MAX_ALL:
        judged = [i for i in items if i["state"] in JUDGED]
        if not judged:
            raise ValueError(f"{MAX_ALL} hypotheses are kept: drop one first")
        oldest = min(judged, key=lambda i: (i["verdict"].get("at") or i["at"], i["at"], i["id"]))
        items = [i for i in items if i is not oldest]
    return items


def add(state_dir: Path, text: str, signal: str, *, axis: str = "", on: str = "", rests: object = (), by: str = "person", party: str = "") -> dict:
    """One more hypothesis → the item: a person's is `open` at once, a leader's `proposed` (by `party`, its slug). ValueError in plain words for no words, an axis or a job that is none, a `by`
    that is none, and past the bounds (seven open or testing, twelve proposed, forty in all: with every one of them kept and none judged)."""
    if by not in BY:
        raise ValueError(f"A hypothesis is kept by the person or a leader, not {by!r}")
    text = _need(text, "A hypothesis says what we believe")
    signal = _need(signal, "A hypothesis says what we'll know when")
    axis, on, rests = _axis(axis), _on(on), _rests(rests)
    party = party.strip() if by == "leader" and isinstance(party, str) and _SLUG.fullmatch(party.strip()) else ""
    state = "open" if by == "person" else "proposed"
    with ideas.LOCK:
        items = read(state_dir)["items"]
        _room(items, state)
        items = _make_room(items)
        item = {"id": _id_of(text, {i["id"] for i in items}), "text": text, "signal": signal, "axis": axis, "on": on, "rests": rests, "tests": [], "by": by, "party": party, "state": state,
                "evidence": [], "verdict": {}, "at": ideas._now()}
        _save(state_dir, items + [item])
    return item


def edit(state_dir: Path, id: str, **fields: object) -> dict:
    """The words of a hypothesis changed (`text`, `signal`, `axis`, `on`, `rests`; only the ones given) → the item; its id stays. ValueError for a hypothesis gone, any other field, no words."""
    other = sorted(set(fields) - set(FIELDS))
    if other:
        raise ValueError(f"A hypothesis's {other[0]} is not changed this way")
    with ideas.LOCK:
        items = read(state_dir)["items"]
        item = _find(items, id)
        if "text" in fields:
            item["text"] = _need(fields["text"], "A hypothesis says what we believe")
        if "signal" in fields:
            item["signal"] = _need(fields["signal"], "A hypothesis says what we'll know when")
        if "axis" in fields:
            item["axis"] = _axis(fields["axis"])
        if "on" in fields:
            item["on"] = _on(fields["on"])
        if "rests" in fields:
            item["rests"] = _rests(fields["rests"])
        _save(state_dir, items)
    return item


def keep(state_dir: Path, id: str) -> dict:
    """A proposed hypothesis becomes an open one → the item (one already kept stays as it is). ValueError for one gone, and when seven are open or being tested."""
    with ideas.LOCK:
        items = read(state_dir)["items"]
        item = _find(items, id)
        if item["state"] == "proposed":
            _room(items, "open")
            item["state"] = "open"
            _save(state_dir, items)
    return item


def drop(state_dir: Path, id: str) -> None:
    """The hypothesis gone, whatever its state. ValueError when it is already gone."""
    with ideas.LOCK:
        items = read(state_dir)["items"]
        _find(items, id)
        _save(state_dir, [i for i in items if i["id"] != id])


def _slug(value: object, what: str) -> str:
    slug = value.strip() if isinstance(value, str) else ""
    if not _SLUG.fullmatch(slug):
        raise ValueError(f"{what} is a goal's name")
    return slug


def attach(state_dir: Path, id: str, goal: str = "", test: str = "") -> dict | None:
    """A `goal` rests on the hypothesis (`rests`, twelve at most; a goal may rest on several), and/or a goal `test`s it (`tests`, twelve at most). A goal tests one hypothesis at most: attached to
    another it moves. An empty `id` detaches the `goal` from every hypothesis it rests on and/or the `test` from the one it tests (→ None). ValueError for a hypothesis gone, a name that is none,
    nothing to attach, and past twelve."""
    goal, test = (v.strip() if isinstance(v, str) else "" for v in (goal, test))
    if not goal and not test:
        raise ValueError("Say which goal rests on the hypothesis or tests it")
    goal, test = (_slug(v, "What rests on or tests a hypothesis") if v else "" for v in (goal, test))
    id = id.strip() if isinstance(id, str) else ""
    with ideas.LOCK:
        items = read(state_dir)["items"]
        item = _find(items, id) if id else None
        for i in items:
            if goal and not id:
                i["rests"] = [s for s in i["rests"] if s != goal]
            if test and (not id or i is not item):
                i["tests"] = [s for s in i["tests"] if s != test]
        if item is not None:
            if goal and goal not in item["rests"]:
                if len(item["rests"]) >= GOALS:
                    raise ValueError(f"A hypothesis rests on {GOALS} goals at most")
                item["rests"].append(goal)
            if test and test not in item["tests"]:
                if len(item["tests"]) >= GOALS:
                    raise ValueError(f"A hypothesis is tested by {GOALS} goals at most")
                item["tests"].append(test)
        _save(state_dir, items)
    return item


def evidence(state_dir: Path, id: str, text: str, ref: str = "") -> dict:
    """A line of what was found, with where from (`ref`: a goal's slug, a mark's, or none) → the item; twelve at most, the newest kept. ValueError for a hypothesis gone and no words."""
    line = _need(text, "Evidence is a line on what was found")
    with ideas.LOCK:
        items = read(state_dir)["items"]
        item = _find(items, id)
        item["evidence"] = (item["evidence"] + [{"text": line, "ref": _words(ref, 80), "at": ideas._now()}])[-EVIDENCE:]
        _save(state_dir, items)
    return item


def judge(state_dir: Path, id: str, state: str, why: str = "", decision: int = 0) -> dict:
    """The person's answer to *Did it hold?* → the item. "held" and "refuted" end it (`verdict` {state, why, decision, at}: `decision` the number of the decision written, 0 with none); "unsure"
    keeps it open and adds the why, if there is one, to the evidence. ValueError for a hypothesis gone, a state that is none, one still only proposed, and one judged already."""
    if state not in VERDICTS:
        raise ValueError("A hypothesis held, was refuted or is not sure yet")
    why = _words(why, TEXT_CHARS)
    with ideas.LOCK:
        items = read(state_dir)["items"]
        item = _find(items, id)
        if item["state"] == "proposed":
            raise ValueError("Keep the hypothesis before judging it")
        if item["state"] in JUDGED:
            raise ValueError("That hypothesis is judged already")
        now = ideas._now()
        if state == "unsure":
            if why:
                item["evidence"] = (item["evidence"] + [{"text": why, "ref": "", "at": now}])[-EVIDENCE:]
        else:
            item["state"] = state
            item["verdict"] = {"state": state, "why": why, "decision": decision if isinstance(decision, int) and not isinstance(decision, bool) and decision > 0 else 0, "at": now}
        _save(state_dir, items)
    return item


# -- as shown, and what is due ----------------------------------------------------------------------------------------------------------

def state_of(item: dict, places: dict) -> str:
    """The state as shown: "testing" for an open hypothesis while any of its tests is in line or at work (`places`: {slug: "line"|"work"|"done"}, as `opportunity_tree.place_of` gives them),
    else the state kept."""
    if item.get("state") == "open" and any(places.get(t) in ("line", "work") for t in item.get("tests", [])):
        return "testing"
    return item.get("state", "")


def due(state_dir: Path, places: dict) -> list[dict]:
    """The open hypotheses that have a test, every test done, and that are not judged: what the hand asks *Did it hold?* about, in the order kept."""
    return [i for i in read(state_dir)["items"] if i["state"] == "open" and i["tests"] and all(places.get(t) == "done" for t in i["tests"])]


def _shown(items: list[dict], places: dict, states: tuple[str, ...]) -> list[tuple[dict, str]]:
    """The items whose state as shown is one of `states`, each with it, in the order kept (the file's order, which a clock with a second's grain does not tell apart), so the same record is the same text."""
    return [(i, s) for i in items if (s := state_of(i, places)) in states]


def _sentence(item: dict, state: str, cap: int = TEXT_CHARS) -> str:
    """`Hypothesis (open): <text> — we'll know when <signal>`, each of the two cut to `cap`."""
    return f"Hypothesis ({state}): {_cut(item['text'], cap)} — we'll know when {_cut(item['signal'], cap)}"


def text(state_dir: Path, places: dict) -> str:
    """For a leader's call: the open and testing hypotheses, a line each (`Hypothesis (open): … — we'll know when …`), LIMIT characters at most (the words cut before a line goes); "" with none.
    The same bytes for the same record and places."""
    shown = _shown(read(state_dir)["items"], places, ("open", "testing"))
    if not shown:
        return ""
    for cap in CAPS:
        out = "\n".join(_sentence(i, s, cap) for i, s in shown)
        if len(out) <= LIMIT:
            return out
    lines = [_sentence(i, s, CAPS[-1]) for i, s in shown]
    while len("\n".join(lines)) > LIMIT:
        lines.pop()
    return "\n".join(lines)


# -- a leader's proposal ------------------------------------------------------------------------------------------------------------------

def parse(answer: object) -> list[dict] | None:
    """A leader's proposal, strictly: `{"hypotheses": [{text, signal, axis?, on?, rests?}]}` → `[{text, signal, axis, on, rests}]`, three at most (the riskiest come first, so the first three).
    What is not of the shape is dropped: an item with no text or no signal, an axis that is none, an `on` or goals' names that are none, one the same as an earlier. None for an answer that is not
    that, a list that is not one, and when nothing is left."""
    if not isinstance(answer, dict) or not isinstance(answer.get("hypotheses"), list):
        return None
    out, seen = [], set()
    for r in answer["hypotheses"]:
        if not isinstance(r, dict):
            continue
        text, signal = _words(r.get("text"), TEXT_CHARS), _words(r.get("signal"), TEXT_CHARS)
        try:
            axis, on, rests = _axis(r.get("axis")), _on(r.get("on")), _rests(r.get("rests"))
        except ValueError:
            continue
        if not (text and signal) or text.lower() in seen:
            continue
        seen.add(text.lower())
        out.append({"text": text, "signal": signal, "axis": axis, "on": on, "rests": rests})
    return out[:MAX_PROPOSE] or None
