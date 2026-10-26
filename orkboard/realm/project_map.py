"""The Architect's *System* (docs/specs/89-the-tech-lens-system.md §1–§3, decisions §104.1–3): the project's parts as
realm/code_map.py reads them, kept at each landing in dev, laid out in a layout that stays, and what changed between two of
them, each change with the goal that made it (realm/commit_goal.py). Beside the parts a snapshot keeps the overview of the project's
architecture (realm/system_overview.py, spec 90 §6): a snapshot kept before it has `overview` None and gets it at the next `ensure`.

    project_map.snapshot(state_dir, tree, commit)      # <state_dir>/maps/system/<commit>.json: the parts and overview of `tree`, at `commit`
    project_map.landed(state_dir, root, tree, commit)  # the runner's one call after a task landed: a snapshot that never raises
    project_map.ensure(state_dir, root, "dev")         # the snapshot of dev's head, made from a detached worktree when none is kept
    project_map.read(state_dir, commit) / newest(state_dir) / kept(state_dir)
    project_map.place(state_dir, paths)                # the layout (layout.json): each part's column and row, a new part at its column's end
    project_map.rearrange(state_dir, paths)            # *Rearrange*: laid out again, the gone parts' places taken away
    project_map.table(layout, parts, marked, recent)   # the columns as the face lays them: at most 8, 14 cards a column, a stack beyond
    project_map.changed(state_dir, root, since, "dev") # the parts new, gone and changed and the uses new and gone, each with its goal

Read from the files and git, no model, no face. Every git call has fixed arguments (no shell), `--` before a path.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path, PurePosixPath

from orkboard.realm import code_map, commit_goal, event_log, idea_git, system_overview

FOLDER = ("maps", "system")
LAYOUT = "layout.json"
KEEP = 60                            # the newest snapshots kept
COLUMNS = 8                          # the most columns; the smallest areas folded into OTHER
CARDS = 14                           # the most cards a column; beyond, the least changed lie in its stack
OTHER = "Other"
TOP = "."                            # the area (and the part) of the files at the project's top
HISTORY = 5_000                      # the newest commits looked through for a snapshot at or before a commit
TREE = "tree"                        # ensure's detached worktree, `<state_dir>/maps/tree`, removed after
_LOCK = threading.RLock()


# -- the snapshots (§1) -------------------------------------------------------------------------------------------------------------

def folder(state_dir: Path) -> Path:
    return Path(state_dir).joinpath(*FOLDER)


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _json(path: Path) -> dict | None:
    try:
        got = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return got if isinstance(got, dict) else None


def read(state_dir: Path, commit: str) -> dict | None:
    """The snapshot kept for `commit` (a full sha): `{commit, at, taken, parts, overview}`, `overview` None for one kept before spec 90;
    None when none is kept."""
    if not isinstance(commit, str) or not commit_goal.FULL_SHA.fullmatch(commit):
        return None
    got = _json(folder(state_dir) / f"{commit}.json")
    if not (got and got.get("commit") == commit and isinstance(got.get("parts"), list)):
        return None
    return {**got, "overview": got.get("overview") if isinstance(got.get("overview"), dict) else None}


def kept(state_dir: Path) -> list[str]:
    """The commits snapshots are kept for, the newest taken first."""
    rows = []
    for f in folder(state_dir).glob("*.json") if folder(state_dir).is_dir() else []:
        if commit_goal.FULL_SHA.fullmatch(f.stem):
            try:
                rows.append((f.stat().st_mtime_ns, f.stem))
            except OSError:
                continue
    return [c for _t, c in sorted(rows, reverse=True)]


def newest(state_dir: Path) -> dict | None:
    rows = kept(state_dir)
    return read(state_dir, rows[0]) if rows else None


def _at(tree: Path, commit: str) -> str:
    try:
        got = commit_goal.git(tree, "show", "-s", "--format=%cI", commit)
    except (OSError, subprocess.SubprocessError):
        return ""
    return got.stdout.strip() if got.returncode == 0 else ""


def _overview(tree: Path, parts: list[dict]) -> dict:
    """The tree's overview (realm/system_overview.py); an empty one when its files cannot be read."""
    try:
        return system_overview.read(Path(tree), parts)
    except (OSError, ValueError):                                        # the parts stand without it
        return system_overview.empty()


