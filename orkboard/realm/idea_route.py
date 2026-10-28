"""A goal's route across parties (docs/specs/68-release-and-route.md §2, decisions §83.2–§83.4): where it came from, where it is, where it
went. Read from what the Board keeps (the pitch a goal was sent from, its flag, the releases it went into) and one small file beside its
state, `<state_dir>/ideas/<slug>/route.json` (`{"moved": [{from, to, at, by}]}`, the last 20). A goal moves to another party only before
its work starts (`move`). **A goal's work goes by steps** (docs/specs/99-a-goals-way.md §9; decisions §117.4): its route's parties one after another, each planning its
own step when the one before is merged in dev; `way` is that route, `begin` records a step as it is planned, and the route reads each step as history.

    route(root, state_dir, "dark-mode")        # [{step, party, goal, at, …}], oldest first; [] for a goal with only its party step
    move(root, state_dir, "dark-mode", "web")  # to another party: refused once a task has run; else recorded and moved (realm/ideas.py `move`)
    started(state_dir, "dark-mode")            # whether its work has started
    goal_state(root, state_dir, "pitch")       # a sent pitch's goal: its party, state, tasks, flag and release (`dropped` when it is gone)
    way(root, state_dir, "dark-mode")          # the steps of its work: [{party, leader}], [] for a goal routed to nothing (an older one)
    at_step(plan) / step_done(plan, n)         # the step a plan is at (the highest a task is stamped with); whether step n's tasks are all merged or dropped, one merged at least
    next_step(plan) / steps_left(plan)         # {n, party, leader} when the plan's step is done and the route it was made for (`plan.route`) has another, else None
    begin(state_dir, "dark-mode", 2, "web", "architect", ["k3"])   # step 2 planned: recorded (`route.json` `steps`), the steps after a re-planned one forgotten
    waits(plan) / holds(plan, task)            # a later step planned and held for the person's Start (`plan.waits`, decisions §169.3): {step, party, cost}; whether a task is of it

The steps: `pitch` {answer, word, title}, `moved` {from, to} (its `party` is the one it was moved from), `party` {state, done, total} (a goal of a route of
two steps or more has one for each, with `n` and `of`: the ones done `done`, the one at `state`, the ones after `waiting`), `main` {by}, `release` {version, out};
each has `step`, `party`, `goal` (the slug a press opens) and `at`. The faces word them. No face, no model.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import goal_team, idea_flag, ideas, pitches, releases
from orkboard.realm.goal_types import GONE

FILE = "route.json"
KEEP = 20                                # the moves kept
RUNNING = ("waiting", "ready")           # a task in these has not run
STARTED = "Its work has started in {party}: a goal moves only before its work starts. Add a new goal there."


def _path(state_dir: Path, slug: str) -> Path:
    return ideas.state_folder(state_dir, slug) / FILE


def _read(state_dir: Path, slug: str) -> dict:
    try:
        return ideas._json(_path(state_dir, slug)) or {}
    except ValueError:
        return {}


def moves(state_dir: Path, slug: str) -> list[dict]:
    """The moves kept, oldest first: `{from, to, at, by}`."""
    got = _read(state_dir, slug).get("moved")
    return [{k: str(m.get(k) or "") for k in ("from", "to", "at", "by")} for m in got if isinstance(m, dict)][-KEEP:] if isinstance(got, list) else []


def started(state_dir: Path, slug: str, st: dict | None = None, plan: dict | None = None) -> bool:
    """Whether the goal's work has started: its plan passed, a task past waiting and ready, or it is working or done."""
    st = st or ideas.state(state_dir, slug)
    plan = plan if plan is not None else ideas.plan(state_dir, slug)
    return (st["state"] in ("working", "done") or bool((plan or {}).get("passed_at"))
            or any(t.get("state") not in (*RUNNING, None) for t in (plan or {}).get("tasks") or []))


def move(root: Path, state_dir: Path, slug: str, to: str | None = None, before: str | None = None, by: str = "") -> dict:
    """The goal to another party and/or before another goal (`ideas.move`). To another party it is refused once its work has started
    (ValueError, STARTED), else recorded in `route.json`. Within its party (its order) nothing is recorded. `{from, to, moved}`."""
    with ideas.LOCK:
        page = ideas.idea_page(root, slug)
        if page is None:
            raise ValueError(f"No goal {slug!r}")
        was = page.get("track") or ideas.GENERAL
        now = to or was
        if now != was and started(state_dir, slug):
            names = {t["slug"]: t["title"] for t in ideas.tracks(root, make=False)}
            raise ValueError(STARTED.format(party=names.get(was, was)))
        ideas.move(root, slug, to, before, by=by)
        if now != was:
            row = {"from": was, "to": now, "at": ideas._now(), "by": by}
            ideas._write_json(_path(state_dir, slug), {**_read(state_dir, slug), "moved": [*moves(state_dir, slug), row][-KEEP:]})
    return {"from": was, "to": now, "moved": now != was}


