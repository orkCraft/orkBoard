"""Jobs: one run of an AI tool for the Board's keeper and runner. A job runs off the UI thread; the caller
passes a `cancel` event and gets (text, cost, tokens) back or an exception.

    claude   `claude -p`; read-only in the repository unless `workdir` is given (a worktree)
    agy      `agy --print` in a sandbox limited to `workdir` (a scratch dir when none is given)
    codex    `codex exec` in a read-only sandbox; may write only inside `workdir` when one is given

`run_work` changes files in a worktree, `run_read` reads. `ensure_repo` makes a folder a git repository with a first commit,
so agents can work in worktrees of it.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable

from orkboard.realm import call_log, halt, harnesses, task_commands, tool_errors, tool_run  # noqa: F401  (halt: its runs wait under it, tool_run.wait)
from orkboard.sources import telemetry

WORK_TIMEOUT_S = 1800


_wait = tool_run.wait               # the Board's gate and the town's jobs wait the same way (realm/tool_run.py)


# What the person can do when a working run ended with no answer because a command was refused (an unchained building is
# not a setting a task's run reads yet, so the step is the other tool).
EMPTY_WORK_STEP = "Pick another AI tool for this party."


def work_cmd(harness: str, prompt: str, workdir: Path, model: str = "", resume: str = "",
             dirs: tuple = (), free: bool = False, effort: str = "", task: dict | None = None,
             root: Path | None = None) -> list[str]:
    """An agent that may change files — only inside `workdir` (a Barracks worktree); `dirs` it may read too;
    `free`: it asks nothing (the tool's `free_args`). A tool that takes a list of commands (Claude
    Code in `-p`, where nobody can be asked) gets the project's at `root` (default: `workdir`, a checkout of it) and
    the task's (`task["pick"]`: also the media tools), spec 86 §2."""
    h = harnesses.get(tool_run.resolve(harness))
    if h is None:
        raise RuntimeError(f"harness {harness!r} cannot work in a worktree")
    allow, deny = (task_commands.allowed(root or workdir, task), task_commands.denied()) if h.work_rules else ((), ())
    return h.work(prompt, workdir, model, resume if h.resumable else "", dirs, free, effort, allow, deny)


def run_work(harness: str, prompt: str, workdir: Path, cancel: threading.Event, model: str = "",
             env: dict | None = None, resume: str = "",
             timeout_s: int = WORK_TIMEOUT_S, dirs: tuple = (),
             free: bool = False, effort: str = "", task: dict | None = None, root: Path | None = None,
             before_cost: float | None = None, on_output: Callable[[str], None] | None = None) -> tuple[str, float | None, int | None, str]:
    """(text, cost, tokens, session) of an agent working in `workdir` (and reading `dirs` too); `effort`: the model's
    reasoning, where the tool takes one (spec 35 §1); `task`, `root`: whose commands it may run (see `work_cmd`). `cost` is the tool's
    figure; for a resumed Claude session that is the session's running total, so `before_cost` (the total after its last call) makes the
    call's own cost, the one logged as `cost_own` and charged. `on_output` is handed the tool's stdout as it is written (a
    task's steps are read along the way, realm/task_steps_run.py)."""
    harness = tool_run.resolve(harness)
    cmd = work_cmd(harness, prompt, workdir, model, resume, dirs, free, effort, task, root)
    h = harnesses.get(harness)
    tool_env = h.env("work", workdir) if h else {}
    run_env = {**os.environ, **tool_env, **(env or {})}
    resumed = tool_run.codex_thread_usage(resume, run_env) if harness == "codex" and resume else None
    before = resumed or 0
    start = time.monotonic()
    code, out, err = tool_run.run_proc(
        cmd, workdir, run_env, tool_run.harness_stdin(harness, prompt),
        lambda proc: _wait(proc, cancel, timeout_s, run_env.get("ORKCRAFT_ORC") or harness, True), harness, **({"on_output": on_output} if on_output is not None else {}))
    if code != 0:
        call_log.record(env, "work", harness, model, prompt, out, err, code, time.monotonic() - start, workdir=workdir)
        raise tool_run.failure(harness, code, out, err)
    text, cost, tokens, session = tool_run.result_of(harness, out, before, model)
    if harness == "codex" and resume and resumed is None:
        cost = None                       # its running total holds earlier runs we cannot tell apart
    own = tool_run.cost_once(cost, before_cost) if harness == "claude" and resume and before_cost is not None else None
    call_log.record(env, "work", harness, model, prompt, out, err, code, time.monotonic() - start, cost, tokens,
                    session, workdir, cost_own=own)
    what = dict(tokens=tokens, building=telemetry.building_of(run_env), model=model)
    paid = cost if own is None else own
    if not telemetry.charged(run_env):
        telemetry.charge(paid, f"{harness} worker", **what)
    else:
        telemetry.noted(paid, f"{harness} worker", **what)
    if h is not None and not text.strip() and (why := h.error(out)):    # it ended well with no answer, and says why (agy's refused command)
        # agy's words are a clause ("it wanted to run RunCommand, …"): they say whose, and what the person can do
        raise tool_errors.ToolError(harness, f"{h.title} {why.removeprefix('it ')}. {EMPTY_WORK_STEP}" if why.startswith("it ") else why)
    return text, cost, tokens, session


class BudgetSpent(RuntimeError):
    """A read that ended on its `--max-budget-usd` cap with no answer to use."""


