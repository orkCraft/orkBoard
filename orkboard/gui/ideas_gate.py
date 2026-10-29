"""The gate (docs/specs/49-one-window.md §2.1) as `gui/ideas.py`'s `Ideas` has it: `ideas.gate`, what dev holds that main
lacks (less what main holds by patch id), and `ideas.gate_merge`, the one press that merges dev into main (realm/idea_gate.py). A goal goes
to main on its own through `ideas.to_main_plan` and `ideas.to_main` (realm/goal_main.py, spec 105 §5). `dev` is the branch results
merge into (`ideas.into`), `main` the repository's default branch. Results still land in dev one by one; nothing reaches
main but through this press. Spec 50 §2.2: a goal raises its flag (realm/idea_flag.py) when this press takes it into main, or when it is done where there is
no gate. Split from ideas.py to keep it under ~600 lines.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard import settings
from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import event_log, goal_main, idea_flag, idea_gate, ideas
from orkboard.realm.idea_git import IdeaGit


class GateMixin:
    def _gate_main(self, git: IdeaGit) -> str:
        """The repository's default branch; "" where there is no git yet (the gate is then off, as with no main)."""
        try:
            return git.default_branch()
        except Exception:                       # not a git folder yet
            return ""

    def _gate_ideas(self, shas: list[str]) -> list[dict]:
        """The ideas with a merged task whose commit is among `shas`, in the Board's order."""
        rows = []
        for i in ideas.ideas(self.root(False)):
            plan = ideas.plan(self.state_dir, i["slug"])
            if plan:
                rows.append((i["slug"], i["title"], i["track"], plan.get("tasks") or []))
        return idea_gate.ideas_in(shas, rows)

    def gate(self, args: dict) -> dict:
        """`{}`: `{into, main, same, commits, files, ideas: [{slug, title, goal, tasks}]}`. `same`: dev and main are one
        branch, or main does not exist: there is no gate (and nothing else is counted)."""
        into = self._into()
        git = IdeaGit(Path(self.host.repo_root))
        main = self._gate_main(git)
        out = {"into": into, "main": main, "same": idea_gate.same(into, main), "commits": 0, "files": 0, "ideas": []}
        if out["same"]:
            return out
        try:
            shas, files = idea_gate.waiting_by_patch(git, into, main)      # a goal sent alone is not counted again
        except Exception:                       # a repository git cannot read: nothing waits that the Board can see
            return out
        return {**out, "commits": len(shas), "files": files, "ideas": self._gate_ideas(shas)}

    def gate_merge(self, args: dict) -> dict:
        """`{}`: merge dev into main (fast-forward, else a merge commit), pushed when the project pushes after merging.
        `{ok, commit, note}`: main's new head and the push's note ("" when pushed or there is no origin)."""
        into = self._into()
        git = IdeaGit(Path(self.host.repo_root))
        main = self._gate_main(git)
        push = bool(self.settings_now().get("push", settings.IDEAS["push"]))
        try:
            got = idea_gate.merge(git, into, main, push)
        except RuntimeError as e:               # a refusal (GateRefused) or git's own words
            raise IdeasError(" ".join(str(e).split())[:300] or "The merge failed") from None
        brought = self._gate_ideas(got["commits"])
        self._ev(event_log.GATE_MERGED, args, commits=len(got["commits"]), ideas=len(brought),
                 files=got["files"], how=got["how"], pushed=got["pushed"], into=into, main=main)
        self._flag_after_gate(brought, got["commit"], git, main)
        self.changed("")
        return {"ok": True, "commit": got["commit"], "note": got["note"]}

    # -- a goal to main on its own (spec 105 §5) ------------------------------------------------------------

    def _to_main_args(self, args: dict) -> tuple[str, dict]:
        slug = _text(args, "idea", 100)
        git = IdeaGit(Path(self.host.repo_root))
        return slug, {"root": self.root(False), "into": self._into(), "main": self._gate_main(git)}

    def to_main_plan(self, args: dict) -> dict:
        """`{idea}`: what sending the goal to main takes, before anything moves. `{idea, goals, titles, commits, files, sealed, into, main}`:
        `goals` the goal first and then the goals it stands on that main lacks, `titles` their short titles, `commits` the shas in the
        order they go, `sealed` the reason in words (None when it can go)."""
        slug, where = self._to_main_args(args)
        got = goal_main.plan(Path(self.host.repo_root), self.state_dir, slug, **where)
        return {"idea": slug, **got, "into": where["into"], "main": where["main"]}

    def to_main(self, args: dict) -> dict:
        """`{idea}`: the goal's commits (and its dependencies') cherry-picked onto main, pushed when the project pushes after merging.
        `{ok, commit, goals, note}`; a sealed goal is refused in words."""
        slug, where = self._to_main_args(args)
        push = bool(self.settings_now().get("push", settings.IDEAS["push"]))
        git = IdeaGit(Path(self.host.repo_root))
        try:
            got = goal_main.merge(Path(self.host.repo_root), self.state_dir, slug, push, **where)
        except RuntimeError as e:               # a refusal (GoalRefused) or git's own words
            raise IdeasError(" ".join(str(e).split())[:300] or "The merge failed") from None
        self._ev(event_log.GOAL_TO_MAIN, args, idea=slug, goals=got["goals"], commits=len(got["commits"]), files=got["files"],
                 pushed=got["pushed"], into=where["into"], main=where["main"])
        self._flag_after_goal(got["goals"], got["commit"], git, where["into"], where["main"])
        self.changed("")
        return {"ok": True, "commit": got["commit"], "goals": got["goals"], "note": got["note"]}

    def _flag_after_goal(self, goals: list[str], commit: str, git: IdeaGit, into: str, main: str) -> None:
        """After the pick: each goal it took that is done and has no flag, all of whose commits are in main now (by patch id: a pick is a
        new commit). A flag never troubles the merge."""
        for slug in goals:
            try:
                if ideas.state(self.state_dir, slug)["state"] == "done" and idea_flag.flag_of(self.state_dir, slug) is None \
                        and goal_main.in_main(git, idea_flag.commits_of(self.state_dir, slug), into, main):
                    self._raise_flag(slug, "gate", commit)
            except Exception:
                pass

    # -- a goal's flag (spec 50 §2.2) ---------------------------------------------------------------------------

    def _raise_flag(self, slug: str, by: str, commit: str = "") -> bool:
        """The goal's flag, once: written, logged (`idea_flagged`) and published (`ideas.changed` with its slug). False when
        it had one already."""
        if idea_flag.flag_of(self.state_dir, slug) is not None:
            return False
        root = self.root(False)
        got = idea_flag.raise_flag(root, self.state_dir, slug, by, commit)
        party = (ideas.idea_page(root, slug) or ideas.Page()).get("track") or ""
        self._ev(event_log.IDEA_FLAGGED, None, idea=slug, goal=party, by=by, tasks=got["tasks"], first_time=got["first_time"],
                 usd=got["usd"], days=got["days"])
        self.changed(slug)
        self.collide_released(slug)             # the goals of other parties that waited for this flag may start (spec 71 §4)
        return True

    def _flag_after_gate(self, brought: list[dict], commit: str, git: IdeaGit, main: str) -> None:
        """After the press: each done goal without a flag that this merge brought commits of, all of whose commits are in main
        now. (A goal done and in main before this spec has none of its commits among them: no backfill.) A flag never troubles
        the merge."""
        for row in brought:
            slug = row["slug"]
            try:
                if ideas.state(self.state_dir, slug)["state"] == "done" and idea_flag.flag_of(self.state_dir, slug) is None \
                        and idea_gate.all_in(git, idea_flag.commits_of(self.state_dir, slug), main):
                    self._raise_flag(slug, "gate", commit)
            except Exception:
                pass

    def _flag_when_done(self, slug: str) -> None:
        """A goal became done: where there is no gate (results merge into main itself), or when all its commits are in main
        already (its last task a clean check, after an earlier merge), its flag is raised. Done in dev, it waits for the gate."""
        try:
            git = IdeaGit(Path(self.host.repo_root))
            main, commits = self._gate_main(git), idea_flag.commits_of(self.state_dir, slug)
            if idea_gate.same(self._into(), main) or idea_gate.all_in(git, commits, main):
                self._raise_flag(slug, "done", commits[-1] if commits else "")
        except Exception:
            pass


def gate_commands(ideas_: Any) -> dict:
    """The goal-to-main commands by name (`gui/ideas.py` adds them to its table: `**gate_commands(self)`)."""
    return {"ideas.to_main_plan": ideas_.to_main_plan, "ideas.to_main": ideas_.to_main}
