"""The Map (docs/specs/39-map.md §1): a project's goals, ideas and tasks on one screen, as data. A pure read of what the
Board holds (the pages, `plan.json`, the claims' notes, the ledger): it writes nothing, starts nothing and writes no
words for a node's state — the faces word it with the functions that word the Board's row.

`row` and `idea_needs` are the Board's own (`gui/ideas_board.py` calls them), so a node and a Board row never differ.
`build` takes the host's reading of an idea's and a goal's state (`state_of`, `goal_state_of`: the keeper's busy flag
is the host's), else the files'.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Callable

from orkboard.realm import (collide, goal_flags, goal_team, goal_types, goal_verdict, harnesses, idea_change, idea_checks, idea_flag, idea_pick, idea_questions, idea_shots,
                            idea_risk, idea_spend, idea_route, idea_target, ideas, library, map_party, map_stage, pitches, releases, roles, tool_errors)
from orkboard.realm.idea_words import short_of

NEEDS = ("asks", "plan", "change", "todo", "failed", "proposal", "pitch", "collide")        # the Needs you kinds that sit on an idea, as a node names them (a plan change: spec 62; a judged pitch: spec 65; a collision: spec 71)
_HELD_FILES = re.compile(r"^files(?: beside)? · (.+)$")
_AFTER = re.compile(r"after (\d{1,2}:\d{2})")
SIGN_IN_TOOL = "claude"          # what the Board runs by itself runs on Claude (core/idea_runner.py `HARNESS`)


def sign_in_needs(entries: list[dict]) -> list[dict]:
    """The Needs you rows of the tools that need a sign-in and hold work (spec 45 §7): one per tool, from the host's
    `sign_in` entries (core/sign_ins.py). It blocks: the work in progress waits for it."""
    out = []
    for e in entries:
        if e.get("state") == "done" or not e.get("waiting"):
            continue
        tool = str(e.get("tool") or harnesses.title(str(e.get("harness") or "")))
        out.append({"kind": "sign_in", "harness": e["harness"], "tool": tool, "title": tool, "blocks": True,
                    "priority": "normal", "at": dt.datetime.fromtimestamp(float(e.get("since") or 0)).isoformat(timespec="seconds"),
                    "text": tool_errors.LINES[tool_errors.LOGIN].format(tool=tool), "waiting": int(e["waiting"])})
    return out


def list_of_dicts(text: object) -> list[dict]:
    """A page field that holds a JSON list of objects (`checks`)."""
    try:
        got = json.loads(text) if str(text or "").strip() else []
    except ValueError:
        return []
    return [x for x in got if isinstance(x, dict)] if isinstance(got, list) else []


def list_of(text: object) -> list[str]:
    """A page field that holds a JSON list of text (`depends_on`, `risk_triggers`)."""
    try:
        got = json.loads(text) if str(text or "").strip() else []
    except ValueError:
        return []
    return [str(x) for x in got if isinstance(x, str)] if isinstance(got, list) else []


def idea_needs(root: Path, state_dir: Path, i: dict, st: dict, plan: dict | None, asks: list[str], at: str | None = None) -> list[dict]:
    """What of one idea needs the person (spec 35 §10): its questions, its plan waiting, the leader's plan change waiting (spec 62), a to-do only when it blocks (spec 87 §4.1),
    a failure, a proposal; a judged pitch (spec 65 §5: low, blocking nothing, its answer)."""
    slug, state = i["slug"], st["state"]
    base = {"idea": slug, "goal": i["track"], "title": i["title"], "priority": i["priority"], "blocks": False,
            "at": ideas.touched_at(root, state_dir, slug) if at is None else at}
    tasks = (plan or {}).get("tasks") or []
    out = []
    if state == "asks":
        looks = st.get("asks_look") if isinstance(st.get("asks_look"), int) and not isinstance(st.get("asks_look"), bool) else 0
        asked = [{**idea_questions.parse(q), "look": n < looks} for n, q in enumerate(asks[:5])]          # the first ones are of the look (spec 85 §1)
        out.append({**base, "kind": "asks", "text": asked[0]["ask"] if asked else "The keeper asks you", "questions": asks[:5],
                    "asked": asked})
    if state == "plan" and plan and not plan.get("passed_at"):            # its `missing`: what no one of the party does, read now (spec 52 §2.6)
        out.append({**base, "kind": "plan", "text": "Plan ready" + (f" · {len(tasks)} tasks" if tasks else ""),
                    "at": str(plan.get("made_at") or base["at"]),
                    "missing": goal_types.still_missing(state_dir, root, i["track"], plan.get("missing"))})
    if plan and (change := idea_change.live(state_dir, slug, plan, state)) is not None:        # the leader's plan change waits (spec 62 §4.1)
        said = idea_change.summary(change, plan)
        out.append({**base, "kind": "change", "text": idea_change.text_of(said), "at": said["made_at"] or base["at"], "why": said["why"],
                    **{k: said[k] for k in ("added", "changed", "dropped", "usd_low", "usd_high")}})
    if state == "proposed":
        out.append({**base, "kind": "proposal", "text": ideas.thesis(
            (ideas.idea_page(root, slug) or ideas.Page()).section("Gist")) or "The keeper proposes this"})
    if state == "judged":
        out.append({**base, **pitches.need_of(state_dir, slug)})
    if state == "failed":
        out.append({**base, "kind": "failed", "text": st.get("error") or "Something failed"})
    merged = {t.get("id") for t in tasks if t.get("state") == "merged"}
    if state == "working":
        for t in tasks:
            if t.get("state") == "failed":
                out.append({**base, "kind": "failed", "blocks": True, "text": f"{t.get('title', '')}: {t.get('error') or 'failed'}",
                            "at": str(t.get("finished") or base["at"])})
    if plan and state == "working":                  # a to-do is a stop only when it blocks (spec 87 §4.1); before that it is a line of the plan (`todo_lines`)
        for td in plan.get("todos") or []:
            if td.get("done"):
                continue
            waits = [t for t in tasks if t.get("id") in (td.get("for") or []) and t.get("state") != "merged"
                     and set(t.get("after") or []) <= merged]
            if waits:
                out.append({**base, "kind": "todo", "text": td.get("title") or "", "blocks": True,
                            "at": str(plan.get("made_at") or base["at"]),
                            "todo": {k: td.get(k) for k in ("id", "title", "kind", "why", "choices", "steps", "accept", "done")}})
    return out


def todo_lines(plan: dict | None, tasks: list[dict] | None = None) -> list[str]:
    """The lines of a goal's plan for its to-dos (spec 87 §4.2): "Before <task title>: <to-do title>", for each task not merged (or dropped), in the
    plan's order, each to-do not done that is `for` it (within a task, the to-dos' order): the same lines the faces work out for themselves.
    A to-do done, or one for no task still to come, is not said. `tasks`: the plan's own when not given."""
    plan = plan or {}
    tasks = [t for t in (plan.get("tasks") if tasks is None else tasks) or [] if isinstance(t, dict)]
    todos = [d for d in plan.get("todos") or [] if isinstance(d, dict) and not d.get("done") and str(d.get("title") or "").strip()]
    return [f"Before {t.get('title') or t.get('id')}: {str(d['title']).strip()}" for t in tasks if t.get("state") not in ("merged", "dropped")
            for d in todos if t.get("id") in (d.get("for") or [])]


