"""An Unreal project read for the maps (docs/specs/145-the-engines-read.md part C, decisions §208.5): its modules as containers, its folders of C++ as parts, by
code with no model. There are no screens for Unreal in this spec.

    detect(root)                 # whether a `.uproject` lies at the root
    containers(root, parts=None) # system_overview's rows: each `Source/<Name>/<Name>.Build.cs` (and a plugin's), stack Unreal, its `Type` (Runtime, Editor) the `role`
    links(root)                  # [{"from": path, "to": path, "http": [], "socket": []}]: the `Public`/`PrivateDependencyModuleNames` that are the project's own modules
    parts(root, files=None)      # code_map.parts's rows of the `.h`/`.hpp`/`.cpp`/`.inl` under each module: `#include "…"` that resolves to a file of the project

A module's `Type` is read from the `.uproject`'s `Modules` (a plugin's from its `.uplugin`). The engine's modules (`Core`, `Engine`) are no container and no link, and an
angle-bracket include is left out. `Binaries/`, `Intermediate/`, `Saved/` and `DerivedDataCache/` are left out, as are code_map's folders. Every pattern has bounded repeats.
"""
from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path

from orkboard.realm import engine_kit

SKIP = {"Binaries", "Intermediate", "Saved", "DerivedDataCache"}
SOURCE = {".h", ".hpp", ".cpp", ".inl"}
_DEPS = re.compile(r"\b(?:Public|Private)DependencyModuleNames\s*\.\s*(?:Add|AddRange)\s*\(([^;]{0,2000}?)\)\s*;")
_STR = re.compile(r'"([A-Za-z_]\w{0,100})"')
_INCLUDE = re.compile(r'^[ \t]*#[ \t]*include[ \t]+"([^"\n]{1,300})"', re.M)


def _uproject(root: Path) -> str:
    try:
        return next((e.name for e in sorted(Path(root).iterdir()) if e.suffix == ".uproject" and e.is_file() and not e.is_symlink()), "")
    except OSError:
        return ""


def detect(root: Path) -> bool:
    return bool(_uproject(Path(root)))


def _types(root: Path, rel: str, key: str = "Modules") -> dict[str, str]:
    try:
        doc = json.loads(engine_kit.read(root, rel))
    except ValueError:
        return {}
    rows = doc.get(key) if isinstance(doc, dict) else None
    return {str(m["Name"]): str(m.get("Type") or "") for m in (rows if isinstance(rows, list) else []) if isinstance(m, dict) and isinstance(m.get("Name"), str)}


def _modules(root: Path) -> list[dict]:
    """Each module: `{name, dir, file, role}` (`dir` relative to the root)."""
    types = _types(root, _uproject(root))
    files = engine_kit.walk(root, "Source", {".cs"}, SKIP) + engine_kit.walk(root, "Plugins", {".cs"}, SKIP)
    plugin_types: dict[str, dict[str, str]] = {}
    out = []
    for rel in files:
        if not rel.endswith(".Build.cs"):
            continue
        name = rel.rpartition("/")[2][:-len(".Build.cs")]
        folder = engine_kit.part_of(rel)
        if folder.rpartition("/")[2] != name:
            continue
        role = types.get(name, "")
        if not role and folder.startswith("Plugins/"):                      # a plugin's modules are in its `.uplugin`
            top = "/".join(folder.split("/")[:2])
            if top not in plugin_types:
                try:
                    pf = next(f for f in sorted((Path(root) / top).glob("*.uplugin")) if f.is_file())
                    plugin_types[top] = _types(root, pf.relative_to(root).as_posix())
                except (OSError, StopIteration):
                    plugin_types[top] = {}
            role = plugin_types[top].get(name, "")
        out.append({"name": name, "dir": folder, "file": rel.rpartition("/")[2], "role": role, "rel": rel})
    return out


def containers(root: Path, parts_: list[dict] | None = None) -> list[dict]:
    root = Path(root)
    return [{"path": m["dir"], "name": m["name"], "manifests": [m["file"]], "stack": [{"name": "Unreal", "role": "game"}], "unknown": 0, "ways_in": [],
             "role": m["role"]} for m in _modules(root)]


def links(root: Path) -> list[dict]:
    """Module to module: the names of `Public`/`PrivateDependencyModuleNames` that are modules of the project (`Core`, `Engine` are the engine's: left out)."""
    root = Path(root)
    mods = _modules(root)
    by_name = {m["name"]: m for m in mods}
    out = []
    for m in mods:
        seen = set()
        for body in _DEPS.findall(engine_kit.read(root, m["rel"])):
            for name in _STR.findall(body):
                hit = by_name.get(name)
                if hit and hit["dir"] != m["dir"] and hit["dir"] not in seen:
                    seen.add(hit["dir"])
                    out.append({"from": m["dir"], "to": hit["dir"], "http": [], "socket": []})
    return out


def parts(root: Path, files: list[str] | None = None) -> list[dict]:
    """The parts under each module (`files`, the caller's list, is not needed: the modules are walked here), in `code_map.parts`'s shape."""
    root = Path(root)
    mods = _modules(root)
    sources: dict[str, str] = {}                                 # file → its module's folder
    for m in mods:
        for rel in engine_kit.walk(root, m["dir"], SOURCE, SKIP):
            sources.setdefault(rel, m["dir"])
    known = set(sources)
    roots = [m["dir"] for m in mods]
    names: dict[str, list[str]] = {}
    uses: dict[str, set[str]] = {}

    def resolve(rel: str, include: str) -> str:
        own = sources[rel]
        for base in (engine_kit.part_of(rel), f"{own}/Private", f"{own}/Public", own, *(f"{d}/Public" for d in roots)):
            cand = posixpath.normpath(posixpath.join(base, include))
            if cand in known:
                return cand
        return ""

    for rel in sorted(known):
        part = engine_kit.part_of(rel)
        names.setdefault(part, []).append(rel.rpartition("/")[2])
        found = uses.setdefault(part, set())
        for inc in _INCLUDE.findall(engine_kit.read(root, rel)):
            hit = resolve(rel, inc)
            if hit and engine_kit.part_of(hit) != part:
                found.add(engine_kit.part_of(hit))
    return engine_kit.shape(names, uses)
