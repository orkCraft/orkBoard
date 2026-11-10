"""Findings and a goal's quality record (docs/specs/132-four-levels-the-way-down-and-findings.md D.1, D.3; decisions §234.3–§234.4, §237.1–§237.2, §237.8). No model, no face: a read and a write of
files. The gathering where each thing is found is `realm/findings_gather.py`; the leaders' calls are `core/idea_findings.py`; the commands are `gui/ideas_findings.py`.

    findings.add(state_dir, finding)                 # one finding a source's thing (`source` + `on` + `idea`): kept once; the stored finding (the old one when it was there)
    findings.of_goal(state_dir, idea)                # the goal's findings, the oldest first (`idea` "": the findings of no goal)
    findings.open_of_goal(state_dir, idea)           # …those not answered
    findings.get(state_dir, fid)                     # the finding of that id, wherever it lies; None when there is none
    findings.told(state_dir, idea, fid, content)     # the finder's content in (`what`, `shows`, `promised`, `cause`): status `told`
    findings.sorted_(state_dir, idea, fid, level, change)   # the Orkmaster's level in: status `sorted`
    findings.answer(state_dir, fid, answer, fix=None)       # `fix` · `later` · `moved`: `fix` and `later` end the finding's wait in the hand (status `answered`), `fix` says what was made of it
    findings.move(state_dir, fid, level)             # the person moved its level (`answer` "moved", the finding still waits)
    findings.record(state_dir, idea) / findings.save_record(state_dir, idea, **changes)   # a goal's quality record
    findings.ripe(state_dir, idea, now=None)         # the goal's findings are in: its verdict read, its checks done and the lenses' looks of the day after (or QUIET_H hours after the verdict)
    findings.pending(state_dir)                      # the goals ("" for no goal) that hold a finding not told yet
    findings.waiting(state_dir)                      # …or told and not sorted yet
    findings.rows(state_dir, root)                   # the hand's rows: one `quality` card a goal, a `finding` row for each of no goal
    findings.clean_told(raw, ids) / findings.clean_levels(raw, ids)   # the two calls' answers, strictly
    findings.pulls_of(state_dir, root, finding)      # what its fix pulls after it, and the price (realm/way_down.py)

**The record** is `<state_dir>/ideas/<slug>/quality.json` `{verdict: [goal_result rows], checks: [...], findings: [finding], hypothesis: {...} | null, at, status}`; a finding of no goal is in
`<state_dir>/findings.json` `{findings: [...]}`. `realm/way_down.py` `open_levels` reads `findings[].status != "answered"`.

A finding is `{id, at, source, idea, party, on, found, what, shows, promised, cause, level, change, status, answer, fix}`: `source` verdict · check · lens · concern · hypothesis · measure · accept; `found` code's words
(`what` is `found` until its leader tells it); `level` work · spec · decision and `change` the Orkmaster's; `status` found → told → sorted → answered; `answer` fix · later · moved; `fix` what was made of it
(`{idea}` a goal, `{cascade}`, `{change}`).

**The rows** (D.3): a goal with a finding sorted and not answered has one `kind: "quality"` row, its findings in the order of their level (Decision first); a finding of no goal is a `kind: "finding"` row of its
own. Never urgent (`blocks` False); the hand's order puts them after a failure and a question.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from orkboard.realm import ideas

QUALITY = "quality.json"
FILE = "findings.json"
SOURCES = ("verdict", "check", "lens", "concern", "hypothesis", "measure", "accept")      # `accept`: what a leader's acceptance of a step left (spec 152 B.3)
LEVELS = ("decision", "spec", "work")                       # a finding's level, in the order of its card: the heaviest first
STATUS = ("found", "told", "sorted", "answered")
ANSWERS = ("fix", "later", "moved")
LINE_CHARS = 300                                            # a finding's `what`, `shows`, `promised`, `cause`, one line each
CHANGE_CHARS = 200
FOUND_CHARS = 400
QUIET_H = 24                                                # hours after the verdict is read when the findings are told whether or not the checks and looks are in
MAX_FINDINGS = 60                                           # a record keeps this many (the oldest answered go first)
_FIELDS = ("id", "at", "source", "idea", "party", "on", "found", "what", "shows", "promised", "cause", "level", "change", "status", "answer", "fix")


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _line(value: object, n: int = LINE_CHARS) -> str:
    return " ".join(value.split())[:n].rstrip() if isinstance(value, str) else ""


def _id(source: str, on: str, idea: str) -> str:
    return "f-" + hashlib.sha1(f"{source}\n{on}\n{idea}".encode()).hexdigest()[:10]


# -- the files ---------------------------------------------------------------------------------------------------------------------------------

def _path(state_dir: Path, idea: str) -> Path:
    return Path(state_dir) / FILE if not idea else ideas.state_folder(Path(state_dir), idea) / QUALITY


def _read(path: Path) -> dict:
    got = ideas._json(path)
    return got if isinstance(got, dict) else {}


def _clean(raw: object) -> dict | None:
    """A finding as the file keeps it: every field, the strings as lines; None for what is no finding."""
    if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not raw["id"]:
        return None
    f = {k: _line(raw.get(k), FOUND_CHARS if k == "found" else CHANGE_CHARS if k == "change" else LINE_CHARS) for k in ("source", "idea", "party", "on", "found", "what", "shows", "promised", "cause", "change", "at")}
    f["id"] = raw["id"]
    f["level"] = raw["level"] if raw.get("level") in LEVELS else ""
    f["status"] = raw["status"] if raw.get("status") in STATUS else "found"
    f["answer"] = raw["answer"] if raw.get("answer") in ANSWERS else ""
    fix = raw.get("fix")
    f["fix"] = {k: str(v)[:100] for k, v in fix.items() if isinstance(k, str) and isinstance(v, (str, int))} if isinstance(fix, dict) else None
    return {k: f[k] for k in _FIELDS}


def record(state_dir: Path, idea: str) -> dict:
    """A goal's quality record (`idea` "": the findings of no goal), every key there."""
    try:
        got = _read(_path(state_dir, idea))
    except ValueError:
        got = {}
    rows = [f for f in (_clean(x) for x in got.get("findings") or []) if f is not None]
    hyp = got.get("hypothesis")
    return {"verdict": [x for x in got.get("verdict") or [] if isinstance(x, dict)], "checks": [x for x in got.get("checks") or [] if isinstance(x, dict)], "findings": rows,
            "hypothesis": hyp if isinstance(hyp, dict) else None, "at": str(got.get("at") or ""), "status": str(got.get("status") or "")}


