"""The way down (docs/specs/132-four-levels-the-way-down-and-findings.md C; decisions §234.2, §237.7): what a change pulls after it, below the level it enters, and
what that costs; and the levels of a goal that hold something open. No model, no face: a read of the files.

    pulls(state_dir, root, level, *, slug="", party="", changes=(), parties=())
        → {level, sections: [{idea, party}], tasks: [{idea, id}], checks: int, estimate: {usd_low, usd_high}}
    open_levels(state_dir, slug)                 # → the levels ("decision", "spec", "work", "quality") that hold something open of the goal, in that order
    empty(level)                                 # the same dict with nothing pulled

`level` **decision**: `changes` the decision numbers changed, `parties` the parties whose slices changed: the goals not done that rest on one of the decisions (their decision's
number, or one it changes) and each section of theirs that one of `parties` wrote; then their open tasks of those parties, then the checks. **spec**: `slug`, `party`: the
party's open tasks of the goal, then the checks. **work**: `slug`; `changes` the tasks the change redoes, a task's id or (an added task) a dict `{tier}`; their checks.
Nothing above the level is pulled, nor what the change does not touch. The estimate: a section at `idea_target.budget("section", target)`, a check at `budget("accept", target)`
(the cap each is held to), a task at the board's learnt cost of its tier (`idea_spend.tier_costs`, as a plan's estimate is made) ±50 %; `target` the goal's party's.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from orkboard.realm import idea_change, idea_spend, idea_target, ideas, leader_change, plans, spec_sections

LEVELS = ("decision", "spec", "work", "quality")
CASCADES = "cascades.json"             # spec 131 B: <state_dir>/cascades.json {"cascades": [{status, sections: [{idea, party}]}]}, read defensively until realm/cascades.py is there
QUALITY = "quality.json"               # spec 132 D.1: <state_dir>/ideas/<slug>/quality.json {findings: [{status, ...}]}


def empty(level: str) -> dict:
    return {"level": level, "sections": [], "tasks": [], "checks": 0, "estimate": {"usd_low": 0.0, "usd_high": 0.0}}


def _num(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _checks_of(page: ideas.Page | None) -> int:
    """The goal's checks that apply and were not skipped (what its page kept of the team's checks)."""
    got = ideas._json_list(str(page.get("checks") or "")) if page else []
    return sum(1 for c in got if isinstance(c, dict) and c.get("applies") and not c.get("skipped"))


def _target(root: Path, party: str, settings: dict | None) -> str:
    return idea_target.target_for(settings, ideas.track_page(root, party) if party else None)


def _task_cost(task: dict, target: str, costs: dict[str, float]) -> float:
    tier = idea_target.tier_of(idea_target.task_pick(str(task.get("tier") or "warrior"), target)[0])
    return float(costs.get(tier, plans.DEFAULT_COST.get(tier, plans.DEFAULT_COST["warrior"])))


def pulls(state_dir: Path, root: Path, level: str, *, slug: str = "", party: str = "", changes: Any = (), parties: Any = (), settings: dict | None = None) -> dict:
    """What a change entering at `level` pulls below it, and its price (see the module). An unknown level pulls nothing."""
    out = empty(level)
    if level not in ("decision", "spec", "work"):
        return out
    state_dir, root = Path(state_dir), Path(root)
    costs = idea_spend.tier_costs(state_dir)
    low = high = 0.0

    def add_tasks(idea: str, ids: list[dict | str], page: ideas.Page | None, target: str) -> None:
        nonlocal low, high
        plan_tasks = {str(t.get("id")): t for t in (ideas.plan(state_dir, idea) or {}).get("tasks") or [] if isinstance(t, dict)}
        for t in ids:
            task = t if isinstance(t, dict) else plan_tasks.get(str(t))
            if task is None:
                continue
            out["tasks"].append({"idea": idea, "id": str(task.get("id") or "")})
            cost = _task_cost(task, target, costs)
            low, high = low + cost * 0.5, high + cost * 1.5
        if ids:                                                                   # the goal's checks are run again over what changed, once
            n = _checks_of(page)
            out["checks"] += n
            each = idea_target.budget("accept", target) or 0.0
            low, high = low + n * each, high + n * each

    if level == "work":
        page = ideas.idea_page(root, slug) if slug else None
        party = party or (page.get("track") if page else "") or ""
        plan_tasks = {str(t.get("id")): t for t in (ideas.plan(state_dir, slug) or {}).get("tasks") or [] if isinstance(t, dict)}
        redone = [c for c in changes or () if isinstance(c, dict) or idea_change.open_task(plan_tasks.get(str(c)))]        # an added task (a dict) and the tasks not started
        add_tasks(slug, redone, page, _target(root, party, settings))
    elif level == "spec":
        page = ideas.idea_page(root, slug) if slug else None
        plan = ideas.plan(state_dir, slug) if slug else None
        ids = sorted(leader_change.owned(root, plan, (page.get("track") if page else "") or "", party)) if party else []
        add_tasks(slug, ids, page, _target(root, party, settings))
    else:
        numbers = {n for n in (_num(c) for c in changes or ()) if n is not None}
        wrote = {str(p) for p in parties or ()}
        known = [{"slug": t["slug"], "title": t["title"]} for t in ideas.tracks(root, make=False)]
        for i in ideas.ideas(root):
            idea = i["slug"]
            if ideas.state(state_dir, idea)["state"] == "done":
                continue
            d = spec_sections.record(state_dir, idea).get("decision")
            if not isinstance(d, dict) or not (numbers & {_num(d.get("number")), *(_num(n) for n in d.get("changes") or [])} - {None}):
                continue
            page = ideas.idea_page(root, idea)
            if page is None:
                continue
            plan = ideas.plan(state_dir, idea)
            for s in spec_sections.read(page, known, i["track"])["sections"]:
                if s.older or s.party not in wrote:
                    continue
                target = _target(root, s.party, settings)
                out["sections"].append({"idea": idea, "party": s.party})
                each = idea_target.budget("section", target) or 0.0
                low, high = low + each, high + each
                add_tasks(idea, sorted(leader_change.owned(root, plan, i["track"], s.party)), page, target)
    out["estimate"] = {"usd_low": round(low, 2), "usd_high": round(high, 2)}
    return out


# -- the levels open on a goal ----------------------------------------------------------------------------------------------------------------

def _read(path: Path) -> dict:
    try:
        got = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return got if isinstance(got, dict) else {}


def _cascade_ready(state_dir: Path, slug: str) -> bool:
    """A cascade ready whose sections name the goal (read from `cascades.json` while no module of spec 131 B is there)."""
    for c in _read(Path(state_dir) / CASCADES).get("cascades") or []:
        if isinstance(c, dict) and c.get("status") == "ready" and any(isinstance(s, dict) and s.get("idea") == slug for s in c.get("sections") or []):
            return True
    return False


def open_levels(state_dir: Path, slug: str) -> list[str]:
    """The levels that hold something open of the goal, in the order of LEVELS: `decision` (a cascade ready that names it, or its decision worded and not confirmed), `spec` (a
    leader's change ready, a fork open), `work` (a plan change live, a task failed), `quality` (a finding not answered)."""
    state_dir = Path(state_dir)
    st = ideas.state(state_dir, slug)
    way = spec_sections.record(state_dir, slug)
    d = way.get("decision") if isinstance(way.get("decision"), dict) else None
    plan = ideas.plan(state_dir, slug)
    got = []
    if _cascade_ready(state_dir, slug) or (st["state"] == "decided" and d and not d.get("confirmed")):
        got.append("decision")
    if any(r.get("status") == "ready" for r in leader_change.read(state_dir, slug)) or any(isinstance(f, dict) and f.get("status") == "open" for f in way.get("forks") or []):
        got.append("spec")
    failed = any(isinstance(t, dict) and t.get("state") == "failed" for t in (plan or {}).get("tasks") or [])
    if (plan and idea_change.live(state_dir, slug, plan, st["state"]) is not None) or failed:
        got.append("work")
    findings = _read(ideas.state_folder(state_dir, slug) / QUALITY).get("findings")
    if any(isinstance(f, dict) and f.get("status") != "answered" for f in findings or []):
        got.append("quality")
    return got
