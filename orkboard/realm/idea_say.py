"""What a leader said beside its verdict, and what the person did with it (docs/specs/168 §C1, §C2; decisions §283.23–§283.25). Pure code, no model, no face: the keeper's calls
(`core/idea_rewrite.py`, `core/idea_verdict.py`) and the Board's rows (`realm/board_map.py`) both read it from here.

A leader's say is in its stance (`ideas/<slug>/talk.json`): `needs` (`{id, kind, line, rests_on, ways: [{name, line}]}`) and `better` (`{id, line, weight}`), cleaned by
`idea_talk_parse`. What the person did with them is `ideas/<slug>/say.json`:

    {"answers": {<id>: {state: "taken"|"left", way: <index>|null, at, written: bool}},
     "rewrites": [{id, at, ids, parties, before, after, undone}],        # the Gist before and after, whole: undo puts `before` back exactly
     "fork": {id, at, ids, card, answer} | null,                        # the taken ones that contradict, as one card of choices
     "since": {"taken": [id], "left": [id]},                            # taken and turned down since the leaders last judged: who is judged again (the part a rewrite touched, a proposal turned down) and what they are told
     "judged": <n>}                                                     # the leaders have judged again this many times (`MAX_JUDGED` at most)

    idea_say.node(root, state_dir, slug)       # the Board's row of an idea: {leaders, rewrite, fork, judged, judge_left, answered, waiting, to_judge} or None before any leader spoke
    idea_say.leaders(state_dir, slug)          # per leader: its verdict, `needs` (the old questions among them, kind question) and `better`, each with its state: open · taken · left
    idea_say.take(state_dir, slug, ident, way=None) / leave(state_dir, slug, ident)     # one need's way or one better taken, or turned down; ValueError in plain words
    idea_say.waiting(state_dir, slug)          # what is taken and not written into the goal yet: the items a rewrite is given (a fork answered stands in place of the ones it settled)
    idea_say.written(state_dir, slug, ids, before, after) / forked(...) / fork_answer(...) / undo(...)   # what a rewrite did
    idea_say.to_judge(state_dir, slug)         # the parties to judge again, in the stances' order; idea_say.judged(state_dir, slug) counts one more round and clears who was waiting
    idea_say.told(state_dir, slug, party)      # what the person took and turned down, as the leader judged again is told it
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from orkboard.realm import idea_questions, ideas, way_kinds

FILE = "say.json"
MAX_JUDGED = 2                    # the leaders judge again twice at most, then a hearing (decisions §283.25)
TOLD = 8                          # the lines of what was taken and turned down a leader judged again is told, each


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def record(state_dir: Path, slug: str) -> dict:
    """The record of a goal's say, whole (a missing or broken file reads as nothing done)."""
    got = ideas._json(ideas.state_folder(state_dir, slug) / FILE)
    got = got if isinstance(got, dict) else {}
    since = got.get("since") if isinstance(got.get("since"), dict) else {}
    return {"answers": dict(got["answers"]) if isinstance(got.get("answers"), dict) else {},
            "rewrites": [r for r in got.get("rewrites") or [] if isinstance(r, dict)] if isinstance(got.get("rewrites"), list) else [],
            "fork": got["fork"] if isinstance(got.get("fork"), dict) else None,
            "since": {"taken": list(since.get("taken") or []), "left": list(since.get("left") or [])},
            "judged": got["judged"] if isinstance(got.get("judged"), int) and not isinstance(got.get("judged"), bool) else 0}


def save(state_dir: Path, slug: str, rec: dict) -> None:
    ideas._write_json(ideas.state_folder(state_dir, slug) / FILE, rec)


def _stances(state_dir: Path, slug: str) -> list[dict]:
    return [s for s in idea_questions.record(state_dir, slug).get("stances") or [] if isinstance(s, dict) and s.get("party")]


def items(state_dir: Path, slug: str) -> dict[str, dict]:
    """Every need and better the leaders said, by id: the item with `type` ("need" | "better"), its `party` and `leader`."""
    out: dict[str, dict] = {}
    for s in _stances(state_dir, slug):
        for kind, key in (("need", "needs"), ("better", "better")):
            for it in s.get(key) or []:
                if isinstance(it, dict) and it.get("id"):
                    out[str(it["id"])] = {**it, "type": kind, "party": s["party"], "leader": s.get("leader") or ""}
    return out


# -- the rows --------------------------------------------------------------------------------------------------------------------------