def _fill(state_dir: Path, snap: dict, tree: Path) -> dict:
    """A snapshot kept before spec 90 given its overview, read from `tree` (standing at its commit), its place in the order kept."""
    target = folder(state_dir) / f"{snap['commit']}.json"
    with _LOCK:
        try:
            stamp = target.stat().st_mtime_ns
        except OSError:
            stamp = time.time_ns()
        snap = {**snap, "overview": _overview(tree, snap["parts"])}
        _write(target, snap)
        os.utime(target, ns=(stamp, stamp))
    return snap


def _keep(state_dir: Path, commit: str, at: str, parts: list[dict], overview: dict) -> dict:
    snap = {"commit": commit, "at": at, "taken": time.time(), "parts": parts, "overview": overview}
    with _LOCK:
        target = folder(state_dir) / f"{commit}.json"
        ahead = kept(state_dir)
        last = (folder(state_dir) / f"{ahead[0]}.json").stat().st_mtime_ns if ahead else 0
        _write(target, snap)
        stamp = max(time.time_ns(), last + 1)                     # the order taken, even within the clock's grain
        os.utime(target, ns=(stamp, stamp))
        for old in kept(state_dir)[KEEP:]:
            try:
                (folder(state_dir) / f"{old}.json").unlink()
            except OSError:
                pass
        place(state_dir, [p["path"] for p in parts])
    return snap


def snapshot(state_dir: Path, tree: Path, commit: str) -> dict:
    """The parts of `tree` (a worktree standing at `commit`) and its overview kept as `<state_dir>/maps/system/<commit>.json`, its new
    parts placed in the layout; the newest KEEP kept. A commit already kept is not read again (one kept without an overview gets it).
    ValueError for a commit that is not a full sha."""
    if not isinstance(commit, str) or not commit_goal.FULL_SHA.fullmatch(commit):
        raise ValueError(f"not a commit: {commit!r}")
    got = read(state_dir, commit)
    if got is not None:
        return got if got["overview"] is not None else _fill(state_dir, got, Path(tree))
    parts = code_map.parts(Path(tree))
    return _keep(state_dir, commit, _at(Path(tree), commit), parts, _overview(Path(tree), parts))


def landed(state_dir: Path, root: Path, tree: Path, commit: str, events: bool = True) -> dict | None:
    """After a task landed in dev, on the task's worktree before it is removed (core/idea_runner.py): its snapshot. Never raises: a
    failure is the event `map_snapshot_failed` (commit, why), and None."""
    try:
        return snapshot(state_dir, tree, commit)
    except Exception as e:                       # the map never troubles a landing
        if events:
            event_log.record(Path(root), event_log.MAP_SNAPSHOT_FAILED, commit=str(commit or "")[:12],
                             why=" ".join(str(e).split())[:300] or type(e).__name__)
        return None


def _sources_changed(root: Path, old: str, new: str) -> bool:
    """Whether a file code_map or system_overview reads may differ between two commits (any changed path with a source file's extension,
    a manifest, a page: `system_overview.matters`); True when git cannot say."""
    try:
        got = commit_goal.git(root, "diff", "--name-only", "--no-renames", old, new, "--")
    except (OSError, subprocess.SubprocessError):
        return True
    if got.returncode != 0:
        return True
    return any(system_overview.matters(p.strip('"')) for p in got.stdout.splitlines() if p)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=idea_git.GIT_TIMEOUT_S)


def _remove_tree(root: Path, path: Path) -> None:
    with idea_git.lock_of(root):
        if path.exists() or path.is_symlink():
            _git(root, "worktree", "remove", "--force", str(path))
            if path.is_symlink():
                path.unlink()
            elif path.exists():
                shutil.rmtree(path, ignore_errors=True)
        _git(root, "worktree", "prune")