def _write(state_dir: Path, idea: str, rec: dict) -> None:
    if not idea:
        rec = {"findings": rec["findings"]}
    ideas._write_json(_path(state_dir, idea), rec)


def save_record(state_dir: Path, idea: str, **changes: Any) -> dict:
    """The record with `changes` (verdict, checks, hypothesis, at, status, findings) kept, under the Board's lock."""
    with ideas.LOCK:
        rec = {**record(state_dir, idea), **{k: v for k, v in changes.items() if k in ("verdict", "checks", "findings", "hypothesis", "at", "status")}}
        rec["findings"] = rec["findings"][-MAX_FINDINGS:]
        _write(state_dir, idea, rec)
    return rec


def _goals(state_dir: Path) -> list[str]:
    """The goals that have a quality record, and "" for the findings of no goal when there are some."""
    out = []
    base = Path(state_dir) / "ideas"
    try:
        out = sorted(p.parent.name for p in base.glob(f"*/{QUALITY}"))
    except OSError:
        pass
    return out + ([""] if (Path(state_dir) / FILE).exists() else [])


# -- the findings --------------------------------------------------------------------------------------------------------------------------------

def add(state_dir: Path, finding: dict) -> dict | None:
    """One finding of one thing, kept once: `source` + `on` + `idea` make its id, and a second `add` of it changes nothing (an answered finding is not raised again). `finding` needs `source` (one of
    SOURCES), `on` (the part, the check, the concern's id …) and `found` (code's words); `idea` is the goal's slug ("" for no goal), `party` its finder. Returns the stored finding, None when `finding` is no finding."""
    if not isinstance(finding, dict) or finding.get("source") not in SOURCES:
        return None
    idea, on, found = _line(finding.get("idea")), _line(finding.get("on")), _line(finding.get("found"), FOUND_CHARS)
    if not found:
        return None
    fid = _id(finding["source"], on, idea)
    with ideas.LOCK:
        rec = record(state_dir, idea)
        if mine := next((f for f in rec["findings"] if f["id"] == fid), None):
            return mine
        new = _clean({"id": fid, "at": _now(), "source": finding["source"], "idea": idea, "party": _line(finding.get("party")), "on": on, "found": found, "what": found,
                      "status": "found"})
        rec["findings"].append(new)
        save_record(state_dir, idea, findings=rec["findings"])
    return new


