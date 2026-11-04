"""What a task made, by its party's craft, read by code for its card's window (docs/specs/142-a-cards-window-where-it-has-something-to-show.md part D, decisions §249.3).
A task done (merged) or being checked (at Review) carries `craft_made` in the snapshot, one of these, by the craft of the party it belongs to; a craft or a task with
nothing of these has no key, and its card keeps the type's sign. (`made` stays the task's first commit subject, board_map.made_of.) No model is called and nothing is
written: git is read, and a file the Board keeps is read.

    task_made.parse_numstat(text)                        # [{"path", "added", "removed"}] of `git diff --numstat --no-renames` (a binary file counts 0 and 0)
    task_made.top_files(files, 3)                        # the three with most lines (added + removed), the most first; ties keep git's order
    task_made.first_image(name_status_text)              # the path of the first image (png, jpg, gif, webp) a `--name-status` text adds or changes, "" for none
    task_made.image_size(data)                           # (w, h) of a png, gif, jpeg or webp read from its first bytes, None when it is none of them
    task_made.range_of(task, slug)                       # (the git range of the task's commits, its tip) from the task as the plan keeps it, or ("", "")
    task_made.diff_of(files)                             # {"kind": "diff", "files": [...]} or None
    task_made.asset_of(url, w, h, name)                  # {"kind": "asset", "url", "w", "h", "name"} or None
    task_made.screen_of(before, after)                   # {"kind": "screen", "before", "after"} or None (no after: none)
    task_made.checks_of(items)                           # {"kind": "checks", "items": [{"name", "state"}]} or None
    task_made.hypothesis_of(items, goal)                 # {"kind": "hypothesis", "text", "state"} of the one the goal tests (else rests on), or None
    task_made.git_made(repo, slug, task, craft, url_of)  # Tech's diff or Art's asset of a task from git, cached per its tip commit, or None

**The kinds, by craft** (`party_recipes.CRAFTS`): `tech` the three files with most lines of the task's commits (`git diff --numstat`: a merged task's `<commit>~n..<commit>`,
n the commits it brought; one at Review its branch since its base); `art` the first image those commits added or changed, as the page can address it (the host signs it,
gui/ideas_map.py: an asset of the commit); `design` the picture of what the task changed that the Board keeps (`idea_shots`, the preview's shot; no *before* is kept
today, so it is ""); `release` the checks on the way into main the host has (§188.3; gui/ideas_gate.py `main_checks_now`); `product` the hypothesis the goal tests
(`realm/hypotheses.py`, §235). **Run and LiveOps have none**: §215's dated events are not in the code yet. The cache is per project, goal, task and its tip commit, so a task
that did not move is not read again; only the git kinds are cached (the others are read from what the host already holds). A git that fails leaves `made` absent.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable

FILES = 3                                   # the files a Tech window names
IMAGES = (".png", ".jpg", ".jpeg", ".gif", ".webp")
MADE_STATES = ("merged", "review", "testing")   # done, or being checked (at the gate or at Review): what it made so far
GIT_TIMEOUT_S = 10
CACHE_MAX = 512
_SHA = re.compile(r"[0-9a-f]{7,64}")
_cache: dict[tuple[str, str, str, str, str], dict | None] = {}


def parse_numstat(text: str) -> list[dict]:
    """`[{"path", "added", "removed"}]` of the lines of `git diff --numstat --no-renames`; a binary file (`-\\t-\\tpath`) counts nothing, a line that is none is left out."""
    out = []
    for line in str(text or "").splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3 or not parts[2].strip():
            continue
        a, r, path = parts
        out.append({"path": path.strip(), "added": int(a) if a.isdigit() else 0, "removed": int(r) if r.isdigit() else 0})
    return out


def top_files(files: list[dict], n: int = FILES) -> list[dict]:
    """The `n` files with most lines changed (added + removed), the most first; equal ones keep their order."""
    return sorted(files, key=lambda f: -(f["added"] + f["removed"]))[:n]


def first_image(name_status: str) -> str:
    """The path of the first image a `git diff --name-status --no-renames` text adds (A) or changes (M); a deleted one is none. "" when there is none."""
    for line in str(name_status or "").splitlines():
        status, _, path = line.partition("\t")
        if status.strip()[:1] in ("A", "M") and path.strip().lower().endswith(IMAGES):
            return path.strip()
    return ""


def image_size(data: bytes) -> tuple[int, int] | None:
    """(width, height) of a png, a gif, a jpeg or a webp, from its first bytes (and a jpeg's markers); None for anything else."""
    d = bytes(data or b"")
    if d[:8] == b"\x89PNG\r\n\x1a\n" and len(d) >= 24:
        return int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big")
    if d[:6] in (b"GIF87a", b"GIF89a") and len(d) >= 10:
        return int.from_bytes(d[6:8], "little"), int.from_bytes(d[8:10], "little")
    if d[:4] == b"RIFF" and d[8:12] == b"WEBP" and len(d) >= 30:
        kind = d[12:16]
        if kind == b"VP8X":
            return 1 + int.from_bytes(d[24:27], "little"), 1 + int.from_bytes(d[27:30], "little")
        if kind == b"VP8 " and d[23:26] == b"\x9d\x01\x2a":
            return int.from_bytes(d[26:28], "little") & 0x3FFF, int.from_bytes(d[28:30], "little") & 0x3FFF
        if kind == b"VP8L" and d[20] == 0x2F:
            bits = int.from_bytes(d[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        return None
    if d[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(d):
            if d[i] != 0xFF:
                i += 1
                continue
            marker = d[i + 1]
            if marker == 0xFF:
                i += 1
            elif marker in (0x01, 0xD8) or 0xD0 <= marker <= 0xD7:
                i += 2
            elif 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                return int.from_bytes(d[i + 7:i + 9], "big"), int.from_bytes(d[i + 5:i + 7], "big")
            else:
                i += 2 + int.from_bytes(d[i + 2:i + 4], "big")
    return None


def range_of(task: dict, slug: str) -> tuple[str, str]:
    """(the git range of a task's commits, the revision that is its tip) from the task as the plan keeps it: a merged task landed `commit` with `subjects` as its
    commits, so `commit~n..commit`; one at Review has its branch (`idea/<goal>/<task>`) and its `base`, so `base...branch`. ("", "") when neither is known."""
    sha = str(task.get("commit") or "")
    if task.get("state") == "merged":
        n = len(task.get("subjects") or [])
        return (f"{sha}~{n}..{sha}", sha) if n > 0 and _SHA.fullmatch(sha) else ("", "")
    base, branch = str(task.get("base") or ""), str(task.get("branch") or f"idea/{slug}/{task.get('id')}")
    return (f"{base}...{branch}", branch) if _SHA.fullmatch(base) else ("", "")


def diff_of(files: list[dict]) -> dict | None:
    got = top_files(files)
    return {"kind": "diff", "files": got} if got else None


def asset_of(url: str, w: int, h: int, name: str) -> dict | None:
    return {"kind": "asset", "url": url, "w": int(w), "h": int(h), "name": name} if url and w > 0 and h > 0 and name else None


def screen_of(before: str, after: str) -> dict | None:
    return {"kind": "screen", "before": before or "", "after": after} if after else None


def checks_of(items: list[dict] | None) -> dict | None:
    rows = [{"name": str(c.get("name") or ""), "state": str(c.get("state") or "waiting")} for c in items or [] if isinstance(c, dict) and c.get("name")]
    return {"kind": "checks", "items": rows} if rows else None


def hypothesis_of(items: list[dict], goal: str) -> dict | None:
    """The hypothesis the goal tests, else the first it rests on (`realm/hypotheses.read(...)["items"]`): `{"kind": "hypothesis", "text", "state"}`; None when it has none."""
    mine = [h for h in items if goal in h.get("tests", [])] or [h for h in items if goal in h.get("rests", [])]
    return {"kind": "hypothesis", "text": mine[0]["text"], "state": mine[0]["state"]} if mine else None


def _git(repo: Path, *args: str) -> bytes | None:
    try:
        got = subprocess.run(["git", *args], cwd=repo, capture_output=True, timeout=GIT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError):
        return None
    return got.stdout if got.returncode == 0 else None


def _tip(repo: Path, rev: str) -> str:
    out = _git(repo, "rev-parse", "--verify", "-q", rev + "^{commit}") if rev else None
    return out.decode().strip() if out else ""


def git_made(repo: Path, slug: str, task: dict, craft: str, url_of: Callable[[str, str], str]) -> dict | None:
    """Tech's `diff` or Art's `asset` of a task, from git; cached by the tip commit. `url_of(commit, path)` is the host's signed address of an asset of a commit."""
    if craft not in ("tech", "art") or task.get("state") not in MADE_STATES:
        return None
    rng, rev = range_of(task, slug)
    tip = _tip(repo, rev) if rng else ""
    if not tip:
        return None
    key = (str(repo), slug, str(task.get("id")), tip, craft)
    if key in _cache:
        return _cache[key]
    got = None
    if craft == "tech":
        out = _git(repo, "diff", "--numstat", "--no-renames", rng)
        got = diff_of(parse_numstat(out.decode("utf-8", "replace"))) if out is not None else None
    else:
        out = _git(repo, "diff", "--name-status", "--no-renames", rng)
        path = first_image(out.decode("utf-8", "replace")) if out else ""
        blob = _git(repo, "show", f"{tip}:{path}") if path else None
        size = image_size(blob) if blob else None
        got = asset_of(url_of(tip, path), *size, Path(path).name) if size else None
    if len(_cache) >= CACHE_MAX:
        _cache.clear()
    _cache[key] = got
    return got