def type_of(st: dict) -> dict | None:
    """A goal's type as a node carries it (spec 52 §2.2): `{id, name, sign}`; None with none or an unknown key."""
    t = goal_types.get(st.get("type"))
    return {"id": t.id, "name": t.name, "sign": t.sign} if t is not None else None


def flag_of(state_dir: Path, slug: str, held: dict[str, list[dict]]) -> dict | None:
    """A goal's flag as a node carries it: the flag with `release`, the last release that holds the goal (`{goal, party, version, out}`) or None."""
    flag = idea_flag.flag_of(state_dir, slug)
    return None if flag is None else {**flag, "release": releases.step_of(held[slug][-1]) if held.get(slug) else None}


def release_of(r: dict | None) -> dict | None:
    """A release goal's node carries its file: `{version, goals: [slugs], out}`; None for any other goal (spec 68 §3.3)."""
    return None if r is None else {"version": r["version"], "goals": list(r["goals"]), "out": r["out"]}


def task_short(t: dict) -> str:
    """A task's short name: the plan's, else made from its title (a plan of before spec 41)."""
    return str(t.get("short") or "") or short_of(str(t.get("title") or ""))


def _night_by(i: dict, st: dict, plan: dict | None) -> str:
    """Who put it off to the night, for what waits for it; "board" only while the idea is still Low (raised to High or Normal it is as the person's)."""
    low = i["priority"] == "low"
    if st["state"] == "raw" and ideas.queue_of(st) == "night":
        return ideas.night_by_of(st) if low else "person"
    if st["state"] == "plan" and (plan or {}).get("start_at") == "night":
        return "board" if low and (plan or {}).get("start_at_by") == "board" else "person"
    return ""


