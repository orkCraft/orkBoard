"""When a result lands by itself, and how many tasks run beside each other (docs/specs/84-the-next-task-goes-on.md, 86 §3): the runner's
land path and its slots, split from core/idea_runner.py to keep it under ~600 lines. `IdeaRunner` has them through `LandingMixin`.

    look_reason(...)       # "" when a result lands in dev by itself; else the first reason it waits for the person's look
    room(slug, task, ...)  # whether a ready task may start now: the Board's slots, its party's by size, one per member, never on the same files

A result lands by itself when its tests ran and are green, no finding is left, its diff touches no risk path its goal's risk left out,
and it holds no media; `ideas.review` on keeps every result for the look. A task starts by the Board's `max_parallel`, and its party's size
(Lean 1, Standard 2, Full 3; a party with no size, the Board's `max_parallel`, 1 by default); a party's members (the roles its team picked)
one task at a time each; and never beside a task whose `touches` meet its own (realm/claims.py). No face, no model.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from orkboard.realm import claims, ideas, idea_risk

SIZE_SLOTS = {"lean": 1, "standard": 2, "full": 3}
MEDIA = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".ico", ".svg", ".mp3", ".wav", ".ogg", ".oga", ".flac", ".m4a", ".aac", ".opus",
         ".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}      # images, sound and video: judged one by one (decisions §49.6)
NO_TESTS, NOT_RUN, RED, LEFT, PICTURES, ASKED = ("no tests in this project", "tests did not run", "the tests are red", "findings left",
                                                  "holds pictures", "you asked to look at each result")
COULD_NOT_RUN, DOCS = "the tests could not run", "it changes only documents"       # spec 107 §1.2: a gate that tested nothing; a task that changed only documents
_BRIEF_PATH = re.compile(r"`([A-Za-z0-9_./-]+)`")
SCAN_FILES = 200


def _r():
    """The runner's module (it imports this one: looked up when a task lands or starts)."""
    from orkboard.core import idea_runner
    return idea_runner


def media_in(files: list[str]) -> str:
    """The first picture, sound or video among the files of a diff, else ""."""
    return next((f for f in files if Path(f).suffix.lower() in MEDIA), "")


def risky_path(files: list[str], known: set[str], risk_paths: list[str]) -> str:
    """The first file of the diff that meets a risk trigger the goal's risk (`known`: its `risk_triggers`) left out, else "". A path
    only: the trigger that reads many folders (*wide*) is the plan's, not a file's."""
    for f in files[:SCAN_FILES]:
        got = idea_risk.assess(touches=[f], risk_paths=risk_paths)
        if any(t not in known and t != idea_risk.WIDE for t in got.triggers):
            return f
    return ""


def _cut(path: str) -> str:
    """A glob cut to the folder before its first wildcard (`gui/static/*` → `gui/static`)."""
    path = str(path).strip().strip("`")
    return path.split("*", 1)[0].rsplit("/", 1)[0] if "*" in path else path


def paths_of(task: dict) -> list[str]:
    """What a task names it changes: its `files`, and the paths in backticks in its brief; narrowed (never the root or a whole top folder)."""
    found = [str(f) for f in task.get("files") or [] if isinstance(f, str)]
    found += [m for m in _BRIEF_PATH.findall(str(task.get("brief") or "")) if "/" in m]
    return claims.narrow([_cut(p) for p in found])


