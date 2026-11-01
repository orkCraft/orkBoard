"""While you were away (docs/specs/42-coming-back.md §1): what the Board did since a device's last look, as data. A pure
read of the event log and the ledgers: no face, no model, it writes nothing, starts nothing and moves nothing.

    board_recap.build(root, state_dir, since, now, rows)      # §1.1's object
    board_recap.when("2026-10-20T09:00:00+02:00")             # a log's time or a ledger's, as a datetime
    board_recap.night(root, state_dir, since, now, rows, into="dev", hints=None)   # the morning's card (spec 121 §5.2): the recap cut to the night, each goal with the screens it changed
    board_recap.night_since(settings, now, seen=None)         # …where that starts: the last night's window or the device's last look, whichever is later

`flags` holds a party's old flags (`goal_accepted`: `{goal, short, title, met, by}`) and then the goals' (`idea_flagged`, spec 50
§2.4: the same fields and the goal's `idea`, `goal` being its party; a face reads one "⚑ <goal> is in main"). `root` is the project's
folder (where the event log is). `rows`: the Board's `{"ideas": [...], "tracks": [...]}` (`ideas.board`), for titles and short names;
an idea or a party the Board no longer has is left out of every list. Times are never compared as text.
"""
from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path
from typing import Any

from orkboard.realm import event_log, idea_spend, ideas

LOOK_BACK = dt.timedelta(days=1)         # the log is read from a day earlier (its lines carry an offset), then cut exactly


def when(text: object) -> dt.datetime | None:
    """A time as the log writes it (local ISO with an offset) or a ledger does (local, naive); None when it is neither."""
    try:
        got = dt.datetime.fromisoformat(str(text or ""))
    except ValueError:
        return None
    return got.astimezone()


def events_between(root: Path, since: dt.datetime, now: dt.datetime, *names: str) -> list[dict]:
    """The log's lines of these events whose time is in `[since, now)`, oldest first."""
    coarse = (since - LOOK_BACK).strftime("%Y-%m-%d")
    out = []
    for r in event_log.read(root, since=coarse):
        at = when(r.get("at"))
        if r.get("event") in names and at is not None and since <= at < now:
            out.append(r)
    return sorted(out, key=lambda r: when(r.get("at")))


def merges(events: list[dict]) -> tuple[int, int]:
    """(merged, merged the first time) over `task_state` lines: the person's merge and a result that lands by itself
    both write one; the first time is round 1. A check that found nothing (`clean`) is no result (spec 43 §1.4)."""
    merged = [r for r in events if r.get("state") == "merged" and r.get("clean") is not True]
    return len(merged), sum(1 for r in merged if int(r.get("round") or 1) <= 1)


def _int(value: object) -> int:
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def idea_flags(log: list[dict], by_idea: dict[str, dict]) -> list[dict]:
    """The goals that raised their flag in `log` (spec 50 §2.4), oldest first, each once: `{goal (its party), idea, short, title,
    met: True, by ("gate" · "done")}`. A goal the Board no longer has is left out. A party's old flag (`goal_accepted`) has no
    `idea`; it keeps its own line."""
    out: dict[str, dict] = {}
    for r in log:
        slug = str(r.get("idea") or "")
        if r["event"] == event_log.IDEA_FLAGGED and slug in by_idea and slug not in out:
            i = by_idea[slug]
            out[slug] = {"goal": i.get("track") or str(r.get("goal") or ""), "idea": slug, "short": i.get("short") or i.get("title") or slug,
                         "title": i.get("title") or slug, "met": True, "by": str(r.get("by") or "")}
    return list(out.values())


