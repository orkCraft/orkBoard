"""Where you are on the running product (docs/specs/115-the-live-product-under-each-leaders-eyes.md §3, decisions §193): a page's path and the files the probe named → the parts of every
map that this place touches, by rule, from the newest snapshot of dev (the maps' own reads, never a model). No model, no face.

    play_place.screen(state_dir, root, path)                          # Design's screen the path reaches: {id, name, step} or None (screen_map.screen_of)
    play_place.parts(state_dir, root, path, files=(), pages=None)     # {map: [{id, name}]} of every map this place touches; {} when none

`path` is the page's (`location.pathname`, a route in the hash too); `files` the repository files the probe named for the element (a dev build's `data-source`; a path with a line and a
column, a `./`, or the project's own folder in front is read as the file it names); `pages` where the Board's pages are, for Product's goals (without it Product has none). The keys are the
maps' ids and the parts carry the very ids the maps' faces stamp (`realm/map_parts.py`), so a mark can pick them:
- `screens` (Design): the screen the path reaches.
- `system` (Tech): the parts whose folder holds a named file (the file's own folder, else the deepest part above it), else, with none named or none held, the screen's component file's.
- `art` (Art): the assets whose file name the screen's file or a named file holds (as Art's *unused* hint reads a name: `git grep -F` at dev's head).
- `marketing` (Marketing): the files of the way in that are the screen's file or a named one.
- `game-design` (Game design): the loop's steps that rest on one of them (the file itself, or a folder holding it).
- `product` (Product): the jobs a goal serves whose `touches` (`realm/collide.py`) hold one of them; weak by nature, none is fine.
Release has no place on a screen. A map that has nothing here has no key; at most MAX_PARTS parts a map; a map that cannot be read gives nothing, never an exception.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from orkboard.hooks.warder import is_secret
from orkboard.realm import art_map, collide, commit_goal, loop, opportunity_tree, project_map, screen_map, way_map

MAX_PARTS = 10                                   # the most parts of one map
MAX_FILES = 12                                   # the most files named that are read
MAX_NAMES = 400                                  # the most asset names looked for in the files
_POSITION = re.compile(r"(?::\d+){1,2}$")


def _file(root: Path, raw: object) -> str:
    """A file the probe named as a path of the repository (posix, relative, no secret): "" for what is not one. Its `file://`, its `:line:column` and its `./` are taken off; an absolute path
    is the file's only under the project's own folder."""
    if not isinstance(raw, str):
        return ""
    text = _POSITION.sub("", raw.strip().replace("\\", "/")).removeprefix("file://").split("?")[0]
    base = root.as_posix().rstrip("/") + "/"
    if text.startswith(base):
        text = text[len(base):]
    elif text.startswith("/") and root.is_absolute():
        return ""                                # an absolute path outside the project is a machine's, not a repository file
    while text.startswith("./"):
        text = text[2:]
    text = text.strip("/")
    bits = text.split("/")
    if not text or len(text) > 300 or any(b in ("", ".", "..") for b in bits) or "\0" in text or is_secret(text):
        return ""
    return text


def _files(root: Path, files: object, screen_file: str) -> tuple[list[str], list[str]]:
    """(the files the probe named, those and the screen's file), each once, bounded, as paths of the repository."""
    named = list(dict.fromkeys(f for f in (_file(root, x) for x in (files if isinstance(files, (list, tuple)) else ())) if f))[:MAX_FILES]
    return named, list(dict.fromkeys(named + ([screen_file] if screen_file else [])))


def _under(path: str, folder: str) -> bool:
    """Whether `path` is `folder` or lies in it (`folder` as a loop step's `rests_on` or a goal's `touches` names it, with or without a trailing slash)."""
    folder = folder.rstrip("/")
    return path == folder or path.startswith(folder + "/")


# -- the maps ---------------------------------------------------------------------------------------------------------------------------

def screen(state_dir: Path, root: Path, path: str) -> dict | None:
    """Design's screen the path reaches, `{id, name, step}`; None for a path no screen fits."""
    try:
        return screen_map.screen_of(state_dir, root, path)
    except Exception:                            # a map that cannot be read has no place
        return None


def _system(state_dir: Path, root: Path, named: list[str], screen_file: str) -> list[dict]:
    tip = commit_goal.head(root, screen_map.REF)
    snap = (project_map.read(state_dir, tip) if tip else None) or project_map.newest(state_dir) or project_map.ensure(state_dir, root, screen_map.REF)
    held = sorted({p["path"] for p in (snap or {}).get("parts") or [] if isinstance(p, dict) and isinstance(p.get("path"), str) and p["path"]})
    if not held:
        return []

    def part_of(file: str) -> str:
        folder = file.rpartition("/")[0] or project_map.TOP
        if folder in held:
            return folder
        above = [p for p in held if p != project_map.TOP and _under(folder, p)]
        return max(above, key=len) if above else ""

    found = list(dict.fromkeys(p for p in (part_of(f) for f in named) if p))
    if not found and screen_file:
        found = [p for p in [part_of(screen_file)] if p]
    return [{"id": p, "name": p} for p in found]


def _text_names(root: Path, sha: str, names: list[str], files: list[str]) -> set[str]:
    """The names among `names` that one of `files` holds at `sha` (`git grep -F -o -h`); empty when none is or git could not say."""
    args = ["--literal-pathspecs", "-c", "core.quotePath=false", "grep", "-F", "-o", "-h", "-I", *[x for n in names for x in ("-e", n)], sha, "--", *files]
    try:
        got = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, errors="replace", timeout=commit_goal.GIT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError):
        return set()
    return set(got.stdout.splitlines()) if got.returncode == 0 else set()