class LandingMixin:
    """Needs the runner's `repo_root`, `state_dir`, `settings`, `size_of`, `_runs`, `plan` and `_role`."""

    # -- the goal's page ---------------------------------------------------------------------------

    def _page(self, slug: str) -> Any:
        """The goal's page (`ideas.Page`), found as the spec is (`idea_git.spec_paths`): the Board's tree, else the repository's; None without."""
        for base in (Path(self.state_dir) / "board", Path(self.repo_root)):
            for pattern in (f"llm-wiki/*/pages/ideas/{slug}.md", f"*/pages/ideas/{slug}.md", f"pages/ideas/{slug}.md"):
                found = [p for p in base.glob(pattern) if p.is_file()]
                if found:
                    try:
                        return ideas.parse(max(found, key=lambda p: p.stat().st_mtime).read_text(encoding="utf-8"))
                    except (OSError, UnicodeDecodeError):
                        return None
        return None

    @staticmethod
    def _list(page: Any, key: str) -> list[str]:
        try:
            got = json.loads(page.get(key) or "[]") if page is not None else []
        except ValueError:
            return []
        return [str(x) for x in got if isinstance(x, str)] if isinstance(got, list) else []

    def _party_of(self, slug: str, page: Any = None) -> str:
        """The party a goal is in (its page's `track`); the goal itself when it names none."""
        page = page if page is not None else self._page(slug)
        return str(page.get("track") or "") if page is not None and page.get("track") else slug

    # -- when a result lands by itself (spec 84 §1) --------------------------------------------------

    def look_reason(self, slug: str, tests: dict, left: int, files: list[str], red: bool = False, gated: bool = True,
                    looked: bool = False) -> str:
        """"" when the result lands in dev by itself; else why it waits for the person's look, the first that holds: no tests in this
        project (the gate is `none`), it changes only documents, the tests did not run, the tests could not run, the tests are red, findings left, `touches <path>` of a risk path its goal's
        risk left out, it holds pictures, you asked to look at each result (`ideas.review`). `gated`: False for a check that changed no file,
        which has no tests to speak of. `looked`: the person picked the variant it holds (a pick, §49.6), so its pictures were seen."""
        r = _r()
        if gated and tests.get("none"):
            return NO_TESTS
        if gated and tests.get("docs"):
            return DOCS
        if gated and not tests.get("ran"):
            return NOT_RUN
        if gated and tests.get("env"):
            return COULD_NOT_RUN
        if gated and (red or tests.get("green") is False):
            return RED
        if left:
            return LEFT
        page = self._page(slug)
        path = risky_path(files, set(self._list(page, "risk_triggers")), list(r.setting(self.settings, "risk_paths") or []))
        if path:
            return f"touches {path}"
        if media_in(files) and not looked:
            return PICTURES
        return ASKED if r.setting(self.settings, "review") else ""

    # -- the slots (spec 84 §2) ----------------------------------------------------------------------

    def _running_touches(self, slug: str, mine: list[dict]) -> list[tuple[str, str, list[str]]]:
        """(goal, task id, its paths) of the tasks that run now: the task's own paths, else its goal's `touches`; `mine`: the tasks of `slug`
        as the tick holds them (one just launched is not on disk yet)."""
        out = []
        for s, tid in list(self._runs):
            tasks = mine if s == slug else (self.plan(s) or {}).get("tasks") or []
            task = next((t for t in tasks if t.get("id") == tid), None)
            if task is not None:
                out.append((s, tid, paths_of(task)))
        return out

    def room(self, slug: str, task: dict, tasks: list[dict]) -> bool:
        """Whether a ready task may start now: the Board's `max_parallel` (raised to its party's size where that is more), its party's slots by
        size, a party's member (a role its team picked) one task at a time, and never beside a running task whose paths meet its own."""
        r = _r()
        running = list(self._runs) + [k for k in getattr(self, "_ticked", []) if k not in self._runs]
        board = max(1, int(r.setting(self.settings, "max_parallel") or 1))
        size = (self.size_of(slug) if self.size_of is not None else "") or ""
        cap = SIZE_SLOTS.get(size, board)
        if len(running) >= max(board, cap):
            return False
        page = self._page(slug) if running else None
        if running:
            party = self._party_of(slug, page)
            mine = [k for k in running if self._party_of(k[0]) == party]
            if len(mine) >= cap:
                return False
            role = str(task.get("role") or "")
            if size and role and any(self._runs[k].role == role for k in mine if k in self._runs):
                return False
            own = paths_of(task)
            goal = claims.narrow([_cut(p) for p in self._list(page, "touches")])
            for s, _tid, there in self._running_touches(slug, tasks):
                if s == slug:
                    meet = bool(own and there and claims.meets(own, there))
                else:
                    other = claims.narrow([_cut(p) for p in self._list(self._page(s), "touches")])
                    meet = bool((own or goal) and (there or other) and claims.meets(own or goal, there or other))
                if meet:
                    return False
        return True
