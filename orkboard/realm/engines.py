"""The engines the maps read (docs/specs/145-the-engines-read.md): the one place the callers ask, so each adds one call and an engine is one module
(realm/engine_godot.py, engine_unity.py, engine_unreal.py; what they share is realm/engine_kit.py). A project that has an engine is read as well as the web and
Python code beside it: the engine's parts and containers are added to what code_map and system_overview read, never in place of it.

    parts(root, files=None)             # [code_map.parts's rows] of every engine that detects `root`
    merge(base, extra)                  # code_map's parts and an engine's: one row a folder
    containers(root)                    # [system_overview's container rows] (`path`, `name`, `manifests`, `stack`, `unknown`, `ways_in`, `role`)
    links(root)                         # the engines' links between containers: `{from, to, http: [], socket: []}`
    matters(path)                       # whether a changed file may change what an engine reads
    screens(tree)                       # (source, rows) of a screen_routes.Tree: the first engine that gives screens ("", [] with none)
    screen_links(source, tree, rows, ids)   # [{from, to}] of the engine's screens, None for a source that is no engine's
    screen_entry(source, tree, rows, ids)   # the id of the screens' entry the engine names, "" when it names none
    TREE_SUFFIXES, TREE_NAMES           # the files screen_routes.Tree keeps beside its routers'

No face, no model.
"""
from __future__ import annotations

from pathlib import PurePosixPath

from orkboard.realm import engine_godot

ENGINES = {"godot": engine_godot}
CODE = {".gd", ".tscn", ".cs", ".asmdef", ".h", ".hpp", ".cpp", ".uproject", ".godot", ".csproj", ".uxml", ".unity"}
TREE_SUFFIXES = (".gd", ".tscn", ".godot", ".cs", ".unity", ".uxml")
TREE_NAMES = ("EditorBuildSettings.asset",)


def _each():
    return list(ENGINES.values())


def parts(root, files=None) -> list[dict]:
    out: list[dict] = []
    for e in _each():
        if e.detect(root):
            out = merge(out, e.parts(root, files))
    return out


def merge(base: list[dict], extra: list[dict]) -> list[dict]:
    """`base`'s rows and `extra`'s: a folder in both is one row (its files and uses together)."""
    if not extra:
        return base
    from orkboard.realm import code_map
    rows = {r["path"]: {**r, "files": list(r["files"]), "uses": set(r["uses"])} for r in base}
    for r in extra:
        have = rows.get(r["path"])
        if have is None:
            rows[r["path"]] = {**r, "files": list(r["files"]), "uses": set(r["uses"])}
        else:
            have["files"] = sorted(set(have["files"]) | set(r["files"]))[:code_map.FILES_SHOWN]
            have["count"] += r["count"]
            have["uses"] |= set(r["uses"])
    used_by: dict[str, set[str]] = {p: set() for p in rows}
    for p, r in rows.items():
        for u in r["uses"]:
            used_by.setdefault(u, set()).add(p)
    return [{**rows[p], "uses": sorted(rows[p]["uses"] - {p}), "used_by": sorted(used_by.get(p, set()) - {p})} for p in sorted(rows)]


def containers(root) -> list[dict]:
    out: list[dict] = []
    for e in _each():
        if e.detect(root):
            out += e.containers(root)
    return out


def links(root) -> list[dict]:
    out: list[dict] = []
    for e in _each():
        if hasattr(e, "links") and e.detect(root):
            out += e.links(root)
    return out


def matters(path: str) -> bool:
    p = PurePosixPath(path)
    return p.suffix in CODE or p.name.endswith((".Build.cs", ".asmdef.meta", ".cs.meta")) or p.name in TREE_NAMES or p.name == "ProjectVersion.txt"


def screens(tree) -> tuple[str, list[dict]]:
    for e in _each():
        source, rows = e.screens(tree)
        if rows:
            return source, rows
    return "", []


def screen_links(source: str, tree, rows: list[dict], ids: list[str]) -> list[dict] | None:
    e = ENGINES.get(source)
    return e.screen_links(tree, rows, ids) if e is not None else None


def screen_entry(source: str, tree, rows: list[dict], ids: list[str]) -> str:
    e = ENGINES.get(source)
    return e.entry(tree, rows, ids) if e is not None else ""
