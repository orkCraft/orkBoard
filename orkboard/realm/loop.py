"""Game design's loop (docs/specs/102-the-other-maps-and-picking-on-them.md §2; decisions §112.8, §156.3): four to six cards the person and Game design's leader keep,
each tied to the files it rests on. Read by code, no model (the leader's first proposal is `core/idea_loop.py`'s); no face.

    loop.read(state_dir)                           # the cards kept: [{id, name, line, rests_on: [paths], by: "person"|"leader", at}], in order; [] before any
    loop.keep(state_dir, root, cards, by)          # the cards replaced whole → (kept, dropped): four to six, names and lines bounded, a `rests_on` path only where dev's tree has it
    loop.parse(answer, root)                       # the leader's answer, strictly → [{name, line, rests_on}] (four to six cards) or None
    loop.config_files(root)                        # the project's configs by name, chosen by code from dev's tree: balance*, config/, levels/, *.config.*; bounded
    loop.heads(root, paths)                        # {path: its first lines} of the first few of them, bounded
    loop.text(state_dir, root, since="")           # the cards in order as text for a leader's call (~3,000 characters); None when none is kept
    loop.proposal(state_dir) / save_proposal(...)   # what the first proposal did: {status: "asking"|"done"|"failed", error, at}

`<state_dir>/loop.json` is `{cards: [...], proposal: {...}}`. A card's `id` stays with it (a name's slug at first); a card kept again unchanged keeps its `by` and `at`, so the
leader's cards the person did not touch stay *Proposed by the leader*. A `rests_on` path is a file of dev's tree or a folder of it, posix, relative, never a secret's; one that
is not is dropped and said (`dropped`), never kept. With no `dev` branch no path can be checked, so none is kept. The text is the same bytes for the same record and the
same dev head; with `since` (the commit of the party's last call) it ends with what changed under the cards' files, each with its goal.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from orkboard.hooks.warder import is_secret
from orkboard.realm import commit_goal, ideas

FILE = "loop.json"
REF = "dev"
MIN_CARDS, MAX_CARDS = 4, 6
NAME_CHARS, LINE_CHARS = 40, 160
PATHS, PATH_CHARS = 6, 200            # the most files a card rests on; one path's length
LIMIT = 3000                          # the text, at most (map_text.LIMIT's)
CHANGED = 1200                        # … and what changed under the cards, at most (map_text.CHANGED's)
SHOWN = 3                             # the most files a card's line names in the text
CONFIGS, PER_FOLDER = 40, 8           # the most config files named, and of one folder
HEAD_FILES, HEAD_LINES, HEAD_CHARS, HEAD_TOTAL = 10, 6, 300, 2500
READ_BYTES = 200_000                  # a file larger than this is named, never read
_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
_WORDS = re.compile(r"[a-z0-9]+")
_MODES = ("100644", "100755")
_SKIP = {"node_modules", "vendor", "dist", "build", "target", "venv", ".venv", "__pycache__", ".git", ".next", "Pods"}
_TEXT = {".json", ".jsonc", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".tsv", ".txt", ".xml", ".lua", ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".cs",
         ".gd", ".tres", ".tscn", ".tmx", ".ldtk", ".dart", ".kt", ".java", ".rs", ".go", ".swift", ".md"}
BY = ("person", "leader")


def _words(value: object, n: int) -> str:
    return " ".join(value.split())[:n] if isinstance(value, str) else ""


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:max(0, n - 1)].rstrip() + "…"


def _file(state_dir: Path) -> Path:
    return Path(state_dir) / FILE


def _record(state_dir: Path) -> dict:
    got = ideas._json(_file(state_dir))
    return got if isinstance(got, dict) else {}


# -- dev's tree -----------------------------------------------------------------------------------------------------------------------

def tree(root: Path) -> dict[str, int]:
    """`{path: bytes}` of the files of dev's head (`git ls-tree -r -l`: blobs only, no link, no submodule); {} with no `dev`."""
    tip = commit_goal.head(Path(root), REF)
    if not tip:
        return {}
    try:
        got = commit_goal.git(Path(root), "ls-tree", "-r", "-l", "-z", tip)
    except (OSError, subprocess.SubprocessError):
        return {}
    out: dict[str, int] = {}
    for row in got.stdout.split("\0") if got.returncode == 0 else []:
        head, _, path = row.partition("\t")
        bits = head.split()
        if len(bits) == 4 and bits[0] in _MODES and bits[1] == "blob" and bits[3].isdigit() and path:
            out[path] = int(bits[3])
    return out


