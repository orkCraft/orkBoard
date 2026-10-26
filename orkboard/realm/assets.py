"""What the project is made of that people see or hear (docs/specs/88-assets-and-play.md §1–§4, decisions §104.11): its screens,
art and icons, sounds, music, clips and fonts, read from dev's tree (never the working tree), the picks and git. No model, no face.

    changes = assets.changed(state_dir, root, since)       # {"since", "added": [...], "changed": [...], "removed": [...]}, each with its goal
    rows = assets.listed(state_dir, root, "dev", changes)  # [{"id": path, "kind", "name", "bytes", "w", "h", "seconds", "goal", "task", "at", …}]
    assets.stacks(rows)                                    # [{"folder", "kind", "n"}]: a folder of one kind with more than six files
    assets.before(state_dir, root, path, since)            # the file as it was at `since`, written once into the before-cache; None when added since
    assets.materialize(state_dir, root, commit, path)      # a file of a commit, from the cache (written once): what gui/media.py serves

A kind is the file's extension (and, for a sound, its path or length): **art** `png jpg jpeg webp gif svg`, **sound** `wav ogg mp3 flac`
under a folder naming `sfx`, `sound(s)` or `audio`, or shorter than SOUND_S when its header says, **music** the other sounds, **clip**
`mp4 webm mov`, **font** `ttf otf woff woff2`; a **screen** is a task's newest picture (realm/idea_shots.py). Left out: the folders
code_map.SKIP names and any hidden folder, `design/looks/` (a look picked is the pick's), a file over MAX_BYTES, a file `is_secret` names,
a link or a submodule. A file's size and length are read from its bytes once and kept by its blob (`measured.json`).

The before-cache is `<state_dir>/assets-before/<commit>/<path>`: a file of a commit, written once from git (`git cat-file`), the newest
CACHE_KEEP commits kept. Nothing outside it and the repository's objects is ever read for a face.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from orkboard.hooks.warder import is_secret
from orkboard.realm import code_map, commit_goal, idea_pick, idea_shots, ideas, media_sniff

KINDS = ("screen", "art", "sound", "music", "clip", "font")          # the order the faces lay them out in (spec 88 §0)
EXT = {"png": ("art", "image/png"), "jpg": ("art", "image/jpeg"), "jpeg": ("art", "image/jpeg"), "webp": ("art", "image/webp"),
       "gif": ("art", "image/gif"), "svg": ("art", "image/svg+xml"),
       "wav": ("sound", "audio/wav"), "ogg": ("sound", "audio/ogg"), "mp3": ("sound", "audio/mpeg"), "flac": ("sound", "audio/flac"),
       "mp4": ("clip", "video/mp4"), "webm": ("clip", "video/webm"), "mov": ("clip", "video/quicktime"),
       "ttf": ("font", "font/ttf"), "otf": ("font", "font/otf"), "woff": ("font", "font/woff"), "woff2": ("font", "font/woff2")}
MAX_ASSETS = 600
MAX_BYTES = 50 * 1024 * 1024
STACK_OVER = 6                       # a folder of one kind with more files than this is a stack (×n, spec 50 §3.4)
SOUND_S = 10.0                       # a sound shorter than this is a sound, longer music
SOUND_DIR = re.compile(r"(?:^|[-_. ])(?:sfx|sounds?|audio)(?:$|[-_. ])", re.I)
LOOKS = "design/looks/"
CACHE = "assets-before"
CACHE_KEEP = 16
MEASURED = "measured.json"
MEASURED_MAX = 5_000
MEASURE_S = 8.0                      # the most one listing spends reading new files' headers; the rest are read next time
PATH_MAX, NAME_MAX = 1000, 255
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_MODES = ("100644", "100755")


def _git(root: Path, *args: str, text: bool = True, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--literal-pathspecs", "-c", "core.quotePath=false", *args], cwd=root, capture_output=True,
                          text=text, timeout=timeout, **({"errors": "replace"} if text else {}))


# -- what a path is ----------------------------------------------------------------------------------------------------

def ext_of(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return name.rsplit(".", 1)[-1].lower() if "." in name.lstrip(".") else ""


def allowed(path: object) -> bool:
    """Whether `path` may be an asset: a plain relative path inside the repository (no `..`, `.`, empty part, backslash or control
    character), of a known extension, in no skipped or hidden folder, not under `design/looks/`, and no secret's."""
    if not isinstance(path, str) or not path or len(path) > PATH_MAX or path.startswith("/") or "\\" in path or _CONTROL.search(path):
        return False
    parts = path.split("/")
    if any(p in ("", ".", "..") or len(p) > NAME_MAX for p in parts):
        return False
    if any(p in code_map.SKIP or p.startswith(".") for p in parts[:-1]) or path.startswith(LOOKS):
        return False
    return ext_of(path) in EXT and not is_secret(path)


