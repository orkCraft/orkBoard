"""A Godot project read for the maps (docs/specs/145-the-engines-read.md part A, decisions §208.5, §209.5): its parts, its container and its screens,
by code with no model.

    detect(root)                 # whether a `project.godot` lies at the root or one or two folders down
    parts(root, files=None)      # code_map.parts's rows of the `.gd` files (and `.cs`): `preload`/`load`/`extends "res://…"`, `extends Name` and `Name.` of a
                                 #   `class_name`, a `.tscn`'s scripts and instanced scenes, C#'s `using`
    containers(root, parts=None) # system_overview's rows: the project, stack Godot (Godot C# beside a `.csproj` of `Godot.NET.Sdk`), its ways in
    is_csharp(root)              # whether a project of the tree is a Godot C# one
    screens(tree)                # ("godot", [{path: "res://ui/menu.tscn", name: "Menu", file: "game/ui/menu.tscn"}, …]) of a screen_routes.Tree
    screen_links(tree, rows, ids)  # [{"from": id, "to": id}]: `change_scene_to_file("res://….tscn")`, `change_scene_to_packed(preload(…))`, a const or var holding it
    entry(tree, rows, ids)       # the id of `run/main_scene` when it is a screen, else ""

`res://` resolves in the folder of `project.godot`. `.godot/` and `.import/` are left out, as are code_map's folders. Engine classes (`Node`, `Control`) are
no part and no link: only a `class_name` of the project is a name. Every pattern has bounded repeats.
"""
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from orkboard.realm import code_map, engine_kit

SKIP = {".godot", ".import"}
SCRIPTS, SCENES, CSHARP = {".gd"}, {".tscn"}, {".cs"}
CONTROLS = {"Control", "Container", "Panel", "PanelContainer", "MarginContainer", "VBoxContainer", "HBoxContainer", "CenterContainer", "GridContainer",
            "ScrollContainer", "TabContainer", "SplitContainer", "HSplitContainer", "VSplitContainer", "FlowContainer", "HFlowContainer",
            "VFlowContainer", "AspectRatioContainer", "SubViewportContainer", "TextureRect", "ColorRect", "NinePatchRect", "ReferenceRect", "Label",
            "RichTextLabel", "Button", "CheckBox", "CheckButton", "OptionButton", "MenuButton", "LinkButton", "TextureButton", "ItemList", "Tree",
            "LineEdit", "TextEdit", "CodeEdit", "TabBar", "ProgressBar", "TextureProgressBar", "HSlider", "VSlider", "SpinBox", "ScrollBar",
            "HScrollBar", "VScrollBar", "MenuBar", "GraphEdit", "VideoStreamPlayer"}
NAMES = 400                                # the most class_names a project's uses are looked for

_AUTOLOAD_SECTION = re.compile(r"^\[(\w{1,40})\]", re.M)
_KEY = re.compile(r'^([\w/.]{1,80})[ \t]*=[ \t]*"([^"\n]{0,300})"', re.M)
_RES = r'"res://([^"\n]{1,300})"'
_PRELOAD = re.compile(r"\b(?:preload|load)\s*\(\s*" + _RES)
_EXTENDS_PATH = re.compile(r"^[ \t]*extends\s+" + _RES, re.M)
_EXTENDS_NAME = re.compile(r"^[ \t]*extends[ \t]+([A-Za-z_]\w{0,80})", re.M)
_CLASS_NAME = re.compile(r"^[ \t]*class_name[ \t]+([A-Za-z_]\w{0,80})", re.M)
_DOTTED = re.compile(r"\b([A-Z][A-Za-z0-9_]{0,80})\s*\.")
_EXT = re.compile(r"^\[ext_resource\b([^\]\n]{0,400})\]", re.M)
_NODE = re.compile(r"^\[node\b([^\]\n]{0,400})\]", re.M)
_ATTR_TYPE = re.compile(r'\btype="(\w{1,60})"')
_ATTR_PATH = re.compile(r'\bpath="res://([^"\n]{1,300})"')
_ATTR_NAME = re.compile(r'\bname="([^"\n]{1,80})"')
_CHANGE = re.compile(r"\bchange_scene_to_(file|packed)\s*\(\s*(?:preload\s*\(\s*|load\s*\(\s*)?(?:" + _RES + r"|([A-Za-z_]\w{0,80}))")
_NAMED = re.compile(r"^[ \t]*(?:@\w+(?:\([^)\n]{0,100}\))?[ \t]+)*(?:const|var)[ \t]+([A-Za-z_]\w{0,80})[ \t]*(?::[ \t]*\w{1,40}[ \t]*)?:?=[ \t]*"
                    r"(?:(?:preload|load)\s*\(\s*)?" + _RES, re.M)
_GODOT_SDK = re.compile(r"Godot\.NET\.Sdk")


def _marker(d: Path) -> bool:
    return (d / "project.godot").is_file() and not (d / "project.godot").is_symlink()


