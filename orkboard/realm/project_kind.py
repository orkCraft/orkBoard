"""What the project is (docs/specs/75-parties-fitted-to-the-project.md §1, decisions §90): the Orkmaster reads the folder's names, never a
model, and says an empty folder, a mobile app, a web app, a backend, a game, data work, a team's wiki, a designer's folder, texts, or code.

    read(root)                    # {"kind": "mobile", "signs": ["ios/", "android/"]}: from the cache while the folder's top level is as it was
    read(root, fresh=True)        # …read again now (`ideas.proposals`)
    scan(root)                    # the same with the facts the recipes ask (`facts`: {"sql": n, "files": n, "pictures": n, ...})
    WORDS["mobile"]               # "a mobile app": the kind as the interface says it
    in_words(["ios/", "android/"])  # "ios/ and android/ are here"

Only names and counts are read: never a file's contents, but `package.json`'s dependencies' names. At most `LIMIT` entries are walked, the
top level first (a folder at a time, breadth first); `.git` and every dot folder are skipped (so the Board's own `.orkcraft/` is), and so are
the Wiki's pages (`pages/tracks/`, `pages/ideas/`) and the folders that hold other people's code (`node_modules/`, `__pycache__/`, `Pods/`).
In this order, the first that holds: empty · mobile · game · web · backend · data · wiki · design · texts · code. No model, no write.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

LIMIT = 2_000                                # entries walked, files and folders together
KINDS = ("empty", "mobile", "game", "web", "backend", "data", "wiki", "design", "texts", "code")
WORDS = {"empty": "an empty folder", "mobile": "a mobile app", "web": "a web app", "backend": "a backend", "game": "a game",
         "data": "data work", "wiki": "a team's wiki", "design": "a designer's folder", "texts": "texts", "code": "code"}
SIGNS = 4                                    # the most signs said
SIGN_CHARS = 40
SKIP_DIRS = {"node_modules", "__pycache__", "Pods"}
BOARD_PAGES = ("pages/tracks", "pages/ideas")   # the Wiki's pages of the Board (realm/ideas.py): not the project's
EMPTY_OK = {"readme", "license", "licence", "orkcraft.toml"}      # a stem: a README (any extension), a licence, the gate's file
WEB_DEPS = ("react", "next", "vue", "svelte", "vite", "astro")
MOBILE_DEPS = ("react-native", "expo")
MOBILE_FILES = ("pubspec.yaml", "AndroidManifest.xml")
GAME_FILES = ("project.godot",)
BACKEND_FILES = ("pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml", "Gemfile", "Dockerfile")
CODE = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".kts", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp",
        ".cs", ".rb", ".php", ".scala", ".lua", ".sh", ".dart", ".m", ".mm", ".r", ".jl", ".ex", ".exs", ".clj", ".hs", ".vue", ".svelte", ".gd",
        ".sql", ".ipynb"}
DATA_CODE = {".ipynb", ".sql"}
PICTURES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".fig", ".sketch", ".psd", ".ai", ".pen"}
DOCUMENTS = {".md", ".txt", ".docx", ".pdf"}
MARKDOWN = {".md", ".markdown"}

_cache: dict[str, tuple[tuple, dict]] = {}


def _deps(path: Path) -> set[str]:
    """The names of a `package.json`'s dependencies (never a version or a script); empty for a file that is not JSON."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    out: set[str] = set()
    if isinstance(data, dict):
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            if isinstance(data.get(key), dict):
                out |= {str(k) for k in data[key]}
    return out


def _walk(root: Path) -> dict[str, Any]:
    """The names under `root`, at most LIMIT entries: the top level's names and its dot folders', every file's extension counted, and the
    folders' names by their relative path."""
    top: list[tuple[str, bool]] = []                 # (name, is a folder) at the top level, dot ones too
    files: list[tuple[str, str]] = []                # (relative path, name) of every file walked, no dot ones
    dirs: list[str] = []                             # relative paths of the folders walked
    seen, queue = 0, [""]
    while queue and seen < LIMIT:
        rel = queue.pop(0)
        try:
            it = os.scandir(root / rel if rel else root)
        except OSError:
            continue
        with it:
            for entry in it:
                if seen >= LIMIT:
                    break
                name = entry.name
                path = f"{rel}/{name}" if rel else name
                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                except OSError:
                    continue
                if not rel:
                    top.append((name, is_dir))
                seen += 1
                if name.startswith("."):
                    continue
                if is_dir:
                    if name in SKIP_DIRS or path in BOARD_PAGES or path.endswith(tuple("/" + p for p in BOARD_PAGES)):
                        continue
                    dirs.append(path)
                    queue.append(path)
                else:
                    files.append((path, name))
    return {"top": top, "files": files, "dirs": dirs, "seen": seen}


def _suffix(name: str) -> str:
    return os.path.splitext(name)[1].lower()


def _signs(*parts: str) -> list[str]:
    return [p[:SIGN_CHARS] for p in parts if p][:SIGNS]