def mime_of(path: str) -> str:
    return EXT.get(ext_of(path), ("", "application/octet-stream"))[1]


def kind_of(path: str, seconds: float | None = None) -> str:
    """The kind of an asset's path (`art`, `sound`, `music`, `clip`, `font`), a sound's by its folder, else by its length."""
    kind = EXT.get(ext_of(path), ("", ""))[0]
    if kind != "sound":
        return kind
    if any(SOUND_DIR.search(p) for p in path.split("/")[:-1]):
        return "sound"
    return "sound" if isinstance(seconds, (int, float)) and seconds < SOUND_S else "music"


# -- the tree of a commit ----------------------------------------------------------------------------------------------

def tree(root: Path, commit: str) -> dict[str, tuple[str, int]]:
    """`{path: (blob, bytes)}` of the assets in `commit`'s tree (`git ls-tree -r -l`): files only, allowed, at most MAX_BYTES."""
    if not commit_goal.FULL_SHA.fullmatch(commit or ""):
        return {}
    try:
        got = _git(root, "ls-tree", "-r", "-l", "-z", commit)
    except (OSError, subprocess.SubprocessError):
        return {}
    out: dict[str, tuple[str, int]] = {}
    for row in got.stdout.split("\0") if got.returncode == 0 else []:
        head, _, path = row.partition("\t")
        bits = head.split()
        if len(bits) != 4 or bits[0] not in _MODES or bits[1] != "blob" or not bits[3].isdigit():
            continue
        if int(bits[3]) <= MAX_BYTES and allowed(path):
            out[path] = (bits[2], int(bits[3]))
    return out


def _one(root: Path, commit: str, path: str) -> tuple[str, int] | None:
    """(blob, bytes) of one asset of `commit`, None when it has none there."""
    if not commit_goal.FULL_SHA.fullmatch(commit or "") or not allowed(path):
        return None
    try:
        got = _git(root, "ls-tree", "-l", "-z", commit, "--", path)
    except (OSError, subprocess.SubprocessError):
        return None
    for row in got.stdout.split("\0") if got.returncode == 0 else []:
        head, _, name = row.partition("\t")
        bits = head.split()
        if name == path and len(bits) == 4 and bits[0] in _MODES and bits[1] == "blob" and bits[3].isdigit() and int(bits[3]) <= MAX_BYTES:
            return bits[2], int(bits[3])
    return None


# -- the cache: <state_dir>/assets-before/<commit>/<path> --------------------------------------------------------------

def cache_root(state_dir: Path) -> Path:
    return Path(state_dir) / CACHE


def _inside(path: Path, root: Path) -> bool:
    """`path` is under `root` with no link on the way (a link laid in the cache never leads out of it)."""
    try:
        rel = path.relative_to(root)
        if not path.resolve().is_relative_to(root.resolve()):
            return False
    except (ValueError, OSError, RuntimeError):
        return False
    step = root
    for part in rel.parts:
        step = step / part
        if step.is_symlink():
            return False
    return True


