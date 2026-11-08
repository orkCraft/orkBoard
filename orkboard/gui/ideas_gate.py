"""The gate (docs/specs/49-one-window.md §2.1) as `gui/ideas.py`'s `Ideas` has it: `ideas.gate`, what dev holds that main
lacks (less what main holds by patch id), and `ideas.gate_merge`, the one press that merges dev into main (realm/idea_gate.py). A goal goes
to main on its own through `ideas.to_main_plan` and `ideas.to_main` (realm/goal_main.py, spec 105 §5). `dev` is the branch results
merge into (`ideas.into`), `main` the repository's default branch. Results still land in dev one by one; nothing reaches
main but through this press. Spec 50 §2.2: a goal raises its flag (realm/idea_flag.py) when this press takes it into main, or when it is done where there is
no gate. Split from ideas.py to keep it under ~600 lines.

The checks on the way into main (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4.2, realm/main_checks.py): `ideas.to_main_checks {idea}` starts
them in the background, one run at a time for a goal, and publishes each step on the bus (`main.check`, `{idea, checks}`: the face draws the snapshot's
`main_checks` again); their last results are kept per goal until the goal's plan changes (a new commit in it, or main moving), and `ideas.to_main` refuses a goal whose checks were never run or passed for another head of main, and
while any of them is not passed.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

from orkboard import settings
from orkboard.core import bus
from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import commit_goal, event_log, findings_gather, first_open, gate_config, goal_main, goal_types, idea_flag, idea_gate, ideas, journal_notes, main_checks, party_recipes
from orkboard.realm.idea_git import IdeaGit, _git


class GateMixin:
    def _gate_main(self, git: IdeaGit) -> str:
        """The repository's main: the release branch kept at the first open (realm/first_open.py) while it is still there, else the default branch;
        "" where there is no git yet (the gate is then off, as with no main)."""
        try:
            return first_open.release_branch(self.state_dir, git.branches(), git.default_branch())
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
            pile = self._pile(git, into, main)
        except Exception:                       # a repository git cannot read: nothing waits that the Board can see
            return out
        if pile["ready"]:
            self._release_reads()                # a goal is ready for main: Release has something to ask about (spec 143 E.1)
        return {**out, "commits": len(pile["shas"]), "files": pile["files"], "ideas": pile["ready"]}

    def _pile(self, git: IdeaGit, into: str, main: str) -> dict:
        """What waits in dev for main: `{shas, files, ready, held}`. `shas` and `files` count only the commits of goals ready for main and of no goal:
        not the Board's own, nor those of a goal a task of which is not done (spec 149 G.3, decisions §253.8); `ready` the goals ready (`ideas_in`'s rows),
        `held` the goals with commits in dev that are not, each `{slug, title, done, of}` (the tasks merged of the tasks there are)."""
        shas, files = idea_gate.waiting_by_patch(git, into, main)      # a goal sent alone is not counted again
        try:
            shas, files = idea_gate.without_board_pages(git, shas, files)      # the Board's own commits are no pile: they go with the next goal (spec 143 F.4, §247.1; spec 149 G.4)
        except Exception:
            pass
        rows = self._gate_ideas(shas)
        ready = self._ready_ideas(rows)
        names = {r["slug"] for r in ready}
        held = [self._held(r) for r in rows if r["slug"] not in names]
        if held:
            try:
                owners = commit_goal.index(self.state_dir, git.root, into)
                mine = {h["slug"] for h in held}
                shas, files = idea_gate.without_commits(git, shas, files, {s for s in shas if owners.get(s, {}).get("goal") in mine})
            except Exception:
                pass
        return {"shas": shas, "files": files, "ready": ready, "held": held}

    def _held(self, row: dict) -> dict:
        """A goal with work in dev that is not ready for main: `{slug, title, done, of}`, the title short."""
        tasks = [t for t in (ideas.plan(self.state_dir, row["slug"]) or {}).get("tasks") or [] if isinstance(t, dict) and not goal_types.is_dropped(t)]
        short = next((i["short"] or i["title"] for i in ideas.ideas(self.root(False)) if i["slug"] == row["slug"]), row["title"])
        return {"slug": row["slug"], "title": short or row["title"], "done": sum(1 for t in tasks if t.get("state") == "merged"), "of": len(tasks)}

    NOT_YET = ("failed", "waiting", "ready", "running", "testing", "picking", "review")        # a task in one of these is not done: its goal is not ready for main

    def _ready_ideas(self, rows: list[dict]) -> list[dict]:
        """Of the goals with work in dev, those ready for main: none of its tasks is failed, waiting, ready, running or to look at (spec 143 F.3,
        decisions §250.7). The page reads this answer; it decides nothing."""
        out = []
        for r in rows:
            plan = ideas.plan(self.state_dir, r["slug"]) or {}
            if not any(t.get("state") in self.NOT_YET and not goal_types.is_dropped(t) for t in plan.get("tasks") or []):
                got = self._main_checks.get(r["slug"]) or {}
                red = any(c["state"] == "failed" for c in got.get("checks", []))
                out.append({**r, "main_ready": not red, "main_reason": next((c["words"] for c in got.get("checks", []) if c["state"] == "failed"), "")})
        return out

    def _release_reads(self) -> None:
        try:
            for t in ideas.tracks(self.root(False), make=False):
                if party_recipes.is_release(t):
                    self.read_release(t["slug"])
        except Exception:                        # a reading that cannot start never breaks the gate's count
            pass

    def gate_merge(self, args: dict) -> dict:
        """`{}`: merge dev into main (fast-forward, else a merge commit), pushed when the project pushes after merging.
        `{ok, commit, note}`: main's new head and the push's note ("" when pushed or there is no origin)."""
        into = self._into()
        git = IdeaGit(Path(self.host.repo_root))
        main = self._gate_main(git)
        push = bool(self.settings_now().get("push", settings.IDEAS["push"]))
        if not idea_gate.same(into, main):
            try:
                pile = self._pile(git, into, main)
                held = pile["held"]
                red = next((r for r in pile["ready"] if r.get("main_ready") is False), None)
                if red:
                    raise IdeasError(f"Sealed: {red['main_reason']}. Use Test again on the goal first")
            except IdeasError:
                raise
            except Exception:                   # a repository git cannot read: the merge says so itself
                held = []
            if held:                            # nothing reaches main half made by a press that does not say so (spec 149 G.2, decisions §253.7)
                raise IdeasError(self._half_made(held, main))
        tested = self._merge_tested(git, into, main)            # the tests run with the repository free; the merge then takes what they ran on, or nothing
        try:
            got = idea_gate.merge(git, into, main, push, tested=tested)
        except RuntimeError as e:               # a refusal (GateRefused) or git's own words
            raise IdeasError(" ".join(str(e).split())[:300] or "The merge failed") from None
        brought = self._gate_ideas(got["commits"])
        self._ev(event_log.GATE_MERGED, args, commits=len(got["commits"]), ideas=len(brought),
                 files=got["files"], how=got["how"], pushed=got["pushed"], into=into, main=main)
        self._flag_after_gate(brought, got["commit"], git, main)
        self.changed("")
        return {"ok": True, "commit": got["commit"], "note": got["note"]}

    def _merge_tested(self, git: IdeaGit, into: str, main: str) -> tuple[str, str] | None:
        """Nothing reaches main untested (decisions §274.2): the checks after *The merge* run on what main would become, here and now, and a red stops the
        press with main as it was, naming the test (realm/main_checks.py `verify`; the trial worktree is gone). Nothing waiting is the merge's own refusal.
        `(main, into)` as the checks found them, for the merge to refuse should either move while they ran (None: nothing was tested)."""
        if idea_gate.same(into, main) or not idea_gate.waiting_by_patch(git, into, main)[0]:
            return None
        if gate_config.read(Path(self.host.repo_root)).none:     # no tests, no green: the one way is To main without the tests (decisions §274.3)
            raise IdeasError(self._NO_TESTS)
        try:
            with git.lock:
                heads = idea_gate.heads(git, into, main)
                tip = idea_gate.tip(git, into, main)
            base = heads[0]
            ok, name, words = main_checks.verify(Path(self.host.repo_root), tip, base)
        except idea_gate.GateRefused as e:
            raise IdeasError(" ".join(str(e).split())[:300]) from None
        except RuntimeError as e:
            raise IdeasError(" ".join(str(e).split())[:300] or "The tests could not run") from None
        if not ok:
            raise IdeasError(f"Sealed: {name} is red: {words}")
        return heads

    @staticmethod
    def _half_made(held: list[dict], main: str) -> str:
        """*Lobby is at 2 of 4: it would reach main half made.* for the first goal held, the others counted."""
        first = held[0]
        more = f" Nor would {len(held) - 1} more goal{'s' if len(held) > 2 else ''}." if len(held) > 1 else ""
        return f"{first['title']} is at {first['done']} of {first['of']}: it would reach {main} half made.{more}"

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
        `{ok, commit, goals, note}`; a sealed goal is refused in words, and so is one whose checks (`to_main_checks`) are running or not passed.
        `untested: true` (a literal boolean; nothing else skips the checks, decisions §274.3) sends it without the tests; a project whose gate has no tests
        is refused unless it is given. The event says `tests: "run"` (and `checks_s`, the checks' seconds) or `"skipped"`."""
        slug, where = self._to_main_args(args)
        untested = args.get("untested") is True                # the one named skip (decisions §274.3): a literal true, nothing truthy else
        refused = self._untested_refusal(slug, where) if untested else self._no_tests_refusal(slug, where) or self._checks_refusal(slug, where)
        if refused:
            raise IdeasError(refused)
        took = None if untested else self._checks_took(slug)
        push = bool(self.settings_now().get("push", settings.IDEAS["push"]))
        git = IdeaGit(Path(self.host.repo_root))
        try:
            with git.lock:                     # the checks' record is read under its own lock, briefly: none is held through the push
                got = goal_main.merge(Path(self.host.repo_root), self.state_dir, slug, push, **where,
                                      validate=None if untested else lambda commits, base: self._validate_checks(slug, commits, base))
        except RuntimeError as e:               # a refusal (GoalRefused) or git's own words
            raise IdeasError(" ".join(str(e).split())[:300] or "The merge failed") from None
        self._ev(event_log.GOAL_TO_MAIN, args, idea=slug, goals=got["goals"], commits=len(got["commits"]), files=got["files"],
                 pushed=got["pushed"], into=where["into"], main=where["main"],
                 tests="skipped" if untested else "run", **({} if took is None else {"checks_s": took}))
        self._flag_after_goal(got["goals"], got["commit"], git, where["into"], where["main"])
        self._gather_verdict(got["goals"])
        self.changed("")
        return {"ok": True, "commit": got["commit"], "goals": got["goals"], "note": got["note"]}

    def _gather_verdict(self, goals: list[str]) -> None:
        """The goals that reached the discard: each one's verdict against its spec read once, a `differs` or `missing` line a finding (spec 132 D.2, realm/findings_gather.py). Never fails the merge."""
        for slug in goals:
            try:
                findings_gather.verdict(self.state_dir, self.root(False), Path(self.host.repo_root), slug, self._ref())
            except Exception:
                pass

    # -- the checks on the way into main (spec 111 §4.2) -----------------------------------------------------

    def _checks_key(self, slug: str, where: dict) -> tuple[str, str]:
        """(a name for what the checks would run on, the plan's seal for a reason no check owns): the plan's commits and main's head, hashed.
        Nothing is tried here (no worktree)."""
        plan = goal_main.plan(Path(self.host.repo_root), self.state_dir, slug, **where, pick=False)
        head = _git(Path(self.host.repo_root), "rev-parse", "--verify", "-q", f"refs/heads/{where['main']}").stdout.strip()
        return hashlib.sha1(json.dumps([plan["commits"], head]).encode()).hexdigest()[:16], plan["sealed"] or ""

    def _validate_checks(self, slug: str, commits: list[str], base: str) -> None:
        """The goal's checks passed on exactly these picks onto exactly this main (called by the merge, under the repository's lock, before and after
        the picks); else refused: no older green carries a changed way into main."""
        key = hashlib.sha1(json.dumps([commits, base]).encode()).hexdigest()[:16]
        with self._main_lock:
            got = self._main_checks.get(slug) or {}
            if (got.get("key") != key or got.get("binding") != [commits, base]
                    or got.get("running", True) or not got.get("checks")
                    or any(c["state"] != "passed" for c in got["checks"])):
                raise IdeasError("The way into main changed: run the checks again")

    def _untested_refusal(self, slug: str, where: dict) -> str:
        """The skip still stops at a reason no check owns (not done, in main already, a pick that conflicts)."""
        return self._checks_key(slug, where)[1]

    _NO_TESTS = "This project has no tests, so nothing can show the goal is safe for main: send it with To main without the tests"

    def _no_tests_refusal(self, slug: str, where: dict) -> str:
        """A project whose gate has no tests cannot show a green: it is refused in words, naming the one way out (decisions §274.3)."""
        sealed = self._checks_key(slug, where)[1]
        if sealed:
            return sealed
        if gate_config.read(Path(self.host.repo_root)).none:
            return self._NO_TESTS
        return ""

    def _checks_took(self, slug: str) -> float | None:
        """The seconds the goal's last checks took; None when they did not finish."""
        with self._main_lock:
            return (self._main_checks.get(slug) or {}).get("took")

    def _checks_refusal(self, slug: str, where: dict) -> str:
        """Why the goal may not go to main yet for its checks, in words; "" when it may (decisions §274.2: the checks passed against main as it is now).
        A goal whose checks were never run is refused too, saying to run them."""
        key, sealed = self._checks_key(slug, where)
        if sealed:                               # a reason no check owns (not done, in main already, a pick that conflicts) is the first thing said
            return sealed
        with self._main_lock:
            got = self._main_checks.get(slug)
            if got is None:
                return "Its checks have not been run: run the checks on the way into main first"
            checks, running, kept = list(got["checks"]), got["running"], got["key"]
        if running:
            return "Checking the way into main"
        if kept != key:
            return "The way into main changed since its checks passed (a new commit, or main moved): run the checks again"
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
            if got and ((any(c["state"] == "failed" for c in got["checks"]) and args.get("again") is not True)
                        or (got["key"] == key and (got["running"] or args.get("again") is not True))):
                return {"idea": slug, "checks": list(got["checks"]), "running": got["running"]}
            if got:
                got["stop"].set()                                   # an older run of this goal ends, its worktree gone
            entry = {"key": key, "checks": [{"name": c.name, "state": "waiting", "words": ""} for c in gate_config.main_checks(Path(self.host.repo_root))],
                     "running": True, "stop": threading.Event(), "began": time.monotonic(), "took": None}
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
                    binding = entry.get("binding")
                    entry["checks"] = [{**s, **({"candidate": list(binding[0]), "main_base": binding[1]} if binding else {})} for s in steps]
            self._checks_said(slug, entry)

        def binding(commits, base):
            with self._main_lock:
                entry["binding"] = [commits, base]

        try:
            main_checks.run(Path(self.host.repo_root), self.state_dir, slug, root=where["root"], into=where["into"], main=where["main"],
                            on_step=step, cancel=entry["stop"], on_binding=binding)
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
                entry["took"] = round(time.monotonic() - entry["began"], 1)
            self._checks_said(slug, entry)

    def _checks_said(self, slug: str, entry: dict) -> None:
        """`main.check` on the host's bus, from whichever thread (the host's own, as the keeper's changes are)."""
        with self._main_lock:
            if self._main_checks.get(slug) is not entry:                # an older run of the goal ended: its steps say nothing now
                return
            checks = [dict(c) for c in entry["checks"]]
        def publish():
            with self._main_lock:
                if self._main_checks.get(slug) is not entry:
                    return
            self.host.publish(bus.MAIN_CHECK, idea=slug, checks=checks)
        self.host.call(publish)

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
        journal_notes.done(self.state_dir, root, slug)                  # the project's journal: the goal is in main (spec 125 B)
        self._fold_spec(slug)
        self.changed(slug)
        self.collide_released(slug)             # the goals of other parties that waited for this flag may start (spec 71 §4)
        return True

    def _fold_spec(self, slug: str) -> None:
        """The goal reached main: its party's leader folds it into the product's living specs, in the background (spec 127 C.2). Quiet: busy, not allowed or broken, it is skipped, and the flag
        is raised all the same."""
        try:
            fold = getattr(self.keeper, "fold", None)
            if fold is not None:
                fold(slug)
        except Exception:
            pass

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
