"""`orkboard steps-check --tool claude|codex|agy [--yes]` (docs/specs/129-a-tasks-steps.md H1.6, decisions §207.3): one small real task
in a scratch git repository, run as a working task of that tool (its real argv, the real rule of the working prompt), and what
the look at its steps saw: each update with where it came from and when. `ok` when at least two updates came from the worker's
file or the tool's own list and the last of those had every step done. It spends a little of the tool's limit, so it says so
and asks first. Nothing else in Orkboard depends on it, and no test runs a real tool.

    code = run("codex", yes=True)       # 0 ok · 1 the tool ran but did not show its steps · 2 not installed, not signed in, or declined
"""
from __future__ import annotations

import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable

from orkboard.realm import call_log, harnesses, jobs, task_steps, task_steps_run, tool_errors
from orkboard.realm.idea_git import IdeaGit

TOOLS = ("claude", "codex", "agy")
TASK = ("Add a function `double(x)` to `calc.py` that returns x twice, and a test for it in `test_calc.py`. "
        "Write the two files, run nothing, then stop.")
RUN_TIMEOUT_S = 600
WHERE = {"file": "the steps file", "todo": "the tool's own list", "activity": "what it is doing"}


def _git(cwd: Path, *args: str) -> None:
    jobs._ok(jobs._git(cwd, "-c", "user.name=Orkboard", "-c", "user.email=orkboard@localhost", *args))


def scratch(folder: Path) -> Path:
    """A git repository with a tiny project in it and one commit, on `main`; the folder."""
    folder.mkdir(parents=True, exist_ok=True)
    _git(folder, "init", "-q", "-b", "main")
    (folder / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (folder / "test_calc.py").write_text("from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")
    _git(folder, "add", "-A")
    _git(folder, "commit", "-q", "-m", "a tiny project")
    return folder


def line(at: float, steps: dict) -> str:
    """One update, as it is printed: when, from where, and the steps (done of all, the one now) or what it is doing."""
    count = f"{steps['done']}/{steps['total']}" if steps["total"] else "-"
    now = steps["items"][steps["now"]]["text"] if 0 <= steps["now"] < len(steps["items"]) else ""
    return f"  +{at:5.1f}s  {steps['source']:<8} {count:>5}  {now or steps['doing']}"


def verdict(seen: list[tuple[float, dict]]) -> tuple[bool, str]:
    """(ok, why): at least two updates from the file or the tool's list, the last of them all done."""
    listed = [s for _t, s in seen if s["source"] != "activity"]
    from_ = {k: sum(1 for s in listed if s["source"] == k) for k in ("file", "todo")}
    said = f"{len(seen)} updates seen ({from_['file']} from {WHERE['file']}, {from_['todo']} from {WHERE['todo']}, {len(seen) - len(listed)} from {WHERE['activity']})"
    if len(listed) < 2:
        return False, f"{said}: fewer than two came from a list, so the person would see no steps move"
    last = listed[-1]
    if not last["total"] or last["done"] != last["total"]:
        return False, f"{said}: the last list had {last['done']} of {last['total']} steps done, not all"
    return True, said


def run(tool: str, yes: bool = False, out: Callable[[str], None] = print, ask: Callable[[str], str] = input,
        work: Callable[..., tuple] = jobs.run_work, every: float = 1.0) -> int:
    """The check; the exit code. `work` stands in for `jobs.run_work` where a test must not run a real tool."""
    h = harnesses.get(tool)
    if h is None or tool not in TOOLS:
        out(f"steps-check: no tool {tool!r}; one of {', '.join(TOOLS)}")
        return 2
    if not shutil.which(h.bin) and work is jobs.run_work:
        out(f"{h.title} is not installed here ({h.bin} is not on the PATH). Install it: {h.install}")
        return 2
    out(f"This runs one small real task on {h.title} in a scratch folder and spends a little of its limit.")
    if not yes and ask("Go on? [y/N] ").strip().lower() not in ("y", "yes"):
        out("not run")
        return 2
    started, seen = time.monotonic(), []
    with tempfile.TemporaryDirectory(prefix="orkboard-steps-") as tmp:
        repo = scratch(Path(tmp) / "repo")
        path, _branch = IdeaGit(repo).prepare("steps", "t1", "main")           # the task's worktree: its steps file already left out of git
        watch = task_steps_run.Watch(tool, path, Path(tmp) / "t1.steps.json", every=every,
                                     on_change=lambda steps: (seen.append((time.monotonic() - started, steps)), out(line(seen[-1][0], steps))))
        prompt = f"{task_steps.RULE}\n\n# Your task\n\n{TASK}"
        argv = [a for a in jobs.work_cmd(tool, prompt, path, root=repo, task={"id": "t1"}) if a != prompt]       # the real argv, the prompt left out
        shown = argv[:argv.index("--allowedTools")] if "--allowedTools" in argv else argv       # up to the long list of commands
        out(f"running {h.title}: {' '.join(shown[:14])} …\nupdates:")
        watch.start()
        try:
            with call_log.of_project(repo):
                work(tool, prompt, path, threading.Event(), env={}, timeout_s=RUN_TIMEOUT_S, task={"id": "t1"}, root=repo,
                     on_output=watch.feed)
        except tool_errors.ToolError as e:
            watch.stop()
            out(f"{h.title} could not run the task: {tool_errors.plainly(e)}")
            return 2
        except Exception as e:
            watch.stop()
            out(f"{h.title} could not run the task: {' '.join(str(e).split())[:300]}")
            return 2
        watch.stop()
    ok, why = verdict(seen)
    out("ok" if ok else f"not ok: {why}")
    if ok:
        out(why)
    return 0 if ok else 1