# -- the work by steps (spec 99 §9) ------------------------------------------------------------------------------------------------

def way(root: Path, state_dir: Path, slug: str) -> list[dict]:
    """The steps of a goal's work: its route as it stands, `[{party, leader}]` (a party since removed left out, each leader as its party has it now). [] for a goal
    routed to nothing (an older one): it works as a goal of one step, in its own party."""
    out: list[dict] = []
    for r in ideas.state(state_dir, slug).get("route") or []:
        party = r.get("party") if isinstance(r, dict) else None
        if isinstance(party, str) and ideas.track_page(root, party) is not None and all(o["party"] != party for o in out):
            out.append({"party": party, "leader": goal_team.leader_of(root, party)})
    return out


def step_of(task: dict) -> int:
    """The step a task belongs to (1-based): the one it was planned for; a task of before steps is the first's."""
    n = task.get("step") if isinstance(task, dict) else None
    return n if isinstance(n, int) and not isinstance(n, bool) and n >= 1 else 1


def at_step(plan: dict | None) -> int:
    """The step a plan is at: the highest a task is stamped with (1 for a plan with none)."""
    return max((step_of(t) for t in (plan or {}).get("tasks") or [] if isinstance(t, dict)), default=1)


def step_done(plan: dict | None, n: int) -> bool:
    """Step `n`'s tasks are all merged or dropped, and one of them is merged (a step whose tasks were all dropped landed nothing: the next does not follow)."""
    mine = [t for t in (plan or {}).get("tasks") or [] if isinstance(t, dict) and step_of(t) == n]
    return bool(mine) and all(t.get("state") in GONE for t in mine) and any(t.get("state") == "merged" for t in mine)


def legs_of(plan: dict | None) -> list[dict]:
    """The steps a plan was made for, `[{party, leader}]`: the route when its first step was planned (`plan.route`, kept for a route of two steps or more); [] for a goal of one step."""
    got = (plan or {}).get("route")
    return [{"party": str(r["party"]), "leader": str(r.get("leader") or "")} for r in got if isinstance(r, dict) and r.get("party")] if isinstance(got, list) else []


def steps_left(plan: dict | None) -> bool:
    """The plan is passed, its step is done (`step_done`) and the route it was made for has another after it: the goal is not done."""
    n = at_step(plan)
    return bool(plan and plan.get("passed_at")) and n < len(legs_of(plan)) and step_done(plan, n)


def next_step(plan: dict | None) -> dict | None:
    """The step to plan next, `{n, party, leader}`; None when the goal has none (`steps_left`)."""
    return {"n": at_step(plan) + 1, **legs_of(plan)[at_step(plan)]} if steps_left(plan) else None


def waits(plan: dict | None) -> dict | None:
    """The later step that waits for the person's Start (decisions §169.3): `plan.waits` = `{step, party, cost: {usd_low, usd_high}}`, laid when the keeper planned the step (a step
    after the first, `core/idea_plan.py`) and `idea_risk.decide` held it; None when no step waits. Its tasks stay `waiting` (`holds`) until the person starts it."""
    got = (plan or {}).get("waits")
    n = got.get("step") if isinstance(got, dict) else None
    return got if isinstance(n, int) and not isinstance(n, bool) and n >= 2 else None


def holds(plan: dict | None, task: dict) -> bool:
    """The task is of the step that waits (or one after it): it does not become `ready`."""
    got = waits(plan)
    return got is not None and step_of(task) >= got["step"]


def begin(state_dir: Path, slug: str, n: int, party: str, leader: str, tasks: list[str]) -> None:
    """Step `n` was planned (`route.json` `steps`: `{n, party, leader, at, tasks}`; the steps from `n` on are replaced: a first step planned again forgets the rest)."""
    with ideas.LOCK:
        kept = _read(state_dir, slug)
        before = [s for s in kept.get("steps") or [] if isinstance(s, dict) and isinstance(s.get("n"), int) and s["n"] < n]
        ideas._write_json(_path(state_dir, slug), {**kept, "steps": [*before, {"n": n, "party": party, "leader": leader, "at": ideas._now(), "tasks": list(tasks)}]})


def recorded(state_dir: Path, slug: str) -> list[dict]:
    """The steps planned so far, oldest first: `{n, party, leader, at, tasks}`."""
    got = _read(state_dir, slug).get("steps")
    return [s for s in got if isinstance(s, dict) and isinstance(s.get("n"), int)] if isinstance(got, list) else []