def _legacy(talk: dict, party: str) -> list[dict]:
    """The questions of a leader as needs of the kind `question` (decisions §283.23): the cards waiting (`open`), answered (`taken`, the answer its one way) or closed by the leader's pick (`left`).
    `legacy` is true: they are answered as before (`ideas.talk_answer`), never by the commands that take a say."""
    out = []
    for c in talk.get("waiting") or []:
        if isinstance(c, dict) and c.get("by") == party:
            lines = c.get("lines") if isinstance(c.get("lines"), list) and len(c.get("lines")) == len(c.get("choices") or []) else [""] * len(c.get("choices") or [])
            kinds = way_kinds.of_card(c)
            out.append({"id": c["id"], "kind": "question", "line": c.get("why") or c.get("q") or "", "title": c.get("q") or "", "rests_on": "", "legacy": True, "state": "open", "way": None,
                        "ways": [{"name": str(ch), "line": str(ln), "way_kind": k} for ch, ln, k in zip(c.get("choices") or [], lines, kinds)], "pick": c.get("pick"), "blocks": False})
    for key, state in (("answers", "taken"), ("defaults", "left")):
        for a in talk.get(key) or []:
            if isinstance(a, dict) and a.get("by") == party and a.get("id"):
                out.append({"id": a["id"], "kind": "question", "line": a.get("why") or a.get("q") or "", "title": a.get("q") or "", "rests_on": "", "legacy": True, "state": state, "way": 0,
                            "ways": [{"name": str(a.get("answer") or ""), "line": "", "way_kind": way_kinds.OTHER}], "pick": None, "blocks": False})
    return out


def _row(it: dict, say: dict) -> dict:
    a = say["answers"].get(it["id"]) or {}
    ways = [{**w, "way_kind": way_kinds.clean(w.get("way_kind"))} for w in it["ways"] if isinstance(w, dict)] if isinstance(it.get("ways"), list) else None     # an old need's ways have no kind: `other`
    return {**it, **({"ways": ways} if ways is not None else {}), "legacy": False, "state": a.get("state") or "open", "way": a.get("way"), "written": a.get("written") is True}


def leaders(state_dir: Path, slug: str) -> list[dict]:
    """Per leader that has spoken (the route's order; Product weighing a goal it is not routed on, `weigher`, speaks too): `{party, leader, craft, weigher, verdict, why, instead, after, priority,
    risk, needs: [need], better: [better]}`. A need is `{id, kind, line, rests_on, ways, legacy, state, way}`, a better `{id, line, weight, state, written}`, `state` "open" · "taken" · "left"."""
    talk, say = idea_questions.record(state_dir, slug), record(state_dir, slug)
    out = []
    for s in _stances(state_dir, slug):
        out.append({"party": s["party"], "leader": s.get("leader") or "", "craft": s.get("craft") or "", "weigher": s.get("weigher") is True, "verdict": s.get("verdict") or "go",
                    "why": s.get("why") or "", "instead": s.get("instead") or "", "after": s.get("after") or "", "priority": s.get("priority") or "", "risk": s.get("risk") or "",
                    "needs": [_row(n, say) for n in s.get("needs") or [] if isinstance(n, dict) and n.get("id")] + _legacy(talk, s["party"]),
                    "better": [_row(b, say) for b in s.get("better") or [] if isinstance(b, dict) and b.get("id")]})
    return out


def waiting(state_dir: Path, slug: str) -> list[dict]:
    """What a rewrite is given: the items taken and not written yet, in the order they were said, each `{id, type, party, leader, line, weight?|kind?, way?: {name, line}}`. The items a fork
    answered settled are one item in their place: `{id: <fork id>, type: "fork", line: <the choice>, ids}`. None while a fork is open: the person's answer comes first (`[]`)."""
    say, every = record(state_dir, slug), items(state_dir, slug)
    fork = say["fork"]
    if fork and fork.get("answer") is None:
        return []
    settled = set(fork.get("ids") or []) if fork else set()
    out: list[dict] = []
    for ident, it in every.items():
        a = say["answers"].get(ident) or {}
        if a.get("state") != "taken" or a.get("written") or ident in settled:
            continue
        way = it["ways"][a["way"]] if it["type"] == "need" and isinstance(a.get("way"), int) and 0 <= a["way"] < len(it.get("ways") or []) else None
        out.append({**{k: it.get(k) for k in ("id", "type", "party", "leader", "line", "weight", "kind", "rests_on")}, **({"way": way} if way else {})})
    if fork and settled and any((say["answers"].get(i) or {}).get("state") == "taken" and not (say["answers"].get(i) or {}).get("written") for i in settled):
        choice = fork["card"]["choices"][fork["answer"]]
        lines = fork["card"].get("lines") or []
        out.append({"id": fork["id"], "type": "fork", "party": "", "leader": "", "line": f"{choice}" + (f" — {lines[fork['answer']]}" if fork["answer"] < len(lines) and lines[fork["answer"]] else ""),
                    "ids": list(settled)})
    return out