def ensure(state_dir: Path, root: Path, ref: str = "dev") -> dict | None:
    """The snapshot of `ref`'s head: the one kept; else, when no source file (nor manifest, nor page) changed since the newest kept with
    an overview, that one's parts and overview kept for the head too; else read from a detached worktree of the head
    (`<state_dir>/maps/tree`, removed after), which also gives a head kept before spec 90 its overview. None when `ref` is no branch."""
    root = Path(root)
    tip = commit_goal.head(root, ref)
    if not tip:
        return None
    with _LOCK:
        got = read(state_dir, tip)
        if got is not None and got["overview"] is not None:
            return got
        last = newest(state_dir)
        if got is None and last is not None and last["overview"] is not None and not _sources_changed(root, last["commit"], tip):
            return _keep(state_dir, tip, _at(root, tip), last["parts"], last["overview"])
        path = Path(state_dir) / FOLDER[0] / TREE
        try:
            with idea_git.lock_of(root):
                _remove_tree(root, path)
                path.parent.mkdir(parents=True, exist_ok=True)
                made = _git(root, "worktree", "add", "--detach", str(path), tip)
                if made.returncode != 0:
                    raise RuntimeError("could not make its worktree: " + (made.stderr or made.stdout).strip()[:200])
            return snapshot(state_dir, path, tip)
        finally:
            _remove_tree(root, path)


# -- the layout (§2) ---------------------------------------------------------------------------------------------------------------

def _bits(path: str) -> list[str]:
    return [] if path in ("", TOP) else path.split("/")


def _prefix(paths: list[str]) -> list[str]:
    """The folders every part but the top's lies under. Taken over the parts but the top's, it is also §2's *by their second*: parts
    that are all under one folder (with the top's files beside them) are grouped by the folder under it."""
    rows = [_bits(p) for p in paths if p != TOP]
    if not rows:
        return []
    out = []
    for bits in zip(*rows):
        if len(set(bits)) != 1:
            break
        out.append(bits[0])
    return out


def _area(path: str, prefix: list[str]) -> str:
    """A part's area: the first folder of its path with the prefix taken off (the prefix's own part: its last folder; the top's: TOP)."""
    bits = _bits(path)
    rest = bits[len(prefix):] if bits[:len(prefix)] == prefix else bits
    if not rest:
        return TOP if not bits else bits[-1]
    return rest[0]


def _fresh(paths: list[str]) -> dict:
    """The layout laid out anew: the areas as columns (the top's first, then by name), the smallest folded into Other beyond
    COLUMNS; in a column, the parts by path."""
    paths = sorted(set(paths))
    prefix = _prefix(paths)
    groups: dict[str, list[str]] = {}
    for p in paths:
        groups.setdefault(_area(p, prefix), []).append(p)
    names = sorted(groups, key=lambda a: (a != TOP, a.lower()))
    if len(names) > COLUMNS:
        big = sorted(names, key=lambda a: (-len(groups[a]), a.lower()))[:COLUMNS - 1]
        names = [a for a in names if a in big] + [OTHER]
    areas = {a: (a if a in names else OTHER) for a in groups}
    places: dict[str, dict] = {}
    for col in names:
        mine = sorted(p for p in paths if areas[_area(p, prefix)] == col)
        places.update({p: {"column": col, "row": n} for n, p in enumerate(mine)})
    return {"prefix": prefix, "columns": names, "areas": areas, "parts": places}


def _layout_file(state_dir: Path) -> Path:
    return folder(state_dir) / LAYOUT


def layout(state_dir: Path) -> dict:
    """The layout kept (`{prefix, columns, areas, parts: {path: {column, row}}}`); an empty one when none is."""
    got = _json(_layout_file(state_dir)) or {}
    ok = isinstance(got.get("columns"), list) and isinstance(got.get("parts"), dict) and isinstance(got.get("areas"), dict)
    return got if ok else {"prefix": [], "columns": [], "areas": {}, "parts": {}}


def _put(lay: dict, path: str) -> None:
    """A part seen for the first time: the next row of its area's column. An area with no column yet takes a new one while there are
    fewer than COLUMNS, else goes to Other (the smallest column becomes Other when there is none)."""
    area = _area(path, list(lay.get("prefix") or []))
    cols, places = lay["columns"], lay["parts"]
    col = lay["areas"].get(area)
    if col not in cols:
        if len(cols) < COLUMNS and area not in cols:
            col = area
            cols.append(col)
        else:
            if OTHER not in cols:
                size = {c: sum(1 for v in places.values() if v["column"] == c) for c in cols}
                small = min(reversed(cols), key=lambda c: size[c])
                cols[cols.index(small)] = OTHER
                for v in places.values():
                    if v["column"] == small:
                        v["column"] = OTHER
                lay["areas"] = {a: (OTHER if c == small else c) for a, c in lay["areas"].items()}
            col = OTHER
        lay["areas"][area] = col
    rows = [v["row"] for v in places.values() if v["column"] == col]
    places[path] = {"column": col, "row": max(rows) + 1 if rows else 0}


