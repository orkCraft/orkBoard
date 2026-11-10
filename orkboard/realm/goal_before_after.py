"""A goal's work before and after, where the code keeps both (docs/specs/168-the-window-played-as-a-card-games-table.md G2, decisions §283.16.11). By code, no model, nothing written.

    goal_before_after.system(state_dir, root, slug, ref)   # Tech's System by commit: {kind: "parts", before, after, parts: [...], none}
    goal_before_after.shots(state_dir, root, slug, ref)    # Design's screens: [{screen, name, path, before, after}] each a picture or None
    goal_before_after.of(state_dir, root, slug, ref, crafts)   # {party: one of them} for each party whose craft keeps both

**Tech's System.** The System is kept as a snapshot at each landing in dev (realm/project_map.py). The goal's commits are those `commit_goal.index` says its tasks brought; *before* is the newest snapshot at or before the parent of the earliest
of them, *after* the newest at or before the latest. `parts` are the parts the goal's files are in (the folders, as `goal_result.touched`), each with its file count and the parts it uses before and after, and `change`: `new`, `gone`, `changed` (its files
or its uses differ) or `same`. With no snapshot from before the goal `before` is None and every part says what it is after, `none` saying why: nothing is compared that was not kept.

**Design's shots.** A task that changed what people see keeps a picture (realm/idea_shots.py). A screen the goal changed (`goal_screens.of`) has as *after* the newest picture of a task of the goal that changed its component's file, as *before* the newest
picture of any other goal's task on that file taken before the goal's first one. A picture is `{goal, task, id, file, w, h, at}` (the host signs its address); None where none was kept.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from orkboard.realm import commit_goal, goal_screens, ideas, project_map, screen_map

PARTS_MAX = 14
TECH, DESIGN = "tech", "design"


def _git(root: Path, *args: str) -> str:
    try:
        got = commit_goal.git(root, *args)
    except (OSError, subprocess.SubprocessError):
        return ""
    return got.stdout.strip() if got.returncode == 0 else ""


def _stamp(snap: dict | None) -> dict | None:
    return {"commit": snap["commit"], "short": snap["commit"][:7], "at": str(snap.get("at") or "")} if snap else None


def _row(path: str, root: Path, a: dict | None, b: dict | None) -> dict:
    """One part: its file count and uses before (`a`) and after (`b`)."""
    ua, ub = list((a or {}).get("uses") or []), list((b or {}).get("uses") or [])
    change = "new" if a is None and b is not None else "gone" if b is None and a is not None else \
        "changed" if (a or {}).get("count") != (b or {}).get("count") or set(ua) != set(ub) else "same"
    return {"path": path, "name": project_map.name_of(path, root.name),
            "before": None if a is None else {"count": int(a.get("count") or 0), "uses": ua}, "after": None if b is None else {"count": int(b.get("count") or 0), "uses": ub},
            "change": change, "uses_new": sorted(set(ub) - set(ua)), "uses_gone": sorted(set(ua) - set(ub))}


def system(state_dir: Path, root: Path, slug: str, ref: str = "dev") -> dict | None:
    """Tech's System before and after the goal, see the module; None when no commit of the goal is in `ref`."""
    root = Path(root)
    shas = [s for s, who in commit_goal.index(Path(state_dir), root, ref).items() if who.get("goal") == slug]
    if not shas:
        return None
    tip = commit_goal.head(root, ref)
    place = {sha: i for i, (sha, _p) in enumerate(commit_goal._history(root, tip))}            # parents before children: the order they landed in
    shas = sorted((s for s in shas if s in place), key=place.get)
    if not shas:
        return None
    first, full_last = shas[0], shas[-1]
    parent = _git(root, "rev-parse", f"{first}^")
    before = project_map.at_or_before(Path(state_dir), root, parent) if commit_goal.FULL_SHA.fullmatch(parent) else None
    after = project_map.at_or_before(Path(state_dir), root, full_last) if commit_goal.FULL_SHA.fullmatch(full_last) else None
    out = {"kind": "parts", "before": _stamp(before), "after": _stamp(after), "parts": [], "none": ""}
    if after is None:
        out["none"] = "the System was not kept when this goal landed"
        return out
    out["none"] = "" if before is not None else "the System was not kept from before this goal"
    touched = {project_map._part_of(f) for f in goal_screens.goal_files(Path(state_dir), root, slug, ref)}
    a = {p["path"]: p for p in (before or {}).get("parts") or []}
    b = {p["path"]: p for p in after["parts"]}
    rows = [_row(p, root, a.get(p), b.get(p)) for p in sorted(touched) if p in a or p in b]
    order = {"new": 0, "gone": 1, "changed": 2, "same": 3}
    out["parts"] = sorted(rows, key=lambda r: (order[r["change"]], r["path"]))[:PARTS_MAX]
    return out