def row(root: Path, state_dir: Path, i: dict, st: dict, plan: dict | None, page: ideas.Page | None, asks: list[str],
        states: dict[str, dict], mine: list[dict], at: str | None = None) -> dict:
    """An idea as `ideas.board` lists it: the state and what words it (queue, held_until, start_at, progress, waits_on)."""
    slug = i["slug"]
    tasks = (plan or {}).get("tasks") or []
    depends = list_of(page.get("depends_on")) if page else []
    return {"slug": slug, "title": i["title"], "short": i["short"], "track": i["track"], "order": i["order"],
            "state": st["state"], "size": i["size"], "thesis": i["thesis"], "asks": len(asks),
            "priority": i["priority"],
            "progress": {"done": sum(1 for t in tasks if t.get("state") == "merged"), "total": len(tasks)},
            "updated": ideas.touched_at(root, state_dir, slug) if at is None else at,
            "queue": ideas.queue_of(st), "held_until": st["held_until"],
            **({"held_for": st["held_for"]} if st.get("held_for") and st["held_until"] else {}),
            "risk": idea_risk.level(page.get("risk")) if page and page.get("risk") else "",
            "risk_triggers": list_of(page.get("risk_triggers")) if page else [],
            "depends_on": depends,
            "waits_on": [d for d in depends if states.get(d, {}).get("state") != "done"],
            "start_at": str((plan or {}).get("start_at") or ""),
            "night_by": _night_by(i, st, plan),
            "in_needs_you": any(n["kind"] in ("asks", "plan", "proposal") for n in mine)}


def made_of(task: dict) -> str:
    """What a merged task made (spec 85 §4): its first commit's subject, cut; "" for a task not merged or one that committed nothing."""
    subjects = task.get("subjects") if task.get("state") == "merged" and isinstance(task.get("subjects"), list) else []
    first = next((" ".join(x.split()) for x in subjects if isinstance(x, str) and x.strip()), "")
    return first if len(first) <= MADE_CHARS else first[:MADE_CHARS - 1].rstrip() + "…"


def _by(task: dict, read: tuple[dict, dict]) -> dict:
    """The role a task runs as, `{slug, name}`; a role since dropped reads as Grunt."""
    slug = roles.task_slug(task, read)
    r = read[0].get(slug) or read[0].get(roles.GRUNT) or {}
    return {"slug": r.get("slug") or slug, "name": r.get("name") or slug}


def _asked(st: dict, asks: list[str], by_slug: dict, lead: dict | None, target: str) -> list[dict]:
    """An idea's questions with who asks each: the state's `asks_by` (spec 46 §1), else the goal's leader."""
    who = st.get("asks_by") if isinstance(st.get("asks_by"), list) else []
    looks = st.get("asks_look") if isinstance(st.get("asks_look"), int) and not isinstance(st.get("asks_look"), bool) else 0
    out = []
    for n, q in enumerate(idea_questions.parse(a) for a in asks[:5]):
        r = by_slug.get(who[n]) if n < len(who) and isinstance(who[n], str) else None
        r = r or lead
        out.append({"ask": q["ask"], "choices": q.get("choices") or [], "pick": q.get("pick"), "why": q.get("why") or "", "look": n < looks,
                    "by": {"slug": r["slug"], "name": r["name"], "head": roles.head(r, target)} if r else None})
    return out


