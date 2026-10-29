"""What a party's map says is wrong, by code (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §2.2; decisions §183.4): the hints a leader is given before it looks at its map, each
grounded in what the map holds. A hint is not a verdict (the leader judges it, `core/idea_concerns.py`). Read from the files, the Board and git; no model, no face; nothing is written.

    map_signals.signals(state_dir, root, craft, pages=None, ref="dev")     # [{on, kind, words}], at most MAX_SIGNALS; [] for a craft that has none by code or a map that cannot be read
    map_signals.pictures(state_dir, root, since="", limit=4)               # Design's screens' pictures kept after `since`, to be read: [{id, name, path, at}]

`on` is the id of a part of the map as it is drawn (`realm/map_parts.py`), "" where a hint belongs to no part; `kind` names the rule; `words` is a line for a model, in plain English. A hint that
is about a part of another map (a pain piled on a screen) also has `map` (that map's id). By craft (the craft of the party, as `map_text.of` takes it):
- `tech` (System, from the newest snapshot of the ref): `cycle` (parts that use one another in a loop), `fan_in` (a part used by FAN_IN parts or more), `fan_out` (one using FAN_OUT or more),
  `big` (a part holding a source file of BIG_LINES lines or more, counted at the ref's head), `shared_churn` (a part two containers or more share, changed in the last CHURN_DAYS days in commits
  that also touched files of SHARED_FROM containers or more other than the part's own files), `untested_churn` (a part changed CHURN_TIMES times in the last CHURN_DAYS days with no test mapped
  to it: none by the gate's map (`gate_config.gate_files`), none named after one of its files, none inside it).
- `game-design` (the loop): `loop.findings_on`, each on the loop's step or the currency it names.
- `design` (the screens): `loose` (a screen nothing leads to), `dead_end` (one that leads nowhere and is not where the flow ends), `no_picture` (one with no picture kept).
- `product` (the tree): `unserved` (a job no goal serves), `pains` (a screen or a step with PAINS_PILED pains or more pinned: on that screen, `map` "screens"), `pain_loose` (pains pinned to no
  screen or step: `on` "").
- `art`, `release`, `marketing`: none by code yet; their leader reads the map alone.
"""
from __future__ import annotations

import dataclasses
import re
import subprocess
from pathlib import Path, PurePosixPath

from orkboard.realm import code_map, commit_goal, gate_config, idea_lens, loop, opportunity_tree, project_map, screen_map, system_overview

MAX_SIGNALS = 20
FAN_IN, FAN_OUT = 8, 12             # a part used by this many parts, one using this many
BIG_LINES = 800                     # a source file this long
CHURN_DAYS, CHURN_TIMES = 30, 6     # a part changed this many times in this many days
SHARED_FROM = 2                     # a shared part changed from this many containers
PAINS_PILED = 3                     # pains pinned to one screen or step
TESTS = ("tests", "test", "__tests__", "spec")
ORDER = ("cycle", "fan_in", "fan_out", "big", "shared_churn", "untested_churn")
_SOURCE = tuple(f"*{e}" for e in sorted(code_map.PY | code_map.JS))
_TEST_NAME = re.compile(r"(?:^test_.+|.+_test|.+\.test|.+\.spec)$")


def _git(root: Path, *args: str) -> str:
    try:
        got = commit_goal.git(Path(root), *args)
    except (OSError, subprocess.SubprocessError):
        return ""
    return got.stdout if got.returncode == 0 else ""


def _part(path: str) -> str:
    """The part a file lies in: its folder (`code_map`'s rule), "." at the project's top."""
    return PurePosixPath(path).parent.as_posix()


def _in_skipped(path: str) -> bool:
    return any(bit in code_map.SKIP for bit in path.split("/")[:-1])


# -- Tech: System ---------------------------------------------------------------------------------------------------------------------