def of_goal(state_dir: Path, idea: str) -> list[dict]:
    return record(state_dir, idea)["findings"]


def open_of_goal(state_dir: Path, idea: str) -> list[dict]:
    return [f for f in of_goal(state_dir, idea) if f["status"] != "answered"]


def get(state_dir: Path, fid: str) -> dict | None:
    for idea in _goals(state_dir):
        for f in of_goal(state_dir, idea):
            if f["id"] == fid:
                return f
    return None


def _change(state_dir: Path, fid: str, fn, idea: str | None = None) -> dict | None:
    """The finding of that id changed by `fn(finding)` and kept; None when there is none. `idea`: the goal it lies in when it is known (else every record is looked in)."""
    with ideas.LOCK:
        for idea in _goals(state_dir) if idea is None else [idea]:
            rec = record(state_dir, idea)
            for f in rec["findings"]:
                if f["id"] == fid:
                    fn(f)
                    save_record(state_dir, idea, findings=rec["findings"])
                    return f
    return None


def told(state_dir: Path, idea: str, fid: str, content: dict) -> dict | None:
    """The finder's content in: `what`, `shows`, `promised`, `cause` (each one line; one it left out keeps what there was); status `told` (a finding already sorted or answered keeps its status)."""
    def apply(f: dict) -> None:
        for k in ("what", "shows", "promised", "cause"):
            if line := _line(content.get(k)):
                f[k] = line
        if f["status"] == "found":
            f["status"] = "told"
    return _change(state_dir, fid, apply, idea)


def sorted_(state_dir: Path, idea: str, fid: str, level: str, change: str = "") -> dict | None:
    """The Orkmaster's level in (`work` when it is none of the three): status `sorted`; an answered finding keeps its answer."""
    def apply(f: dict) -> None:
        f["level"] = level if level in LEVELS else "work"
        f["change"] = _line(change, CHANGE_CHARS)
        if f["status"] != "answered":
            f["status"] = "sorted"
    return _change(state_dir, fid, apply, idea)


def answer(state_dir: Path, fid: str, answer_: str, fix: dict | None = None) -> dict | None:
    """The person's answer: `fix` (what was made of it in `fix`) or `later`: the finding is answered, it leaves the hand and stays on the record. `moved` is `move`'s."""
    if answer_ not in ("fix", "later"):
        raise ValueError(f"No answer {answer_!r}")

    def apply(f: dict) -> None:
        f["status"], f["answer"], f["fix"] = "answered", answer_, ({k: str(v)[:100] for k, v in fix.items()} if fix else None)
    return _change(state_dir, fid, apply)


def move(state_dir: Path, fid: str, level: str) -> dict | None:
    """The person moved the finding to another level: it still waits in the hand, marked `moved`. A level that is none of the three is refused (ValueError)."""
    if level not in LEVELS:
        raise ValueError(f"No level {level!r}")

    def apply(f: dict) -> None:
        f["level"], f["answer"] = level, "moved"
        if f["status"] in ("found", "told"):
            f["status"] = "sorted"
    return _change(state_dir, fid, apply)