MADE_CHARS = 120                        # what a merged task made, as the Map carries it (spec 85 §4)
ERROR_CHARS = 300                       # a failed task's error as the Map carries it (spec 49 §2.4)
BRIEF_CHARS = 140                       # a party's brief (spec 50 §2.4)


def brief_of(g: dict) -> str:
    """What a party is for, in one short line (spec 50 §2.4): its Description's first paragraph, else its Summary's first line,
    at most 140 characters."""
    paragraph = next((p for p in re.split(r"\n\s*\n", str(g.get("about") or "").strip()) if p.strip()), "")
    text = " ".join(paragraph.split()) or " ".join(next((ln for ln in str(g.get("summary") or "").splitlines() if ln.strip()), "").split())
    return text if len(text) <= BRIEF_CHARS else text[:BRIEF_CHARS - 1].rstrip() + "…"


def _run_of(t: dict) -> dict:
    """What a task's run left, for its card (spec 49 §2.4): the failure as the runner wrote it (cut), a hold's or a stop's
    note, the round, what it cost (usd; None before it ran) and when it started (ISO, "" before)."""
    cost = t.get("cost")
    return {"error": str(t.get("error") or "")[:ERROR_CHARS], "note": str(t.get("note") or ""), "round": int(t.get("round") or 1),
            "cost": cost if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None,
            "started": str(t.get("started") or "")}


# -- the Map -------------------------------------------------------------------------------------------------

def _tiers(order: list[str], depends: dict[str, list[str]]) -> dict[str, int]:
    """1 for an idea that depends on none of its goal's ideas, else one more than the deepest it depends on (a cycle,
    which spec 35 §3 never closes, is read as no dependency rather than looped on)."""
    tier: dict[str, int] = {}
    walking: set[str] = set()

    def of(slug: str) -> int:
        if slug in tier:
            return tier[slug]
        walking.add(slug)
        deepest = max((of(d) for d in depends[slug] if d in depends and d not in walking), default=0)
        walking.discard(slug)
        tier[slug] = deepest + 1
        return tier[slug]

    for slug in order:
        of(slug)
    return tier


def _sign_in_wait(harness: str, until: str) -> dict:
    """`waits` kind `sign_in`: `ref` the tool, `tool` its title, `until` when it fails as it did (a day from the hold)."""
    title = harnesses.title(harness)
    return {"kind": "sign_in", "ref": harness, "title": title, "tool": title, "until": until}


def _waits(node: dict, tasks: list[dict], titles: dict[str, str], page_waits: list[str], week: dict | None = None) -> dict | None:
    """Why a node that is not done does not move: the first that holds (spec 39 §1). Data, not words. `week`: {"until": the week's reset (local
    time, to the minute), "held": the Board's own Low work waits at night for the week} (spec 44 §4), or None with no week read."""
    if node["needs_you"] or any(t.get("state") == "picking" for t in tasks):          # a task that made variants waits for the person's pick (spec 51)
        return {"kind": "you", "ref": "", "title": "", "until": ""}
    if page_waits:
        return {"kind": "idea", "ref": page_waits[0], "title": titles.get(page_waits[0], page_waits[0]), "until": ""}
    held = [t for t in tasks if t.get("state") == "held"]
    for t in held:                                    # a task held for its tool's sign-in (spec 45 §7)
        if t.get("held_for") == "sign_in":
            return _sign_in_wait(str(t.get("harness") or SIGN_IN_TOOL), str(t.get("held_until") or ""))
    if node.get("held_for") == "sign_in":
        return _sign_in_wait(SIGN_IN_TOOL, node["held_until"])
    for t in held:
        m = _HELD_FILES.match(str(t.get("note") or ""))
        if m:
            return {"kind": "files", "ref": m.group(1), "title": titles.get(m.group(1), m.group(1)), "until": ""}
    if node["held_until"]:
        return {"kind": "limits", "ref": "", "title": "", "until": node["held_until"]}
    for t in held:
        note = str(t.get("note") or "")
        got = _AFTER.search(note)
        if got and not note.startswith(("reserve", "week")):
            return {"kind": "limits", "ref": "", "title": "", "until": got.group(1)}
    for t in held:
        note = str(t.get("note") or "")
        got = _AFTER.search(note)
        if got and note.startswith("reserve"):
            return {"kind": "reserve", "ref": "", "title": "", "until": got.group(1)}
    for t in held:
        note = str(t.get("note") or "")
        got = _AFTER.search(note)
        if got and note.startswith("week"):
            return {"kind": "week", "ref": "", "title": "", "until": (week or {}).get("until") or ""}      # no week read: no time the faces can say
    if (node["queue"] == "night" or node["start_at"] == "night") and node.get("night_by") == "board" and (week or {}).get("held"):
        return {"kind": "week", "ref": "", "title": "", "until": week["until"]}      # the Board's own Low work, held at night by the pace
    if node["queue"] == "night" or node["start_at"] == "night":
        return {"kind": "night", "ref": "", "title": "", "until": ""}
    if node["queue"] == "hold":
        return {"kind": "stopped", "ref": "", "title": "", "until": ""}
    return None


