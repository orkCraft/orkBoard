"""The Board in the project's repository (spec 137 A, decisions §244.1, §244.11–12): its pages and its state on a branch of its own.

    # orkcraft.toml: nothing of this runs until the project asks for it (Settings' switch, on the person's yes)
    #   [board]
    #   remote = "origin"            # the remote's name
    #   branch = "orkboard/board"    # a branch of its own: no history shared with the code, never merged, no workflow in it

    config = board_branch.read_config(root)                       # BoardConfig(remote, branch) · None: off, nothing of A–D runs
    ok, line = board_branch.private_check(root, config)           # (False, "…goes only to a private repository") on a public GitHub repository
    files, held = board_branch.pack(state_dir, wiki_rel)          # {path: bytes} laid out as `.orkcraft/` is; held: the paths something was held back of
    commit = board_branch.commit(root, state_dir, config, files, message, parent)      # by plumbing; "" when the tree is the parent's
    got = board_branch.fetch(root, config)                        # {ok, tip, why}: refs/orkboard/board-remote, no checkout
    board_branch.push(root, config, commit)                       # {ok, refused, why}: never --force
    board_branch.files_at(root, ref)                              # {path: bytes}
    board_branch.unpack(state_dir, files, board_tree)             # a worker takes the Board (B): written whole, a listed file the branch dropped removed

The branch's tree is `<state_dir>`'s own paths, so a working copy is the branch's files and nothing is
renamed. **Goes** (`allowed`, an allow list): `board/<wiki_rel>/pages/` and `board/<wiki_rel>/specs/` (the pages, never the Board tree's
`.git`), `ideas/<slug>/`, `goals/`, `roles/`, `kinds.json`, `segments.json`, `project.json`, `checks.toml`, `canvases.jsonl`, `slices.json`,
`cascades.json`, and `lease.json` (realm/board_lease.py writes it: `pack` never reads it, `unpack` never writes it). **Never** (`NEVER`,
checked again over what goes): `secrets.json`, `sign-in/`, `drive.json`, `worktrees/`, `logs/`, `usage/`, `crashes/`, `repair/`,
`screens/`, `claims.json`, `journal.json`, and anything not listed. A photo larger than `PHOTO_MAX` stays home, said. Every text file is
read line by line for a secret's shape (`plumbing.scrub`): a line that has one is replaced by words (dropped from a `.jsonl`), and a
`.json` file that had one is not sent at all, said by its path.

No face, no model; the network is `git fetch`/`git push` and, once, GitHub's public API (`private_check`).
"""
from __future__ import annotations

import os
import re
import subprocess
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

from orkboard.realm import plumbing

FILE = "orkcraft.toml"
LOCAL_REF = "refs/orkboard/board"
REMOTE_REF = "refs/orkboard/board-remote"
LEASE = "lease.json"
PHOTO_MAX = 2 * 2**20
IMAGES = (".jpg", ".jpeg", ".png", ".webp", ".gif")

TOP_DIRS = ("ideas", "goals", "roles")
TOP_FILES = ("kinds.json", "segments.json", "project.json", "checks.toml", "canvases.jsonl", "slices.json", "cascades.json")
NEVER_FILES = frozenset({"secrets.json", "drive.json", "claims.json", "journal.json"})
NEVER_DIRS = frozenset({"sign-in", "worktree", "worktrees", "logs", "usage", "crashes", "repair", "screens", ".git"})
NEVER = (*sorted(NEVER_FILES), *(d + "/" for d in sorted(NEVER_DIRS)))


@dataclass(frozen=True)
class BoardConfig:
    remote: str = "origin"
    branch: str = "orkboard/board"