def pending(state_dir: Path) -> list[str]:
    """The goals ("" for no goal) that hold a finding not told yet (status `found`)."""
    return [idea for idea in _goals(state_dir) if any(f["status"] == "found" for f in of_goal(state_dir, idea))]


def waiting(state_dir: Path) -> list[str]:
    """The goals ("" for no goal) that hold a finding not told yet or told and not sorted yet: an acceptance tells its own at once (spec 152 B.3), the Orkmaster still sorts them."""
    return [idea for idea in _goals(state_dir) if any(f["status"] in ("found", "told") for f in of_goal(state_dir, idea))]


def ripe(state_dir: Path, idea: str, now: dt.datetime | None = None) -> bool:
    """The goal's findings are in (§237.1): its verdict was read (the record's `at`) and its checks are done and the lenses of its parties looked after it, or `QUIET_H` hours have passed
    since the verdict, whichever is first; and the goal's last step is accepted or gone on (spec 152 B.3). A finding of no goal is ripe at once; a goal whose verdict was not read is not (a finding of its own, a lens's, waits for it)."""
    if not idea:
        return True
    from orkboard.realm import idea_route                            # a step landed and not accepted yet: its leader's findings are not all in (spec 152 B.3)
    if idea_route.due(ideas.plan(Path(state_dir), idea)):
        return False
    rec = record(state_dir, idea)
    try:
        at = dt.datetime.fromisoformat(rec["at"])
    except ValueError:
        return False
    now = now or dt.datetime.now()
    if now - at >= dt.timedelta(hours=QUIET_H):
        return True
    from orkboard.realm import concerns, idea_checks                 # the looks and the checks are the other modules' to know
    plan = ideas.plan(Path(state_dir), idea) or {}
    if any(t.get("kind") in idea_checks.TAGS and t.get("state") not in ("merged", "failed", "dropped") for t in plan.get("tasks") or [] if isinstance(t, dict)):
        return False
    for party in {f["party"] for f in rec["findings"] if f["party"]}:
        try:
            look = concerns.read(Path(state_dir), party)
            if not (look.get("at") and dt.datetime.fromisoformat(look["at"]) > at and look.get("status") == "ready"):
                return False
        except (ValueError, OSError):
            return False
    return True


# -- the calls' answers ----------------------------------------------------------------------------------------------------------------------------

def clean_told(raw: object, ids: list[str]) -> dict[str, dict] | None:
    """The finder's answer, strictly: `{id: {what, shows, promised, cause}}` for the findings it was asked about (each field one line, `LINE_CHARS` at most); an id it was not asked about is dropped. None when the
    answer is no object with a `findings` list."""
    rows = raw.get("findings") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        return None
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, dict) and r.get("id") in ids and r["id"] not in out:
            got = {k: _line(r.get(k)) for k in ("what", "shows", "promised", "cause")}
            if any(got.values()):
                out[r["id"]] = got
    return out


def clean_levels(raw: object, ids: list[str]) -> dict[str, dict] | None:
    """The Orkmaster's answer, strictly: `{id: {level, change}}`; a level that is none of the three is `work`. A finding it left out is left out here (the caller takes it for `work`). None when the answer is no
    object with a `levels` list."""
    rows = raw.get("levels") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        return None
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, dict) and r.get("id") in ids and r["id"] not in out:
            out[r["id"]] = {"level": r["level"] if r.get("level") in LEVELS else "work", "change": _line(r.get("change"), CHANGE_CHARS)}
    return out


# -- what a fix pulls, the hand's rows ------------------------------------------------------------------------------------------------------------

