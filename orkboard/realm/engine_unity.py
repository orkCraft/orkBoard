"""A Unity project read for the maps (docs/specs/145-the-engines-read.md part B, decisions §208.5, §209.5): its containers, its parts and its screens,
by code with no model.

    detect(root)                 # whether a `ProjectSettings/ProjectVersion.txt` (or `Assets/` with `.meta` files beside `ProjectSettings/`) lies at the root
                                 #   or one or two folders down
    parts(root, files=None)      # code_map.parts's rows of the `.cs` files: a folder a part, `using X;` the parts that declare `namespace X`
    containers(root, parts=None) # system_overview's rows: each `.asmdef` (stack Unity), and `Assembly-CSharp` for the scripts of `Assets/` outside them
    links(root)                  # [{"from": path, "to": path, "http": [], "socket": []}]: an `.asmdef`'s `references` (a name, or `GUID:<guid>`)
    screens(tree)                # ("unity", [{path, name, file}, …]) of a screen_routes.Tree: the build settings' enabled scenes, then each `.uxml`
    screen_links(tree, rows, ids)   # [{"from": id, "to": id}]: `SceneManager.LoadScene("Name" | "path" | index)` in the scripts a scene attaches
    entry(tree, rows, ids)       # the id of the build settings' first scene

`Library/`, `Temp/`, `Obj/`, `Logs/`, `UserSettings/` and `Packages/` are left out, as are code_map's folders. A reference to no `.asmdef` of the project (Unity's or a
package's) is left out, and so is `using UnityEngine;`. Every pattern has bounded repeats.
"""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

from orkboard.realm import engine_kit

SKIP = {"Library", "Temp", "Obj", "Logs", "UserSettings", "Packages"}
ASSEMBLY = "Assembly-CSharp"
METAS = 2000                               # the most `.cs.meta` files a scene's scripts are looked up in

_GUID = re.compile(r"^guid:[ \t]*([0-9a-f]{32})", re.M)
_SCENE = re.compile(r"-[ \t]*enabled:[ \t]*([01])[ \t]*\r?\n[ \t]*path:[ \t]*([^\r\n]{1,300})")
_ATTACHED = re.compile(r"\bguid:[ \t]*([0-9a-f]{32})")
_LOAD = re.compile(r"\bLoadScene(?:Async)?\s*\(\s*(?:\"([^\"\n]{1,200})\"|(\d{1,3})\b)")


def _marker(d: Path) -> bool:
    if (d / "ProjectSettings" / "ProjectVersion.txt").is_file():
        return True
    try:
        return (d / "ProjectSettings").is_dir() and (d / "Assets").is_dir() and any((d / "Assets").glob("*.meta"))
    except OSError:
        return False


def _projects(root: Path) -> list[str]:
    return engine_kit.project_dirs(Path(root), _marker, SKIP)


def detect(root: Path) -> bool:
    return bool(_projects(root))


def _asmdefs(root: Path, project: str) -> list[dict]:
    """Each `.asmdef` of the project's `Assets/`: `{name, dir, file, guid, references}`."""
    out = []
    for rel in engine_kit.walk(root, engine_kit.join(project, "Assets"), {".asmdef"}, SKIP):
        try:
            doc = json.loads(engine_kit.read(root, rel))
        except ValueError:
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("name"), str) or not doc["name"].strip():
            continue
        refs = [str(r)[:200] for r in doc.get("references") or [] if isinstance(r, str)] if isinstance(doc.get("references"), list) else []
        meta = _GUID.search(engine_kit.read(root, rel + ".meta"))
        out.append({"name": doc["name"].strip()[:120], "dir": engine_kit.part_of(rel), "file": rel.rpartition("/")[2],
                    "guid": meta.group(1) if meta else "", "references": refs})
    return out


def _owner(rel: str, asm: list[dict]) -> dict | None:
    best = None
    for a in asm:
        if rel.startswith(a["dir"] + "/") and (best is None or len(a["dir"]) > len(best["dir"])):
            best = a
    return best


def parts(root: Path, files: list[str] | None = None) -> list[dict]:
    """The parts of the Unity projects under `root` (`files`, the caller's list, is not needed: `Assets/` is walked here), in `code_map.parts`'s shape."""
    root = Path(root)
    rels: list[str] = []
    for project in _projects(root):
        rels += engine_kit.walk(root, engine_kit.join(project, "Assets"), {".cs"}, SKIP)
    names, uses = engine_kit.cs_uses(root, rels)
    return engine_kit.shape(names, uses)


def containers(root: Path, parts_: list[dict] | None = None) -> list[dict]:
    """Each `.asmdef` a container, stack Unity, its folder and what lies under it to the next `.asmdef`; `Assembly-CSharp` (path: the project's `Assets/`) for the
    scripts outside every `.asmdef`."""
    root = Path(root)
    out = []
    for project in _projects(root):
        asm = _asmdefs(root, project)
        base = {"manifests": [], "stack": [{"name": "Unity", "role": "game"}], "unknown": 0, "ways_in": [], "role": ""}
        for a in asm:
            out.append({**base, "path": a["dir"], "name": a["name"], "manifests": [a["file"]]})
        scripts = engine_kit.walk(root, engine_kit.join(project, "Assets"), {".cs"}, SKIP)
        if any(_owner(r, asm) is None for r in scripts):
            out.append({**base, "path": engine_kit.join(project, "Assets"), "name": ASSEMBLY})
    return out


