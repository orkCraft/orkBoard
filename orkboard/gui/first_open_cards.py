"""The first open's questions, answered from cards (docs/specs/130-the-first-open-is-the-orkmasters.md part A; decisions §232.3, §232.8): which question the
Orkmaster asks now and the answers the host takes. The cards are the page's (part B); what is here is what they send and read.

    first_open.ask {}                       # {step, line, name, path, recent, kind, hand, laid}: the question now (realm/first_open.py `step`)
    first_open.kind {kind? | about?}        # the project's kind answered: *Yes* (the kind read) or another one from the list, or an empty folder's one line
    first_open.tools_skip {}                # the adding card closed with no tool added: the Board opens, and nothing is worked on until a tool is added
    projects.new_folder {parent, name}      # *A new, empty folder…*: made inside the folder the system's dialog chose, and opened
    first_open.branch {branch?}             # the project's card's *Release branch* (spec 150 G.2.2): {branch, branches} read from git (`main` by default); with `branch` it is kept

`projects.open` and `projects.start_git` (gui/board_projects.py) answer *Open a folder…*, the recent projects and *Start git here*; the kind is read by
`ideas.proposals` (gui/ideas_project.py); nothing here asks a model but an empty folder's one line, which is that same call. Desktop only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from orkboard import settings
from orkboard.gui.ideas_args import IdeasError
from orkboard.realm import first_open, project_folder, project_kind, tool_hand
from orkboard.realm.idea_git import IdeaGit

NAME_CHARS = 100


class FirstOpen:
    def __init__(self, host: Any) -> None:
        self.host = host
        self.tools_skipped = False       # this run: the adding card was closed with no tool added (the next project asks again)

    def commands(self) -> dict[str, Callable[[dict], Any]]:
        return {"first_open.ask": self.ask, "first_open.kind": self.kind, "first_open.tools_skip": self.tools_skip, "projects.new_folder": self.new_folder,
                "first_open.branch": self.branch}

    def ask(self, args: dict) -> dict:
        """`{step, line, name, path, recent, kind, hand, laid}`: `step` one of `realm/first_open.STEPS`; `line` what the Orkmaster says in its bubble; `recent` the recent
        projects (`step: project`: the answers beside *Open a folder…* and *A new, empty folder…*); `kind` `{id, words, signs, how, empty}` while it asks what the
        project is (an empty folder asks *What is it for?* instead: `empty`); `hand` how many AI tools are in the hand; `laid` whether the table is laid."""
        project = self.host.projects.current()
        inn = len(tool_hand.hand(self.host.machine))
        if project is None:
            at = first_open.step(open=False, git=False, kind_kept=False, hand=inn, tools_skipped=self.tools_skipped, laid=False)
            return {"step": at, "line": first_open.line(at), "name": "", "path": "", "recent": self.host.projects.list()["recent"] if at == "project" else [], "kind": None,
                    "hand": inn, "laid": False}
        state_dir = project.ideas.state_dir
        laid = first_open.laid(state_dir, project.ideas.root(False))
        at = first_open.step(open=True, git=project_folder.has_git(project.root), kind_kept=bool(project_kind.kept(state_dir)), hand=inn,
                             tools_skipped=self.tools_skipped, laid=laid)
        kind, words = None, ""
        if at == "kind":
            got = project_kind.read_full(project.root)
            how = project_kind.in_words(list(got["signs"]))
            kind = {"id": got["kind"], "words": project_kind.words(got["kind"]), "signs": list(got["signs"]), "how": how, "empty": got["kind"] == "empty"}
            words = "" if kind["empty"] else ", ".join(x for x in (kind["words"], how) if x)
        line = first_open.line(at, project.name, words)
        if at == "kind":                                                  # said once, with the kind, for every kind: a new project's first read (spec 145 D)
            line = f"{line} {project_kind.start_words(project.root)}"
        return {"step": at, "line": line, "name": project.name, "path": project.path, "recent": [], "kind": kind, "hand": inn, "laid": laid}

    def _branches(self, project: Any) -> tuple[str, list[str]]:
        """`(the release branch now, the local branches)`: the one kept while it is there, else git's default (`main` by default); `("", [])` with no commit to read."""
        git = IdeaGit(Path(project.root))
        try:
            rows = git.branches()
            return first_open.release_branch(project.ideas.state_dir, rows, git.default_branch()), rows
        except Exception:                                                 # not a git folder yet
            return "", []

    def branch(self, args: dict) -> dict:
        """`{}`: `{branch, branches}`, the card's *Release branch* and the local branches a press lists. `{branch}`: that local branch is kept as the project's main, the one the
        portal sends into and the gate reads (`realm/first_open.py` `keep_release_branch`). Refused: *That is not a branch of this project*."""
        project = self.host.projects.current(need=True)
        now, rows = self._branches(project)
        want = args.get("branch")
        if want is None:
            return {"branch": now, "branches": rows}
        if not isinstance(want, str) or want not in rows:
            raise IdeasError("That is not a branch of this project")
        first_open.keep_release_branch(project.ideas.state_dir, want)
        self.host.on_change()
        return {"ok": True, "branch": want, "branches": rows}

    def kind(self, args: dict) -> dict:
        """The project's kind answered: `{kind}` is *Yes* (the one read) or another of the list, kept in `<state_dir>/project.json`; `{about}` is an empty folder's one
        line, read into a kind by the cheaper tier (`ideas.proposals`) and kept. Refused: *A kind is one of …*."""
        project = self.host.projects.current(need=True)
        state_dir = project.ideas.state_dir
        about, kind = args.get("about"), args.get("kind")
        read: bool | None = None
        if about is not None:
            if not isinstance(about, str) or not about.strip():
                raise IdeasError("Say in a line what it is for")
            got = project.ideas.proposals({"about": about})
            kind, read = got["kind"]["id"], got.get("read")
        try:
            kept = project_kind.keep(state_dir, str(kind or ""))
        except ValueError as e:
            raise IdeasError(str(e)) from None
        self.host.on_change()
        return {"ok": True, "kind": kept, **({"read": read} if read is not None else {})}

    def tools_skip(self, args: dict) -> dict:
        self.tools_skipped = True
        self.host.machine.onboarded = True                          # the machine is set up, with no tool
        settings.save(self.host.machine)
        self.host.on_change()
        return {"ok": True, "line": "No AI tool: the Board opens, and nothing is worked on until you add one"}

    def new_folder(self, args: dict) -> dict:
        """`{parent, name}`: an empty folder made in `parent` and opened as the project. Refused in words: no name, a name that is a path, a folder that is there already,
        one that may not be a project (`project_folder.refusal`; nothing is left behind)."""
        name = " ".join(str(args.get("name") or "").split())[:NAME_CHARS]
        if not name or name in (".", "..") or any(c in name for c in "/\\\0") or name.startswith("."):
            raise IdeasError("Name the folder with a plain name: no slash, no leading dot")
        parent = Path(str(args.get("parent") or "")).expanduser()
        if not parent.is_dir():
            raise IdeasError("That folder is not there")
        target = parent / name
        if target.exists():
            raise IdeasError(f"A folder named {name} is there already")
        try:
            target.mkdir()
        except OSError:
            raise IdeasError("That folder cannot be made here") from None
        if why := project_folder.refusal(target):
            target.rmdir()
            raise IdeasError(why)
        project = self.host.projects.open(target)
        self.host.on_change()
        return {"ok": True, "path": project.path, "git": project_folder.has_git(project.root)}
