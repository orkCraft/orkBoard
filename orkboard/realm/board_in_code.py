"""The Board in the code, or off it (spec 151 F, decisions §255.10): whether the Board's pages may go to the work branch, and the goal kept off every branch.

    board_in_code.status(root, state_dir, get=...)         # {"visibility": "private" | "public" | "unknown" | "none", "in_code": True | False | None, "goes": bool}
    board_in_code.goes(root, state_dir)                    # status()["goes"]: what a `BoardTree` is given to ask before it lands on the work branch
    board_in_code.write(root, True | False)               # `[board] in_code` in orkcraft.toml, every other line kept (the person's yes or no)
    board_in_code.pending_question(root)                  # {"public": bool, "pages_in_history": n, "visibility": …} while the answer is wanted, else None
    board_in_code.check(root, state_dir, get=...)         # the once-a-day look (the host's tick): {"visibility", "was", "found_public": bool}
    board_in_code.push_hold(root)                         # the words a push waits with, "" when it may go
    board_in_code.keep_off(state_dir, slug, True)         # the person keeps a goal off the repository (its `kept_off` in the goal's state)
    board_in_code.kept_off(root, state_dir, slug)         # whether that goal is kept off now (a public repository with the yes: F.4)
    board_in_code.sync_kept_off(root, state_dir, wiki_rel)  # their pages put in `info/exclude`, so no `git add -A` stages them; the paths from the root
    board_in_code.put_specs(root, worktree, slug)         # a task's spec in its worktree as `.orkcraft/spec/<name>.md` when the Board is not in the code

**Goes** is the person's word when there is one (`in_code`); without it a private GitHub repository and one with no remote go (nothing leaves the
machine), a public or unreadable one does not (decisions §255.10: asked first). The visibility is asked of GitHub's anonymous API once a day
(`board_branch.visibility`), kept in `<state_dir>/board_in_code.json`; a look that says nothing (offline) keeps the last word. Where the tree
lands, and what a goal kept off is: realm/board_tree.py, realm/board_tree_off.py.

**A goal kept off** keeps its page in the Board's tree and its path in the repository's `info/exclude` (shared by every worktree), so it is staged by
no commit; `board_branch.pack` leaves out its page and its `ideas/<slug>/` folder. (The spec's `<state_dir>/kept-off/` folder is not needed.)

No face, no model; the network is the one anonymous GET.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
import tomllib
from pathlib import Path
from typing import Callable

from orkboard.realm import board_branch
from orkboard.realm.jobs import _git

CACHE = "board_in_code.json"
TTL_S = 24 * 3600                           # the visibility is asked once a day (F.3)
RETRY_S = 3600                              # a look that said nothing is asked again in an hour
HELD = "This repository is public now: the Board waits for your answer before anything is pushed."
BLOCK = ("# orkboard: kept off the repository (spec 151 F.4)", "# orkboard: end")
SPEC_DIR = ".orkcraft/spec"                 # a task's spec in its worktree
SECRET_TODOS = ("secret", "file")


# -- `[board] in_code` ------------------------------------------------------------------------------------------------

def read(root: Path) -> bool | None:
    """`[board] in_code` of orkcraft.toml: True, False, None when not said (or not a boolean)."""
    try:
        table = tomllib.loads((Path(root) / board_branch.FILE).read_text(encoding="utf-8")).get("board")
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    value = table.get("in_code") if isinstance(table, dict) else None
    return value if isinstance(value, bool) else None


def write(root: Path, value: bool) -> None:
    """`in_code = true | false` written into `[board]` (the table made when missing), every other line kept. Raises OSError when the file cannot be written."""
    path = Path(root) / board_branch.FILE
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    path.write_text(board_branch.put_key(text, "in_code", "true" if value else "false"), encoding="utf-8")


# -- public or private, once a day ------------------------------------------------------------------------------------

def _cache(state_dir: Path) -> dict:
    try:
        data = json.loads((Path(state_dir) / CACHE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _remote_url(root: Path, remote: str) -> str:
    try:
        got = _git(Path(root), "remote", "get-url", remote)
    except (OSError, subprocess.SubprocessError):
        return ""
    return got.stdout.strip() if got.returncode == 0 else ""


def visibility(root: Path, state_dir: Path, get: Callable[[str], int] | None = None, now: float | None = None, force: bool = False,
               run: Callable = subprocess.run) -> str:
    """`none` · `private` · `public` · `unknown`: the last answer when it is less than a day old and the remote is the same, else GitHub is asked
    (`board_branch.visibility`). A look that says nothing keeps the word before it."""
    now = time.time() if now is None else now
    config = board_branch.read_config(root) or board_branch.BoardConfig()
    url = _remote_url(root, config.remote)
    if not url:
        return "none"
    cache = _cache(state_dir)
    same = cache.get("url") == url and cache.get("visibility") in ("private", "public", "unknown")
    if same and not force and now < float(cache.get("until") or 0):
        return str(cache["visibility"])
    word = board_branch.visibility(root, config, get or board_branch.http_status, run)
    until = now + TTL_S
    on_github = bool(board_branch._GITHUB.search(url))
    if word == "unknown" and on_github:
        until = now + RETRY_S                                           # offline or limited: asked again soon
        if same and cache["visibility"] in ("private", "public"):
            word = str(cache["visibility"])                             # and the word before it stands
    try:
        Path(state_dir).mkdir(parents=True, exist_ok=True)
        (Path(state_dir) / CACHE).write_text(json.dumps({"url": url, "visibility": word, "at": now, "until": until}) + "\n", encoding="utf-8")
    except OSError:
        pass
    return word


def status(root: Path, state_dir: Path, get: Callable[[str], int] | None = None, now: float | None = None) -> dict:
    """`{"visibility", "in_code", "goes"}`. `goes`: whether the Board's pages may go to the work branch."""
    vis, said = visibility(root, state_dir, get, now), read(root)
    return {"visibility": vis, "in_code": said, "goes": said if said is not None else vis in ("private", "none")}


