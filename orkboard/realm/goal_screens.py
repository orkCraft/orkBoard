"""The screens a goal changed (docs/specs/121-the-day-the-morning-and-the-night.md §5.1, decisions §199.5): what the morning's card opens Play on. By code, no model, nothing written.

    goal_screens.of(state_dir, root, slug, ref="dev")   # [{"screen": "orders", "name": "Orders", "path": "/orders"}], at most MAX, in the flow's order; [] with none

The goal's files are those of the commits of `ref` its merged tasks brought (`commit_goal.index`: a task keeps the new head of its branch and the subjects it brought). A screen is *changed* when one
of those files is its component's file (`screen_map`'s screens at `ref`'s head), or a file its component imports, one level down (`import … from "./x"`, `import("./x")`, `require("./x")`, a Dart
`import 'x.dart'`; the file the import names, else the file with an extension or an `index` of one). A file that several screens share (a router's table) changes none of them: it names no screen. The screens
come in the flow's order (`steps`: breadth first from the entry, the screens no link leads to last), the first MAX. A project with no screen, no `ref` or a goal none of whose commits touched one gives [].
`path` is the screen's route as the map has it (`/orders/:id` with a parameter); `ideas.play {path}` takes it as it is. The git reads are fixed arguments, no shell.
"""
from __future__ import annotations

import posixpath
import re
import subprocess
from pathlib import Path

from orkboard.realm import commit_goal, screen_map, screen_routes

MAX = 4                                  # the screens a goal shows, at most
_IMPORT = re.compile(r"""(?:\bfrom\s*|\bimport\s*\(\s*|\brequire\s*\(\s*|^[ \t]*import\s+)["']([^"'\n]{1,300})["']""", re.M)
_ENDS = (".tsx", ".ts", ".jsx", ".js", ".vue", ".svelte", ".mjs", ".dart", ".css", ".scss", ".less")
_TREES: dict[tuple[str, str], screen_routes.Tree] = {}
_TREES_MAX = 4


def _tree(root: Path, sha: str) -> screen_routes.Tree:
    key = (str(root), sha)
    if key not in _TREES:
        if len(_TREES) >= _TREES_MAX:
            _TREES.pop(next(iter(_TREES)))
        _TREES[key] = screen_routes.Tree(root, sha)
    return _TREES[key]


def _files_of(root: Path, sha: str) -> set[str]:
    """The files one commit changed (against its first parent); empty when git cannot say."""
    try:
        got = commit_goal.git(root, "show", "-m", "--first-parent", "--name-only", "--format=", sha)
    except (OSError, subprocess.SubprocessError):
        return set()
    return set(got.stdout.split("\n")) - {""} if got.returncode == 0 else set()


def goal_files(state_dir: Path, root: Path, slug: str, ref: str = "dev") -> set[str]:
    """The files the commits of `ref` that the goal's tasks brought changed."""
    out: set[str] = set()
    for sha, who in commit_goal.index(Path(state_dir), Path(root), ref).items():
        if who.get("goal") == slug:
            out |= _files_of(Path(root), sha)
    return out


def _candidates(here: str, spec: str) -> set[str]:
    """The paths a relative or `@/` import of the file `here` may name: itself, with an extension, or as a folder's `index`."""
    if spec.startswith("."):
        base = posixpath.normpath(posixpath.join(posixpath.dirname(here), spec))
        bases = [base] if not base.startswith("..") else []
    elif spec[:2] in ("@/", "~/"):
        bases = ["src/" + spec[2:], spec[2:]]
    else:
        return set()
    out: set[str] = set()
    for b in bases:
        out.add(b)
        out |= {b + e for e in _ENDS} | {f"{b}/index{e}" for e in _ENDS}
    return out


def _uses(here: str, text: str) -> set[str]:
    """Every path the imports of a screen's component may name (one level down)."""
    out: set[str] = set()
    for spec in _IMPORT.findall(text):
        out |= _candidates(here, spec)
    return out


def of(state_dir: Path, root: Path, slug: str, ref: str = "dev") -> list[dict]:
    """The screens the goal's merged tasks changed, see the module: `[{screen, name, path}]`."""
    root = Path(root)
    core = screen_map.flow(root, ref)
    if core is None or not isinstance(slug, str) or not slug:
        return []
    changed = goal_files(state_dir, root, slug, ref)
    if not changed:
        return []
    files = [s["file"] for s in core["screens"] if s["file"]]
    shared = {f for f in files if files.count(f) > 1}                  # a router's table names no screen
    own = [s for s in core["screens"] if s["file"] and s["file"] not in shared]
    if not own:
        return []
    tree = _tree(root, core["head"])
    tree.load([s["file"] for s in own if s["file"] not in changed])
    hit = {s["id"] for s in own if s["file"] in changed or _uses(s["file"], tree.text(s["file"])) & changed}
    order = [sid for step in core["steps"] for sid in step]
    order += [s["id"] for s in core["screens"] if s["id"] not in order]
    by = {s["id"]: s for s in core["screens"]}
    return [{"screen": sid, "name": by[sid]["name"], "path": by[sid]["path"]} for sid in order if sid in hit][:MAX]