def place(state_dir: Path, paths: list[str]) -> dict:
    """The layout with every part of `paths` placed (the first time: laid out anew); written when it changed. A gone part keeps its
    place until `rearrange`."""
    with _LOCK:
        lay = layout(state_dir)
        if not lay["parts"]:
            lay = _fresh(paths) if paths else lay
        else:
            for p in sorted(set(paths) - set(lay["parts"])):
                _put(lay, p)
        if lay != layout(state_dir):
            _write(_layout_file(state_dir), lay)
        return lay


def rearrange(state_dir: Path, paths: list[str]) -> dict:
    """*Rearrange* (the person's press): the parts of `paths` laid out anew, the gone parts' places taken away."""
    with _LOCK:
        lay = _fresh(paths)
        _write(_layout_file(state_dir), lay)
        return lay


def name_of(path: str, project: str = "") -> str:
    """A part's name: its folder's, as it is (the top's: the project's folder)."""
    return (project or TOP) if path == TOP else path.rsplit("/", 1)[-1]


def table(lay: dict, parts: dict[str, dict], marked: set[str] | None = None, recent: dict[str, str] | None = None,
          project: str = "") -> list[dict]:
    """The columns as the face lays them: `[{name, parts: [{path, name, count, uses, used_by, row, gone}], stack: [...]}]`, in the
    layout's order, each column's cards by row. `parts`: the parts shown by path (a gone one with `gone`: True). A column of more than
    CARDS parts shows the CARDS most changed (`marked` first, then the newest `recent` time, then by row) and stacks the rest."""
    marked, recent = marked or set(), recent or {}
    out = []
    for col in lay.get("columns") or []:
        rows = sorted((v["row"], p) for p, v in (lay.get("parts") or {}).items() if v.get("column") == col and p in parts)
        cards, stack = rows, []
        if len(rows) > CARDS:
            ranked = sorted(rows)                                           # stable sorts: by row, then the newest change, marked first
            ranked.sort(key=lambda r: recent.get(r[1], ""), reverse=True)
            ranked.sort(key=lambda r: r[1] not in marked)
            keep = {p for _r, p in ranked[:CARDS]}
            cards, stack = [r for r in rows if r[1] in keep], [r for r in rows if r[1] not in keep]

        def card(row: int, path: str) -> dict:
            p = parts[path]
            return {"path": path, "name": name_of(path, project), "count": int(p.get("count") or 0), "uses": list(p.get("uses") or []),
                    "used_by": list(p.get("used_by") or []), "row": row, "gone": bool(p.get("gone"))}
        out.append({"name": name_of(col, project) if col == TOP else col,
                    "parts": [card(r, p) for r, p in cards], "stack": [card(r, p) for r, p in stack]})
    return out


# -- what changed (§3) -------------------------------------------------------------------------------------------------------------

def at_or_before(state_dir: Path, root: Path, sha: str) -> dict | None:
    """The newest snapshot kept whose commit is `sha` or one of its ancestors (among the newest HISTORY commits)."""
    have = set(kept(state_dir))
    if not have or not commit_goal.FULL_SHA.fullmatch(sha or ""):
        return None
    if sha in have:
        return read(state_dir, sha)
    try:
        got = commit_goal.git(root, "rev-list", f"-n{HISTORY}", sha, "--")
    except (OSError, subprocess.SubprocessError):
        return None
    for line in got.stdout.splitlines() if got.returncode == 0 else []:
        if line in have:
            return read(state_dir, line)
    return None


def _part_of(file: str) -> str:
    parent = PurePosixPath(file).parent.as_posix()
    return TOP if parent in ("", ".") else parent


def nothing(commit: str = "") -> dict:
    return {"since": "", "commit": commit, "parts": {}, "uses": []}


