"""A task's own parts of the runner (core/idea_runner.py, which imports this one): the gate on its worktree (`_check`,
`_tests_of`), its environment (`_env`) and its prompt (`_prompt`). `IdeaRunner` has them through `TaskMixin`.
"""
from __future__ import annotations

import re
import subprocess
import threading
import time
from pathlib import Path

from orkboard.core.idea_landing import COULD_NOT_RUN
from orkboard.realm import agent_rules, board_in_code, dep_links, event_log, gate_config, gate_env, gate_rerun, idea_checks, jobs, idea_pick, idea_secrets, idea_target, task_brief, task_steps
from orkboard.realm.idea_git import BOARD_PAGE, env_name, has_summary, parse_tests, read_secret, spec_paths


FINDINGS_ASK = (
    f"When you are done, write what you found to `{idea_checks.FINDINGS_FILE}` at the worktree's root, as JSON: "
    '`{"findings": [{"where": "file:line, or the screen", "what": "one line: what goes wrong", "fixed": true, "kind": "code"}]}`, '
    'the worst first, at most 20. Write `{"findings": []}` when you found nothing that blocks, and then change nothing else. Fix only what is '
    'small and certain; leave the rest as findings with `"fixed": false`. Each finding has a `kind`: `"code"` when the code is wrong, '
    '`"env"` when it could not be done here, in the place you ran in (a command was refused, a tool is missing, there is no device or '
    'no network): a person can fix the code, not the place, so never write a finding about the place as `"code"`.')
CANNOT_COMMIT = ("Git cannot write in this sandbox: do not commit; what you leave is committed for you under the task's title. What is settled about "
                 "the change goes in `.ork-commit.md` at the worktree's root: it is put under that title as the commit's message, and is never committed itself.")
NO_BROWSER_HERE = "A browser cannot start here: do not look for one; the gate runs the browser tests."       # spec 149 F.1
NO_BROWSER = "Browser tests did not run: no Chromium here."     # spec 143 B.3
# The reasons a browser module gives when it is skipped for want of a browser (tests/browser_kit.py, `pytest.importorskip`), which the gate's
# `-rfEs` prints: a test's own skip (a case that does not apply at a width) is never read as *no Chromium here*.
NO_BROWSER_SKIP = re.compile(r"no Chromium|could not import 'playwright", re.I)
NOT_THE_BOARDS = ("You are one task of a goal Orkboard leads: the Board's rules in AGENTS.md are for a tool that leads a goal, not for you. "
                  "Do not take a goal, move its phase or write the Board's pages, and do not read BOARD.md for this task.")     # spec 152 D.3, decisions §257.6
NO_FINDINGS = "You left no findings file and changed no file. Write your findings file, as the task asks."
FRESH_TOKENS = 150_000            # a session that read more than this in its last call is not resumed again: a send back starts a fresh one (spec 86 §4)
DIFF_KEEP = 20000                 # the diff so far a fresh session is given, in characters
FRESH = """You are given this task again, in a new session: the one before it grew too long to go on. What it had done so far is
committed in this worktree; the diff of it against `{base}` is below{cut}.

```diff
{diff}
```

"""
PICK_BACK = """The person looked at your last variants and picked none of them:

None of the last variants: "{note}"

Make {n} new ones in this same worktree."""
NO_RUN = {"passed": 0, "failed": 0, "failing": [], "tail": "", "green": True, "ran": False, "command": ""}      # a check that changed no file: no gate ran
NO_DIFF = {"files": 0, "added": 0, "removed": 0}
INSTALL_FAILED = "The install failed: {last}"
_TIMES = re.compile(r"\b\d+(?:\.\d+)?\s?m?s\b|\b\d\d:\d\d:\d\d\b")      # what changes between two runs of the same failure: durations, clock times