def _projects(root: Path) -> list[str]:
    return engine_kit.project_dirs(Path(root), _marker, SKIP)


def detect(root: Path) -> bool:
    return bool(_projects(root))


def _config(root: Path, project: str) -> dict[str, dict[str, str]]:
    """`project.godot`'s `{section: {key: value}}` (strings only; `PackedStringArray(…)` and the like are left out)."""
    text = engine_kit.read(root, engine_kit.join(project, "project.godot"))
    out: dict[str, dict[str, str]] = {}
    at = [(m.start(), m.end(), m.group(1)) for m in _AUTOLOAD_SECTION.finditer(text)]
    for i, (_s, end, name) in enumerate(at):
        block = text[end:at[i + 1][0] if i + 1 < len(at) else len(text)]
        out[name] = dict(_KEY.findall(block))
    return out


def _res(project: str, path: str) -> str:
    """A `res://` path as the repository's."""
    return engine_kit.join(project, PurePosixPath(path.strip().lstrip("/")).as_posix())


def is_csharp_at(root: Path, project: str) -> bool:
    """Whether the project at `project` has a `.csproj` of `Godot.NET.Sdk` beside its `project.godot`."""
    base = Path(root) / project if project != engine_kit.ROOT else Path(root)
    try:
        projs = sorted(base.glob("*.csproj"))[:5]
    except OSError:
        return False
    return any(_GODOT_SDK.search(engine_kit.read(Path(root), p.relative_to(root).as_posix())) for p in projs)


def is_csharp(root: Path) -> bool:
    """Whether a Godot project of the tree is a C# one."""
    return any(is_csharp_at(root, p) for p in _projects(root))


def _scene_refs(text: str, project: str) -> tuple[list[str], list[str]]:
    """(the scripts, the instanced scenes) a `.tscn` names, as the repository's paths."""
    scripts, scenes = [], []
    for attrs in _EXT.findall(text):
        kind, path = _ATTR_TYPE.search(attrs), _ATTR_PATH.search(attrs)
        if kind and path:
            if kind.group(1) == "Script":
                scripts.append(_res(project, path.group(1)))
            elif kind.group(1) == "PackedScene":
                scenes.append(_res(project, path.group(1)))
    return scripts, scenes


def parts(root: Path, files: list[str] | None = None) -> list[dict]:
    """The parts of the Godot projects under `root` (`files`, the caller's own list, is not needed: the project is walked here), in `code_map.parts`'s shape."""
    root = Path(root)
    names: dict[str, list[str]] = {}
    uses: dict[str, set[str]] = {}
    for project in _projects(root):
        scripts = engine_kit.walk(root, project, SCRIPTS, SKIP)
        scenes = engine_kit.walk(root, project, SCENES, SKIP)
        cs = engine_kit.walk(root, project, CSHARP, SKIP)
        known = set(scripts) | set(scenes) | set(cs)
        texts = {r: engine_kit.read(root, r) for r in scripts}
        classes: dict[str, str] = {}
        for r, t in texts.items():
            for name in _CLASS_NAME.findall(t):
                if len(classes) < NAMES:
                    classes.setdefault(name, r)
        edges: set[tuple[str, str]] = set()                       # (file, file) of the project

        def add(src: str, target: str) -> None:
            if target in known and target != src:
                edges.add((src, target))
        for r, t in texts.items():
            for path in _PRELOAD.findall(t) + _EXTENDS_PATH.findall(t):
                add(r, _res(project, path))
            for name in _EXTENDS_NAME.findall(t):
                if name in classes:
                    add(r, classes[name])
            for name in set(_DOTTED.findall(t)) & set(classes):
                add(r, classes[name])
        for r in scenes:
            ss, sc = _scene_refs(engine_kit.read(root, r), project)
            for target in ss + sc:
                add(r, target)
        file_part = {r: engine_kit.part_of(r) for r in scripts + scenes}
        for a, b in edges:
            if file_part[a] != file_part[b]:
                uses.setdefault(file_part[a], set()).add(file_part[b])
        for r in scripts:
            names.setdefault(file_part[r], []).append(r.rpartition("/")[2])
        for p in set(uses) | {u for us in uses.values() for u in us}:    # a folder of scenes only is a part when it uses or is used
            if p not in names:
                names[p] = [r.rpartition("/")[2] for r in scenes if file_part[r] == p]
        cs_names, cs_use = engine_kit.cs_uses(root, cs)
        for p, ns in cs_names.items():
            names.setdefault(p, []).extend(ns)
            uses.setdefault(p, set()).update(cs_use.get(p, ()))
        for p in names:
            uses.setdefault(p, set())
    return engine_kit.shape(names, uses)