LAST = threading.local()          # the last read on this thread: `usage` ({"in", "out", "cache_read"}), `capped`


def last_usage() -> dict | None:
    return getattr(LAST, "usage", None)


def run_read(harness: str, prompt: str, workdir: Path, cancel: threading.Event, model: str = "",
             env: dict | None = None, resume: str = "",
             timeout_s: int = WORK_TIMEOUT_S, effort: str = "", budget: float | None = None, one_shot: bool = False,
             tools: bool = True) -> tuple[str, float | None, int | None, str]:
    """(text, cost, tokens, session) of an agent that only reads, in `workdir` (harness mode `read`: no terminal, no
    file edits) — an Agent pool's reply (docs/design/barracks-flows.md §7). It starts fresh unless `resume` names a
    session of a tool that can reopen one (the board's keeper: one session per idea, spec 29a §4); `session` is
    the one it ran in, "" when the tool does not say."""
    harness = tool_run.resolve(harness)
    h = harnesses.get(harness)
    if h is None:
        raise RuntimeError(f"harness {harness!r} cannot read")
    cmd = h.read(prompt, workdir, model, False, effort, budget, one_shot, tools)
    if resume and h.read_session:
        cmd = cmd + h.read_session(resume, True)
    run_env = {**os.environ, **h.env("read", workdir), **(env or {})}
    start = time.monotonic()
    code, out, err = tool_run.run_proc(
        cmd, workdir, run_env, tool_run.harness_stdin(harness, prompt),
        lambda proc: _wait(proc, cancel, timeout_s, run_env.get("ORKCRAFT_ORC") or harness, True), harness)
    LAST.usage = harnesses.usage_split(out) if harness == "claude" else None
    LAST.capped = budget is not None and harnesses.capped(out, err)
    if code != 0:
        call_log.record(env, "read", harness, model, prompt, out, err, code, time.monotonic() - start, workdir=workdir)
        if LAST.capped:                   # ended on its budget: its answer is used if it has one (spec 35 §0)
            text, cost, tokens, session = tool_run.result_of(harness, out, 0, model)
            if text.strip() and text.strip() != out.strip():
                return text, cost, tokens, session
            raise BudgetSpent("the keeper ran out of its budget for this step")
        raise tool_run.failure(harness, code, out, err)
    text, cost, tokens, session = tool_run.result_of(harness, out, 0, model)
    call_log.record(env, "read", harness, model, prompt, out, err, code, time.monotonic() - start, cost, tokens,
                    session, workdir)
    what = dict(tokens=tokens, building=telemetry.building_of(run_env), model=model)
    if not telemetry.charged(run_env):
        telemetry.charge(cost, f"{harness} reader", **what)
    else:
        telemetry.noted(cost, f"{harness} reader", **what)
    if not text.strip() and (why := h.error(out)):        # it ended well with no answer, and says why (agy's refused command)
        raise tool_errors.ToolError(harness, why)
    return text, cost, tokens, session


# -- git: a folder made a repository the agents can work in -------------------------------------------

GIT_TIMEOUT_S = 60
TEST_TIMEOUT_S = 900


def _git(cwd: Path, *args: str, timeout: int = GIT_TIMEOUT_S) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)


def _ok(proc: subprocess.CompletedProcess) -> str:
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip()[:300] or f"git failed ({proc.returncode})")
    return proc.stdout.strip()


# A folder with no git yet: what its first commit leaves out when it has no .gitignore of its own — secrets, the
# town's own state, what a build or an install makes again.
FIRST_IGNORE = """# written by Orkline when it started git here: what the first commit left out
.env
.env.*
*.pem
*.key
.orkcraft/
node_modules/
.venv/
venv/
__pycache__/
dist/
build/
.DS_Store
"""
FIRST_AUTHOR = ("-c", "user.name=Orkcraft", "-c", "user.email=orkcraft@localhost")   # when git knows nobody here


def ensure_repo(repo_root: Path) -> str:
    """The folder the agents work in is a git repository with a first commit, so worktrees can be made of it: "" when
    it already was, else what was done, in a sentence (git init; a .gitignore when there was none; the files as they
    are in a first commit, secrets and caches left out). Raises RuntimeError when git cannot (not installed)."""
    try:
        inside = _git(repo_root, "rev-parse", "--is-inside-work-tree")
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f"git is not installed or did not answer: {e}") from e
    done = []
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        if _git(repo_root, "init", "-b", "main").returncode != 0:              # the most used name for the first branch (decisions §254.8); git before 2.28 has no -b
            _ok(_git(repo_root, "init"))
            _ok(_git(repo_root, "symbolic-ref", "HEAD", "refs/heads/main"))
        done.append("started git here")
    if _git(repo_root, "rev-parse", "--verify", "HEAD").returncode != 0:      # no commit yet: a worktree needs one
        ignore = repo_root / ".gitignore"
        if not ignore.exists():
            ignore.write_text(FIRST_IGNORE, encoding="utf-8")
            done.append("wrote a .gitignore (.env, keys, caches and .orkcraft/ left out)")
        _ok(_git(repo_root, "add", "-A"))
        who = () if _git(repo_root, "config", "user.email").stdout.strip() else FIRST_AUTHOR
        _ok(_git(repo_root, *who, "commit", "--allow-empty", "-m", "Orkline: the first commit, so agents can work in worktrees"))
        done.append("made a first commit of the files as they are")
    return "; ".join(done)