def verdict(d: dict) -> str:
    """What a gate run came to, for the event log (spec 107 §1.2): `could_not_run` · `docs` · `nothing` (it found nothing to run) · `green` · `red`.
    `d`: a result's `tests`, or a run as {"env", "docs", "ran", "green"}."""
    if d.get("env"):
        return "could_not_run"
    if d.get("docs"):
        return "docs"
    if d.get("ran") is False:
        return "nothing"
    return "green" if d.get("green") else "red"


def same_tail(a: object, b: object) -> bool:
    """Two gate tails are one failure: the same words, durations and clock times left out. Empty tails are none."""
    clean = lambda t: " ".join(_TIMES.sub("", str(t or "")).split())      # noqa: E731
    return bool(clean(a)) and clean(a) == clean(b)


def is_check(task: dict) -> bool:
    """A check task: its `kind` is a checker's tag (realm/idea_checks.py `TAGS`)."""
    return str(task.get("kind") or "") in idea_checks.TAGS


def _r():
    """The runner's module (it imports this one: looked up when a task runs)."""
    from orkboard.core import idea_runner
    return idea_runner


def gate_words(gate: gate_config.Gate) -> str:
    """What a task's prompt says of the gate: this project's own (`gate_config.read`), never Orkboard's by default."""
    if gate.run:
        what = f"Then the gate runs `{gate.run}`"
    elif gate.always:
        what = f"Then the gate runs `python -m pytest -q {' '.join(gate.always)}` and the test files of the modules you touch"
    else:
        return ("Then the gate checks that you changed something. This project has no tests, so the change waits for a "
                "person's look; a gate that finds nothing changed comes back to you once, in this session.")
    return what + ", and a red gate comes back to you once, in this session."


def is_pick(task: dict) -> bool:
    """A task that ends with variants for the person to pick from (spec 51): its plan's task has a `pick`; a check never does."""
    return not is_check(task) and idea_pick.ask_of(task) is not None


def pick_ask(task: dict) -> str:
    """What a task that makes variants is told besides its brief (spec 51 §2.2): how many, of which kind, for what, where to write
    them and the manifest, and that it changes nothing else (as a check's findings file, they are read and never committed)."""
    ask = idea_pick.ask_of(task) or {}
    kind = idea_pick.KINDS[ask["kind"]]
    return (f"This task ends with {ask['n']} variants for the person to pick from, not with a change. Make {ask['n']} {kind.many} "
            f"({kind.formats}; at most {idea_pick.size_words(kind.limit)} each) for this: {ask['ask']}\n"
            f"Write each as a file into `{idea_pick.PICK_DIR}/` at the worktree's root, and a manifest `{idea_pick.PICK_FILE}` at the root, as JSON: "
            '`{"variants": [{"name": "24 characters at most", "file": "its file name in the folder", "why": "one line"}]}`, '
            f"exactly {ask['n']}, each different from the others. Make the files with your own tools. Change nothing else and commit nothing: "
            f"the person picks one, and it is written to `{ask['target']}` for you.")