def to_judge(state_dir: Path, slug: str) -> list[str]:
    """The parties to judge again (decisions §283.25), in the stances' order: those that doubted or said no, those whose proposal was turned down and those whose part a rewrite touched."""
    say, every = record(state_dir, slug), items(state_dir, slug)
    turned = {every[i]["party"] for i in say["since"]["left"] if i in every}
    touched: set[str] = set()
    for i in say["since"]["taken"]:
        if i not in every:
            continue
        touched.add(every[i]["party"])
        if on := every[i].get("rests_on"):                       # another leader's need that rests on the same part is touched too
            touched |= {o["party"] for o in every.values() if o.get("rests_on") == on}
    return [s["party"] for s in _stances(state_dir, slug) if not s.get("weigher") and (s.get("verdict") in ("doubt", "no") or s["party"] in turned | touched)]


def answered(state_dir: Path, slug: str) -> bool:
    """Every need and better of the leaders is taken or turned down, and there was at least one: the round's cards are answered (the old questions are not counted, they have their own flow)."""
    say, every = record(state_dir, slug), items(state_dir, slug)
    return bool(every) and all((say["answers"].get(i) or {}).get("state") in ("taken", "left") for i in every)




def describe(it: dict, you: str = "") -> str:
    """One item as a line of text for a call: a better `"<line>" (lighter|same|heavier)`, a need `<kind>: <line> — the way taken: <name>: <line>`; `you`: the party that is told it, whose own is marked."""
    if it.get("type") == "fork":
        return f"The person settled a disagreement between what was taken: {it['line']}"
    mine = " (yours)" if you and it.get("party") == you else ""
    if it.get("type") == "better":
        return f"\"{it['line']}\" ({it.get('weight') or 'same'}){mine}"
    way = it.get("way") or {}
    return f"{it.get('kind') or 'need'}: {it['line']}" + (f" — the way taken: {way['name']}" + (f": {way['line']}" if way.get("line") else "") if way else "") + mine


def told(state_dir: Path, slug: str, party: str) -> str:
    """What the person took since the leaders last judged, and what it turned down, as the leader judged again is told it ("" with neither)."""
    say, every = record(state_dir, slug), items(state_dir, slug)
    out: list[str] = []
    for head, key in (("Taken, and now written into the goal's words", "taken"), ("Turned down", "left")):
        got = []
        for i in say["since"][key]:
            it = every.get(i)
            if it is None:
                continue
            w = (say["answers"].get(i) or {}).get("way")
            got.append({**it, "way": it["ways"][w]} if key == "taken" and it["type"] == "need" and isinstance(w, int) and 0 <= w < len(it.get("ways") or []) else it)
        if got:
            out += [f"{head}:", *(f"- {describe(it, party)}" for it in got[:TOLD])]
    return "\n".join(out)


# -- what the person does ------------------------------------------------------------------------------------------------------------

def _answer(state_dir: Path, slug: str, ident: str, state: str, way: int | None) -> dict:
    with ideas.LOCK:
        it = items(state_dir, slug).get(ident)
        if it is None:
            raise ValueError("A leader did not say that")
        rec = record(state_dir, slug)
        if (rec["answers"].get(ident) or {}).get("state") in ("taken", "left"):
            raise ValueError("That is answered already")
        if state == "taken" and it["type"] == "need" and (not isinstance(way, int) or isinstance(way, bool) or not 0 <= way < len(it.get("ways") or [])):
            raise ValueError("Take one of its ways")
        way = way if state == "taken" and it["type"] == "need" else None
        rec["answers"][ident] = {"state": state, "way": way, "at": _now(), "written": False}
        rec["since"]["taken" if state == "taken" else "left"].append(ident)
        save(state_dir, slug, rec)
    return {**it, "state": state, "way": way}


def take(state_dir: Path, slug: str, ident: str, way: int | None = None) -> dict:
    """A better taken, or a need's way (its index): the item with its `state` "taken". ValueError in plain words for what no leader said, what is answered already or a need with no way."""
    return _answer(state_dir, slug, ident, "taken", way)


def leave(state_dir: Path, slug: str, ident: str) -> dict:
    """A better or a need turned down: the item with its `state` "left". Its leader is judged again."""
    return _answer(state_dir, slug, ident, "left", None)