def links(root: Path) -> list[dict]:
    """The containers' links: each `.asmdef` to the `.asmdef`s of the project its `references` name (by name, or `GUID:<guid>`)."""
    root = Path(root)
    out = []
    for project in _projects(root):
        asm = _asmdefs(root, project)
        by_name = {a["name"]: a for a in asm}
        by_guid = {a["guid"]: a for a in asm if a["guid"]}
        for a in asm:
            seen = set()
            for ref in a["references"]:
                hit = by_guid.get(ref[5:].strip().lower()) if ref.upper().startswith("GUID:") else by_name.get(ref)
                if hit and hit["dir"] != a["dir"] and hit["dir"] not in seen:
                    seen.add(hit["dir"])
                    out.append({"from": a["dir"], "to": hit["dir"], "http": [], "socket": []})
    return out


# -- the screens (a commit's tree) ---------------------------------------------------------------------------------------------------------------

def _settings(tree) -> list[tuple[str, str]]:
    """(the project's folder, the settings file) of each `ProjectSettings/EditorBuildSettings.asset` in the tree."""
    tail = "ProjectSettings/EditorBuildSettings.asset"
    return [(p[:-len(tail)].rstrip("/") or engine_kit.ROOT, p) for p in sorted(tree.set) if p == tail or p.endswith("/" + tail)]


def _build(tree) -> list[str]:
    """The enabled scenes of the build settings in order, as the repository's paths: their build indexes."""
    out = []
    for project, file in _settings(tree):
        for on, path in _SCENE.findall(tree.text(file)):
            if on == "1":
                out.append(engine_kit.join(project, path.strip().strip("'\"")))
    return out


def screens(tree) -> tuple[str, list[dict]]:
    """("unity", rows): the enabled scenes of the build settings, in its order, then each `.uxml`; ("", []) with neither."""
    settings = _settings(tree)
    tree.load([f for _p, f in settings])
    rows, seen = [], set()
    for path in _build(tree):
        if path not in seen:
            seen.add(path)
            rows.append({"path": path, "name": PurePosixPath(path).stem, "file": path})
    for p in tree.files:
        if p.endswith(".uxml") and p not in seen and not any(b in SKIP for b in p.split("/")):
            seen.add(p)
            rows.append({"path": p, "name": PurePosixPath(p).stem, "file": p})
    return ("unity", rows) if rows else ("", [])


def entry(tree, rows: list[dict], ids: list[str]) -> str:
    build = _build(tree)
    return next((sid for sid, r in zip(ids, rows) if build and r["file"] == build[0]), "")


def _target(want: str, index: int | None, rows: list[dict], ids: list[str], build: list[str]) -> str:
    scenes = [(sid, r) for sid, r in zip(ids, rows) if r["file"].endswith(".unity")]
    if index is not None:
        path = build[index] if index < len(build) else ""
        return next((sid for sid, r in scenes if r["file"] == path), "")
    bare = want[:-len(".unity")] if want.endswith(".unity") else want
    by_path = next((sid for sid, r in scenes if r["file"][:-len(".unity")] == bare or r["file"][:-len(".unity")].endswith("/" + bare)), "")
    return by_path or next((sid for sid, r in scenes if r["name"] == bare), "")


def screen_links(tree, rows: list[dict], ids: list[str]) -> list[dict]:
    """The links `{from, to}`: the scripts a scene attaches (its `guid:`s, through the `.cs.meta` files) call `SceneManager.LoadScene` by name, by path or by build index."""
    scenes = [r["file"] for r in rows if r["file"].endswith(".unity")]
    tree.load(scenes)
    wanted = set()
    for f in scenes:
        wanted |= set(_ATTACHED.findall(tree.text(f)))
    metas = [p for p in tree.files if p.endswith(".cs.meta")][:METAS] if wanted else []
    tree.load(metas)
    script_of = {}
    for m in metas:
        g = _GUID.search(tree.text(m))
        if g and g.group(1) in wanted:
            script_of[g.group(1)] = m[:-len(".meta")]
    tree.load(list(script_of.values()))
    build = _build(tree)
    by_file = {r["file"]: sid for sid, r in zip(ids, rows)}
    out, seen = [], set()
    for f in scenes:
        sid = by_file[f]
        guids = list(dict.fromkeys(_ATTACHED.findall(tree.text(f))))
        for g in guids:
            for m in _LOAD.finditer(tree.text(script_of[g])) if g in script_of else ():
                to = _target(m.group(1) or "", int(m.group(2)) if m.group(2) else None, rows, ids, build)
                if to and to != sid and (sid, to) not in seen:
                    seen.add((sid, to))
                    out.append({"from": sid, "to": to})
    return out