class TaskMixin:
    """Needs the runner's `repo_root`, `state_dir`, `settings`, `git`, `_gate_runs`, `_since`, `on_held`, `_emit`, `_log` and `_role`."""

    def _tests_of(self, path: Path, out: str, problem: str | None) -> dict:
        """The result's `tests` (spec 37 §5): pytest's counts when its summary line is there, else `null` counts and the
        exit code; `ran` False when the gate found nothing to run; `command` as run."""
        run = self._gate_runs.pop(str(path), None)
        tests = parse_tests(out)
        tests["green"] = problem is None
        tests["ran"] = run.ran if run else True
        tests["command"] = run.command if run else ""
        if gate_config.read(self.repo_root).none:      # the project has no tests at all (spec 86 §3): it never lands by itself
            tests["none"] = True
        if run and run.ran:
            tests["exit"] = run.code
            if not has_summary(out):
                tests["passed"] = tests["failed"] = None
        if run and run.env:                            # it tested nothing (spec 107 §1.1): why, and what install would make it run
            what = f"{run.env}\n{run.out}"
            python = gate_env.kind_of(what) == "python"
            tests["env"], tests["install"] = run.env, [] if python or run.timed_out else gate_env.missing(self.repo_root)      # npm ci never runs for pytest (spec 143 C.1)
            if python and not run.timed_out:
                tests["setup"] = gate_env.python_setup(self.repo_root)        # spec 143 C.2: the command for the person to run; nothing runs it
        if run and (run.red_before or run.flaky):          # spec 149 E: what was red but is not this task's is said, and not counted as its failures
            tests["red_before"], tests["flaky"] = list(run.red_before), list(run.flaky)
            if tests["green"]:
                tests["failed"], tests["failing"] = 0, []
        if run and run.left:
            tests["left"] = run.left                   # spec 149 C.3: the browser tests left for the way into main, "56 of pwa/"
        if run and run.docs:
            tests["docs"] = True
        if run and run.browser and tests["green"] and run.ran and (tests.get("skipped") or 0) > 0 and NO_BROWSER_SKIP.search(out):
            tests["no_browser"] = True                 # spec 143 B.3: a browser module skipped for want of a Chromium is not a pass; it does not hold the merge
        return tests

    def _gate_ran(self, slug: str, tid: str, path: Path, rnd: int, attempt: int) -> bool:
        """`gate_ran` for the try that just ran (spec 107 §1.2): True when the run could not test anything (`env`), which no session can mend.
        A try that ran no gate (no commit, an uncommitted file) writes nothing."""
        run = self._gate_runs.get(str(path))
        if run is None:
            return False
        named = re.search(r"`([^`]+)`", run.env)
        self._emit(event_log.GATE_RAN, idea=slug, task=tid, round=rnd, attempt=attempt, command=run.command, exit=run.code, seconds=run.seconds,
                   verdict=verdict({"env": run.env, "docs": run.docs, "ran": run.ran, "green": run.ok}), missing=named.group(1) if named else "",
                   red_before=list(run.red_before), flaky=list(run.flaky),
                   linked=dep_links.present(self.repo_root, path))
        return bool(run.env)

    def _regate(self, slug: str, tid: str, task: dict, path: Path, again: dict, cancel: threading.Event, env: dict) -> bool:
        """*Install and test again* / *Test again* (spec 107 §1.3), before the gate: with `install`, each folder `gate_env.missing` names is installed in
        the main checkout (its lines in the task's log under `== installing`); the worktree is linked again. True when the install failed: the task is at Review
        again, its `tests.env` *The install failed:* and the last line (the output is in the log)."""
        r = _r()
        self._log(slug, tid, f"== testing again · {r.now_iso()}\n", env)
        before = task.get("tests") or {}
        what = f"{before.get('env') or ''}\n{before.get('tail') or ''}".strip()       # what the run lacked: a Python tool is never installed by npm (spec 143 C.1)
        rows = lambda: [] if gate_env.kind_of(what) == "python" else gate_env.missing(self.repo_root)      # noqa: E731
        if again.get("install"):
            ok, out = gate_env.install(self.repo_root, rows(), cancel, log=lambda text: self._log(slug, tid, text, env))
            if not ok:
                last = next((ln.strip() for ln in reversed(out.splitlines()) if ln.strip()), "it said nothing")
                tests = {**(task.get("tests") or {}), "env": INSTALL_FAILED.format(last=last)[:300], "install": rows()}
                self._set_task(slug, tid, state="review", tests=tests, finished=r.now_iso(), look=COULD_NOT_RUN, error="the tests could not run")
                self._log(slug, tid, f"== at Review · {r.now_iso()}\n", env)
                return True
        dep_links.link(self.repo_root, path)
        return False

    def _sent_from(self, again: dict | None, path: Path) -> str:
        """The worktree's head before a send back's session (spec 107 §1.4), else "": what a conflict, a pick, the tests again or a variant taken are not."""
        if not again or not again.get("why") or again.get("files") or again.get("pick") or again.get("regate") or again.get("taken"):
            return ""
        return self.git.head(path)

    def _same(self, path: Path, head: str, task: dict, tests: dict) -> bool:
        """A send back that changed nothing and failed the same way (spec 107 §1.4): the worktree's head did not move, the tests are red, and their
        tail is the round before's (`task`'s tests, as they were before the session)."""
        return bool(head) and tests.get("green") is False and self.git.head(path) == head and same_tail(tests.get("tail"), (task.get("tests") or {}).get("tail"))

    def _note(self, slug: str, was: dict, tasks: list[dict]) -> None:
        """The event log's lines for the tasks whose state changed (spec 33 §9): `task_state`, and `result_ready` at Review."""
        now = time.time()
        for t in tasks:
            tid, new, old = t.get("id"), t.get("state"), was.get(t.get("id"))
            if new == old or old is None:
                continue
            since = self._since.get((slug, tid))
            self._since[(slug, tid)] = now
            check = ({"check": True, **({"clean": True} if new == "merged" and t.get("note") == "clean" else {})}
                     if is_check(t) else {})            # a check task's lines say so; a clean one is no result (spec 43 §1.3)
            self._emit(event_log.TASK_STATE, idea=slug, task=tid, state=new, was=old, round=int(t.get("round") or 1),
                       tier=t.get("tier") or "", role=t.get("role") or "", seconds=round(now - since, 1) if since else None, tokens=t.get("tokens"),
                       cost=t.get("cost"), ran_tier=t.get("ran_tier") or "", effort=t.get("effort") or "",
                       tool=t.get("tool") or "", model=t.get("model") or "", **check,
                       **({"ran_why": idea_target.ran_why(t.get("tier") or "", t.get("ran_tier") or "", *self._picks(t, slug))} if new == "running" else {}),
                       **({"error": str(t["error"])[:600]} if t.get("error") and new in ("failed", "review") else {}))     # (spec 107 §2.3)
            if new == "review":
                tests, diff = t.get("tests") or {}, t.get("diff") or {}
                self._emit(event_log.RESULT_READY, idea=slug, task=tid, round=int(t.get("round") or 1), passed=tests.get("passed"),
                           failed=tests.get("failed"), files=diff.get("files"), added=diff.get("added"),
                           removed=diff.get("removed"), cost=t.get("cost"), role=t.get("role") or "", exit=tests.get("exit"), verdict=verdict(tests))
            if new == "held" and self.on_held is not None:
                try:
                    self.on_held()
                except Exception:               # a log never stops the work
                    pass

    def _checker_of(self, task: dict) -> str:
        """The checker's slug of a check task: its role, else the library's checker of its tag."""
        role = str(task.get("role") or "")
        if role and idea_checks.is_checker(role):
            return role
        return idea_checks.checker_of_tag(str(task.get("kind") or ""))

    def _again_ask(self, task: dict, ask: bool = True) -> str:
        """What a check task is told besides a send back's line: the code findings left of the last round (the place's are not the
        code's to fix), and the ask for the file again (`ask`: False when the prompt before already holds it)."""
        rows = "".join(f"\n- {f.get('where')}: {f.get('what')}" for f in idea_checks.code_left(task.get("findings")))
        return (f"\n\nThe findings left from the last round:{rows}" if rows else "") + ("\n\n" + FINDINGS_ASK if ask else "")

    def _diff_so_far(self, path: Path, start_sha: str, base: str) -> str:
        """The task's work so far for a fresh session: `git diff` of the worktree against where it was cut, cut to DIFF_KEEP characters."""
        try:
            text = subprocess.run(["git", "diff", "--no-color", f"{start_sha or base}...HEAD"], cwd=path, capture_output=True, text=True,
                                  timeout=60).stdout
        except (OSError, subprocess.SubprocessError):
            text = ""
        cut = f" (cut to its first {DIFF_KEEP} characters)" if len(text) > DIFF_KEEP else ""
        return FRESH.format(base=base, cut=cut, diff=text[:DIFF_KEEP].rstrip() or "(nothing yet)")

    def _findings_round(self, path: Path, start_sha: str, title: str) -> tuple[list[dict] | None, bool]:
        """(the findings a check task wrote, whether it changed a file): its findings file is read (at most 64 KB) and removed before
        the commit, so it is never committed; `None` for a missing file, bad JSON or a bad shape. What it left is committed here."""
        target, text = path / idea_checks.FINDINGS_FILE, ""
        try:
            with target.open("rb") as f:
                raw = f.read(idea_checks.FINDINGS_BYTES + 1)
            text = raw.decode("utf-8") if len(raw) <= idea_checks.FINDINGS_BYTES else ""
        except (OSError, UnicodeDecodeError):
            pass
        try:
            target.unlink()
        except OSError:
            pass
        self.git.commit_left(path, title)
        return idea_checks.parse_findings(text), bool(self.git.commits(path, start_sha))

    def _check(self, path: Path, start_sha: str, cancel: threading.Event, title: str = "", slug: str = "", tid: str = "",
               env: dict | None = None) -> tuple[str | None, str]:
        """(None, the gate's run) when the task's work passes; else (what is wrong, in words the session can act on,
        the gate's run: "" when the gate did not run). What the session left uncommitted is committed first, under
        the task's title: its session may edit files but not run git. The Board's pages it touched are put back by code first."""
        self._gate_runs.pop(str(path), None)                 # the run of a try before is not this one's
        self.git.commit_left(path, title)
        into = self._landing(slug) if slug else str(_r().setting(self.settings, "merge_into") or "dev")
        board = [f for f in self.git.touched(path, into) if BOARD_PAGE.search(f)]
        if board:                          # spec 35 §13: the Board's pages are the Board's; put back by code, no session called, no try spent (spec 143 A.4)
            put = self.git.restore_pages(path, into, board)
            if put and slug:
                self._log(slug, tid, f"== the Board's pages put back: {', '.join(put)}\n", env)
                self._emit(event_log.TASK_PAGES_PUT_BACK, idea=slug, task=tid, files=put)
        if not self.git.changed(path, start_sha):
            return "You changed no file. Make the change the task asks for in this worktree.", ""
        if self.git.dirty(path):
            return ("You left uncommitted changes: `git status` shows them. Commit them (or remove what is not "
                    "work)."), ""
        run = self.git.gate_run(path, start_sha, cancel)
        problem = None if run.ok else f"The tests failed:\n{run.out[-3000:]}"
        out = run.out
        if not run.ok and run.ran and not run.env:             # spec 149 E: a red from before is not the task's
            clock = (gate_config.read(self.repo_root).timeout_min or 0) * 60 or jobs.TEST_TIMEOUT_S
            found = gate_rerun.sort_out(self.git, path, start_sha, into, run, cancel, clock - run.seconds)
            if found is not None:
                run = run._replace(ok=not found.left, red_before=found.red_before, flaky=found.flaky)
                out = "\n".join([run.out, *gate_rerun.words(found)])
                problem = None if run.ok else gate_rerun.told(found, run.out)
        self._gate_runs[str(path)] = run
        return problem, out

    def _env(self, slug: str, tid: str, plan: dict) -> dict[str, str]:
        """The task's environment: who runs (for the town's counts) and the values of its `secret` to-dos."""
        env = {"ORKCRAFT_ORC": f"ideas/{slug}-{tid}", "ORKCRAFT_IDEA": slug, "ORKCRAFT_TASK": tid}
        for todo in plan.get("todos") or []:
            if not isinstance(todo, dict) or todo.get("kind") != "secret" or tid not in (todo.get("for") or []):
                continue
            name = env_name(str(todo.get("title") or ""))
            value = read_secret(self.state_dir, slug, str(todo.get("id") or "")) if name else None
            if name and value:
                env[name] = value
        return {**env, **idea_secrets.file_env(self.state_dir, slug, plan, tid)}

    # -- the prompt ------------------------------------------------------------------------------

    def _prompt(self, slug: str, plan: dict, task: dict) -> str:
        """Stable first (spec 36 §6): the role's instruction and the finishing rules; then the task's own: where, its
        spec's path, the task, its `after` tasks, the secrets' names. No CLAUDE.md: Claude Code reads it itself."""
        spec, deps = spec_paths(self.repo_root, self.state_dir, slug)
        reading_of = spec                                                # the page as the Board's tree holds it, for what a task may read of it
        if spec and board_in_code.spec_in_worktree(self.repo_root, self.state_dir, slug):       # the Board is not in the code (spec 151 F.2): the spec is in the worktree's `.orkcraft/spec/`
            spec, deps = board_in_code.worktree_specs(self.repo_root, self.state_dir, slug)
        after = set(task.get("after") or [])
        done = [f"- {t.get('id')} · {t.get('title', '')} ({t.get('state')})"
                + (f" — merged: {'; '.join(t.get('subjects') or [])}" if t.get("state") == "merged" and t.get("subjects") else "")
                + f"\n  {t.get('brief', '')}" + (f"\n  {idea_pick.picked_words(t['picked'])}" if t.get("picked") else "")
                for t in plan.get("tasks") or [] if t.get("id") in after]
        env = self._env(slug, task.get("id"), plan)
        files = [n for n in env if n.startswith("ORKCRAFT_FILE_")]
        secrets = [n for n in env if n not in ("ORKCRAFT_ORC", "ORKCRAFT_IDEA", "ORKCRAFT_TASK", *files)]
        parts, role = [], self._role(task)
        if (instruction := str(role.get("instruction") or "").strip()):
            parts.append(f"# Your role: {role['name']}\n\n{instruction}")
        if agent_rules.has_rules(self.repo_root):                        # a project with the Board's rules in its AGENTS.md: they are not a task's own (spec 152 D.3)
            parts.append(NOT_THE_BOARDS)
        h = _r().harnesses.get(self.tool_of(slug, task))
        commits, browsers = getattr(h, "commits", True), getattr(h, "browsers", True)
        parts.append("# When you are done\n\n" + (
            "Commit your work with git if you can, with clear messages; what you leave changed is committed for you under the task's title."
            if commits else CANNOT_COMMIT) + f" {gate_words(gate_config.read(self.repo_root))}" + ("" if browsers else f"\n\n{NO_BROWSER_HERE}"))
        parts.append(task_steps.RULE)                                    # every tool's working prompt: its steps in a file (spec 129 H1.1)
        parts += [
            f"You do one task of the idea `{slug}` in this repository: a git worktree on branch "
            f"`idea/{slug}/{task.get('id')}`, cut from `{_r().setting(self.settings, 'merge_into') or 'main'}`. "
            "Work only here.",
            "# The idea\n\n" + (f"Its spec is at `{spec}` in this worktree: " + (self._reading(reading_of, task) or "read it if you need it.")
                                  + " That page is the Board's: read it, never write to it."
                                  + "".join(f" It depends on `{d}`." for d in deps) if spec else "(its spec was not found)"),
            f"# Your task: {task.get('title', '')}\n\n{task.get('brief', '')}",
        ]
        if sketch := task_brief.sketch_note(self.state_dir, slug):        # the sketch the person picked: a reference to follow (spec 121 §2.6)
            parts.insert(len(parts) - 1, sketch)
        if done:
            parts.append("# The tasks before yours\n\n" + "\n".join(done))
        if secrets:
            parts.append("The environment holds " + ", ".join(secrets) + ": use them from the environment, never "
                         "print them, write them to a file or commit them.")
        parts += self._without(plan, task)
        parts += [f"The file is at ${name}; copy it into the repository only if the task says so." for name in files]
        if is_check(task):
            parts.append(FINDINGS_ASK)
        elif is_pick(task):
            parts.append(pick_ask(task))
        if start := task_brief.start_at(task):                          # where its planner read, just before the spec's part (spec 153 B.3): the role and the rules stay the stable head (spec 36 §6)
            parts.insert(next((i for i, p in enumerate(parts) if p.startswith("# The idea")), len(parts)), start)
        return "\n\n".join(parts)

    def _reading(self, spec: str, task: dict) -> str:
        """What a task may read of its spec (spec 99 §9.3): for a page of the new format and a task planned for a party's section, the common part, that section whole and
        of the others only their contract (realm/task_brief.py); "" otherwise: the page is read as it was."""
        page = task_brief.page_of(self.repo_root, self.state_dir, spec) if task.get("section") else None
        return task_brief.note(page, str(task.get("section") or "")) if page is not None else ""

    @staticmethod
    def _without(plan: dict, task: dict) -> list[str]:
        """The lines for the to-dos this task is `for` that the person went without or described (spec 54 §1.2)."""
        out = []
        for todo in plan.get("todos") or []:
            if not isinstance(todo, dict) or task.get("id") not in (todo.get("for") or []) or not todo.get("done"):
                continue
            title = todo.get("title") or ""
            if todo.get("skipped"):
                out.append(f"The person left “{title}” to you: choose one of {', '.join(todo.get('choices') or [])}, and "
                           "say which and why in your result." if todo.get("kind") == "choice" else
                           f"The person went without “{title}”: do the task without it; if it cannot be done without it, "
                           "say what it blocks and stop.")
            elif todo.get("words") and todo.get("kind") == "file":
                out.append(f"Instead of the file “{title}”, the person described it: {todo.get('value') or ''}")
        return out

    def _again_prompt(self, slug: str, plan: dict, task: dict, again: dict, base: str, path: Path | None = None,
                      start_sha: str = "") -> tuple[str, str]:
        """(what a task is told, the session it resumes) when it goes on: a send back, the gate's conflict, a pick of none of them
        (spec 51 §2.3); a pick taken needs no turn, the gate runs on what was committed. The task's own prompt comes first when
        there is no session to resume. A send back of a task whose last call read more than FRESH_TOKENS (spec 86 §4) starts a fresh
        session: its prompt, the diff so far (`path` against `start_sha`) and the why."""
        resume = str(task.get("session") or "")
        if again.get("taken") or again.get("regate"):       # nothing is sent: the gate runs on what is there (a variant taken; the tests again, spec 107 §1.3)
            return "", resume
        fresh = bool(resume) and not again.get("pick") and int(task.get("last_tokens") or 0) > FRESH_TOKENS
        if fresh:
            resume = ""
        extra, tests = "", task.get("tests") or {}
        if again["files"]:
            extra += (f"Your branch conflicted with `{base}` in {', '.join(again['files'])}. The merge of "
                      f"`{base}` into your branch is open in this worktree: rebase onto {base} and resolve "
                      "it by editing those files until no conflict marker is left (keep what both sides "
                      "meant). Do not abort the merge.\n\n")
        if tests and not tests.get("green", not tests.get("failed")):
            extra += f"The tests were red:\n{tests.get('tail', '')}\n\n"
        if again.get("pick"):
            prompt = PICK_BACK.format(note=again["why"], n=(idea_pick.ask_of(task) or {}).get("n")) + "\n\n" + pick_ask(task)
        else:
            prompt = _r().BACK.format(why=again["why"], extra=extra)
            if is_check(task):
                prompt += self._again_ask(task, ask=bool(resume))          # with no session the task's prompt, first, holds the ask
        if not resume:
            lead = self._prompt(slug, plan, task) + "\n\n"
            if fresh and path is not None:
                lead += self._diff_so_far(path, start_sha, base)
            prompt = lead + prompt
        return prompt, resume