def _legs(root: Path, state_dir: Path, slug: str, party: str, st: dict, plan: dict | None, at: str) -> list[dict]:
    """The `party` steps of a goal: one (its party's, the goal's state) for a route of one step or none; for a route of two steps or more, one for each step, the ones
    done `done`, the one the goal is at its state, the ones after `waiting`."""
    legs = legs_of(plan) or way(root, state_dir, slug)
    if len(legs) < 2:
        done, total = _tasks(plan)
        return [{"step": "party", "party": legs[0]["party"] if legs else party, "goal": slug, "at": at, "state": st["state"], "done": done, "total": total}]      # the route's party, else the goal's own
    tasks = [t for t in (plan or {}).get("tasks") or [] if isinstance(t, dict)]
    when = {s["n"]: str(s.get("at") or "") for s in recorded(state_dir, slug)}
    cur = at_step(plan)
    live = cur + 1 if cur < len(legs) and step_done(plan, cur) else cur          # the next step once the one before is done, planned or not
    out = []
    for n, leg in enumerate(legs, start=1):
        mine = [t for t in tasks if step_of(t) == n]
        out.append({"step": "party", "party": leg["party"], "goal": slug, "at": when.get(n) or (at if n == 1 else ""),
                    "state": "done" if n < live else st["state"] if n == live else "waiting",
                    "done": sum(1 for t in mine if t.get("state") == "merged"), "total": len(mine), "n": n, "of": len(legs)})
    return out


def _tasks(plan: dict | None) -> tuple[int, int]:
    tasks = (plan or {}).get("tasks") or []
    return sum(1 for t in tasks if t.get("state") == "merged"), len(tasks)


def steps(root: Path, state_dir: Path, slug: str, page: ideas.Page | None = None, st: dict | None = None, plan: dict | None = None,
          held: dict | None = None, flag: dict | None | bool = False) -> list[dict]:
    """Every step of the route, its `party` step among them (`route` leaves a route of that alone out). `page`, `st`, `plan`, `held`
    (`releases.holding`) and `flag` (None for none) when the caller has them read."""
    page = page or ideas.idea_page(root, slug)
    st = st or ideas.state(state_dir, slug)
    plan = plan if plan is not None else ideas.plan(state_dir, slug)
    held = releases.holding(root, state_dir) if held is None else held
    party = (page.get("track") if page is not None else "") or ideas.GENERAL
    out = []
    src = str(st.get("from_pitch") or "")
    if re.fullmatch(r"[a-z0-9-]+", src) and (pitch := ideas.idea_page(root, src)) is not None:
        j = pitches.read(state_dir, src)
        answer = str((j["decision"] or {}).get("answer") or "")
        out.append({"step": "pitch", "party": pitch.get("track") or ideas.GENERAL, "goal": src, "at": j["judged_at"], "answer": answer,
                    "word": pitches.ANSWER_WORDS.get(answer, ""), "title": pitch.title or src})
    moved = moves(state_dir, slug)
    out += [{"step": "moved", "party": m["from"], "goal": slug, "at": m["at"], "from": m["from"], "to": m["to"]} for m in moved]
    out += _legs(root, state_dir, slug, party, st, plan, (moved or [{"at": ""}])[-1]["at"])
    if (flag := idea_flag.flag_of(state_dir, slug) if flag is False else flag) is not None:
        out.append({"step": "main", "party": party, "goal": slug, "at": flag["at"], "by": flag.get("by") or ""})
    out += [{"step": "release", "at": r["out"] or r["at"], **releases.step_of(r)} for r in held.get(slug, [])]
    return out


def route(root: Path, state_dir: Path, slug: str, **read) -> list[dict]:
    """A goal's route, oldest first (§2.1); [] for a goal with only its `party` step (the faces draw nothing) — unless that step is a party other than the one the goal lies in: a
    goal routed to one party that is not its own yet (the person took its first party off the route) carries it, so the table's dot for that party is lit from `routed` on
    (spec 100 As built E; decisions §169). `read`: `steps`' reads."""
    got = steps(root, state_dir, slug, **read)
    if len(got) > 1:
        return got
    page = read.get("page") or ideas.idea_page(root, slug)
    own = (page.get("track") if page is not None else "") or ideas.GENERAL
    return got if got and got[0]["step"] == "party" and got[0]["party"] != own else []


def goal_state(root: Path, state_dir: Path, pitch: str, held: dict | None = None) -> dict | None:
    """What became of the goal a pitch was sent (§2.4): `{goal, party, state, done, total, flag, release}`; `flag` its date ("" before),
    `release` the last release that holds it (`{goal, party, version, out}`) or None. A goal dropped since: `state: "dropped"`, nothing
    else. None for a pitch not sent."""
    sent = pitches.read(state_dir, pitch)["sent"]
    goal = str((sent or {}).get("goal") or "") if isinstance(sent, dict) else ""
    if not goal:
        return None
    page = ideas.idea_page(root, goal)
    if page is None:
        return {"goal": goal, "party": "", "state": "dropped", "done": 0, "total": 0, "flag": "", "release": None}
    held = releases.holding(root, state_dir) if held is None else held
    done, total = _tasks(ideas.plan(state_dir, goal))
    flag = idea_flag.flag_of(state_dir, goal)
    mine = held.get(goal) or []
    return {"goal": goal, "party": page.get("track") or ideas.GENERAL, "state": ideas.state(state_dir, goal)["state"], "done": done,
            "total": total, "flag": flag["at"] if flag else "", "release": releases.step_of(mine[-1]) if mine else None}