def goes(root: Path, state_dir: Path, get: Callable[[str], int] | None = None) -> bool:
    return bool(status(root, state_dir, get)["goes"])


def check(root: Path, state_dir: Path, get: Callable[[str], int] | None = None, now: float | None = None) -> dict:
    """The host's tick (F.3): the visibility asked again when a day has passed. `{"visibility", "was", "found_public"}`: `found_public` when the repository
    was not public before and is, with no `in_code` said."""
    was = str(_cache(state_dir).get("visibility") or "")
    vis = visibility(root, state_dir, get, now)
    return {"visibility": vis, "was": was, "found_public": vis == "public" and was != "public" and read(root) is None}


def push_hold(root: Path) -> str:
    """The words Orkboard's own pushes wait with, "" when they may go: a public repository whose `in_code` is not said. Asks GitHub only when the
    last answer is a day old."""
    if read(root) is not None:
        return ""
    return HELD if visibility(Path(root), Path(root) / ".orkcraft") == "public" else ""


def pages_in_history(root: Path, branch: str) -> int:
    """How many Board pages (goals and parties) the work branch's history holds, each counted once."""
    try:
        got = _git(Path(root), "log", "--format=", "--name-only", branch, "--", ":(glob)**/pages/ideas/*.md", ":(glob)**/pages/tracks/*.md")
    except (OSError, subprocess.SubprocessError):
        return 0
    return len({ln for ln in got.stdout.splitlines() if ln.strip()}) if got.returncode == 0 else 0


def pending_question(root: Path, branch: str = "", get: Callable[[str], int] | None = None) -> dict | None:
    """The question F.1 asks while it is wanted (a public or unreadable remote, `in_code` not said): `{"public": bool, "pages_in_history": n, "visibility"}`;
    None otherwise. Asks nothing of the network beyond the day's look. `branch`: the work branch (settings' `merge_into`; `dev` when not given)."""
    root = Path(root)
    if read(root) is not None:
        return None
    vis = visibility(root, root / ".orkcraft", get)
    if vis not in ("public", "unknown"):
        return None
    return {"public": vis == "public", "visibility": vis, "pages_in_history": pages_in_history(root, branch or "dev")}


# -- a goal kept off (F.4) --------------------------------------------------------------------------------------------

def _json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def keep_off(state_dir: Path, slug: str, on: bool = True) -> None:
    """The person keeps a goal off the repository (or lets it go again): `kept_off` in its state. Its page is in the exclude file at the next `sync_kept_off`."""
    from orkboard.realm import ideas
    ideas.save_state(Path(state_dir), slug, kept_off=bool(on))


def qualifies(state_dir: Path, slug: str) -> bool:
    """Whether the goal is one to keep off a public repository: marked `kept_off`, of the kind *security*, or with secrets of its own (`idea_secrets`)."""
    folder = Path(state_dir) / "ideas" / slug
    st = _json(folder / "state.json")
    if st.get("kept_off") is True:
        return True
    how = st.get("route_how") if isinstance(st.get("route_how"), dict) else {}
    if "security" in (str(st.get("type") or "").rsplit("/", 1)[-1], str(how.get("kind") or "")):
        return True
    todos = _json(folder / "plan.json").get("todos")
    if any(isinstance(t, dict) and t.get("kind") in SECRET_TODOS for t in todos or []):
        return True
    files = folder / "files"
    return files.is_dir() and any(files.iterdir())


def _active(root: Path, state_dir: Path) -> bool:
    """A public (or unreadable) repository with the yes: the one place a page may be on the work branch and a goal must still be kept off."""
    if read(root) is not True:
        return False
    return str(_cache(state_dir).get("visibility") or "unknown") in ("public", "unknown")


