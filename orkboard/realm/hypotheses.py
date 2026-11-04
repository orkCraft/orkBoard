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
    hypotheses.parse(answer)                           # a leader's proposal, strictly → [{text, signal, axis, on, rests, refuted, if_holds}] (three at most) or None
    hypotheses.draft(item, state, way="")              # the draft of the decision a verdict writes: `if_holds` for held, the way's `change` for refuted (spec 133 A.1)

Spec 133 A: `signal` is the *Holds when* (its key stays); `refuted` is one to three ways it is refuted, `[{name, when, change}]` (`name` what the way would teach, `when` required, `change` what changes if it is
refuted this way); `if_holds` what changes if it holds. An item kept before has neither (`[]`, ""); a verdict keeps the `way` the person picked.

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
FIELDS = ("text", "signal", "axis", "on", "rests", "refuted", "if_holds")
NAME_CHARS, DRAFT_CHARS, MAX_WAYS = 40, 600, 3                # a refuted way's name, a draft of the decision (what changes if it holds / if refuted this way), the ways a hypothesis is refuted in (spec 133 A.1)
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
            "way": _words(value.get("way"), NAME_CHARS), "at": str(value.get("at") or "")}


def _way(raw: object) -> dict | None:
    """One way it is refuted, `{name, when, change}`, or None when it is none (no `when`)."""
    if not isinstance(raw, dict):
        return None
    when = _words(raw.get("when"), TEXT_CHARS)
    return {"name": _words(raw.get("name"), NAME_CHARS), "when": when, "change": _words(raw.get("change"), DRAFT_CHARS)} if when else None


def _clean_ways(value: object) -> list[dict]:
    """The ways of a record read, leniently: what is not a way is dropped, a name twice keeps the first, three at most."""
    out: list[dict] = []
    for raw in value if isinstance(value, list) else []:
        w = _way(raw)
        if w and (not w["name"] or w["name"].lower() not in {x["name"].lower() for x in out}):
            out.append(w)
    return out[:MAX_WAYS]


def _ways(value: object) -> list[dict]:
    """The ways a person or code gives, strictly: ValueError in plain words for more than three, one with no `when` and a name twice."""
    if value in (None, ""):
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError("A hypothesis is refuted in ways: a list of when and what it would teach")
    if len(value) > MAX_WAYS:
        raise ValueError(f"A hypothesis is refuted in {MAX_WAYS} ways at most")
    out: list[dict] = []
    for raw in value:
        w = _way(raw)
        if w is None:
            raise ValueError("A way it is refuted says when")
        if w["name"] and w["name"].lower() in {x["name"].lower() for x in out}:
            raise ValueError("Two ways it is refuted have the same name")
        out.append(w)
    return out


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
                      "state": r["state"], "evidence": _evidence(r.get("evidence")), "verdict": _verdict(r.get("verdict")), "at": str(r.get("at") or ""),
                      "refuted": _clean_ways(r.get("refuted")), "if_holds": _words(r.get("if_holds"), DRAFT_CHARS)})
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


def add(state_dir: Path, text: str, signal: str, *, axis: str = "", on: str = "", rests: object = (), by: str = "person", party: str = "", refuted: object = (), if_holds: str = "") -> dict:
    """One more hypothesis → the item: a person's is `open` at once, a leader's `proposed` (by `party`, its slug). ValueError in plain words for no words, an axis or a job that is none, a `by`
    that is none, and past the bounds (seven open or testing, twelve proposed, forty in all: with every one of them kept and none judged)."""
    if by not in BY:
        raise ValueError(f"A hypothesis is kept by the person or a leader, not {by!r}")
    text = _need(text, "A hypothesis says what we believe")
    signal = _need(signal, "A hypothesis says what we'll know when")
    axis, on, rests, ways = _axis(axis), _on(on), _rests(rests), _ways(refuted)
    party = party.strip() if by == "leader" and isinstance(party, str) and _SLUG.fullmatch(party.strip()) else ""
    state = "open" if by == "person" else "proposed"
    with ideas.LOCK:
        items = read(state_dir)["items"]
        _room(items, state)
        items = _make_room(items)
        item = {"id": _id_of(text, {i["id"] for i in items}), "text": text, "signal": signal, "axis": axis, "on": on, "rests": rests, "tests": [], "by": by, "party": party, "state": state,
                "evidence": [], "verdict": {}, "at": ideas._now(), "refuted": ways, "if_holds": _words(if_holds, DRAFT_CHARS)}
        _save(state_dir, items + [item])
    return item


