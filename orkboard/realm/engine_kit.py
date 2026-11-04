"""What the engines' readers share (docs/specs/145-the-engines-read.md, Common to A, B, C): the bounded walk of a project's files (code_map's limits and
folders, an engine's own caches left out), a file's text when it may be read, the project folders an engine's marker finds, `part_of`, the parts' shape
and C#'s `using` between folders (a Godot C# project and a Unity one read it alike). Used by realm/engine_godot.py, engine_unity.py and engine_unreal.py;
realm/engines.py calls them. Nothing is run, nothing fetched. No face, no model.

    project_dirs(root, marker)   # the folders (relative, "." the root) at most DEPTH down whose `marker(path)` holds
    walk(root, base, exts, skip) # the files under a folder with an extension of `exts`, relative to the root, at most code_map.MAX_FILES
    read(root, rel)              # a file's text ("" when it is a link, a secret, gone or over code_map.MAX_BYTES)
    shape(names, uses)           # `code_map.parts`'s rows from {part: [file names]} and {part: {parts it uses}}
    cs_uses(root, rels)          # (the names, the uses) of C# files: `using X;` of the folders that declare `namespace X`
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from orkboard.hooks.warder import is_secret
from orkboard.realm import code_map

DEPTH = 2                                  # a project's folder lies at most two folders under the root
ROOT = "."
NAMESPACE = re.compile(r"^[ \t]*namespace[ \t]+([A-Za-z_][\w.]{0,200})[ \t]*[;{\r\n]", re.M)
USING = re.compile(r"^[ \t]*(?:global[ \t]+)?using[ \t]+(static[ \t]+)?(?:[A-Za-z_]\w{0,80}[ \t]*=[ \t]*)?([A-Za-z_][\w.]{0,200})[ \t]*;", re.M)


def hidden(name: str) -> bool:
    return name.startswith(".")


def project_dirs(root: Path, marker: Callable[[Path], bool], skip: set[str] = frozenset()) -> list[str]:
    """The folders (relative to `root`, "." the root itself) at most DEPTH folders down that `marker` holds for, a folder under a found one left out."""
    root = Path(root)
    out: list[str] = []

    def visit(rel: str, d: Path, depth: int) -> None:
        if marker(d):
            out.append(rel)
            return
        if depth >= DEPTH:
            return
        try:
            kids = sorted(e for e in d.iterdir() if e.is_dir() and not e.is_symlink() and not hidden(e.name)
                          and e.name not in code_map.SKIP and e.name not in skip)
        except OSError:
            return
        for e in kids:
            visit(e.name if rel == ROOT else f"{rel}/{e.name}", e, depth + 1)

    visit(ROOT, root, 0)
    return out


def join(base: str, rel: str) -> str:
    return rel if base == ROOT else f"{base}/{rel}"


def walk(root: Path, base: str, exts: set[str] | tuple[str, ...], skip: set[str], names: tuple[str, ...] = ()) -> list[str]:
    """Files under `root/base` whose suffix is in `exts` (or whose name is in `names`), as paths relative to `root`, sorted; at most code_map.MAX_FILES.
    Hidden folders, links, code_map.SKIP, `skip` and files that may hold a secret are left out."""
    root = Path(root)
    out: list[str] = []
    stack = [root / base if base != ROOT else root]
    while stack and len(out) < code_map.MAX_FILES:
        d = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.is_symlink():
                continue
            if e.is_dir():
                if not hidden(e.name) and e.name not in code_map.SKIP and e.name not in skip:
                    stack.append(e)
            elif e.suffix in exts or e.name in names:
                rel = e.relative_to(root).as_posix()
                if not is_secret(rel):
                    out.append(rel)
                    if len(out) >= code_map.MAX_FILES:
                        break
    return sorted(out)


def read(root: Path, rel: str) -> str:
    f = Path(root) / rel
    try:
        if is_secret(rel) or f.is_symlink() or not f.is_file() or f.stat().st_size > code_map.MAX_BYTES:
            return ""
        return f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def part_of(rel: str) -> str:
    parent = rel.rpartition("/")[0]
    return parent or ROOT


def shape(names: dict[str, list[str]], uses: dict[str, set[str]]) -> list[dict]:
    """`code_map.parts`'s rows: each part, its files (at most code_map.FILES_SHOWN), the parts it uses and those that use it."""
    used_by: dict[str, set[str]] = {p: set() for p in names}
    for p, us in uses.items():
        for u in us:
            if p in names and u in names and u != p:
                used_by[u].add(p)
    return [{"path": p, "files": sorted(names[p])[:code_map.FILES_SHOWN], "count": len(names[p]),
             "uses": sorted(u for u in uses.get(p, ()) if u in names and u != p), "used_by": sorted(used_by.get(p, ()))} for p in sorted(names)]


def cs_uses(root: Path, rels: list[str]) -> tuple[dict[str, list[str]], dict[str, set[str]]]:
    """C# files (relative paths) as parts: ({folder: [file names]}, {folder: {folders it uses}}). A folder uses the folders that declare the namespace
    a file `using`s (`using static X.Y;` too: the longest namespace a folder declares); a file with no namespace declares the global one, which nothing
    uses. A namespace that no folder here declares (`UnityEngine`, `System`) is no use."""
    names: dict[str, list[str]] = {}
    declared: dict[str, set[str]] = {}                   # namespace → the folders that declare it
    wanted: dict[str, set[tuple[bool, str]]] = {}        # folder → (static?, namespace) its files use
    for rel in rels:
        part = part_of(rel)
        names.setdefault(part, []).append(rel.rpartition("/")[2])
        text = read(root, rel)
        if not text:
            continue
        for ns in NAMESPACE.findall(text):
            declared.setdefault(ns, set()).add(part)
        wanted.setdefault(part, set()).update((bool(st), ns) for st, ns in USING.findall(text))
    uses: dict[str, set[str]] = {p: set() for p in names}
    for part, spaces in wanted.items():
        for static, ns in spaces:
            bits = ns.split(".")
            for n in range(len(bits), 0 if static else len(bits) - 1, -1):    # `using static X.Y;` names a class: the longest namespace declared
                hit = declared.get(".".join(bits[:n]))
                if hit:
                    uses[part] |= hit - {part}
                    break
    return names, uses