def _prune(base: Path, keep: str) -> None:
    try:
        folders = sorted((d for d in base.iterdir() if d.is_dir() and not d.is_symlink() and commit_goal.FULL_SHA.fullmatch(d.name)),
                         key=lambda d: d.stat().st_mtime, reverse=True)
    except OSError:
        return
    for d in [d for d in folders if d.name != keep][CACHE_KEEP - 1:]:
        shutil.rmtree(d, ignore_errors=True)


def materialize(state_dir: Path, root: Path, commit: str, path: str) -> Path | None:
    """The file `path` of `commit` in the cache, written from git once (a regular file of the tree, at most MAX_BYTES); None when the
    commit has no such asset, the path is not one an asset may have, or the cache cannot hold it."""
    if not commit_goal.FULL_SHA.fullmatch(commit or "") or not allowed(path):
        return None
    base = cache_root(state_dir)
    dest = base / commit / path
    if dest.is_file() and _inside(dest, base):
        return dest
    found = _one(root, commit, path)
    if found is None:
        return None
    try:
        data = _git(root, "cat-file", "blob", found[0], text=False).stdout
        if len(data) != found[1]:
            return None
        new = not (base / commit).is_dir()
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not _inside(dest.parent, base) or dest.is_symlink():
            return None
        tmp = dest.with_name(f".{dest.name}.{os.getpid()}.{time.monotonic_ns()}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, dest)
        if new:
            _prune(base, commit)
    except (OSError, subprocess.SubprocessError):
        return None
    return dest if _inside(dest, base) else None


# -- sizes and lengths, read once by blob --------------------------------------------------------------------------------

def _ogg_seconds(data: bytes) -> float | None:
    """A Vorbis or Opus stream's length: the last page's granule over its rate (Opus: 48 kHz, less its pre-skip)."""
    at = data.find(b"\x01vorbis")
    rate, skip = (int.from_bytes(data[at + 12:at + 16], "little"), 0) if at >= 0 else (0, 0)
    at = data.find(b"OpusHead")
    if not rate and at >= 0:
        rate, skip = 48000, int.from_bytes(data[at + 10:at + 12], "little")
    last = data.rfind(b"OggS")
    if not rate or last < 0 or len(data) < last + 14:
        return None
    granule = int.from_bytes(data[last + 6:last + 14], "little")
    return round(max(0, granule - skip) / rate, 1) if 0 < granule < 1 << 62 else None


def _flac_seconds(data: bytes) -> float | None:
    """A FLAC's length from its STREAMINFO: total samples over the sample rate."""
    if data[:4] != b"fLaC" or len(data) < 26 or data[4] & 0x7F != 0:
        return None
    info = data[8:26]
    rate = int.from_bytes(info[10:13], "big") >> 4
    total = ((info[13] & 0x0F) << 32) | int.from_bytes(info[14:18], "big")
    return round(total / rate, 1) if rate and total else None


def _measure_bytes(data: bytes, path: str, scratch: Path) -> dict:
    mime = mime_of(path)
    if mime == "audio/ogg":
        return {"w": None, "h": None, "seconds": _ogg_seconds(data)}
    if mime == "audio/flac":
        return {"w": None, "h": None, "seconds": _flac_seconds(data)}
    if mime.startswith("font/"):
        return dict(media_sniff.NONE)
    file = scratch / "asset"
    file.write_bytes(data)
    return media_sniff.measure(file, "video/mp4" if mime == "video/quicktime" else mime)


def measure(state_dir: Path, root: Path, blobs: dict[str, str], budget_s: float = MEASURE_S) -> dict[str, dict]:
    """`{blob: {"w", "h", "seconds"}}` of the blobs `{blob: path}`: from `measured.json`, the new ones read from git (one
    `git cat-file --batch`) while `budget_s` lasts. The file keeps the newest MEASURED_MAX blobs."""
    file = cache_root(state_dir) / MEASURED
    try:
        kept = json.loads(file.read_text(encoding="utf-8"))
        kept = kept if isinstance(kept, dict) else {}
    except (OSError, ValueError):
        kept = {}
    out = {b: kept[b] for b in blobs if isinstance(kept.get(b), dict)}
    todo = [b for b in blobs if b not in out]
    if todo:
        end = time.monotonic() + budget_s
        try:
            with tempfile.TemporaryDirectory(prefix="orkboard-assets-") as tmp, subprocess.Popen(
                    ["git", "cat-file", "--batch"], cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL) as proc:
                for blob in todo:
                    if time.monotonic() > end:
                        break
                    proc.stdin.write(blob.encode("ascii") + b"\n")
                    proc.stdin.flush()
                    head = proc.stdout.readline().split()
                    if len(head) != 3 or head[1] != b"blob":
                        continue
                    data = proc.stdout.read(int(head[2]) + 1)[:-1]
                    try:
                        out[blob] = _measure_bytes(data, blobs[blob], Path(tmp))
                    except (OSError, ValueError, IndexError):
                        out[blob] = dict(media_sniff.NONE)
                proc.stdin.close()
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    if set(out) - set(kept):
        merged = {**{b: v for b, v in kept.items() if b not in out}, **out}
        try:
            file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = file.with_name(f".{MEASURED}.{os.getpid()}.tmp")
            tmp_file.write_text(json.dumps(dict(list(merged.items())[-MEASURED_MAX:])), encoding="utf-8")
            os.replace(tmp_file, file)
        except OSError:
            pass
    return out


# -- what changed since a commit (§3) ------------------------------------------------------------------------------------

def _goal_of(state_dir: Path, root: Path, ref: str, sha: str) -> dict:
    return commit_goal.of(state_dir, root, sha, ref) if sha else {}


def changed(state_dir: Path, root: Path, since: str, ref: str = "dev") -> dict:
    """`{"since", "added", "changed", "removed"}` of the assets between `since` (a commit or a time, commit_goal.resolve) and `ref`'s
    head: each `{"id", "kind", "goal", "task", "at"}` by the last commit of since..ref that touched it (`{}`'s goal "" for the person's
    own). No `since`, or one that names no commit of `ref`: nothing is marked."""
    out: dict = {"since": "", "added": [], "changed": [], "removed": []}
    sha, tip = commit_goal.resolve(root, since, ref), commit_goal.head(root, ref)
    if not sha or not tip or sha == tip:
        out["since"] = sha
        return out
    out["since"] = sha
    try:
        got = _git(root, "diff", "--name-status", "--no-renames", "-z", sha, tip)
    except (OSError, subprocess.SubprocessError):
        return out
    bits = got.stdout.split("\0") if got.returncode == 0 else []
    pairs = [(bits[i], bits[i + 1]) for i in range(0, len(bits) - 1, 2)]
    now, then = tree(root, tip), tree(root, sha)
    seconds = measure(state_dir, root, {**{now[p][0]: p for _s, p in pairs if p in now}, **{then[p][0]: p for _s, p in pairs if p in then}})
    touched = commit_goal.last_touch(root, ref, sha)
    for status, path in pairs:
        word = {"A": "added", "M": "changed", "T": "changed", "D": "removed"}.get(status[:1])
        side = then if word == "removed" else now
        if word is None or path not in side:
            continue
        last = touched.get(path) or {}
        goal = _goal_of(state_dir, root, ref, last.get("sha", ""))
        out[word].append({"id": path, "kind": kind_of(path, (seconds.get(side[path][0]) or {}).get("seconds")),
                          "goal": goal.get("goal", ""), "task": goal.get("task", ""), "at": last.get("at", "")})
    return out


# -- the assets (§1, §2) -------------------------------------------------------------------------------------------------

def _stamp(at: str) -> float:
    try:
        return dt.datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return 0.0


def screens(state_dir: Path) -> list[dict]:
    """A task's newest picture (spec 85 §3) as a screen: `{"id": "screen:<goal>/<task>", "kind": "screen", "name", "bytes", "w", "h",
    "seconds": None, "goal", "task", "at", "shot": {"goal", "id", "file"}}`."""
    out: list[dict] = []
    base = Path(state_dir) / "ideas"
    if not base.is_dir():
        return out
    for goal in sorted(d for d in base.iterdir() if d.is_dir() and re.fullmatch(r"[a-z0-9-]+", d.name)):
        newest: dict[str, dict] = {}
        for folder in sorted((goal / idea_pick.PICKS).glob("*-shot-r*")) if (goal / idea_pick.PICKS).is_dir() else []:
            data = idea_pick.load(state_dir, goal.name, folder.name)
            v = (data or {}).get("variants") or []
            if not data or not data.get("shot") or not v or not isinstance(v[0], dict) or v[0].get("file") != idea_shots.FILE:
                continue
            task = str(data.get("task") or "")
            if task not in newest or int(data.get("round") or 0) > int(newest[task].get("round") or 0):
                newest[task] = data
        titles = {str(t.get("id")): str(t.get("short") or t.get("title") or "") for t in (ideas.plan(state_dir, goal.name) or {}).get("tasks") or []
                  if isinstance(t, dict)}
        for task, data in sorted(newest.items()):
            v = data["variants"][0]
            out.append({"id": f"screen:{goal.name}/{task}", "kind": "screen", "name": titles.get(task) or task, "bytes": v.get("bytes"),
                        "w": v.get("w"), "h": v.get("h"), "seconds": None, "goal": goal.name, "task": task, "at": str(data.get("at") or ""),
                        "shot": {"goal": goal.name, "id": str(data["id"]), "file": idea_shots.FILE}})
    return out


def others(state_dir: Path) -> dict[str, dict]:
    """`{path: {"goal", "pick", "picked", "variants": [...]}}`: for a file a *Pick one* wrote (its pick answered with a variant), the
    variants not picked (`{"key", "name", "file", "mime", "w", "h", "seconds"}`), the face signs their addresses (gui/media.py)."""
    out: dict[str, dict] = {}
    base = Path(state_dir) / "ideas"
    if not base.is_dir():
        return out
    for goal in sorted(d.name for d in base.iterdir() if d.is_dir() and re.fullmatch(r"[a-z0-9-]+", d.name)):
        for t in (ideas.plan(state_dir, goal) or {}).get("tasks") or []:
            if not isinstance(t, dict) or idea_pick.ask_of(t) is None:
                continue
            picks = [p for p in idea_pick.history(state_dir, goal, str(t.get("id"))) if isinstance(p.get("picked"), str)]
            if not picks:
                continue
            p = picks[-1]
            chosen = next((v for v in p["variants"] if isinstance(v, dict) and v.get("key") == p["picked"]), None)
            target = idea_pick.clean_target(p.get("target"))
            if chosen is None or not target:
                continue
            if p.get("look"):
                target = f"{target}.{idea_pick.EXT.get(str(chosen.get('mime')), '')}"
            out[target] = {"goal": goal, "pick": str(p["id"]), "picked": p["picked"],
                           "variants": [{k: v.get(k) for k in ("key", "name", "file", "mime", "w", "h", "seconds")}
                                        for v in p["variants"] if isinstance(v, dict) and v.get("key") != p["picked"]]}
    return out


def listed(state_dir: Path, root: Path, ref: str = "dev", changes: dict | None = None) -> list[dict]:
    """The assets of `ref`'s head and the screens, the changed first (`changes`, from `changed`), then the newest: at most MAX_ASSETS.
    Each `{"id": path, "kind", "name", "bytes", "w", "h", "seconds", "goal", "task", "at", "change"}` (`change`: "added",
    "changed" or ""), a screen with its `shot`, a picked file with `others` (§2)."""
    tip = commit_goal.head(root, ref)
    files = tree(root, tip) if tip else {}
    marks = {r["id"]: w for w in ("added", "changed") for r in (changes or {}).get(w) or []}
    touched = commit_goal.last_touch(root, ref) if files else {}
    rows: list[dict] = []
    for path, (blob, size) in files.items():
        last = touched.get(path) or {}
        rows.append({"id": path, "kind": EXT[ext_of(path)][0], "name": path.rsplit("/", 1)[-1], "bytes": size, "w": None, "h": None,
                     "seconds": None, "sha": last.get("sha", ""), "at": last.get("at", ""), "change": marks.get(path, ""), "blob": blob})
    since = (changes or {}).get("since") or ""
    since_ts = _commit_time(root, since) if since else 0.0
    for s in screens(state_dir):
        s["change"] = "added" if since_ts and _stamp(s["at"]) > since_ts else ""
        rows.append(s)
    rows.sort(key=lambda r: (not r["change"], -_stamp(r["at"]), r["id"]))
    rows = rows[:MAX_ASSETS]
    sizes = measure(state_dir, root, {r["blob"]: r["id"] for r in rows if "blob" in r and r["kind"] in ("art", "sound", "clip")})
    picked = others(state_dir)
    for r in rows:
        blob = r.pop("blob", None)
        sha = r.pop("sha", None)
        if blob is not None:
            r.update({k: (sizes.get(blob) or {}).get(k) for k in ("w", "h", "seconds")})
            if r["kind"] == "sound":
                r["kind"] = kind_of(r["id"], r["seconds"])
            if r["kind"] not in ("art", "clip"):
                r["w"] = r["h"] = None
            goal = _goal_of(state_dir, root, ref, sha or "")
            r["goal"], r["task"] = goal.get("goal", ""), goal.get("task", "")
        if r["id"] in picked:
            r["others"] = picked[r["id"]]
    return rows


def _commit_time(root: Path, sha: str) -> float:
    try:
        got = _git(root, "show", "-s", "--format=%cI", sha)
    except (OSError, subprocess.SubprocessError):
        return 0.0
    return _stamp(got.stdout.strip()) if got.returncode == 0 else 0.0


def stacks(rows: list[dict]) -> list[dict]:
    """`[{"folder", "kind", "n"}]`: each folder holding more than STACK_OVER assets of one kind; its assets gain `stack` (the folder)."""
    count: dict[tuple[str, str], int] = {}
    for r in rows:
        if r["kind"] != "screen":
            count[(r["id"].rpartition("/")[0], r["kind"])] = count.get((r["id"].rpartition("/")[0], r["kind"]), 0) + 1
    out = [{"folder": f, "kind": k, "n": n} for (f, k), n in sorted(count.items()) if n > STACK_OVER]
    big = {(s["folder"], s["kind"]) for s in out}
    for r in rows:
        if r["kind"] != "screen" and (r["id"].rpartition("/")[0], r["kind"]) in big:
            r["stack"] = r["id"].rpartition("/")[0]
    return out


# -- the version before (§4) ---------------------------------------------------------------------------------------------

def before(state_dir: Path, root: Path, path: str, since: str, ref: str = "dev") -> dict | None:
    """`{"commit", "file", "bytes", "w", "h", "seconds"}` of `path` as it was at `since` (a commit or a time), written once into the
    before-cache; None when it was not there then (added since), or `since` names no commit of `ref`."""
    sha = commit_goal.resolve(root, since, ref)
    found = _one(root, sha, path) if sha else None
    if found is None:
        return None
    file = materialize(state_dir, root, sha, path)
    if file is None:
        return None
    size = measure(state_dir, root, {found[0]: path}) if EXT[ext_of(path)][0] in ("art", "sound", "clip") else {}
    got = size.get(found[0]) or dict(media_sniff.NONE)
    return {"commit": sha, "file": file, "bytes": found[1], **{k: got.get(k) for k in ("w", "h", "seconds")}}