def pulls_of(state_dir: Path, root: Path, f: dict, level: str = "") -> dict:
    """What fixing the finding at its level (or `level`) pulls after it and the price (realm/way_down.py): **work** a fix goal (one task, the checks again); **spec** the party's section written again (one section at
    the section's price) and its open tasks; **decision** the goals not done that rest on the goal's decision and the sections of the party. Never an error: a read that fails pulls nothing."""
    from orkboard.realm import idea_target, spec_sections, way_down
    level = level or f.get("level") or "work"
    try:
        idea, party = f.get("idea") or "", f.get("party") or ""
        if level == "decision":
            d = spec_sections.record(Path(state_dir), idea).get("decision") if idea else None
            return way_down.pulls(state_dir, root, "decision", changes=[d.get("number")] if isinstance(d, dict) and d.get("number") else [], parties=[party] if party else [])
        if level == "spec":
            got = way_down.pulls(state_dir, root, "spec", slug=idea, party=party)
            if idea:
                target = idea_target.target_for(None, ideas.track_page(Path(root), party) if party else None)
                each = idea_target.budget("section", target) or 0.0
                got["sections"] = [{"idea": idea, "party": party}, *got["sections"]]
                got["estimate"] = {"usd_low": round(got["estimate"]["usd_low"] + each, 2), "usd_high": round(got["estimate"]["usd_high"] + each, 2)}
            return got
        return way_down.pulls(state_dir, root, "work", slug=idea, party=party, changes=[{"tier": "warrior"}])
    except Exception:
        return way_down.empty(level)


def _sum(parts: list[dict], level: str) -> dict:
    from orkboard.realm import way_down
    out = way_down.empty(level)
    for p in parts:
        out["sections"] += [s for s in p["sections"] if s not in out["sections"]]
        out["tasks"] += [t for t in p["tasks"] if t not in out["tasks"]]
        out["checks"] += p["checks"]
        out["estimate"] = {k: round(out["estimate"][k] + p["estimate"][k], 2) for k in ("usd_low", "usd_high")}
    return out


def _view(state_dir: Path, root: Path, f: dict) -> dict:
    return {"id": f["id"], "party": f["party"], "level": f["level"] or "work", "what": f["what"], "cause": f["cause"], "change": f["change"], "shows": f["shows"], "promised": f["promised"],
            "source": f["source"], "on": f["on"], "answer": f["answer"], "pulls": pulls_of(state_dir, root, f)}


def rows(state_dir: Path, root: Path) -> list[dict]:
    """The hand's rows: one `quality` row a goal that has findings told or sorted and not answered (a told one has no level yet: it reads as `work` until the Orkmaster sorts it) (`{kind, idea, goal, title, priority, blocks, at, level, findings: [{id, party, level, what, cause, change, pulls …}], pulls}`,
    its findings in the order of their level, Decision first, then as they were found; `pulls` the sum of theirs: *Fix all there*) and a `finding` row for each of no goal (`{kind, id, level, party, what, …, pulls}`).
    Never urgent: `blocks` False."""
    out: list[dict] = []
    for idea in _goals(state_dir):
        waiting = [f for f in of_goal(state_dir, idea) if f["status"] in ("sorted", "told")]      # a finding told (an acceptance's, a seat's) is a card at once, not only once the Orkmaster has sorted it (spec 168 G1)
        if not waiting:
            continue
        if not idea:
            out += [{**_view(state_dir, root, f), "kind": "finding", "idea": "", "goal": f["party"], "title": f["what"], "text": f["what"], "priority": "normal", "blocks": False,
                     "at": f["at"]} for f in waiting]
            continue
        page = ideas.idea_page(Path(root), idea)
        if page is None:
            continue
        waiting.sort(key=lambda f: (LEVELS.index(f["level"]) if f["level"] in LEVELS else len(LEVELS), f["at"]))
        views = [_view(state_dir, root, f) for f in waiting]
        top = waiting[0]["level"] or "work"
        out.append({"kind": "quality", "idea": idea, "goal": page.get("track") or "", "title": page.title or idea, "text": f"Quality of {page.title or idea}", "priority": "normal", "blocks": False,
                    "at": max(f["at"] for f in waiting), "level": top, "findings": views, "pulls": _sum([v["pulls"] for v in views], top)})
    return out