def _folders(files: dict[str, int]) -> set[str]:
    return {"/".join(p.split("/")[:n]) for p in files for n in range(1, len(p.split("/")))}


def _path(raw: object) -> str:
    """A path as it is kept (posix, relative, no `..`, no secret, bounded), "" for one that is none."""
    if not isinstance(raw, str):
        return ""
    path = raw.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    path = path.strip("/")
    bits = path.split("/")
    if not path or len(path) > PATH_CHARS or any(b in ("", ".", "..") for b in bits) or "\0" in path or is_secret(path):
        return ""
    return path


def _rests(raw: object, have: set[str]) -> tuple[list[str], list[str]]:
    """(the paths kept, the paths dropped) of a card's `rests_on`: each a file or a folder of dev's tree, once, at most PATHS."""
    if not isinstance(raw, list):
        raise ValueError("What a card rests on is a list of files")
    kept: list[str] = []
    dropped: list[str] = []
    for item in raw:
        path = _path(item)
        if path and path in kept:
            continue
        if path and path in have and len(kept) < PATHS:
            kept.append(path)
        elif isinstance(item, str) and item.strip():
            dropped.append(item.strip()[:PATH_CHARS])
    return kept, dropped


# -- the cards kept -------------------------------------------------------------------------------------------------------------------

def read(state_dir: Path) -> list[dict]:
    """The cards kept, each checked: whatever is not of the shape reads as absent (the file is not trusted)."""
    rows = _record(state_dir).get("cards")
    out: list[dict] = []
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict):
            continue
        name, line = _words(r.get("name"), NAME_CHARS), _words(r.get("line"), LINE_CHARS)
        if not (name and line and isinstance(r.get("id"), str) and _ID.fullmatch(r["id"])):
            continue
        paths = [p for p in (_path(x) for x in r["rests_on"]) if p][:PATHS] if isinstance(r.get("rests_on"), list) else []
        out.append({"id": r["id"], "name": name, "line": line, "rests_on": paths, "by": r["by"] if r.get("by") in BY else "person", "at": str(r.get("at") or "")})
    return out[:MAX_CARDS]


def _id_of(name: str, taken: set[str]) -> str:
    base = "-".join(_WORDS.findall(name.lower()))[:36].strip("-") or "card"
    out, n = base, 1
    while out in taken:
        n += 1
        out = f"{base}-{n}"
    return out


def _clean(cards: object, have: set[str]) -> tuple[list[dict], list[dict]]:
    """The cards as they would be kept, before their `id`, `by` and `at`: [{id?, name, line, rests_on}], and what was dropped [{name, path}]. ValueError in plain words."""
    if not isinstance(cards, list) or not MIN_CARDS <= len(cards) <= MAX_CARDS:
        raise ValueError(f"A loop has {MIN_CARDS} to {MAX_CARDS} cards")
    out, dropped, seen = [], [], set()
    for c in cards:
        if not isinstance(c, dict):
            raise ValueError("A card is a name, a line and the files it rests on")
        name, line = _words(c.get("name"), NAME_CHARS), _words(c.get("line"), LINE_CHARS)
        if not name or not line:
            raise ValueError("A card has a name and a line")
        if name.lower() in seen:
            raise ValueError(f"Two cards are named {name}")
        seen.add(name.lower())
        kept, lost = _rests(c.get("rests_on", []), have)
        dropped += [{"name": name, "path": p} for p in lost]
        out.append({"id": c.get("id") if isinstance(c.get("id"), str) else "", "name": name, "line": line, "rests_on": kept})
    return out, dropped