def _art(state_dir: Path, root: Path, files: list[str]) -> list[dict]:
    got = art_map.read(state_dir, root)
    if not got["commit"] or not files:
        return []
    rows = sorted((a for k in got["kinds"] if k["kind"] != "screen" for a in k["assets"]), key=lambda a: a["id"])
    names = sorted({a["name"] for a in rows})[:MAX_NAMES]
    found = _text_names(root, got["commit"], names, files) if names else set()
    return [{"id": a["id"], "name": a["name"]} for a in rows if a["name"] in found]


def _marketing(state_dir: Path, root: Path, files: list[str]) -> list[dict]:
    got = way_map.read(state_dir, root)
    return [{"id": h["path"], "name": h["path"].rsplit("/", 1)[-1]} for step in got["steps"] for h in (got.get(step) or {}).get("holds") or [] if h["path"] in files]


def _loop(state_dir: Path, files: list[str]) -> list[dict]:
    return [{"id": st["id"], "name": st["name"]} for lp in loop.read(Path(state_dir)).get("loops") or [] for st in lp.get("steps") or []
            if st.get("id") and st.get("name") and any(_under(f, r) for r in st.get("rests_on") or [] for f in files)]


def _product(state_dir: Path, pages: Path, files: list[str]) -> list[dict]:
    rec = opportunity_tree.read(state_dir)
    touched: dict[str, bool] = {}
    jobs: set[str] = set()
    for s in rec["serves"]:
        if s["goal"] not in touched:
            touched[s["goal"]] = any(_under(f, t) for t in collide.touches(pages, state_dir, s["goal"]) for f in files)
        if touched[s["goal"]]:
            jobs.add(s["job"])
    return [{"id": j["id"], "name": j["want"]} for j in rec["jobs"] if j["id"] in jobs]


def parts(state_dir: Path, root: Path, path: str, files: object = (), pages: Path | None = None) -> dict[str, list[dict]]:
    """The parts of every map this place touches, `{map: [{id, name}]}` (see the module); {} when it touches none."""
    state_dir, root = Path(state_dir), Path(root)
    here = screen(state_dir, root, path)
    screen_file = ""
    if here:
        try:
            screen_file = screen_map.file_of(root, here["id"])
        except Exception:
            pass
    named, every = _files(root, files, screen_file)
    reads = {"screens": lambda: [{"id": here["id"], "name": here["name"]}] if here else [],
             "system": lambda: _system(state_dir, root, named, screen_file),
             "art": lambda: _art(state_dir, root, every),
             "marketing": lambda: _marketing(state_dir, root, every),
             "game-design": lambda: _loop(state_dir, every),
             "product": lambda: _product(state_dir, Path(pages), every) if pages is not None else []}
    out: dict[str, list[dict]] = {}
    for map_id, read in reads.items():
        try:
            rows = read()[:MAX_PARTS]
        except Exception:                        # a map that cannot be read gives nothing here
            rows = []
        if rows:
            out[map_id] = rows
    return out
