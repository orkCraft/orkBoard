"""The Board's own tree (spec 35 §13): its pages in a worktree of their own, committed and fast-forwarded onto the work branch.
Split out of `realm/idea_git.py` (which still offers `BoardTree`, `spec_paths` and `COMMIT_AFTER_S` under its own name).

    tree = BoardTree(repo_root, state_dir, "llm-wiki/general", lambda: "dev")
    tree.ensure(); tree.note("Dark mode", "drafted", now); tree.flush(force=True)
    spec_paths(repo_root, state_dir, slug)               # an idea's spec path, and the paths of the specs it depends on
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from orkboard import brand
from orkboard.realm.idea_git import PUSH_TIMEOUT_S, IdeaGit, _git, _ok

COMMIT_AFTER_S = 10.0                # the writes within this as one commit


def spec_paths(repo_root: Path, state_dir: Path, slug: str) -> tuple[str, list[str]]:
    """An idea's spec as a path in a task's worktree (the work branch holds the Board's pages), and the paths of the
    specs it depends on: named, never pasted (spec 35 §0, §13). ("", []) when not found."""
    for base in (Path(state_dir) / "board", Path(repo_root)):
        found = [p for pattern in (f"llm-wiki/*/pages/ideas/{slug}.md", f"*/pages/ideas/{slug}.md", f"pages/ideas/{slug}.md")
                 for p in base.glob(pattern) if p.is_file()]
        if not found:
            continue
        page = max(found, key=lambda p: p.stat().st_mtime)
        try:
            head = page.read_text(encoding="utf-8")[:20000]
        except OSError:
            head = ""
        m = re.search(r"^depends_on:[ \t]*(\[.*\])$", head, re.M)
        try:
            deps = [d for d in json.loads(m.group(1)) if isinstance(d, str)] if m else []
        except ValueError:
            deps = []
        folder = page.relative_to(base).parent
        return page.relative_to(base).as_posix(), [(folder / f"{d}.md").as_posix() for d in deps]
    return "", []


class BoardTree:
    """The Board's pages in a worktree of their own, `<state_dir>/board/`, detached at the work branch's tip: it locks
    no branch, so the person can check out any. A change is a commit of the Board's pages only (the writes within 10 s
    as one), author *<the product> board* (`brand.board_author`); the work branch is then fast-forwarded to it under the repository's lock, by
    `IdeaGit._fast_forward`'s rules (in place when the person's checkout is on it, by `update-ref` when not). Refused
    when the person has uncommitted changes in those files: held, tried again at the next write. Nothing is pushed."""

    def __init__(self, repo_root: Path, state_dir: Path, wiki_rel: str, branch) -> None:
        self.git = IdeaGit(Path(repo_root))
        self.path = Path(state_dir) / "board"
        self.wiki_rel, self.branch = wiki_rel.strip("/"), branch
        self._since: float | None = None
        self._notes: list[tuple[str, str]] = []
        self.held = ""

    def exists(self) -> bool:
        return (self.path / ".git").exists()

    def root(self) -> Path:
        return self.path / self.wiki_rel

    def pages(self) -> list[str]:
        return [f"{self.wiki_rel}/pages/tracks", f"{self.wiki_rel}/pages/ideas", f"{self.wiki_rel}/specs",
                f"{self.wiki_rel}/journals", f"{self.wiki_rel}/project.md"]     # the living specs (spec 127 C.1), the journals' Markdown and the brief (spec 151 B)

    def _tip(self) -> str:
        return _ok(_git(self.git.root, "rev-parse", f"refs/heads/{self.branch()}"))

    def ensure(self) -> None:
        """The tree, made when missing (detached at the work branch's tip), else moved to the tip when behind."""
        with self.git.lock:
            self.git.ensure_branch(self.branch())
            if not self.exists():
                _git(self.git.root, "worktree", "prune")
                self.path.parent.mkdir(parents=True, exist_ok=True)
                _ok(_git(self.git.root, "worktree", "add", "--detach", str(self.path), self.branch()))
            else:
                self.follow()

    def follow(self) -> None:
        """A tree behind its branch (a task landed) moves to the tip; one that holds commits of its own the branch has
        not taken is rebased onto the tip (its pages never conflict: a task never edits them)."""
        tip, head = self._tip(), self.git.head(self.path)
        if tip == head or _git(self.path, "merge-base", "--is-ancestor", tip, head).returncode == 0:
            return
        if _git(self.path, "merge-base", "--is-ancestor", head, tip).returncode == 0:
            _ok(_git(self.path, "checkout", "-q", "--detach", tip))
        elif _git(self.path, "rebase", "-q", tip, timeout=PUSH_TIMEOUT_S).returncode != 0:
            _git(self.path, "rebase", "--abort")
            raise RuntimeError(f"the Board's tree could not follow {self.branch()}")

    def last_change(self, path: Path) -> tuple[str, str]:
        """The commit that last changed a file of the tree and its author, `(short hash, name)`; ("", "") when no commit has (or it has uncommitted changes: the change is not in one yet)."""
        rel = Path(path).resolve().relative_to(self.path.resolve()).as_posix()
        if _git(self.path, "status", "--porcelain", "--", rel).stdout.strip():
            return "", ""
        got = _git(self.path, "log", "-1", "--format=%h%x09%an", "--", rel).stdout.strip().split("\t")
        return (got[0], got[1]) if len(got) == 2 else ("", "")

    def note(self, title: str, what: str, now: float) -> None:
        """A write of the Board's: committed with the others within COMMIT_AFTER_S."""
        if self._since is None:
            self._since = now
        self._notes.append((" ".join(str(title or "the Board").split())[:80], what))

    def touch(self, now: float) -> None:
        """A change with nothing to say yet (a goal's phase, which the keys written at the commit say): the writes' clock starts, as a note's would."""
        if self._since is None:
            self._since = now

    def due(self, now: float) -> bool:
        return self._since is not None and now - self._since >= COMMIT_AFTER_S

    def flush(self, now: float = 0.0, force: bool = False, message: str = "", files: tuple[str, ...] = ()) -> dict | None:
        """Commit the Board's pages when due (or `force`) and fast-forward the work branch: {"commit", "pages", "what",
        "held"} (commit "" when nothing changed), None when nothing was due. `files`: paths from the repository's root the commit may hold besides the pages
        (a goal's decision: the project's decisions file, nothing else)."""
        if not self.exists() or not (force or self.due(now)):
            return None
        title, what = self._notes[0] if self._notes else ("the Board", "edited")
        self._since, self._notes = None, []
        out = {"commit": "", "pages": 0, "what": what, "held": ""}
        with self.git.lock:
            folders = [p for p in self.pages() if (self.path / p).exists()]
            if folders or files:
                _git(self.path, "add", "-A", "--", *folders, *files)
            staged = [f for f in _git(self.path, "diff", "--cached", "--name-only").stdout.splitlines() if f.strip()]
            if staged:
                who, email = brand.board_author()
                _ok(_git(self.path, "-c", f"user.name={who}", "-c", f"user.email={email}", "commit", "-q",
                         "-m", message or f"board: {title} — {what}", "--author", f"{who} <{email}>"))
                out.update(commit=self.git.head(self.path), pages=len(staged))
            out["held"] = self.land()
        return out

    def edit_file(self, rel: str, edit, message: str) -> dict:
        """A file of the project (its decisions file: spec 99 §6.2) changed in the tree and committed with the pages in one commit, the work branch moved: `edit(old
        text)` is called under the repository's lock with the file as the tree's branch holds it ("" when it is missing) and answers its new text, so a number read in it
        is the branch's own at the commit. Returns `flush`'s answer. RuntimeError for a path outside the repository."""
        base = self.path.resolve()
        path = (base / rel).resolve()
        if path == base or not path.is_relative_to(base):
            raise RuntimeError(f"{rel!r} is outside the project")
        with self.git.lock:
            self.follow()
            old = path.read_text("utf-8", errors="replace") if path.is_file() else ""
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(edit(old), "utf-8")
            return self.flush(force=True, message=message() if callable(message) else message, files=(path.relative_to(base).as_posix(),)) or {}

    def add_file(self, folder: str, make, message) -> dict:
        """A new file in a folder of the project (a decision as the next ADR file: spec 126 D) made in the tree and committed with the pages in one commit, the work branch
        moved: `make(folder path)` is called under the repository's lock with the folder as the tree's branch holds it (made when missing) and answers `(file name,
        text)`, so a number read in the folder is the branch's own at the commit. A file that is there already is never written over. Returns `flush`'s answer plus
        `path`, the new file from the repository's root. RuntimeError for a folder outside the repository or a name that is taken."""
        base = self.path.resolve()
        where = (base / folder).resolve()
        if where == base or not where.is_relative_to(base):
            raise RuntimeError(f"{folder!r} is outside the project")
        with self.git.lock:
            self.follow()
            where.mkdir(parents=True, exist_ok=True)
            name, text = make(where)
            if Path(name).name != name or not name:
                raise RuntimeError(f"{name!r} is no file name")
            try:
                with (where / name).open("x", encoding="utf-8") as out:
                    out.write(text)
            except FileExistsError:
                raise RuntimeError(f"{name} is there already") from None
            rel = (where / name).relative_to(base).as_posix()
            return {**(self.flush(force=True, message=message() if callable(message) else message, files=(rel,)) or {}), "path": rel}

    def land(self) -> str:
        """The work branch fast-forwarded to the tree: "" when it moved (or had nothing to take), else why it is held."""
        try:
            self.follow()
            tip, head = self._tip(), self.git.head(self.path)
            if tip != head:
                self.git._fast_forward(self.branch(), tip, head)
        except RuntimeError as e:
            self.held = str(e)[:300]
            return self.held
        self.held = ""
        return ""

    def move(self, legacy: Path) -> dict | None:
        """The first start after spec 35: the Board's pages in the person's Wiki that the work branch does not hold are
        copied into the tree and committed; then, and only then, the person's untracked copies are removed (they would
        block a checkout of the work branch). Tracked copies are left alone."""
        copied = []
        for folder in ("pages/tracks", "pages/ideas", "specs"):
            for page in sorted((Path(legacy) / folder).glob("*.md")) if (Path(legacy) / folder).is_dir() else []:
                target = self.root() / folder / page.name
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(page.read_bytes())
                    copied.append(page)
        if not copied:
            return None
        got = self.flush(force=True, message=f"board: the pages move to {self.branch()}")
        if got and got["commit"]:
            for page in copied:
                rel = page.resolve().relative_to(self.git.root.resolve()).as_posix()
                if _git(self.git.root, "ls-files", "--error-unmatch", "--", rel).returncode != 0:
                    page.unlink(missing_ok=True)
        return got