def build(root: Path, state_dir: Path, since: dt.datetime, now: dt.datetime, rows: dict, into: str = "dev") -> dict[str, Any]:
    from orkboard.realm.board_map import task_short           # board_map reads goal_flags, which reads `when`
    by_idea = {i["slug"]: i for i in rows.get("ideas") or []}
    by_goal = {g["slug"]: g for g in rows.get("tracks") or []}
    log = events_between(root, since, now, event_log.TASK_STATE, event_log.GOAL_ACCEPTED, event_log.IDEA_FLAGGED, event_log.NIGHT_RUN,
                         event_log.PROPOSAL_MADE)

    def idea(slug: str) -> dict:
        i = by_idea[slug]
        return {"slug": slug, "short": i.get("short") or i.get("title") or slug, "title": i.get("title") or slug, "goal": i.get("track") or ""}

    states = [r for r in log if r["event"] == event_log.TASK_STATE]
    tasks, first = merges(states)
    mine: list[str] = []
    for r in states:
        slug = str(r.get("idea") or "")
        if r.get("state") == "merged" and r.get("clean") is not True and slug in by_idea and slug not in mine:
            mine.append(slug)
    done = [{**idea(s), "done": by_idea[s].get("state") == "done"} for s in mine]

    accepted: dict[str, dict] = {}
    for r in log:
        if r["event"] == event_log.GOAL_ACCEPTED and str(r.get("goal") or "") in by_goal:
            accepted[str(r["goal"])] = r
    flags = [{"goal": g, "short": by_goal[g].get("short") or by_goal[g].get("title") or g, "title": by_goal[g].get("title") or g,
              "met": bool(r.get("met")), "by": str(r.get("by") or "")} for g, r in accepted.items()]
    flags += idea_flags(log, by_idea)                       # a goal's flag reads "⚑ <goal> is in main" (spec 50 §2.4)

    sums = {k: sum(_int(r.get(k)) for r in log if r["event"] == event_log.NIGHT_RUN) for k in ("drafted", "started", "refreshed", "proposed")}
    night = sums if any(sums.values()) else None

    proposed: list[dict] = []
    for r in log:
        slug = str(r.get("idea") or "")
        if r["event"] == event_log.PROPOSAL_MADE and slug in by_idea and by_idea[slug].get("state") == "proposed" \
                and not any(p["slug"] == slug for p in proposed):
            proposed.append(idea(slug))

    failed: list[dict] = []
    for r in states:
        slug, tid = str(r.get("idea") or ""), str(r.get("task") or "")
        if r.get("state") != "failed" or slug not in by_idea or any(f["slug"] == slug and f["_id"] == tid for f in failed):
            continue
        task = next((t for t in (ideas.plan(state_dir, slug) or {}).get("tasks") or [] if t.get("id") == tid), None)
        if task is not None and task.get("state") == "failed":
            failed.append({**{k: idea(slug)[k] for k in ("slug", "short", "title")}, "task": task_short(task), "_id": tid})
    for f in failed:
        f.pop("_id")

    spent = idea_spend.between(state_dir, since, now)
    out = {"since": since.isoformat(timespec="seconds"), "hours": max(0, round((now - since).total_seconds() / 3600)), "into": into,
           "merged": {"tasks": tasks, "first_time": first, "ideas": done}, "flags": flags, "night": night, "proposed": proposed,
           "failed": failed, "usd": None if spent is None else round(spent, 2), "nights": 0, "waits": {"you": 0, "review": 0}}
    out["empty"] = not (tasks or flags or proposed or failed or night)
    return out


# -- the night (docs/specs/121-the-day-the-morning-and-the-night.md §5.2) --------------------------------------------------------------

NIGHT_ROWS = 20                          # the most a list of the night's record holds
WHY_MAX = 200                            # a failed task's reason, at most
NO_WINDOW = dt.timedelta(hours=12)       # the morning's record reaches this far back when the Board has no night window and the device no last look


def night_start(settings: dict, now: dt.datetime) -> dt.datetime | None:
    """When the last night's window opened (the night in progress counts): the latest start of the Board's `night` window at or before `now`; None when the Board has no window."""
    from orkboard.realm import board_week           # board_week reads this module's `when`
    win = board_week.window((settings or {}).get("night"))
    if win is None:
        return None
    a, b = win
    now = now.astimezone()
    for k in (1, 0, -1):                            # a window that crosses midnight starts the day before the day it ends on
        midnight = dt.datetime.combine(now.date() + dt.timedelta(days=k), dt.time())
        start = ((midnight if a < b else midnight - dt.timedelta(days=1)) + dt.timedelta(minutes=a)).astimezone()
        if start <= now:
            return start
    return None


def night_since(settings: dict, now: dt.datetime, seen: dt.datetime | None = None) -> dt.datetime:
    """Where the morning's record starts: the last night's window or the device's last look, whichever is later (twelve hours back when the Board has no window and the device no look)."""
    start = night_start(settings, now) or now - NO_WINDOW
    return max(start, seen.astimezone()) if seen is not None else start


def _cut(text: object, n: int) -> str:
    one = " ".join(str(text or "").split())
    return one if len(one) <= n else one[:n - 1].rstrip() + "…"


