"""The gate (docs/specs/49-one-window.md §2.1) as `gui/ideas.py`'s `Ideas` has it: `ideas.gate`, what dev holds that main
lacks (less what main holds by patch id), and `ideas.gate_merge`, the one press that merges dev into main (realm/idea_gate.py). A goal goes
to main on its own through `ideas.to_main_plan` and `ideas.to_main` (realm/goal_main.py, spec 105 §5). `dev` is the branch results
merge into (`ideas.into`), `main` the repository's default branch. Results still land in dev one by one; nothing reaches
main but through this press. Spec 50 §2.2: a goal raises its flag (realm/idea_flag.py) when this press takes it into main, or when it is done where there is
no gate. Split from ideas.py to keep it under ~600 lines.

The checks on the way into main (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4.2, realm/main_checks.py): `ideas.to_main_checks {idea}` starts
them in the background, one run at a time for a goal, and publishes each step on the bus (`main.check`, `{idea, checks}`: the face draws the snapshot's
`main_checks` again); their last results are kept per goal until the goal's plan changes (a new commit in it, or main moving), and `ideas.to_main` refuses
while any of them is not passed.
"""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Any

from orkboard import settings
from orkboard.core import bus
from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import event_log, gate_config, goal_main, idea_flag, idea_gate, ideas, main_checks
from orkboard.realm.idea_git import IdeaGit, _git


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
        `{ok, commit, goals, note}`; a sealed goal is refused in words, and so is one whose checks (`to_main_checks`) are running or not passed."""
        slug, where = self._to_main_args(args)
        refused = self._checks_refusal(slug, where)
        if refused:
            raise IdeasError(refused)
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

    # -- the checks on the way into main (spec 111 §4.2) -----------------------------------------------------

    def _checks_key(self, slug: str, where: dict) -> tuple[str, str]:
        """(a name for what the checks would run on, the plan's seal for a reason no check owns): the plan's commits and main's head, hashed.
        Nothing is tried here (no worktree)."""
        plan = goal_main.plan(Path(self.host.repo_root), self.state_dir, slug, **where, pick=False)
        head = _git(Path(self.host.repo_root), "rev-parse", "--verify", "-q", f"refs/heads/{where['main']}").stdout.strip()
        return hashlib.sha1(json.dumps([plan["commits"], head]).encode()).hexdigest()[:16], plan["sealed"] or ""

    def _checks_refusal(self, slug: str, where: dict) -> str:
        """Why the goal may not go to main yet for its checks, in words; "" when none stands (a goal whose checks were never asked goes as before)."""
        with self._main_lock:
            got = self._main_checks.get(slug)
            if got is None:
                return ""
            checks, running, key = list(got["checks"]), got["running"], got["key"]
        if running:
            return "Checking the way into main"
        if self._checks_key(slug, where)[0] != key:
            return "The way into main changed: choose the goal again"
        for c in checks:
            if c["state"] != "passed":
                return f"Sealed: {c['name']} is red: {c['words']}" if c["state"] == "failed" else "Checking the way into main"
        return ""

    def to_main_checks(self, args: dict) -> dict:
        """`{idea, again?}`: starts the checks on the way into main in the background (realm/main_checks.py), publishing each step (`main.check`).
        `{idea, checks: [{name, state, words}], running}`; the last results of the same plan are answered as they are, not run again, unless `again`
        (the person chose the goal anew after a red check). A seal no check owns (a goal not done, main behind its origin) is `{idea, checks: [], sealed}`."""
        slug, where = self._to_main_args(args)
        key, sealed = self._checks_key(slug, where)
        if sealed:
            return {"idea": slug, "checks": [], "running": False, "sealed": sealed}
        with self._main_lock:
            got = self._main_checks.get(slug)
            if got and got["key"] == key and (got["running"] or not (args.get("again") and any(c["state"] != "passed" for c in got["checks"]))):
                return {"idea": slug, "checks": list(got["checks"]), "running": got["running"]}
            if got:
                got["stop"].set()                                   # an older run of this goal ends, its worktree gone
            entry = {"key": key, "checks": [{"name": c.name, "state": "waiting", "words": ""} for c in gate_config.main_checks(Path(self.host.repo_root))],
                     "running": True, "stop": threading.Event()}
            self._main_checks[slug] = entry
        threading.Thread(target=self._checks_run, args=(slug, where, entry), name=f"main-checks-{slug}", daemon=True).start()
        self._checks_said(slug, entry)
        return {"idea": slug, "checks": list(entry["checks"]), "running": True}

    def _checks_run(self, slug: str, where: dict, entry: dict) -> None:
        """The run, on its own thread: each step is kept and published; whatever happens the run ends (a failure of the run itself fails the first check
        that has not passed, in words)."""
        def step(steps: list[dict]) -> None:
            with self._main_lock:
                if self._main_checks.get(slug) is entry:
                    entry["checks"] = steps
            self._checks_said(slug, entry)

        try:
            main_checks.run(Path(self.host.repo_root), self.state_dir, slug, root=where["root"], into=where["into"], main=where["main"],
                            on_step=step, cancel=entry["stop"])
        except InterruptedError:
            with self._main_lock:
                if self._main_checks.get(slug) is entry:
                    del self._main_checks[slug]
        except Exception as e:                                  # a run that cannot go on says why on the check it stopped at
            steps = [dict(c) for c in entry["checks"]]
            at = next((i for i, c in enumerate(steps) if c["state"] != "passed"), 0)
            steps[at] = {**steps[at], "state": "failed", "words": " ".join(str(e).split())[:160] or "The check could not run"}
            step(steps)
        finally:
            with self._main_lock:
                entry["running"] = False
            self._checks_said(slug, entry)

    def _checks_said(self, slug: str, entry: dict) -> None:
        """`main.check` on the host's bus, from whichever thread (the host's own, as the keeper's changes are)."""
        with self._main_lock:
            if self._main_checks.get(slug) is not entry:                # an older run of the goal ended: its steps say nothing now
                return
            checks = [dict(c) for c in entry["checks"]]
        self.host.call(lambda: self.host.publish(bus.MAIN_CHECK, idea=slug, checks=checks))

    def main_checks_now(self) -> dict[str, list[dict]]:
        """The last results of the checks, by goal, for the snapshot (the face follows them there): `{slug: [{name, state, words}]}`."""
        with self._main_lock:
            return {slug: [dict(c) for c in got["checks"]] for slug, got in self._main_checks.items()}

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
    return {"ideas.to_main_plan": ideas_.to_main_plan, "ideas.to_main": ideas_.to_main, "ideas.to_main_checks": ideas_.to_main_checks}