def changed(state_dir: Path, root: Path, since: object, ref: str = "dev") -> dict:
    """What changed since the person's last look: `{since, commit, parts: {path: {kind, goal, task, sha, at}}, uses: [{from, to, kind,
    goal, task, sha, at}]}`. `since` (a commit of `ref`, or a time) is read as the newest snapshot at or before it; `commit` is `ref`'s
    snapshot (else the newest kept). A part is **new** in `ref`'s snapshot and not in `since`'s, **gone** the reverse, **changed** when a
    file in its folder is in `git diff <since>..<commit>`; each with the goal and task of the last commit that touched it there
    (commit_goal: `goal` "" is the person's own, *By you*). No `since`, or no snapshot at or before it: nothing is marked."""
    root = Path(root)
    tip = commit_goal.head(root, ref)
    now = (read(state_dir, tip) if tip else None) or newest(state_dir)
    if now is None:
        return nothing()
    sha = commit_goal.resolve(root, since, ref) if since else ""
    before = at_or_before(state_dir, root, sha) if sha else None
    if before is None:
        return nothing(now["commit"])
    out = {**nothing(now["commit"]), "since": before["commit"]}
    if before["commit"] == now["commit"]:
        return out
    try:
        got = commit_goal.git(root, "diff", "--name-only", "--no-renames", before["commit"], now["commit"], "--")
        files = [f for f in got.stdout.splitlines() if f and not f.startswith('"')] if got.returncode == 0 else []
    except (OSError, subprocess.SubprocessError):
        files = []
    under: dict[str, list[str]] = {}
    for f in files:
        under.setdefault(_part_of(f), []).append(f)
    touch = commit_goal.last_touch(root, ref, before["commit"]) if tip else {}
    goals = commit_goal.index(state_dir, root, ref)

    def last(part: str) -> dict:
        rows = [touch[f] for f in under.get(part, []) if f in touch]
        if not rows:
            return {"goal": "", "task": "", "sha": "", "at": ""}
        hit = max(rows, key=lambda r: r["at"])
        g = goals.get(hit["sha"]) or {}
        return {"goal": g.get("goal", ""), "task": g.get("task", ""), "sha": hit["sha"], "at": hit["at"]}

    a = {p["path"]: p for p in before["parts"]}
    b = {p["path"]: p for p in now["parts"]}
    for path in sorted(set(a) | set(b)):
        kind = "new" if path not in a else "gone" if path not in b else "changed" if under.get(path) else ""
        if kind:
            out["parts"][path] = {"kind": kind, **last(path)}
    was = {(p, u) for p, row in a.items() for u in row.get("uses") or []}
    is_ = {(p, u) for p, row in b.items() for u in row.get("uses") or []}
    for kind, pairs in (("new", is_ - was), ("gone", was - is_)):
        for frm, to in sorted(pairs):
            out["uses"].append({"from": frm, "to": to, "kind": kind, **last(frm)})
    return out


def commits_of(root: Path, ref: str, since: str, files: list[str], limit: int = 200) -> list[dict]:
    """`[{sha, at}]` of the commits of `since..ref` that touched any of `files`, the oldest first (for a part's changes)."""
    tip = commit_goal.head(root, ref)
    if not tip or not files or not commit_goal.FULL_SHA.fullmatch(since or ""):
        return []
    try:
        got = commit_goal.git(root, "--literal-pathspecs", "log", "--no-renames", f"-n{limit}", "--format=%H %cI",
                              f"{since}..{tip}", "--", *files[:limit])
    except (OSError, subprocess.SubprocessError):
        return []
    rows = [line.split(" ", 1) for line in got.stdout.splitlines() if " " in line] if got.returncode == 0 else []
    return [{"sha": s, "at": t} for s, t in reversed(rows) if commit_goal.FULL_SHA.fullmatch(s)]


def files_under(root: Path, since: str, commit: str, part: str) -> list[str]:
    """The files of `part`'s folder (not its sub-folders) that differ between two commits."""
    try:
        got = commit_goal.git(root, "diff", "--name-only", "--no-renames", since, commit, "--")
    except (OSError, subprocess.SubprocessError):
        return []
    return [f for f in got.stdout.splitlines() if f and not f.startswith('"') and _part_of(f) == part] if got.returncode == 0 else []