def written(state_dir: Path, slug: str, ids: list[str], before: str, after: str, parties: list[str]) -> dict:
    """A rewrite done: the items `ids` (a fork's id stands for the items it settled) are written, the Gist before and after kept whole for the undo; the row."""
    with ideas.LOCK:
        rec = record(state_dir, slug)
        real: list[str] = []
        for i in ids:
            if rec["fork"] and i == rec["fork"].get("id"):
                real += list(rec["fork"].get("ids") or [])
                rec["fork"] = None
            else:
                real.append(i)
        for i in real:
            if i in rec["answers"]:
                rec["answers"][i]["written"] = True
        row = {"id": f"w-{len(rec['rewrites']) + 1}", "at": _now(), "ids": list(dict.fromkeys(real)), "parties": parties, "before": before, "after": after, "undone": False}
        rec["rewrites"].append(row)
        save(state_dir, slug, rec)
    return row


def forked(state_dir: Path, slug: str, ids: list[str], card: dict) -> dict:
    """The taken ones that contradict come back as one card of choices (`ids`: those of the waiting ones it is between, every one of them when the call named none)."""
    with ideas.LOCK:
        rec = record(state_dir, slug)
        known = [w["id"] for w in waiting(state_dir, slug)]
        rec["fork"] = {"id": f"fork-{len(rec['rewrites']) + 1}", "at": _now(), "ids": [i for i in ids if i in known] or known, "card": card, "answer": None}
        save(state_dir, slug, rec)
    return rec["fork"]


def fork_answer(state_dir: Path, slug: str, pick: int) -> dict:
    """The person's choice on the open fork (an index of its choices); the fork. ValueError where none is open or the pick is none of its choices."""
    with ideas.LOCK:
        rec = record(state_dir, slug)
        fork = rec["fork"]
        if not fork or fork.get("answer") is not None:
            raise ValueError("No fork waits for an answer")
        if not isinstance(pick, int) or isinstance(pick, bool) or not 0 <= pick < len(fork["card"]["choices"]):
            raise ValueError("Take one of the choices")
        fork["answer"] = pick
        save(state_dir, slug, rec)
    return fork


def undo(state_dir: Path, slug: str, gist: str) -> dict:
    """The last rewrite not undone taken back (`gist`: the goal's Gist now): its row, with the items it wrote open again. ValueError where there is none or the goal's words changed since."""
    with ideas.LOCK:
        rec = record(state_dir, slug)
        row = next((r for r in reversed(rec["rewrites"]) if not r.get("undone")), None)
        if row is None:
            raise ValueError("Nothing was rewritten")
        if (gist or "").strip() != str(row.get("after") or "").strip():
            raise ValueError("The goal's words changed since: nothing is put back")
        row["undone"] = True
        for i in row["ids"]:
            rec["answers"].pop(i, None)
            for k in ("taken", "left"):
                rec["since"][k] = [x for x in rec["since"][k] if x != i]
        save(state_dir, slug, rec)
    return row


def judged(state_dir: Path, slug: str) -> int:
    """One more round of judging again is done: the count; who was waiting to be judged (what was taken, what was turned down) is cleared."""
    with ideas.LOCK:
        rec = record(state_dir, slug)
        rec["judged"] += 1
        rec["since"] = {"taken": [], "left": []}
        save(state_dir, slug, rec)
    return rec["judged"]


def node(root: Path, state_dir: Path, slug: str) -> dict | None:
    """The Board's row of an idea's say, or None before any leader spoke: `{leaders, rewrite, fork, judged, judge_left, answered, waiting, to_judge}`. `rewrite` is the last one not undone,
    `{id, at, ids, parties, before, after, undoable}` (`undoable`: the goal's words are still as it left them); `fork` the open card `{id, at, ids, card}`, else None; `waiting` the ids taken and not
    written; `to_judge` the parties judged again at *Judge again now*."""
    rows = leaders(state_dir, slug)
    if not rows:
        return None
    say = record(state_dir, slug)
    last = next((r for r in reversed(say["rewrites"]) if not r.get("undone")), None)
    page = ideas.idea_page(root, slug) if last else None
    fork = say["fork"] if say["fork"] and say["fork"].get("answer") is None else None
    return {"leaders": rows,
            "rewrite": {**{k: last.get(k) for k in ("id", "at", "ids", "parties", "before", "after")},
                        "undoable": page is not None and page.section("Gist").strip() == str(last.get("after") or "").strip()} if last else None,
            "fork": {k: fork.get(k) for k in ("id", "at", "ids", "card")} if fork else None,
            "judged": say["judged"], "judge_left": max(MAX_JUDGED - say["judged"], 0), "answered": answered(state_dir, slug), "waiting": [w["id"] for w in waiting(state_dir, slug)],
            "to_judge": to_judge(state_dir, slug)}