def cycles(uses: dict[str, list[str]]) -> list[list[str]]:
    """The groups of two parts or more that use one another round and round (strongly connected components), each sorted, in order of their first part."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on: set[str] = set()
    out: list[list[str]] = []
    count = 0
    for start in sorted(uses):
        if start in index:
            continue
        work = [(start, iter(sorted(t for t in uses.get(start, []) if t in uses)))]
        index[start] = low[start] = count
        count += 1
        stack.append(start)
        on.add(start)
        while work:
            node, it = work[-1]
            for nxt in it:
                if nxt not in index:
                    index[nxt] = low[nxt] = count
                    count += 1
                    stack.append(nxt)
                    on.add(nxt)
                    work.append((nxt, iter(sorted(t for t in uses.get(nxt, []) if t in uses))))
                    break
                if nxt in on:
                    low[node] = min(low[node], index[nxt])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == index[node]:
                    group = []
                    while True:
                        top = stack.pop()
                        on.discard(top)
                        group.append(top)
                        if top == node:
                            break
                    if len(group) >= 2:
                        out.append(sorted(group))
    return sorted(out)


def _lines(root: Path, sha: str) -> dict[str, tuple[str, int]]:
    """`{part: (its longest source file, its lines)}` at `sha` (git grep counts the lines; a binary file is skipped)."""
    best: dict[str, tuple[str, int]] = {}
    for row in _git(root, "grep", "-I", "-c", "", sha, "--", *_SOURCE).splitlines():
        head, _sep, n = row.rpartition(":")
        path = head[len(sha) + 1:] if head.startswith(sha + ":") else head
        if not n.isdigit() or _in_skipped(path):
            continue
        part = _part(path)
        if int(n) > best.get(part, ("", 0))[1]:
            best[part] = (PurePosixPath(path).name, int(n))
    return best


def _churn(root: Path, sha: str) -> list[list[str]]:
    """The files each commit of the last CHURN_DAYS days changed (merges apart), newest first."""
    out = _git(root, "log", sha, f"--since={CHURN_DAYS}.days.ago", "--no-merges", "--name-only", "--format=%x1e")
    return [[f for f in chunk.splitlines() if f.strip()] for chunk in out.split("\x1e")[1:]]


def _tracked(root: Path, sha: str) -> list[str]:
    return [p for p in _git(root, "ls-tree", "-r", "--name-only", sha).splitlines() if p]


def _tested(part: str, files: list[str], tracked: set[str], gate: gate_config.Gate, root: Path) -> bool:
    """A test is mapped to the part: the gate's map finds one for a file of it, a file of it is a test or lies in a tests folder, or a test is named after one of its files."""
    if any(bit in TESTS for bit in part.split("/")):
        return True
    names = [PurePosixPath(f).name for f in files]
    if any(_TEST_NAME.match(PurePosixPath(n).stem) for n in names):
        return True
    touched = [f"{part}/{n}" if part != "." else n for n in names]
    if gate_config.gate_files(dataclasses.replace(gate, always=()), touched, Path(root)):
        return True
    stems = {PurePosixPath(n).stem for n in names if PurePosixPath(n).stem != "__init__"}
    return any(_TEST_NAME.match(PurePosixPath(t).stem) and re.sub(r"^test_|_test$|\.test$|\.spec$", "", PurePosixPath(t).stem) in stems for t in tracked)


def _tech(state_dir: Path, root: Path, ref: str) -> list[dict]:
    snap = project_map.ensure(state_dir, root, ref)
    if not snap:
        return []
    sha = snap["commit"]
    by = {p["path"]: p for p in snap["parts"] if isinstance(p, dict) and p.get("path")}
    out: dict[str, list[dict]] = {k: [] for k in ORDER}
    for group in cycles({p: list(v.get("uses") or []) for p, v in by.items()}):
        shown = ", ".join(group[:4]) + (f" and {len(group) - 4} more" if len(group) > 4 else "")
        out["cycle"].append({"on": group[0], "kind": "cycle", "words": f"{shown} use one another in a cycle"})
    for p, v in sorted(by.items()):
        if len(v.get("used_by") or []) >= FAN_IN:
            out["fan_in"].append({"on": p, "kind": "fan_in", "words": f"{p} is used by {len(v['used_by'])} parts"})
        if len(v.get("uses") or []) >= FAN_OUT:
            out["fan_out"].append({"on": p, "kind": "fan_out", "words": f"{p} uses {len(v['uses'])} parts"})
    for part, (name, n) in sorted(_lines(root, sha).items()):
        if n >= BIG_LINES and part in by:
            out["big"].append({"on": part, "kind": "big", "words": f"{part} holds {name} of {n} lines"})
    commits = _churn(root, sha)
    containers = [c["path"] for c in (snap.get("overview") or {}).get("containers") or []]
    touched: dict[str, int] = {}
    outside: dict[str, set[str]] = {}
    shared = {s["path"]: s for s in (snap.get("overview") or {}).get("shared") or [] if isinstance(s, dict)}
    for files in commits:
        parts = {_part(f) for f in files} & set(by)
        for part in parts:
            touched[part] = touched.get(part, 0) + 1
            if part in shared:
                outside.setdefault(part, set()).update(c for f in files if _part(f) != part and (c := system_overview.owner(f, containers)))
    for part, others in sorted(outside.items()):
        if len(others) >= SHARED_FROM:
            out["shared_churn"].append({"on": part, "kind": "shared_churn", "words": f"{part} is shared by {len(shared[part].get('containers') or [])} containers and was changed in the last "
                                        f"{CHURN_DAYS} days along with files of {len(others)} containers ({', '.join(sorted(others)[:4])})"})
    hot = {p: n for p, n in touched.items() if n >= CHURN_TIMES}
    if hot:
        tracked, gate = _tracked(root, sha), gate_config.read(root)
        names = set(tracked)
        for part, n in sorted(hot.items(), key=lambda kv: (-kv[1], kv[0])):
            if not _tested(part, list(by[part].get("files") or []), names, gate, root):
                out["untested_churn"].append({"on": part, "kind": "untested_churn", "words": f"{part} changed {n} times in the last {CHURN_DAYS} days and no test is mapped to it"})
    return [s for k in ORDER for s in out[k]]


# -- Game design: the loop ------------------------------------------------------------------------------------------------------------