def keep(state_dir: Path, root: Path, cards: object, by: str) -> tuple[list[dict], list[dict]]:
    """The loop replaced whole by `cards` (`[{id?, name, line, rests_on}]`) → (the cards kept, what was dropped `[{name, path}]`). `by` is who kept them: "person" or "leader"; a
    card that is the same as the one kept under its `id` keeps its own `by` and `at`. ValueError, in plain words, for a `by` that is none, a count outside four to six, a card with no
    name or line, two cards of one name; a path that is not a file or folder of dev's tree is dropped, not refused."""
    if by not in BY:
        raise ValueError(f"A loop is kept by the person or the leader, not {by!r}")
    files = tree(Path(root))
    clean, dropped = _clean(cards, set(files) | _folders(files))
    with ideas.LOCK:
        before = {c["id"]: c for c in read(state_dir)}
        taken: set[str] = set()
        now, kept = ideas._now(), []
        for c in clean:
            old = before.get(c["id"]) if c["id"] not in taken else None
            same = old is not None and (old["name"], old["line"], old["rests_on"]) == (c["name"], c["line"], c["rests_on"])
            cid = old["id"] if old is not None else _id_of(c["name"], taken | set(before))
            taken.add(cid)
            kept.append({"id": cid, "name": c["name"], "line": c["line"], "rests_on": c["rests_on"], "by": old["by"] if same else by, "at": old["at"] if same else now})
        ideas._write_json(_file(state_dir), {**_record(state_dir), "cards": kept})
    return kept, dropped


def parse(answer: object, root: Path) -> list[dict] | None:
    """The leader's answer, strictly: `{cards: [{name, line, rests_on}]}` with four to six cards, each a name and a line, no two of one name, `rests_on` (when there) a list; the paths
    it names that dev's tree does not have are left out. None for anything else (the call is tried once more)."""
    items = answer.get("cards") if isinstance(answer, dict) else None
    if not isinstance(items, list):
        return None
    files = tree(Path(root))
    try:
        clean, _dropped = _clean([{k: v for k, v in c.items() if k != "id"} if isinstance(c, dict) else c for c in items], set(files) | _folders(files))
    except ValueError:
        return None
    return [{k: c[k] for k in ("name", "line", "rests_on")} for c in clean]


def proposal(state_dir: Path) -> dict:
    """What the first proposal did: `{status: "" | "asking" | "done" | "failed", error, at}`."""
    got = _record(state_dir).get("proposal")
    got = got if isinstance(got, dict) else {}
    return {"status": got.get("status") if got.get("status") in ("asking", "done", "failed") else "", "error": str(got.get("error") or "")[:300], "at": str(got.get("at") or "")}


def save_proposal(state_dir: Path, status: str, error: str = "") -> None:
    """The proposal's state kept beside the cards (`status` "" forgets it: the next press asks again)."""
    with ideas.LOCK:
        rec = _record(state_dir)
        if status:
            rec["proposal"] = {"status": status, "error": " ".join(str(error).split())[:300], "at": ideas._now()}
        else:
            rec.pop("proposal", None)
        ideas._write_json(_file(state_dir), rec)


# -- the project's configs, chosen by code --------------------------------------------------------------------------------------------

def _class_of(path: str) -> int | None:
    """Why a file is a config of the game's: 0 `balance*`, 1 a `config/` folder's, 2 a `levels/` folder's, 3 `*.config.*`; None for one that is none."""
    bits = path.split("/")
    if any(b in _SKIP or b.startswith(".") for b in bits[:-1]) or is_secret(path) or Path(bits[-1]).suffix.lower() not in _TEXT:
        return None
    name = bits[-1].lower()
    if name.startswith("balance"):
        return 0
    if "config" in (b.lower() for b in bits[:-1]):
        return 1
    if "levels" in (b.lower() for b in bits[:-1]):
        return 2
    return 3 if ".config." in name else None


def config_files(root: Path) -> list[str]:
    """The files of dev's tree that are the game's configs, by name (CONFIGS at most, PER_FOLDER of one folder): `balance*`, then `config/`'s, `levels/`'s and `*.config.*`; shallow
    first, then by path. [] with no `dev`."""
    found = sorted(((c, p.count("/"), p) for p in tree(Path(root)) if (c := _class_of(p)) is not None))
    out: list[str] = []
    per: dict[str, int] = {}
    for _c, _depth, path in found:
        folder = path.rpartition("/")[0]
        if per.get(folder, 0) >= PER_FOLDER:
            continue
        per[folder] = per.get(folder, 0) + 1
        out.append(path)
        if len(out) >= CONFIGS:
            break
    return out