def _all_shots(state_dir: Path, root: Path, files: set[str]) -> dict[str, list[dict]]:
    """Every picture of a task that landed, by each of `files` its commit changed: `{file: [picture]}`, the newest first."""
    folder = Path(state_dir) / "ideas"
    out: dict[str, list[dict]] = {}
    if not folder.is_dir():
        return out
    cache: dict[str, set[str]] = {}
    for d in sorted(folder.iterdir()):
        if not d.is_dir():
            continue
        for t in (ideas.plan(state_dir, d.name) or {}).get("tasks") or []:
            shot = t.get("shot") if isinstance(t, dict) else None
            sha = str(t.get("commit") or "") if isinstance(t, dict) else ""
            if not isinstance(shot, dict) or shot.get("none") or not isinstance(shot.get("id"), str) or not isinstance(shot.get("file"), str) or not commit_goal.FULL_SHA.fullmatch(sha):
                continue
            pic = {"goal": d.name, "task": str(t.get("id") or ""), "id": shot["id"], "file": shot["file"], "w": shot.get("w"), "h": shot.get("h"), "at": str(shot.get("at") or "")}
            for f in files & screen_map._changed_files(root, sha, cache):
                out.setdefault(f, []).append(pic)
    for rows in out.values():
        rows.sort(key=lambda p: p["at"], reverse=True)
    return out


def shots(state_dir: Path, root: Path, slug: str, ref: str = "dev") -> list[dict]:
    """Design's screens the goal changed with the picture before and after each, see the module."""
    root = Path(root)
    screens = goal_screens.of(Path(state_dir), root, slug, ref)
    flow = screen_map.flow(root, ref) if screens else None
    if not screens or flow is None:
        return []
    file_of = {s["id"]: s["file"] for s in flow["screens"]}
    pics = _all_shots(Path(state_dir), root, {f for f in (file_of.get(s["screen"]) for s in screens) if f})
    out = []
    for s in screens:
        rows = pics.get(file_of.get(s["screen"]) or "", [])
        mine = [p for p in rows if p["goal"] == slug]
        after = mine[0] if mine else None
        began = min((p["at"] for p in mine), default="")
        before = next((p for p in rows if p["goal"] != slug and (not began or p["at"] < began)), None) if after else None
        out.append({**s, "before": before, "after": after})
    return out


def of(state_dir: Path, root: Path, slug: str, ref: str, crafts: dict[str, str]) -> dict[str, dict]:
    """`{party: …}` for each party whose craft keeps both (Tech's System, Design's shots); a read that fails leaves the party out."""
    out: dict[str, dict] = {}
    for party, craft in crafts.items():
        try:
            if craft == TECH:
                got = system(state_dir, root, slug, ref)
                if got is not None:
                    out[party] = got
            elif craft == DESIGN:
                out[party] = {"kind": "screens", "screens": shots(state_dir, root, slug, ref)}
        except (OSError, ValueError, subprocess.SubprocessError):
            continue
    return out