def _reverts(root: Path, into: str, since: dt.datetime, now: dt.datetime) -> list[dict]:
    """The commits of `into` made in `[since, now)` whose subject begins `Revert`, newest first: `{sha (seven), subject, at}`."""
    from orkboard.realm import commit_goal
    if not commit_goal.head(root, into):
        return []
    try:
        got = commit_goal.git(root, "log", f"--since={since.isoformat()}", f"--until={now.isoformat()}", "--format=%H%x1f%s%x1f%cI", f"refs/heads/{into}", "--")
    except (OSError, subprocess.SubprocessError):
        return []
    out = []
    for line in got.stdout.splitlines() if got.returncode == 0 else []:
        sha, _, rest = line.partition("\x1f")
        subject, _, at = rest.partition("\x1f")
        made = when(at)
        if subject.startswith("Revert") and made is not None and since <= made < now:
            out.append({"sha": sha[:7], "subject": _cut(subject, 120), "at": at})
    return out[:NIGHT_ROWS]


def night(root: Path, state_dir: Path, since: dt.datetime, now: dt.datetime, rows: dict, into: str = "dev", hints: list[dict] | None = None) -> dict[str, Any]:
    """The recap of spec 42 cut to the night (`since`: `night_since`), for the morning's card: `{since, hours, into, goals, failed, reverts, checks, play, empty}`.
    `goals` are the goals that reached `into` in the window, each `{slug, short, title, goal, done, screens}` (`realm/goal_screens.py`: the screens their merged tasks changed, with their route paths);
    `failed` the tasks that failed and have not been mended, `{slug, short, title, task, why}`; `reverts` the commits of `into` that begin `Revert`; `checks` the tasks whose last gate was red and that
    have not landed, `{slug, short, title, task, check}`; `play` `{hints: [{kind, words, on}]}` of the last play's hints (`hints`, from `realm/play_signals.py`), None with none. `empty`: no goal, failure,
    revert or red check (a play's hints alone make no card). A goal the Board no longer has is left out of every list."""
    from orkboard.realm import goal_screens
    from orkboard.realm.board_map import task_short
    by_idea = {i["slug"]: i for i in rows.get("ideas") or []}
    log = events_between(root, since, now, event_log.TASK_STATE, event_log.RESULT_READY, event_log.GATE_RAN)

    def names(slug: str) -> dict:
        i = by_idea[slug]
        return {"slug": slug, "short": i.get("short") or i.get("title") or slug, "title": i.get("title") or slug}

    def plan_task(slug: str, tid: str) -> dict | None:
        return next((t for t in (ideas.plan(state_dir, slug) or {}).get("tasks") or [] if isinstance(t, dict) and t.get("id") == tid), None)

    states = [r for r in log if r["event"] == event_log.TASK_STATE]
    reached: list[str] = []
    for r in states:
        slug = str(r.get("idea") or "")
        if r.get("state") == "merged" and r.get("clean") is not True and slug in by_idea and slug not in reached:
            reached.append(slug)
    goals = [{**names(s), "goal": by_idea[s].get("track") or "", "done": by_idea[s].get("state") == "done",
              "screens": goal_screens.of(state_dir, root, s, into)} for s in reached][:NIGHT_ROWS]

    failed: list[dict] = []
    for r in states:
        slug, tid = str(r.get("idea") or ""), str(r.get("task") or "")
        if r.get("state") != "failed" or slug not in by_idea:
            continue
        task = plan_task(slug, tid)
        if task is not None and task.get("state") == "failed" and not any(f["slug"] == slug and f["_id"] == tid for f in failed):
            failed.append({**names(slug), "task": task_short(task), "why": _cut(task.get("error") or r.get("error"), WHY_MAX), "_id": tid})
    for f in failed:
        f.pop("_id")

    last: dict[tuple[str, str], dict] = {}
    for r in log:                                    # the log is oldest first: the last gate of a task is the one that stands
        if r["event"] in (event_log.RESULT_READY, event_log.GATE_RAN) and r.get("verdict"):
            last[(str(r.get("idea") or ""), str(r.get("task") or ""))] = r
    checks: list[dict] = []
    for (slug, tid), r in last.items():
        task = plan_task(slug, tid) if slug in by_idea else None
        if r.get("verdict") == "red" and task is not None and task.get("state") not in ("merged", "dropped"):
            checks.append({**names(slug), "task": task_short(task), "check": _cut(r.get("command") or "", 120)})

    reverts = _reverts(Path(root), into, since, now)
    play = {"hints": [{"kind": str(h.get("kind") or ""), "words": _cut(h.get("words"), 200), "on": (h.get("on") or {}).get("selector", "") if isinstance(h.get("on"), dict) else ""}
                      for h in hints[:NIGHT_ROWS] if isinstance(h, dict)]} if hints else None
    return {"since": since.isoformat(timespec="seconds"), "hours": max(0, round((now - since).total_seconds() / 3600)), "into": into, "goals": goals, "failed": failed[:NIGHT_ROWS],
            "reverts": reverts, "checks": checks[:NIGHT_ROWS], "play": play, "empty": not (goals or failed or reverts or checks)}