def containers(root: Path, parts_: list[dict] | None = None) -> list[dict]:
    """One container a project: `{path, name, manifests, stack, unknown, ways_in, role}` (system_overview's shape, its layers and parts the caller's)."""
    root = Path(root)
    out = []
    for project in _projects(root):
        conf = _config(root, project)
        app, auto = conf.get("application", {}), conf.get("autoload", {})
        ways = []
        main = app.get("run/main_scene", "")
        if main.startswith("res://"):
            ways.append({"kind": "main", "name": "", "path": _res(project, main[6:])})
        for name, value in auto.items():
            if value.lstrip("*").startswith("res://"):
                ways.append({"kind": "autoload", "name": name[:80], "path": _res(project, value.lstrip("*")[6:])})
        csharp = is_csharp_at(root, project)
        out.append({"path": project, "name": (app.get("config/name") or "")[:80] or (root.name if project == engine_kit.ROOT else PurePosixPath(project).name),
                    "manifests": ["project.godot"], "stack": [{"name": "Godot C#" if csharp else "Godot", "role": "game"}], "unknown": 0,
                    "ways_in": ways, "role": ""})
    return out


# -- the screens (a commit's tree) ---------------------------------------------------------------------------------------------------------------

def _folders(tree) -> list[str]:
    """The folders of the tree that hold a `project.godot`, deepest first."""
    found = [p[:-len("project.godot")].rstrip("/") or engine_kit.ROOT for p in tree.set if p == "project.godot" or p.endswith("/project.godot")]
    return sorted(found, key=lambda f: (-len(f), f))


def _project_of(tree, scene: str) -> str:
    """The project folder a scene of the tree lies in: the deepest folder with a `project.godot` that holds it ("" when none)."""
    return next((f for f in _folders(tree) if f == engine_kit.ROOT or scene.startswith(f + "/")), "")


def _conf_main(tree, project: str) -> str:
    text = tree.text(engine_kit.join(project, "project.godot"))
    app = re.search(r"^\[application\]([^\[]{0,6000})", text, re.M)
    m = re.search(r'^run/main_scene[ \t]*=[ \t]*"res://([^"\n]{1,300})"', app.group(1), re.M) if app else None
    return _res(project, m.group(1)) if m else ""


def screens(tree) -> tuple[str, list[dict]]:
    """("godot", rows) of a tree's `.tscn` whose root node is a `Control` kind (CONTROLS), the main scene first; ("", []) with no Godot project in it."""
    projects = sorted(p[:-len("project.godot")].rstrip("/") or engine_kit.ROOT for p in tree.set
                      if p == "project.godot" or p.endswith("/project.godot"))
    if not projects:
        return "", []
    scenes = [p for p in tree.files if p.endswith(".tscn") and not any(b in SKIP for b in p.split("/"))]
    tree.load(scenes)
    rows = []
    for rel in scenes:
        project = _project_of(tree, rel)
        if not project:
            continue
        root_node = next((a for a in _NODE.findall(tree.text(rel)) if "parent=" not in a), None)
        kind, name = (_ATTR_TYPE.search(root_node), _ATTR_NAME.search(root_node)) if root_node else (None, None)
        if kind and name and kind.group(1) in CONTROLS:
            inside = rel if project == engine_kit.ROOT else rel[len(project) + 1:]
            rows.append({"path": "res://" + inside, "name": name.group(1), "file": rel})
    main = {r["file"] for r in rows}
    first = [m for m in (_conf_main(tree, p) for p in projects) if m in main]
    rows.sort(key=lambda r: (r["file"] not in first, r["file"]))
    return ("godot", rows[:code_map.FILES_SHOWN * 10]) if rows else ("", [])


def entry(tree, rows: list[dict], ids: list[str]) -> str:
    """The id of the main scene (`run/main_scene`) when it is one of the screens."""
    for project in {_project_of(tree, r["file"]) for r in rows} - {""}:
        main = _conf_main(tree, project)
        for sid, r in zip(ids, rows):
            if r["file"] == main:
                return sid
    return ""


def _targets(text: str, project: str, named: dict[str, str]) -> list[tuple[int, str]]:
    out = []
    for m in _CHANGE.finditer(text):
        path = m.group(2) or named.get(m.group(3) or "")
        if path:
            out.append((m.start(), _res(project, path)))
    return out


def screen_links(tree, rows: list[dict], ids: list[str]) -> list[dict]:
    """The links `{from, to}` between screens: a scene's scripts change to another screen's scene by a path, a `preload`, or a `const`/`var` that holds one."""
    by_file = {r["file"]: sid for sid, r in zip(ids, rows)}
    out, seen = [], set()
    for sid, r in zip(ids, rows):
        project = _project_of(tree, r["file"])
        scripts, _scenes = _scene_refs(tree.text(r["file"]), project)
        tree.load(scripts)
        found: list[tuple[int, str]] = []
        for n, s in enumerate(scripts):
            text = tree.text(s)
            named = {k: v for k, v in _NAMED.findall(text)}
            found += [(n * 1_000_000 + at, t) for at, t in _targets(text, project, named)]
        for _at, target in sorted(found):
            to = by_file.get(target)
            if to and to != sid and (sid, to) not in seen:
                seen.add((sid, to))
                out.append({"from": sid, "to": to})
    return out