def heads(root: Path, paths: list[str]) -> dict[str, str]:
    """`{path: its first HEAD_LINES lines}` (each cut to HEAD_CHARS) of the first HEAD_FILES of `paths` that dev's tree has, a file too large or not text left out; HEAD_TOTAL
    characters at most in all."""
    files = tree(Path(root))
    tip = commit_goal.head(Path(root), REF)
    out: dict[str, str] = {}
    used = 0
    for path in [p for p in paths if p in files][:HEAD_FILES]:
        if files[path] > READ_BYTES or is_secret(path) or not tip:
            continue
        try:
            got = commit_goal.git(Path(root), "--literal-pathspecs", "show", f"{tip}:{path}")
        except (OSError, subprocess.SubprocessError):
            continue
        if got.returncode != 0 or "\0" in got.stdout[:2000]:
            continue
        text = _cut("\n".join(got.stdout.replace("\r\n", "\n").split("\n")[:HEAD_LINES]).strip(), HEAD_CHARS)
        if not text or used + len(text) > HEAD_TOTAL:
            continue
        out[path] = text
        used += len(text)
    return out


# -- its text -------------------------------------------------------------------------------------------------------------------------

def _card(n: int, c: dict) -> str:
    files = c["rests_on"]
    rests = ", ".join(_cut(f, 80) for f in files[:SHOWN]) + (f", +{len(files) - SHOWN}" if len(files) > SHOWN else "") if files else "no file named"
    return f"{n}. {c['name']}: {c['line']}\n   Rests on: {rests}"


def _fit(lines: list[str], room: int, more: str) -> list[str]:
    if sum(len(ln) + 1 for ln in lines) <= room + 1:
        return list(lines)
    reserve = len(more.format(n=len(lines))) + 1
    out, used = [], 0
    for line in lines:
        if used + len(line) + 1 + reserve > room + 1:
            break
        out.append(line)
        used += len(line) + 1
    return out + [more.format(n=len(lines) - len(out))]


def _changed(state_dir: Path, root: Path, cards: list[dict], since: str) -> str:
    """*Changed since your last call*, under the cards: each card's file (or a file in its folder) a commit of dev touched since `since`, with the goal that made it (`by you` for the
    person's own)."""
    head = "Changed under the loop since your last call"
    base = commit_goal.resolve(Path(root), since)
    if not base:
        return f"{head}: not known (no map was kept at that commit)."
    touched = commit_goal.last_touch(Path(root), REF, base)
    rows = []
    for c in cards:
        for path in c["rests_on"]:
            for file in sorted(f for f in touched if f == path or f.startswith(path + "/")):
                goal = commit_goal.of(state_dir, root, touched[file]["sha"]).get("goal")
                rows.append(f"- {c['name']}: {file} ({f'goal {goal}' if goal else 'by you'})")
    if not rows:
        return f"{head}: nothing."
    return "\n".join([f"{head}:"] + _fit(rows, CHANGED - len(head) - 2, "- and {n} more changes"))


def text(state_dir: Path, root: Path, since: str = "") -> str | None:
    """Game design's map as text: the cards in order, each its name, its line and what it rests on, after a first line naming dev's head (`The map of the loop at dev <short>`); LIMIT
    characters at most. The same bytes for the same record and the same head. None when no card is kept. With `since` (the commit of the party's last call) ends with what changed under
    the cards' files."""
    cards = read(state_dir)
    if not cards:
        return None
    tip = commit_goal.head(Path(root), REF)
    lines = [f"The map of the loop at dev {tip[:7]}" if tip else "The map of the loop", ""]
    body = "\n".join(lines + [_card(n, c) for n, c in enumerate(cards, 1)])[:LIMIT]
    since = str(since or "").strip()
    return body + "\n\n" + _changed(Path(state_dir), Path(root), cards, since) if since else body