def edit(state_dir: Path, id: str, **fields: object) -> dict:
    """The words of a hypothesis changed (`text`, `signal`, `axis`, `on`, `rests`, `refuted`, `if_holds`; only the ones given) → the item; its id stays. ValueError for a hypothesis gone, any other field, no words."""
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
        if "refuted" in fields:
            item["refuted"] = _ways(fields["refuted"])
        if "if_holds" in fields:
            item["if_holds"] = _words(fields["if_holds"], DRAFT_CHARS)
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


def judge(state_dir: Path, id: str, state: str, why: str = "", decision: int = 0, way: str = "") -> dict:
    """The person's answer to *Did it hold?* → the item. "held" and "refuted" end it (`verdict` {state, why, decision, at}: `decision` the number of the decision written, 0 with none); "unsure"
    keeps it open and adds the why, if there is one, to the evidence. `way` (spec 133 A.1): the name of the way it is refuted that was met, for "refuted" only: an item with ways takes one of
    theirs ("" for an item with one way), an item with none takes "". ValueError for a hypothesis gone, a state that is none, one still only proposed, one judged already, and a way that does not fit."""
    if state not in VERDICTS:
        raise ValueError("A hypothesis held, was refuted or is not sure yet")
    why, way = _words(why, TEXT_CHARS), _words(way, NAME_CHARS)
    with ideas.LOCK:
        items = read(state_dir)["items"]
        item = _find(items, id)
        if item["state"] == "proposed":
            raise ValueError("Keep the hypothesis before judging it")
        if item["state"] in JUDGED:
            raise ValueError("That hypothesis is judged already")
        way = _pick_way(item, state, way)
        now = ideas._now()
        if state == "unsure":
            if why:
                item["evidence"] = (item["evidence"] + [{"text": why, "ref": "", "at": now}])[-EVIDENCE:]
        else:
            item["state"] = state
            item["verdict"] = {"state": state, "why": why, "decision": decision if isinstance(decision, int) and not isinstance(decision, bool) and decision > 0 else 0, "way": way, "at": now}
        _save(state_dir, items)
    return item


def _pick_way(item: dict, state: str, way: str) -> str:
    """The way a verdict names, checked against the item's: "" for held and unsure with none given; ValueError in plain words otherwise (spec 133 A.1)."""
    if state != "refuted":
        if way:
            raise ValueError("Only a refuted hypothesis has a way it is refuted")
        return ""
    ways = item["refuted"]
    if not ways:
        return ""
    if not way and len(ways) == 1:
        return ways[0]["name"]
    if not any(w["name"].lower() == way.lower() for w in ways):
        raise ValueError("Pick the way it is refuted: " + ", ".join(w["name"] or w["when"] for w in ways))
    return next(w["name"] for w in ways if w["name"].lower() == way.lower())


def draft(item: dict, state: str, way: str = "") -> str:
    """The draft of the decision a verdict writes (spec 133 A.1): the item's `if_holds` for "held"; for "refuted" the named way's `change` (the only way's when `way` is "" and the item has one); "" with none."""
    if state == "held":
        return item.get("if_holds", "")
    if state != "refuted":
        return ""
    ways = item.get("refuted", [])
    got = next((w for w in ways if way and w["name"].lower() == way.lower()), ways[0] if len(ways) == 1 and not way else None)
    return got["change"] if got else ""


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
    """`Hypothesis (open): <text> — we'll know when <signal>` (then ` — refuted when <name>: <when> / …` when it has ways), each cut to `cap`."""
    line = f"Hypothesis ({state}): {_cut(item['text'], cap)} — we'll know when {_cut(item['signal'], cap)}"
    ways = item.get("refuted") or []
    if ways:                                                                     # spec 133 A.2: an item with no way has the line it had
        line += " — refuted when " + " / ".join((f"{w['name']}: " if w["name"] else "") + _cut(w["when"], cap) for w in ways)
    return line


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
    """A leader's proposal, strictly: `{"hypotheses": [{text, signal, axis?, on?, rests?, refuted?, if_holds?}]}` → `[{text, signal, axis, on, rests, refuted, if_holds}]`, three at most (the riskiest come first, so the first three).
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
        ways = _clean_ways([{"name": w.get("name"), "when": w.get("when")} for w in r["refuted"] if isinstance(w, dict)] if isinstance(r.get("refuted"), list) else [])
        if not (text and signal) or text.lower() in seen:
            continue
        seen.add(text.lower())
        out.append({"text": text, "signal": signal, "axis": axis, "on": on, "rests": rests, "refuted": ways, "if_holds": _words(r.get("if_holds"), DRAFT_CHARS)})
    return out[:MAX_PROPOSE] or None