def kept_off_slugs(state_dir: Path) -> list[str]:
    """The goals kept off now, by what `<state_dir>` says (the project is its parent). Reads no network: the visibility is the cache's, `unknown` without one."""
    state_dir = Path(state_dir)
    if not (state_dir / "ideas").is_dir() or not _active(state_dir.parent, state_dir):
        return []
    return sorted(p.name for p in (state_dir / "ideas").iterdir() if p.is_dir() and qualifies(state_dir, p.name))


def kept_off(root: Path, state_dir: Path, slug: str) -> bool:
    """Whether this goal is kept off the repository now: it qualifies and the repository is public (or unreadable) with the yes."""
    return _active(Path(root), Path(state_dir)) and qualifies(Path(state_dir), slug)


def _exclude_file(root: Path) -> Path | None:
    try:
        got = _git(Path(root), "rev-parse", "--git-path", "info/exclude")
    except (OSError, subprocess.SubprocessError):
        return None
    if got.returncode != 0:
        return None
    file = Path(got.stdout.strip())
    return file if file.is_absolute() else Path(root) / file


def exclude_block(root: Path, lines: list[str]) -> None:
    """Orkboard's block of `info/exclude` replaced by `lines` (taken away when there are none); the rest of the file is kept. Never raises."""
    file = _exclude_file(root)
    if file is None:
        return
    try:
        text = file.read_text(encoding="utf-8") if file.exists() else ""
        had = text.splitlines()
        if BLOCK[0] in had and BLOCK[1] in had[had.index(BLOCK[0]):]:
            a = had.index(BLOCK[0])
            b = a + had[a:].index(BLOCK[1])
            had = had[:a] + had[b + 1:]
        if lines:
            had += [BLOCK[0], *lines, BLOCK[1]]
        new = "".join(f"{ln}\n" for ln in had)
        if new != text:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(new, encoding="utf-8")
    except OSError:
        pass


def sync_kept_off(root: Path, state_dir: Path, wiki_rel: str) -> list[str]:
    """The pages of the goals kept off (from the project's root, `/`-separated) put in the repository's `info/exclude`, the lines of goals no longer kept off taken
    out. Answers those paths."""
    wiki = wiki_rel.strip("/")
    paths = [f"{wiki + '/' if wiki else ''}pages/ideas/{slug}.md" for slug in kept_off_slugs(state_dir)]
    exclude_block(Path(root), ["/" + re.sub(r"([\\\[\]*?!#])", r"\\\1", p) for p in paths])
    return paths


# -- a task's spec in its worktree (F.2) --------------------------------------------------------------------------------

def spec_in_worktree(root: Path, state_dir: Path, slug: str) -> bool:
    """Whether a task's spec is given inside its worktree: the Board is not in the code, or the goal is kept off it."""
    return not goes(root, state_dir) or kept_off(root, state_dir, slug)


def worktree_specs(root: Path, state_dir: Path, slug: str) -> tuple[str, list[str]]:
    """The goal's spec path and those of the specs it depends on, as a task's worktree holds them (`.orkcraft/spec/<name>.md`); ("", []) when not found."""
    from orkboard.realm.board_tree import spec_paths
    spec, deps = spec_paths(Path(root), Path(state_dir), slug)
    return (f"{SPEC_DIR}/{Path(spec).name}", [f"{SPEC_DIR}/{Path(d).name}" for d in deps]) if spec else ("", [])


def put_specs(root: Path, worktree: Path, slug: str) -> list[str]:
    """The spec page and those it depends on copied from the Board's tree into the task's worktree as `.orkcraft/spec/<name>.md`, the folder in the
    repository's `info/exclude` so the task's commit holds none of it. Nothing when the Board is in the code. Answers the paths written. Never raises."""
    root, state_dir = Path(root), Path(root) / ".orkcraft"
    try:
        if not spec_in_worktree(root, state_dir, slug):
            return []
        from orkboard.realm.board_tree import spec_paths
        spec, deps = spec_paths(root, state_dir, slug)
        done = []
        for rel in ([spec] if spec else []) + deps:
            for base in (state_dir / "board", root):
                src = base / rel
                if src.is_file():
                    dest = Path(worktree) / SPEC_DIR / src.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(src.read_bytes())
                    done.append(f"{SPEC_DIR}/{src.name}")
                    break
        file = _exclude_file(Path(worktree))
        if done and file is not None:
            text = file.read_text(encoding="utf-8") if file.exists() else ""
            if f"/{SPEC_DIR}/" not in text.splitlines():
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(text + ("" if not text or text.endswith("\n") else "\n") + f"/{SPEC_DIR}/\n", encoding="utf-8")
        return done
    except (OSError, subprocess.SubprocessError, RuntimeError):
        return []