def scan(root: Path) -> dict[str, Any]:
    """`{"kind", "signs", "facts"}`: what the folder is, what it was seen by, and the counts the recipes ask (`sql`, `files`, `code`,
    `pictures`, `documents`, `markdown`, `notebooks`, `seen`)."""
    root = Path(root)
    w = _walk(root)
    files, dirs = w["files"], w["dirs"]
    names = {n for _p, n in files}
    top_files = {n for n, d in w["top"] if not d}
    top_dirs = {n for n, d in w["top"] if d}
    ext = Counter(_suffix(n) for _p, n in files)
    code = sum(c for e, c in ext.items() if e in CODE)
    other_code = sum(c for e, c in ext.items() if e in CODE and e not in DATA_CODE)
    data_code = sum(ext[e] for e in DATA_CODE)
    pictures = sum(c for e, c in ext.items() if e in PICTURES)
    documents = sum(c for e, c in ext.items() if e in DOCUMENTS)
    markdown = sum(c for e, c in ext.items() if e in MARKDOWN)
    n = len(files)
    facts = {"sql": ext[".sql"], "notebooks": ext[".ipynb"], "files": n, "code": code, "pictures": pictures, "documents": documents,
             "markdown": markdown, "seen": w["seen"]}

    def done(kind: str, signs: list[str]) -> dict[str, Any]:
        return {"kind": kind, "signs": _signs(*signs), "facts": facts}

    # empty: no file but dot files, a README and the Board's
    if not [x for x in names if os.path.splitext(x)[0].lower() not in EMPTY_OK and x.lower() not in EMPTY_OK]:
        return done("empty", [])

    package = _deps(root / "package.json") if "package.json" in top_files else set()
    # mobile
    sign = [f"{d}/" for d in ("ios", "android") if d in top_dirs]
    if "pubspec.yaml" in top_files:
        sign.append("pubspec.yaml")
    if hit := [d for d in MOBILE_DEPS if d in package]:
        sign.append(f"package.json: {hit[0]}")
    if any(p.endswith(".xcodeproj") for p in dirs):
        sign.append(".xcodeproj")
    if "AndroidManifest.xml" in names and not sign:
        sign.append("AndroidManifest.xml")
    if sign:
        return done("mobile", sign)
    # game
    sign = [f for f in GAME_FILES if f in top_files]
    if "ProjectSettings" in top_dirs:
        sign.append("ProjectSettings/")
    sign += [n_ for n_ in sorted(names) if n_.endswith(".uproject")][:1]
    if sign:
        return done("game", sign)
    # web
    sign = [f"package.json: {d}" for d in WEB_DEPS if d in package][:2]
    if "index.html" in top_files:
        sign.append("index.html")
    if sign:
        return done("web", sign)
    # backend
    sign = [f for f in BACKEND_FILES if f in top_files]
    if sign:
        return done("backend", sign + ([f"{ext['.sql']} .sql files"] if ext[".sql"] else []))
    # data
    if "dbt_project.yml" in top_files:
        return done("data", ["dbt_project.yml"])
    if data_code and data_code > other_code:
        return done("data", [p for p in (f"{ext['.ipynb']} notebooks" if ext[".ipynb"] else "", f"{ext['.sql']} .sql files" if ext[".sql"] else "")])
    # wiki, design, texts: a folder with no code
    if not code:
        sign = [f"{d}/" for d in (".obsidian",) if d in {x for x, _d in w["top"]}]
        if "mkdocs.yml" in top_files:
            sign.append("mkdocs.yml")
        for d in ("docs", "pages"):
            if any(p.startswith(f"{d}/") and _suffix(p) in MARKDOWN for p, _n in files):
                sign.append(f"{d}/")
        if markdown * 2 > n and not sign:
            sign.append(f"{markdown} Markdown pages")
        if sign:
            return done("wiki", sign)
        if pictures * 2 > n:
            return done("design", [f"{pictures} pictures"] + ([".fig"] if ext[".fig"] else []) + ([".sketch"] if ext[".sketch"] else []))
        if documents * 2 > n:
            return done("texts", [f"{documents} documents"])
    most = [e for e, _c in Counter({e: c for e, c in ext.items() if e in CODE}).most_common(1)]
    return done("code", [f"{ext[most[0]]} {most[0]} files"] if most else [])


def _stamp(root: Path) -> tuple:
    """What the cache is keyed by: the root's and its top-level folders' modified times, and `package.json`'s (a file edited in place
    does not move its folder's)."""
    try:
        marks = [os.stat(root).st_mtime_ns]
        with os.scandir(root) as it:
            for e in it:
                if e.name == "package.json" or (e.is_dir(follow_symlinks=False) and not e.name.startswith(".")):
                    marks.append(e.stat(follow_symlinks=False).st_mtime_ns)
        return tuple(sorted(marks))
    except OSError:
        return ()


def read(root: Path, fresh: bool = False) -> dict[str, Any]:
    """`{"kind", "signs"}` (§1). Kept by the root and its top level's modified times, so `ideas.map` does not walk the folder on every read;
    `fresh` reads it again and keeps that. A folder that cannot be read is `empty`."""
    full = read_full(root, fresh)
    return {"kind": full["kind"], "signs": list(full["signs"])}


def read_full(root: Path, fresh: bool = False) -> dict[str, Any]:
    key = str(Path(root))
    stamp = _stamp(Path(root))
    got = _cache.get(key)
    if got is not None and got[0] == stamp and not fresh:
        return got[1]
    out = scan(Path(root))
    _cache[key] = (stamp, out)
    return out


def words(kind: str) -> str:
    return WORDS.get(kind, WORDS["code"])


def in_words(signs: list[str]) -> str:
    """The signs said as a line (`why` of a proposal): "ios/ and android/ are here"; "" with none."""
    if not signs:
        return ""
    head = signs[0] if len(signs) == 1 else ", ".join(signs[:-1]) + " and " + signs[-1]
    return f"{head} {'is' if len(signs) == 1 else 'are'} here"