def _game(state_dir: Path) -> list[dict]:
    return [{"on": on, "kind": "loop", "words": words} for on, words in loop.findings_on(loop.read(state_dir))]


# -- Design: the screens --------------------------------------------------------------------------------------------------------------

def _design(state_dir: Path, root: Path) -> list[dict]:
    got = screen_map.read(state_dir, root)
    screens = got.get("screens") or []
    if len(screens) < 2:
        return []
    ids = {s["id"] for s in screens}
    links = [k for k in got.get("links") or [] if k["from"] in ids and k["to"] in ids]
    led_to, leads = {k["to"] for k in links if k["from"] != k["to"]}, {k["from"] for k in links if k["from"] != k["to"]}
    steps = got.get("steps") or []
    loose = set(got.get("loose") or [])
    last = [row for row in steps if not set(row) <= loose][-1:] or [[]]
    ends = set(last[0])
    out = []
    for s in screens:
        sid, name = s["id"], s["name"]
        if sid != got.get("entry") and sid not in led_to:
            out.append({"on": sid, "kind": "loose", "words": f"Nothing leads to the screen {name} ({s['path']})"})
        elif sid not in leads and sid not in ends and sid not in loose:
            out.append({"on": sid, "kind": "dead_end", "words": f"The screen {name} ({s['path']}) leads nowhere and is not where the flow ends"})
    out += [{"on": s["id"], "kind": "no_picture", "words": f"The screen {s['name']} ({s['path']}) has no picture kept"} for s in screens if not s.get("picture")]
    return out


# -- Product: the tree and the pains ----------------------------------------------------------------------------------------------------

def _product(state_dir: Path, root: Path) -> list[dict]:
    rec = opportunity_tree.read(state_dir)
    served = {s["job"] for s in rec["serves"]}
    out = [{"on": j["id"], "kind": "unserved", "words": f"No goal serves the job: {j['want']}"} for j in rec["jobs"] if j["id"] not in served]
    placed = [p for seg in idea_lens.segments_placed(state_dir) for p in seg["pains"]]
    try:
        got = screen_map.read(state_dir, root)
        known = {s["id"] for s in got.get("screens") or []} | {screen_map.step_id(n) for n in range(1, len(got.get("steps") or []) + 1)}
    except Exception:                                # a map that cannot be read: the pains stand where they were pinned
        known = {p["on"] for p in placed if p["on"]}
    piled: dict[str, list[str]] = {}
    for p in placed:
        if p["on"] in known:
            piled.setdefault(p["on"], []).append(p["text"])
    out += [{"on": on, "map": "screens", "kind": "pains", "words": f"{len(texts)} pains are pinned to {on}: " + "; ".join(texts[:3])}
            for on, texts in sorted(piled.items()) if len(texts) >= PAINS_PILED]
    loose = [p["text"] for p in placed if p["on"] not in known]
    if loose:
        out.append({"on": "", "kind": "pain_loose", "words": f"{len(loose)} pains are pinned to no screen or step: " + "; ".join(loose[:3])})
    return out


def pictures(state_dir: Path, root: Path, since: str = "", limit: int = 4) -> list[dict]:
    """The pictures of Design's screens kept since `since` (an ISO time: a look's; "" all), the newest `limit`: `[{id, name, path, at}]`, `path` a file under the repository to read (relative to it
    when it lies in it). [] for a map that cannot be read."""
    from orkboard.realm import idea_pick
    try:
        screens = screen_map.read(Path(state_dir), Path(root)).get("screens") or []
    except Exception:
        return []
    out = []
    for s in screens:
        pic = s.get("picture")
        if not isinstance(pic, dict) or (since and str(pic.get("at") or "") <= since):
            continue
        if pic.get("kind") == "lens":
            found = next((k["path"] for k in idea_lens.screens(Path(state_dir)) if k["id"] == pic.get("id")), "")
            path = Path(found) if found else None
        else:
            path = idea_pick.folder_of(Path(state_dir), str(pic.get("goal") or ""), str(pic.get("id") or "")) / str(pic.get("file") or "") if pic.get("goal") else None
        if path is not None:
            try:
                path = path.relative_to(root) if path.is_absolute() else path
            except ValueError:
                pass
            out.append({"id": s["id"], "name": s["name"], "path": path.as_posix(), "at": str(pic.get("at") or "")})
    return sorted(out, key=lambda r: (r["at"], r["id"]), reverse=True)[:limit]


def signals(state_dir: Path, root: Path, craft: str, pages: Path | None = None, ref: str = "dev") -> list[dict]:
    """The hints of `craft`'s party's map (see the module): `[{on, kind, words, map?}]`, at most MAX_SIGNALS; [] for a craft that has none by code and for a map that cannot be read."""
    state_dir, root = Path(state_dir), Path(root)
    try:
        rows = {"tech": lambda: _tech(state_dir, root, ref), "game-design": lambda: _game(state_dir), "design": lambda: _design(state_dir, root),
                "product": lambda: _product(state_dir, root)}.get(craft, lambda: [])()
    except Exception:                                # a hint that cannot be read is no hint, never an error for a caller
        return []
    return rows[:MAX_SIGNALS]