def _week_of(settings: dict | None, limits: list | None, now: float) -> dict | None:
    """The Claude week as the Map words a wait on it: {"until": its reset, "held": the Board's own Low work waits at night for it}; None with no
    week read (spec 44 §4)."""
    got = idea_target.week(limits or [], now)
    if got is None:
        return None
    s = settings or {}
    night = idea_target.in_night(str(s.get("night") or "01:00-07:00"), dt.datetime.fromtimestamp(now))
    return {"until": dt.datetime.fromtimestamp(got["reset"]).strftime("%Y-%m-%dT%H:%M"),
            "held": night and bool(s.get("autostart", True)) and idea_target.pace(limits or [], now) == "behind"}


def build(root: Path, state_dir: Path, settings: dict | None = None, limits: list | None = None, now: float = 0.0, *,
          goal: str = "", rev: Any = "", state_of: Callable[[str], dict] | None = None,
          goal_state_of: Callable[[str], dict] | None = None) -> dict:
    """The Map of a project (spec 39 §1): `goal` one goal's slug (else every goal but General). Reads each idea's page,
    state and `plan.json` once; no git, no process, no write. `settings`, `limits` and `now` are the Board's (the faces
    word `until` and the gate); a held task already says when it goes on."""
    state_of = state_of or (lambda slug: ideas.state(state_dir, slug))
    goal_state_of = goal_state_of or (lambda slug: ideas.goal_state(state_dir, slug))
    tracks = [t for t in ideas.tracks(root, make=False) if t["slug"] != ideas.GENERAL]
    shown = [t for t in tracks if not goal or t["slug"] == goal]
    found, read_pages = ideas.ideas_and_pages(root)                                 # the pages read once: the ideas' rows and their pages

    states = {i["slug"]: state_of(i["slug"]) for i in found}
    titles = {i["slug"]: i["title"] for i in found}
    place = {i["slug"]: n for n, i in enumerate(found)}
    pages = {i["slug"]: read_pages.get(i["slug"]) for i in found}
    depends = {s: list_of(p.get("depends_on")) if p else [] for s, p in pages.items()}

    # a done idea stays while an idea that stays depends on it, so every edge has both ends
    kept = {s for s, st in states.items() if st["state"] != "done"}
    todo = list(kept)
    while todo:
        for d in depends.get(todo.pop(), []):
            if d in states and d not in kept:
                kept.add(d)
                todo.append(d)

    goals, nodes, edges = [], [], []
    week = _week_of(settings, limits, now)
    read = roles.known(state_dir)                                                  # a task's head: who does it, at what tier
    today = dt.date.fromtimestamp(now).isoformat() if now else dt.date.today().isoformat()
    offered = pitches.offers(root, state_dir) if any((t.get("leader") or "") == library.INVESTOR for t in shown) else {}
    made = releases.index(root, state_dir, found)                           # the releases, read once: a goal's route, a flag's release (spec 68)
    held, rel = releases.holding(root, state_dir, made), goal_types.release_party(root, tracks)
    releasing = {r["goal"]: r for r in made}
    asked = {}                                                              # the Orkmaster's open questions, each on its goal (spec 71 §8.1)
    for n in collide.rows(root, state_dir, tracks=tracks, state_of=state_of):
        asked.setdefault(n["idea"], []).append(n)
    track_of, party_names = {i["slug"]: i["track"] for i in found}, {t["slug"]: t["title"] for t in tracks}
    for g in shown:
        target = idea_target.target_for(settings, g)                         # a party's size's Target, else the setting's (spec 75 §3)
        mine = [i for i in found if i["track"] == g["slug"]]
        ideation = (g.get("leader") or "") == library.INVESTOR       # Ideation: its goals are pitches (spec 65)
        order = [i["slug"] for i in mine]
        inside = set(order)
        tier = _tiers(order, {s: [d for d in depends[s] if d in inside] for s in order})
        spent = idea_spend.of_goal(state_dir, g["slug"], order)["usd"]
        gst = goal_state_of(g["slug"])
        by_slug = read[0]
        checks = idea_checks.of_team(state_dir, g.get("team") or [], g.get("every") or [])
        checkers = {c["by"] for c in checks}
        tiers = goal_team.tiers_of(root, g["slug"])                                 # the tiers its size gave its seats (spec 81 §2)
        team = [{"slug": s, "name": by_slug[s]["name"], "head": roles.head(goal_team.seat_role(by_slug[s], tiers), target), "checks": s in checkers,
                 "every": s in (g.get("every") or [])} for s in g.get("team") or [] if s in by_slug]
        lead = by_slug.get(g.get("leader") or roles.TASKMASTER) or by_slug.get(roles.TASKMASTER)
        verdict = goal_verdict.read(state_dir, g["slug"])
        goals.append({"slug": g["slug"], "title": g["title"], "short": g["short"], "priority": g["priority"], "state": gst["state"],
                      "craft": g.get("craft") or roles.DEFAULT_CRAFT, "race": roles.RACES.get(g.get("craft"), "peon"), "team": team,
                      "leader": {"slug": lead["slug"], "name": lead["name"], "head": roles.head(goal_team.seat_role(lead, tiers), target)} if lead else None,
                      "size": g.get("size") or "",                                  # the party's size (spec 75 §3): lean · standard · full, "" with none
                      "tool": g.get("tool") or "",                                  # the party's AI tool (spec 81): a harnesses id, "" the Main tool
                      "verdict": {"met": verdict.get("met") is True, "by": verdict.get("by") or "", "at": verdict.get("at") or "",
                                  **({"tally": goal_flags.tally(root, state_dir, g["slug"])} if verdict.get("met") is True else {})}
                      if verdict else None,
                      "brief": brief_of(g), "done_when": [m["name"] for m in g["metrics"]], "ideas": len(mine),
                      "done": sum(1 for s in order if states[s]["state"] == "done"),
                      "usd": None if spent is None else round(spent, 2), "ideation": ideation,
                      "passed": sum(1 for s in order if states[s]["state"] == "passed") if ideation else 0,
                      "releases_from": releases.releases_from(root, g["slug"]), "wait_release": releases.wait(root, state_dir, g["slug"], made, rel)})
        mine_nodes, today_tasks = [], []
        for i in sorted(mine, key=lambda i: (tier[i["slug"]], place[i["slug"]])):
            slug, st, page = i["slug"], states[i["slug"]], pages[i["slug"]]
            plan = ideas.plan(state_dir, slug)
            tasks = (plan or {}).get("tasks") or []
            asks = ideas.items(page.section("Open questions")) if page else []
            at = ideas.touched_at(root, state_dir, slug)                                # read once: the row's `updated` and its needs' `at`
            needs = idea_needs(root, state_dir, i, st, plan, asks, at) + asked.get(slug, [])
            r = row(root, state_dir, i, st, plan, page, asks, states, needs, at)
            started = any(t.get("state") not in (None, "waiting", "ready", "held") for t in tasks)
            est = (plan or {}).get("estimate")
            waves, rows = map_stage.waves_of(tasks), map_stage.row_of(tasks)
            pitch = pitches.face(root, state_dir, slug, r["state"], target, offered) if ideation else None
            node = {"slug": slug, "goal": g["slug"], "title": i["title"], "short": i["short"], "state": r["state"], "queue": r["queue"],
                    "element": st.get("element") or "", "flag": (flag := flag_of(state_dir, slug, held)), "type": type_of(st),
                    "route": idea_route.route(root, state_dir, slug, page=page, st=st, plan=plan, held=held, flag=flag),
                    "goal_state": idea_route.goal_state(root, state_dir, slug, held) if ideation and r["state"] == "sent" else None,
                    "release": release_of(releasing.get(slug)),
                    "held_until": r["held_until"], **({"held_for": r["held_for"]} if r.get("held_for") else {}),
                    "start_at": r["start_at"], "night_by": r["night_by"], "by_pace": bool((plan or {}).get("by_pace")),
                    "priority": r["priority"], "size": r["size"],
                    "risk": r["risk"], "tier": tier[slug], "depends_on": r["depends_on"], "waits_on": r["waits_on"],
                    "waits_for": collide.waits_for(state_dir, slug, r["depends_on"], g["slug"], track_of, titles, party_names) if r["depends_on"] else [],
                    "waits": None, "needs_you": next((k for k in NEEDS if any(n["kind"] == k for n in needs)), "")
                    if r["state"] != "done" else "",
                    "progress": r["progress"], "done": r["progress"]["done"], "of": r["progress"]["total"],        # k of n done (spec 85 §4)
                    "stage": pitches.stage_of(r["state"], sum(v["answered"] for v in pitch["views"])) if pitch
                    else map_stage.stage_of(r["state"], tasks, bool((plan or {}).get("passed_at"))), "round": map_stage.round_of(tasks),
                    "usd": idea_spend.of_idea(state_dir, slug)["usd"] if tasks else None,
                    "plan_estimate": {"usd_low": est.get("usd_low"), "usd_high": est.get("usd_high")} if isinstance(est, dict) and plan else None,
                    "asked": _asked(st, asks, by_slug, lead, target) if r["state"] == "asks" else [],
                    "tasks": [{"id": t.get("id"), "title": t.get("title") or "", "short": task_short(t), "state": t.get("state") or "waiting",
                               "after": list(t.get("after") or []), "tier": t.get("tier") or "",
                               "head": roles.task_head(state_dir, t, target, read, tiers),
                               "by": _by(t, read), "band": "check" if map_stage.is_check(t) else "build", "wave": waves[str(t.get("id"))],
                               "row": rows[str(t.get("id"))],
                               **_run_of(t), "pick": idea_pick.map_of(t), "shot": idea_shots.map_of(t), "made": made_of(t),
                               "tag": roles.KIND_LABELS.get(str(t.get("kind") or ""), roles.KIND_LABELS[roles.DEFAULT_KIND])} for t in tasks],
                    "checks": idea_checks.status(idea_checks.kept(list_of_dicts(page.get("checks")) if page else [], checks),
                                                 checks, tasks) if checks else [],
                    "estimate": {"usd_low": est.get("usd_low"), "usd_high": est.get("usd_high")}
                    if isinstance(est, dict) and plan and not started else None,
                    "by_itself": bool(plan) and plan.get("passed_by") == "auto",
                    "todo_lines": todo_lines(plan, tasks) if r["state"] in ("plan", "working", "failed") else [],      # the to-dos not yet a stop (spec 87 §4.2)
                    "folded": slug not in kept or r["state"] == "passed", "updated": r["updated"], "pitch": pitch}
            if r["state"] != "done":
                node["waits"] = _waits(node, tasks, titles, r["waits_on"], week)
            nodes.append(node)
            mine_nodes.append(node)
            today_tasks += [t for t in tasks if t.get("state") == "merged" and str(t.get("finished") or "").startswith(today)]
            edges += [{"from": d, "to": slug} for d in r["depends_on"] if d in tier and slug in kept and d in kept]
        cost = sum(float(t["cost"]) for t in today_tasks if isinstance(t.get("cost"), (int, float)))
        goals[-1].update(party=map_party.party_of(goals[-1], mine_nodes), today={"merged": len(today_tasks), "usd": round(cost, 2)},
                         flags=sum(1 for n in mine_nodes if n["flag"]),
                         waits_main=sum(1 for n in mine_nodes if n["state"] == "done" and not n["flag"]))
    return {"goals": goals, "nodes": nodes, "edges": edges, "rev": rev}