def read_config(root: Path) -> BoardConfig | None:
    """The `[board]` of `orkcraft.toml`; None with no file, a bad file or no `[board]` (off, never on by itself). A bad value is ignored."""
    try:
        table = tomllib.loads((Path(root) / FILE).read_text(encoding="utf-8")).get("board")
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    if not isinstance(table, dict) or set(table) == {"in_code"}:          # `in_code` alone (realm/board_in_code.py) is no yes to the Board's branch
        return None
    d = BoardConfig()
    ok = lambda s: isinstance(s, str) and re.fullmatch(r"[A-Za-z0-9._/-]{1,100}", s) and not s.startswith("-") and ".." not in s
    remote, branch = table.get("remote", d.remote), table.get("branch", d.branch)
    return BoardConfig(remote if ok(remote) else d.remote, branch if ok(branch) else d.branch)


# -- a private repository only (§244.11) ------------------------------------------------------------------------

PUBLIC = "The Board holds your goals' words and specs: it goes only to a private repository"
NOT_GITHUB = "The repository must be private: the Board holds your goals' words and specs"
_GITHUB = re.compile(r"github\.com[:/]+([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$", re.I)


def http_status(url: str) -> int:
    """An anonymous GET's status; 0 when it could not be asked."""
    req = urllib.request.Request(url, headers={"User-Agent": "orkboard", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return int(r.status)
    except urllib.error.HTTPError as e:
        return int(e.code)
    except Exception:
        return 0


def private_check(root: Path, config: BoardConfig, get: Callable[[str], int] = http_status,
                  run: Callable = subprocess.run) -> tuple[bool, str]:
    """Whether the Board's branch may be turned on for this remote: `(False, words)` when `https://api.github.com/repos/<owner>/<name>`
    answers 200 to an anonymous GET (a public repository); `(True, "")` on a 404 or anything else (private, or not reachable without a
    token); `(True, words)` for a remote not on GitHub (it must be private; nothing to ask)."""
    try:
        url = plumbing.git(root, run, plumbing.env(), "remote", "get-url", config.remote)
    except Exception:
        return True, ""
    m = _GITHUB.search(url.strip())
    if not m:
        return True, NOT_GITHUB
    if get(f"https://api.github.com/repos/{m.group(1)}/{m.group(2)}") == 200:
        return False, PUBLIC
    return True, ""


def visibility(root: Path, config: BoardConfig | None = None, get: Callable[[str], int] = http_status,
               run: Callable = subprocess.run) -> str:
    """The remote's visibility as a word (spec 151 F.1): `none` (no such remote: nothing leaves the machine), `public` (GitHub answers 200 to an
    anonymous GET), `private` (404), `unknown` (a remote not on GitHub, or an answer that says nothing: no network, a limit). `private_check`'s
    own asking, said in a word."""
    config = config or BoardConfig()
    try:
        url = plumbing.git(root, run, plumbing.env(), "remote", "get-url", config.remote)
    except Exception:
        return "none"
    url = url.strip()
    m = _GITHUB.search(url)
    if not m:
        return "private" if re.match(r"(?:file:|/|\./|\.\./|[A-Za-z]:[\\/])", url) else "unknown"       # a folder on this computer or the network is nobody's public repository
    got = get(f"https://api.github.com/repos/{m.group(1)}/{m.group(2)}")
    return "public" if got == 200 else "private" if got == 404 else "unknown"


def put_key(text: str, key: str, literal: str) -> str:
    """`text` (an `orkcraft.toml`) with `key = literal` set in its `[board]` table: a line of that key replaced, else put under the header, the table made
    when missing; every other line kept."""
    lines = text.splitlines(keepends=True)
    head = next((i for i, ln in enumerate(lines) if re.fullmatch(r"\[board\]\s*", ln.rstrip("\r\n"))), None)
    if head is None:
        return text + ("\n" if text and not text.endswith("\n") else "") + ("\n" if text else "") + f"[board]\n{key} = {literal}\n"
    end = next((i for i in range(head + 1, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
    for i in range(head + 1, end):
        if re.match(rf"\s*{re.escape(key)}\s*=", lines[i]):
            lines[i] = f"{key} = {literal}\n"
            return "".join(lines)
    if not lines[head].endswith("\n"):
        lines[head] += "\n"
    lines.insert(head + 1, f"{key} = {literal}\n")
    return "".join(lines)


def turn_on(root: Path, config: BoardConfig | None = None) -> BoardConfig:
    """Write `[board]` into `orkcraft.toml` (spec 137 E; the person said yes, and `private_check` let it): the table made when missing, every other
    line kept, a `[board]` already there left as it is. Raises OSError when the file cannot be written."""
    config = config or BoardConfig()
    path = Path(root) / FILE
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    if not re.search(r"^\[board\]\s*$", text, flags=re.M):
        text += ("\n" if text and not text.endswith("\n") else "") + ("\n" if text else "") + \
            f'[board]\nremote = "{config.remote}"\nbranch = "{config.branch}"\n'
        path.write_text(text, encoding="utf-8")
    elif read_config(root) is None:                         # a `[board]` with `in_code` alone: the branch's keys go in beside it
        path.write_text(put_key(put_key(text, "branch", f'"{config.branch}"'), "remote", f'"{config.remote}"'), encoding="utf-8")
    return read_config(root) or config


# -- what goes ------------------------------------------------------------------------------------------------------

def _page_roots(wiki_rel: str) -> tuple[str, str]:
    base = "board/" + (wiki_rel.strip("/") + "/" if wiki_rel.strip("/") else "")
    return base + "pages/", base + "specs/"


def allowed(rel: str, wiki_rel: str = "") -> bool:
    """Whether `rel` (a path from the state folder, `/`-separated) goes to the branch: listed in `TOP_DIRS`, `TOP_FILES` or the lease, the pages included, and not
    `NEVER` anywhere in its path."""
    parts = rel.split("/")
    if not rel or rel.startswith("/") or any(p in ("", ".", "..") for p in parts):
        return False
    if any(p in NEVER_DIRS or p.startswith("worktree") for p in parts[:-1]) or parts[-1] in NEVER_FILES:
        return False
    if len(parts) == 1:
        return parts[0] in TOP_FILES or parts[0] == LEASE
    return parts[0] in TOP_DIRS or rel.startswith(_page_roots(wiki_rel))


def _is_photo(rel: str) -> bool:
    return rel.lower().endswith(IMAGES) or "/photos/" in rel


def _walk(state_dir: Path, wiki_rel: str) -> Iterator[tuple[str, Path]]:
    """Every regular file of the state folder that `allowed` lets go, as (path from the folder, file); no symlink is followed."""
    state_dir = Path(state_dir)
    tops = [state_dir / d for d in TOP_DIRS] + [state_dir / r.rstrip("/") for r in _page_roots(wiki_rel)]
    for top in tops:
        if top.is_symlink() or not top.is_dir():
            continue
        for here, dirs, names in os.walk(top):
            dirs[:] = sorted(d for d in dirs if d not in NEVER_DIRS and not d.startswith("worktree") and not (Path(here) / d).is_symlink())
            for n in sorted(names):
                f = Path(here) / n
                rel = f.relative_to(state_dir).as_posix()
                if f.is_file() and not f.is_symlink() and allowed(rel, wiki_rel):
                    yield rel, f
    for n in TOP_FILES:
        f = state_dir / n
        if f.is_file() and not f.is_symlink():
            yield n, f


def pack(state_dir: Path, wiki_rel: str = "") -> tuple[dict[str, bytes], list[str]]:
    """`(files, held)`: the Board's files as the branch holds them, path -> bytes, and the paths something was held back of (a photo over
    `PHOTO_MAX`, a `.json` with a line of a secret's shape: not sent; a line of another text file: replaced). Pure but for reading files;
    `lease.json` is not read (realm/board_lease.py adds it)."""
    files: dict[str, bytes] = {}
    held: list[str] = []
    from orkboard.realm import board_in_code
    off = board_in_code.kept_off_slugs(Path(state_dir))                # goals kept off every branch (spec 151 F.4): their page and their folder stay home
    skip = tuple(p for slug in off for p in (f"ideas/{slug}/", *(r + f"ideas/{slug}.md" for r in _page_roots(wiki_rel)[:1])))
    for rel, f in _walk(Path(state_dir), wiki_rel):
        if skip and rel.startswith(skip):
            continue
        try:
            if _is_photo(rel) and f.stat().st_size > PHOTO_MAX:
                held.append(rel)
                continue
            raw = f.read_bytes()
        except OSError:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if text is None or "\0" in text:
            files[rel] = raw                                    # a picture or the like: no lines to read
            continue
        if rel.endswith(".jsonl"):                              # a held line would break the line's JSON: dropped
            keep = [ln for ln in text.splitlines(keepends=True) if not plumbing.SECRETS.search(ln)]
            if len(keep) != len(text.splitlines()):
                held.append(rel)
            files[rel] = "".join(keep).encode("utf-8")
            continue
        clean, n = plumbing.scrub(text)
        if n:
            held.append(rel)
            if rel.endswith(".json"):                           # a broken JSON on the branch is worse than a missing one
                continue
        files[rel] = clean.encode("utf-8")
    return files, held


# -- committed, fetched, pushed and read by plumbing ------------------------------------------------------------

def commit(root: Path, state_dir: Path, config: BoardConfig, files: dict[str, bytes], message: str, parent: str = "",
           run: Callable = subprocess.run) -> str:
    """A commit of `files` on `parent` (none for the first), `refs/orkboard/board` moved to it; "" when the tree is the parent's. A temporary
    index in the state folder, the person's working tree, index and branches untouched. Raises RuntimeError with git's words."""
    root, state_dir = Path(root), Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    index = state_dir / "board.index"
    env = plumbing.env(index)
    try:
        tree = plumbing.tree_of(root, run, env, files)
        if parent and plumbing.git(root, run, env, "rev-parse", f"{parent}^{{tree}}") == tree:
            return ""
        made = plumbing.git(root, run, env, "commit-tree", tree, *(["-p", parent] if parent else []), "-m", message)
        plumbing.git(root, run, env, "update-ref", LOCAL_REF, made)
        return made
    finally:
        try:
            index.unlink(missing_ok=True)
        except OSError:
            pass


def fetch(root: Path, config: BoardConfig, run: Callable = subprocess.run) -> dict:
    """`git fetch <remote> +refs/heads/<branch>:refs/orkboard/board-remote`: no checkout. `{ok, tip, why}`: `tip` is "" when the remote has
    no such branch yet (not a failure) or the fetch failed (`ok` False, `why` in words). Never raises."""
    env = plumbing.env()
    try:
        plumbing.git(root, run, env, "fetch", "--quiet", "--no-tags", config.remote, f"+refs/heads/{config.branch}:{REMOTE_REF}")
        return {"ok": True, "tip": plumbing.git(root, run, env, "rev-parse", REMOTE_REF), "why": ""}
    except RuntimeError as e:
        why = str(e)
        if "couldn't find remote ref" in why.lower():
            return {"ok": True, "tip": "", "why": ""}
        return {"ok": False, "tip": "", "why": why[:300]}
    except Exception as e:                      # no git, a timeout
        return {"ok": False, "tip": "", "why": " ".join(str(e).split())[:300] or type(e).__name__}


def push(root: Path, config: BoardConfig, commit: str, run: Callable = subprocess.run) -> dict:
    """`git push <remote> <commit>:refs/heads/<branch>`, never `--force`. `{ok, refused, why}`: `refused` for a non-fast-forward (another
    pushed first). A public repository whose `in_code` is not said waits (spec 151 F.3). Never raises."""
    from orkboard.realm import board_in_code
    if (held := board_in_code.push_hold(Path(root))):
        return {"ok": False, "refused": False, "why": held}
    try:
        plumbing.git(root, run, plumbing.env(), "push", "--quiet", config.remote, f"{commit}:refs/heads/{config.branch}")
        return {"ok": True, "refused": False, "why": ""}
    except RuntimeError as e:
        why = str(e)
        low = why.lower()
        refused = any(w in low for w in ("rejected", "non-fast-forward", "fetch first", "stale info"))
        return {"ok": False, "refused": refused, "why": why[:300]}
    except Exception as e:
        return {"ok": False, "refused": False, "why": " ".join(str(e).split())[:300] or type(e).__name__}


def files_at(root: Path, ref: str, run: Callable = subprocess.run) -> dict[str, bytes]:
    """The files of `ref`'s tree, path -> bytes, by `ls-tree -r` and one `cat-file --batch`. Raises RuntimeError with git's words."""
    env = plumbing.env()
    listing = plumbing.git_raw(root, run, env, "ls-tree", "-r", "-z", ref).decode("utf-8", "replace")
    entries: list[tuple[str, str]] = []
    for rec in listing.split("\0"):
        meta, _, name = rec.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob" and name:
            entries.append((name, parts[2]))
    if not entries:
        return {}
    out = plumbing.git_raw(root, run, env, "cat-file", "--batch", data="".join(f"{sha}\n" for _, sha in entries).encode("ascii"))
    files: dict[str, bytes] = {}
    at = 0
    for name, sha in entries:
        end = out.index(b"\n", at)
        head = out[at:end].split()
        if len(head) != 3 or head[1] != b"blob":
            raise RuntimeError(f"git could not read {name}")
        size = int(head[2])
        files[name] = out[end + 1:end + 1 + size]
        at = end + 1 + size + 1
    return files


# -- the working copy, kept from the branch (A.4) ------------------------------------------------------------------

def _write(path: Path, body: bytes) -> bool:
    """Whole, to a temporary name and then renamed; False when the file already says this."""
    try:
        if path.is_file() and not path.is_symlink() and path.read_bytes() == body:
            return False
    except OSError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".board-tmp")
    tmp.write_bytes(body)
    os.replace(tmp, path)
    return True


def unpack(state_dir: Path, files: dict[str, bytes], board_tree: Any = None, by: str = "", wiki_rel: str = "") -> dict:
    """Write the branch's `files` into the state folder when a worker takes the Board: each file whole; a listed file on disk that the branch
    does not hold removed (a goal the other worker dropped; never one `pack` held back); **a file not listed is never touched**, nor is a path
    that tries to leave the folder or is `NEVER`. The pages go into the Board's tree and are committed there as one write
    (`flush(force=True, message="board: the Board taken from <by>")`). `board_tree`: a `BoardTree`, whose `wiki_rel` is used;
    without one the pages are written as plain files. Returns `{written, removed, pages, skipped, commit}`."""
    state_dir = Path(state_dir)
    wiki_rel = (getattr(board_tree, "wiki_rel", None) if board_tree is not None else None) or wiki_rel
    out: dict[str, Any] = {"written": 0, "removed": 0, "pages": 0, "skipped": [], "commit": ""}
    pages = _page_roots(wiki_rel)
    mine = {p: b for p, b in files.items() if p != LEASE and allowed(p, wiki_rel)}
    if board_tree is not None and not board_tree.exists() and any(p.startswith(pages) for p in mine):
        try:
            board_tree.ensure()
        except Exception as e:                               # a folder the Board's tree cannot live in: the pages stay on the branch
            out["skipped"] = [p for p in mine if p.startswith(pages)]
            mine = {p: b for p, b in mine.items() if not p.startswith(pages)}
            out["why"] = " ".join(str(e).split())[:200]
    local, held = pack(state_dir, wiki_rel)
    gone = [p for p in local if p not in mine and p not in held and p != LEASE]
    for rel, body in mine.items():
        if _write(state_dir / rel, body):
            out["written"] += 1
            out["pages"] += rel.startswith(pages)
    for rel in gone:
        if rel.startswith("board/") and board_tree is not None and not board_tree.exists():
            continue
        try:
            (state_dir / rel).unlink()
            out["removed"] += 1
            out["pages"] += rel.startswith(pages)
        except OSError:
            pass
    if out["pages"] and board_tree is not None and board_tree.exists():
        try:
            got = board_tree.flush(force=True, message=f"board: the Board taken from {by or 'the branch'}")
            out["commit"] = (got or {}).get("commit", "")
        except Exception as e:
            out["why"] = " ".join(str(e).split())[:200]
    return out
