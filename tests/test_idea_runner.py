"""The idea runner (docs/specs/29a-board-focus.md §5): a temp repository with a bare origin, a stub `claude` on PATH."""
from __future__ import annotations

import datetime as dt
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from orkboard.core import idea_runner
from orkboard.core.idea_runner import IdeaRunner

# What the stub does is chosen per task: STUB_MODE="k1=edit,k2=fail_once". Its calls go to STUB_LOG.
STUB = r'''#!{python}
import json, os, subprocess, sys, time
argv = sys.argv[1:]
resume = "--resume" in argv
branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
tid = branch.rsplit("/", 1)[-1]
modes = dict(p.split("=", 1) for p in os.environ.get("STUB_MODE", "").split(",") if "=" in p)
mode = modes.get(tid, modes.get("*", "edit"))
start = time.time()

def git(*a):
    subprocess.run(["git", *a], check=True, capture_output=True)

def commit(path, text, msg):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w").write(text)
    git("add", "-A")
    git("-c", "user.name=Stub", "-c", "user.email=stub@x", "commit", "-m", msg)

if mode == "limit":
    print("Claude AI usage limit reached", file=sys.stderr)
    sys.exit(1)
if mode == "slow":
    time.sleep(30)
if mode == "env":
    commit(f"{tid}.txt", os.environ.get("API_KEY", "none"), f"{tid}: key")
elif mode == "docs":                                # changes only a document (spec 107 §1.2)
    commit(f"{tid}.md", "# notes\n", f"{tid}: notes")
elif mode in ("fail_once", "fail_always", "fail_moving"):
    if not resume:
        commit("pkg/thing.py", "VALUE = 1\n", f"{tid}: thing")
        commit("tests/test_thing.py", "from pkg.thing import VALUE\n\ndef test_value():\n    assert VALUE == 2\n",
               f"{tid}: its test")
    elif mode == "fail_once":
        commit("pkg/thing.py", "VALUE = 2\n", f"{tid}: fix the value")
    elif mode == "fail_moving":                     # changes the code each time, and the test still fails (another value each time)
        commit("pkg/thing.py", f"VALUE = {time.time_ns()}\n", f"{tid}: another value")
elif mode == "conflict":
    commit("shared.txt", "the task's line\n", f"{tid}: shared")
    root = os.environ["STUB_ROOT"]
    open(os.path.join(root, "shared.txt"), "w").write("main's line\n")
    subprocess.run(["git", "-C", root, "-c", "user.name=O", "-c", "user.email=o@x", "commit", "-am", "main moved"],
                   check=True, capture_output=True)
elif mode == "fix_conflict":                        # the conflict of a send back is resolved by editing, no git
    if resume:
        open(f"{tid}.txt", "w").write("resolved\n")
    else:
        commit(f"{tid}.txt", f"done by {tid}\n", f"{tid}: add {tid}.txt")
elif mode.startswith("check_"):                      # a check task (spec 43): what it found goes to its findings file
    def findings(items):
        open(".orkcraft-findings.json", "w").write(json.dumps({"findings": items}))
    left = {"where": "a.py:1", "what": "a bug", "fixed": False}
    fixed = {"where": "b.py:2", "what": "another bug", "fixed": True}
    if mode == "check_clean" or (mode == "check_late" and resume):
        findings([])
    elif mode == "check_left":
        findings([left, left])
    elif mode == "check_env":                          # what is left is the place's: a command was refused
        findings([{"where": "npm test", "what": "the command was refused", "fixed": False, "kind": "env"}])
    elif mode == "check_mixed_kinds":
        findings([left, {"where": "npm test", "what": "the command was refused", "fixed": False, "kind": "env"}])
    elif mode in ("check_fixed", "check_mixed"):
        commit(f"{tid}.txt", f"fixed by {tid}\n", f"{tid}: fix")
        findings([fixed] if mode == "check_fixed" else [fixed, left])
    elif mode == "check_bad":
        open(".orkcraft-findings.json", "w").write("not json")
    elif mode == "check_claims":                      # says it fixed one, and changed no file
        findings([fixed])
elif mode == "rewrite":                             # writes its file anew each call, resumed or not
    seen = sum(1 for ln in open(os.environ["STUB_LOG"]) if json.loads(ln)["tid"] == tid) if os.path.exists(os.environ["STUB_LOG"]) else 0
    commit(f"{tid}.txt", f"done by {tid} {seen}\n", f"{tid}: write {tid}.txt {seen}")
elif mode == "risk":                                # touches a path the risk rules read: sign-in
    commit("auth/login.py", "X = 1\n", f"{tid}: login")
elif mode == "pictures":                            # holds a picture
    commit("art/logo.png", "not really a picture\n", f"{tid}: logo")
elif mode == "nocommit":
    pass
elif mode == "uncommitted":                         # edits a file, runs no git (acceptEdits allows no Bash)
    open(f"{tid}.txt", "w").write(f"done by {tid}\n")
else:
    time.sleep(float(os.environ.get("STUB_SLEEP", "0")))
    commit(f"{tid}.txt", f"done by {tid}\n", f"{tid}: add {tid}.txt")
prior = [json.loads(ln) for ln in open(os.environ["STUB_LOG"]).read().splitlines()] if os.path.exists(os.environ["STUB_LOG"]) else []
since = 0                                           # this session's calls so far: a fresh session starts its total again
for row in prior:
    if row["tid"] == tid:
        since = since + 1 if row["resume"] else 1
with open(os.environ["STUB_LOG"], "a") as f:
    f.write(json.dumps({"tid": tid, "resume": resume, "start": start, "end": time.time(), "argv": argv}) + "\n")
# a resumed session reports its running total, as Claude does: 0.01 a call, so 0.01, 0.02, 0.03
big = tid in os.environ.get("STUB_BIG", "").split(",")
print(json.dumps({"result": "done", "session_id": f"s-{tid}", "total_cost_usd": round(0.01 * ((since + 1) if resume else 1), 4),
                  "usage": {"input_tokens": 200000 if big else 10, "output_tokens": 5}}))
'''


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def town(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    origin = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(origin)], check=True, capture_output=True)
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "t@x")
    git(repo, "config", "user.name", "T")
    (repo / ".gitignore").write_text(".orkcraft/\n__pycache__/\n.pytest_cache/\n")
    (repo / "CLAUDE.md").write_text("# Rules\n\n- write ork, never orc\n")
    (repo / "shared.txt").write_text("first\n")
    (repo / "tests").mkdir()
    for name in ("test_architecture.py", "test_cli.py", "test_updates.py"):
        (repo / "tests" / name).write_text("def test_ok():\n    assert True\n")
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("")
    (repo / "conftest.py").write_text("")
    # The project's own gate, written down: its stub tasks write `.txt` files, and a task that changed only documents runs no derived gate (spec 107 §1.2).
    (repo / "orkcraft.toml").write_text('[gate]\nalways = ["tests/test_architecture.py", "tests/test_cli.py", "tests/test_updates.py"]\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "start")
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "origin", "main")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    stub = bindir / "claude"
    stub.write_text(STUB.replace("{python}", sys.executable))
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    log = tmp_path / "stub.jsonl"
    monkeypatch.setenv("STUB_LOG", str(log))
    monkeypatch.setenv("STUB_ROOT", str(repo))
    state = repo / ".orkcraft"
    page = repo / "llm-wiki" / "general" / "pages" / "ideas" / "demo.md"
    page.parent.mkdir(parents=True)
    page.write_text("---\nowner: board\n---\n# Demo\n\n## Gist\nA demo idea.\n")
    return SimpleNamespace(repo=repo, origin=origin, state=state, log=log)


def plan_of(town, tasks: list[dict], todos: list[dict] | None = None, slug: str = "demo") -> None:
    d = town.state / "ideas" / slug
    d.mkdir(parents=True, exist_ok=True)
    full = [{"id": t["id"], "title": t.get("title", t["id"]), "brief": t.get("brief", "do " + t["id"]),
             "tier": t.get("tier", "laborer"), "kind": t.get("kind", "code"), "after": t.get("after", []), "state": "waiting", "branch": "",
             "commit": "", "session": "", "cost": None, "tokens": None, "started": "", "finished": "", "error": "",
             "note": ""} for t in tasks]
    (d / "plan.json").write_text(json.dumps({"idea": slug, "made_at": "x", "passed_at": "y", "todos": todos or [],
                                             "tasks": full}))
    (d / "state.json").write_text(json.dumps({"state": "plan"}))


def runner_of(town, limits=None, goal_branches=True, **ideas) -> tuple[IdeaRunner, list]:
    events = []
    bus = SimpleNamespace(publish=lambda topic, **data: events.append((topic, data)))
    settings = SimpleNamespace(ideas={"max_parallel": 1, "merge_into": "main", "push": True, "review": False, **ideas})
    return IdeaRunner(town.repo, town.state, settings, bus, limits=limits or (lambda: []), goal_branches=goal_branches), events


def wait_idle(runner: IdeaRunner, slug: str = "demo", timeout: float = 90) -> dict:
    end = time.time() + timeout
    while time.time() < end:
        runner.tick()
        state = json.loads((runner.state_dir / "ideas" / slug / "state.json").read_text())
        if not runner.busy() and state["state"] in ("done", "failed"):
            return state
        time.sleep(0.1)
    raise AssertionError("the runner did not finish")


def tasks_of(town, slug: str = "demo") -> dict:
    plan = json.loads((town.state / "ideas" / slug / "plan.json").read_text())
    return {t["id"]: t for t in plan["tasks"]}


def calls(town) -> list[dict]:
    return [json.loads(ln) for ln in town.log.read_text().splitlines()] if town.log.exists() else []


def test_tasks_run_in_order_of_after_and_land_on_main_and_origin(town):
    plan_of(town, [{"id": "k2", "after": ["k1"]}, {"id": "k1"}, {"id": "k3", "after": ["k2"]}])
    runner, events = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    assert [c["tid"] for c in calls(town)] == ["k1", "k2", "k3"]
    tasks = tasks_of(town)
    assert all(t["state"] == "merged" for t in tasks.values())
    assert tasks["k3"]["commit"] == git(town.repo, "rev-parse", "main")
    assert tasks["k1"]["branch"] == "idea/demo/k1" and tasks["k1"]["session"] == "s-k1"
    assert tasks["k1"]["cost"] == pytest.approx(0.01)
    assert git(town.origin, "rev-parse", "main") == git(town.repo, "rev-parse", "main")
    assert (town.repo / "k3.txt").read_text() == "done by k3\n"      # main is checked out: its files moved too
    assert ("ideas.changed", {"slug": "demo"}) in events
    assert not list((town.repo / ".orkcraft" / "worktrees").glob("*"))   # the worktrees went


def test_a_red_gate_gets_one_more_turn_on_the_same_session(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fail_once")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    assert [c["resume"] for c in calls(town)] == [False, True]
    assert "VALUE = 2" in git(town.repo, "show", "main:pkg/thing.py")


def test_a_gate_still_red_waits_for_the_look_and_main_stays(town, monkeypatch):
    """Spec 84 §1: tests that ran and are red are not a result that holds: it waits for the person, whatever `review` says."""
    monkeypatch.setenv("STUB_MODE", "k1=fail_always")
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    before = git(town.repo, "rev-parse", "main")
    runner, _ = runner_of(town)
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["look"] == "the tests are red" and task["tests"]["green"] is False
    assert tasks_of(town)["k2"]["state"] == "waiting"             # never started from a result that waits
    assert len(calls(town)) == 2
    assert git(town.repo, "rev-parse", "main") == before == git(town.origin, "rev-parse", "main")


def test_what_the_session_left_uncommitted_is_committed_under_the_tasks_title_and_lands(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=uncommitted")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    assert tasks_of(town)["k1"]["state"] == "merged"
    assert git(town.origin, "log", "-1", "--format=%an", "main") == "Orkboard"
    assert git(town.origin, "show", "main:k1.txt") == "done by k1"


def test_a_rebase_conflict_fails_and_main_keeps_its_own_line(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=conflict")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    state = wait_idle(runner)
    # docs/specs/168 F1: the task lands on the goal's own branch, which main's change does not touch; the conflict is met one level up, when the goal
    # goes into main: it stops there without forcing, says so on the goal, and main keeps its own line.
    assert state["state"] == "done" and tasks_of(town)["k1"]["state"] == "merged"
    why = json.loads((town.state / "ideas" / "demo" / "goal_branch.json").read_text())["blocked"]
    assert "conflict" in why and "shared.txt" in why
    assert git(town.repo, "show", "main:shared.txt") == "main's line"
    assert git(town.repo, "log", "-1", "--format=%s", "main") == "main moved"
    assert git(town.repo, "show", "goal/demo:shared.txt") == "the task's line"


def test_tasks_land_on_the_goals_branch_and_the_goal_goes_into_main_by_itself_once(town):
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    tasks = tasks_of(town)
    assert tasks["k1"]["branch"] == "idea/demo/k1" and all(t["state"] == "merged" for t in tasks.values())
    assert tasks["k2"]["commit"] == git(town.repo, "rev-parse", "main")      # main was moved to the goal's tip, by fast-forward
    assert (town.repo / "k1.txt").exists() and (town.repo / "k2.txt").exists()
    assert not git(town.repo, "branch", "--list", "goal/demo")              # in main: the branch is gone
    assert git(town.origin, "rev-parse", "main") == git(town.repo, "rev-parse", "main")
    assert json.loads((town.state / "ideas" / "demo" / "goal_branch.json").read_text())["merged"] == git(town.repo, "rev-parse", "main")


def test_with_review_on_the_goal_waits_on_its_branch_for_main_and_the_person_sends_it(town):
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    runner, events = runner_of(town, review=True)
    main = git(town.repo, "rev-parse", "main")
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    assert all(t["state"] == "merged" for t in tasks_of(town).values())      # a task is not asked about: the look is the goal's, one level up
    assert git(town.repo, "rev-parse", "main") == main and not (town.repo / "k1.txt").exists()
    assert git(town.repo, "show", "goal/demo:k2.txt") == "done by k2"
    from orkboard.realm import goal_branch
    assert goal_branch.row(town.state, "demo", True)["waits_for_dev"] is True
    got = runner.goal_to_dev("demo")
    assert got["commit"] == git(town.repo, "rev-parse", "main") and (town.repo / "k2.txt").exists()
    assert goal_branch.row(town.state, "demo") == {}
    with pytest.raises(idea_runner.RunnerError, match="no branch waiting"):
        runner.goal_to_dev("demo")


def test_a_goal_already_at_work_in_main_lands_there_as_before(town):
    plan_of(town, [{"id": "k0"}, {"id": "k1", "after": ["k0"]}])
    plan = json.loads((town.state / "ideas" / "demo" / "plan.json").read_text())
    plan["tasks"][0].update(state="merged", commit="abc123", subjects=["k0: before"])        # a task of it landed in main before goals had branches
    (town.state / "ideas" / "demo" / "plan.json").write_text(json.dumps(plan))
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    tasks = tasks_of(town)
    assert tasks["k1"]["state"] == "merged" and tasks["k1"]["commit"] == git(town.repo, "rev-parse", "main")      # landed in main by itself, on no branch
    assert not (town.state / "ideas" / "demo" / "goal_branch.json").exists() and not git(town.repo, "branch", "--list", "goal/demo")
    assert git(town.repo, "show", "main:k1.txt") == "done by k1"


def test_a_nearly_spent_window_holds_the_task_until_its_reset(town):
    reset = dt.datetime.now() + dt.timedelta(hours=2)
    limits = [SimpleNamespace(provider="claude", remaining=0.03, reset=reset)]
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town, limits=lambda: limits)
    runner.start("demo")
    runner.tick()
    task = tasks_of(town)["k1"]
    assert task["state"] == "held" and task["note"] == f"after {reset:%H:%M}"
    assert calls(town) == []
    limits.clear()                                  # the window came back …
    runner._until[("demo", "k1")] = time.time() - 1
    assert wait_idle(runner)["state"] == "done"     # … and it runs


def test_stop_ends_the_running_task_and_the_idea_needs_you(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=slow")
    plan_of(town, [{"id": "k1"}])
    before = git(town.repo, "rev-parse", "main")
    runner, _ = runner_of(town)
    runner.start("demo")
    end = time.time() + 10
    while time.time() < end and not runner.busy():
        time.sleep(0.05)
    time.sleep(0.5)
    runner.stop("demo")
    state = wait_idle(runner, timeout=20)
    assert state["state"] == "failed" and "stopped" in state["error"]
    assert tasks_of(town)["k1"]["state"] == "failed" and "stopped" in tasks_of(town)["k1"]["error"]
    assert git(town.repo, "rev-parse", "main") == before


def test_a_secret_todo_reaches_the_session_only_by_its_environment(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=env")
    (town.state).mkdir(parents=True, exist_ok=True)
    (town.state / "secrets.json").write_text(json.dumps({"ideas/demo/t1": "s3cret"}))
    todos = [{"id": "t1", "title": "Add API_KEY", "kind": "secret", "why": "", "choices": [], "steps": [],
              "for": ["k1"], "done": False, "value": None}]
    plan_of(town, [{"id": "k1"}], todos)
    runner, _ = runner_of(town)
    runner.start("demo")
    runner.tick()
    assert tasks_of(town)["k1"]["state"] == "waiting"       # its to-do is not done
    plan = json.loads((town.state / "ideas" / "demo" / "plan.json").read_text())
    plan["todos"][0].update(done=True, value="stored")
    (town.state / "ideas" / "demo" / "plan.json").write_text(json.dumps(plan))
    assert wait_idle(runner)["state"] == "done"
    assert git(town.repo, "show", "main:k1.txt") == "s3cret"
    prompt = runner._prompt("demo", runner.plan("demo"), runner.plan("demo")["tasks"][0])
    assert "s3cret" not in prompt and "API_KEY" in prompt


# -- spec 33: Review ---------------------------------------------------------------------------------

from orkboard.core.idea_runner import RunnerError


def reviewing(town, **ideas):
    """The Review mechanics of a goal that lands in dev task by task: a goal at work before goals had branches (docs/specs/168 F1), so no goal is given one here."""
    return runner_of(town, goal_branches=False, review=True, merge_into="dev", push=False, **ideas)


def wait_task(runner: IdeaRunner, tid: str, state: str, slug: str = "demo", timeout: float = 90) -> dict:
    end = time.time() + timeout
    while time.time() < end:
        runner.tick()
        task = next(t for t in runner.plan(slug)["tasks"] if t["id"] == tid)
        if task["state"] == state and (slug, tid) not in runner._runs:
            return task
        time.sleep(0.1)
    raise AssertionError(f"{tid} did not reach {state}: {runner.plan(slug)['tasks']}")


def test_green_tests_wait_at_review_and_nothing_is_merged(town):
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    runner, _ = reviewing(town)
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["tests"]["green"] is True and task["tests"]["failed"] == 0 and task["tests"]["passed"] >= 3
    assert task["diff"] == {"files": 1, "added": 1, "removed": 0} and task["round"] == 1 and task["conflict"] == ""
    assert git(town.repo, "branch", "--list", "dev") and git(town.repo, "rev-parse", "dev") == git(town.repo, "rev-parse", "main")
    assert (town.state / "ideas" / "demo" / "k1.log").exists() and "done" in runner.log("demo", "k1")
    time.sleep(0.5)
    runner.tick()
    assert tasks_of(town)["k2"]["state"] == "waiting"               # its dependant waits until k1 is merged
    assert json.loads((town.state / "ideas" / "demo" / "state.json").read_text())["state"] == "working"
    assert len(calls(town)) == 1


def test_merge_lands_into_dev_made_from_main_and_does_not_push_by_default(town):
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    main_before = git(town.repo, "rev-parse", "main")
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    commit = runner.merge("demo", "k1")
    assert git(town.repo, "rev-parse", "dev") == commit
    assert git(town.repo, "rev-parse", "main") == main_before
    assert subprocess.run(["git", "rev-parse", "--verify", "dev"], cwd=town.origin, capture_output=True).returncode != 0
    assert tasks_of(town)["k1"]["state"] == "merged" and tasks_of(town)["k1"]["commit"] == commit
    wait_task(runner, "k2", "review")
    runner.merge("demo", "k2")
    assert wait_idle(runner)["state"] == "done"
    assert git(town.repo, "show", "dev:k2.txt") == "done by k2"
    assert git(town.repo, "branch", "--list", "idea/demo/k1")        # the branch stays
    assert not list((town.repo / ".orkcraft" / "worktrees").glob("*"))


def test_red_after_the_one_retry_waits_at_review_with_its_counts_and_cannot_merge(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fail_always")
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert len(calls(town)) == 2
    assert task["tests"]["green"] is False and task["tests"]["failed"] == 1 and task["tests"]["passed"] >= 3
    assert "tests/test_thing.py::test_value" in task["tests"]["failing"] and "test_value" in task["tests"]["tail"]
    assert json.loads((town.state / "ideas" / "demo" / "state.json").read_text())["state"] == "working"
    before = git(town.repo, "rev-parse", "dev")
    with pytest.raises(RunnerError, match="red"):
        runner.merge("demo", "k1")
    assert git(town.repo, "rev-parse", "dev") == before and tasks_of(town)["k1"]["state"] == "review"


def test_send_back_resumes_the_session_with_the_line_and_counts_the_round(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fix_conflict")           # on a resume it edits the file again
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    with pytest.raises(RunnerError):
        runner.back("demo", "k1", "   ")
    runner.back("demo", "k1", "name it better")
    task = wait_task(runner, "k1", "review")
    assert task["round"] == 2 and task["why"] == "name it better" and task["session"] == "s-k1"
    assert [c["resume"] for c in calls(town)] == [False, True]
    assert "name it better" in runner.log("demo", "k1")


def test_a_conflict_found_at_merge_stays_at_review_and_fix_resolves_it(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fix_conflict")
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    git(town.repo, "checkout", "-q", "dev")
    (town.repo / "k1.txt").write_text("dev's line\n")
    git(town.repo, "add", "-A")
    git(town.repo, "commit", "-m", "dev moved")
    git(town.repo, "checkout", "-q", "main")
    with pytest.raises(RunnerError, match="conflicts with dev in k1.txt"):
        runner.merge("demo", "k1")
    task = tasks_of(town)["k1"]
    assert task["state"] == "review" and "k1.txt" in task["conflict"]
    with pytest.raises(RunnerError, match="conflicts"):
        runner.merge("demo", "k1")
    runner.back("demo", "k1", "resolve it")
    task = wait_task(runner, "k1", "review")
    assert task["conflict"] == "" and task["round"] == 2
    runner.merge("demo", "k1")
    assert git(town.repo, "show", "dev:k1.txt") == "resolved"


def goal_state(town, slug: str = "demo") -> dict:
    return json.loads((town.state / "ideas" / slug / "state.json").read_text())


def hand_of(town, slug: str = "demo") -> list[str]:
    """The kinds of stop the goal has in the hand (realm/board_map.py `idea_needs`), read from its files."""
    from orkboard.realm import board_map
    plan = json.loads((town.state / "ideas" / slug / "plan.json").read_text())
    i = {"slug": slug, "track": "general", "title": "Demo", "priority": "normal"}
    return [n["kind"] for n in board_map.idea_needs(town.repo, town.state, i, goal_state(town, slug), plan, [], at="x")]


def test_dropping_the_failed_task_frees_what_waited_for_it_and_the_goal_goes_on(town, monkeypatch):
    """The owner's 26 October: k1 failed, k2 and k3 waited for it for ever, the goal stayed failed and its card stayed in the hand
    after Drop."""
    monkeypatch.setenv("STUB_MODE", "k1=nocommit")
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}, {"id": "k3", "after": ["k1", "k2"]}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "failed" and hand_of(town) == ["failed"]
    assert tasks_of(town)["k2"]["state"] == "waiting"
    runner.drop_task("demo", "k1")
    assert tasks_of(town)["k1"]["state"] == "dropped" and tasks_of(town)["k1"]["error"] == "dropped by you"
    assert tasks_of(town)["k2"]["after"] == [] and tasks_of(town)["k3"]["after"] == ["k2"]        # nothing waits for k1 any more
    assert goal_state(town)["state"] in ("working", "done") and hand_of(town) == []
    assert wait_idle(runner)["state"] == "done"
    tasks = tasks_of(town)
    assert tasks["k1"]["state"] == "dropped" and tasks["k2"]["state"] == tasks["k3"]["state"] == "merged"
    assert [c["tid"] for c in calls(town)] == ["k1", "k1", "k2", "k3"] and hand_of(town) == []        # k1's turn and its one fix, never again


def test_a_task_runs_as_its_types_role_with_that_roles_model_and_instruction(town):
    from orkboard.realm import roles
    slug = roles.save(town.state, "Scribe", "laborer", 2, "Write like a patient scribe.")
    roles.set_kind(town.state, "docs", slug)
    plan_of(town, [{"id": "k1", "kind": "docs", "tier": "elder"}, {"id": "k2", "tier": "elder"}])
    runner, events = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    by = {c["tid"]: c for c in calls(town)}
    flat = lambda c: " ".join(c["argv"])                                  # noqa: E731
    assert "haiku" in flat(by["k1"]) and "Write like a patient scribe." in flat(by["k1"])      # the role's model, not the tier's
    assert "opus" in flat(by["k2"]) and "patient scribe" not in flat(by["k2"])                 # code: Grunt, the task's tier
    tasks = tasks_of(town)
    assert tasks["k1"]["role"] == slug and tasks["k2"]["role"] == "grunt"


# -- spec 36: the ledger, Merge's `dear`, the prompt stable first ------------------------------------------------

# -- spec 107 §1: a gate that could not run is not red; install and test again; the same failure again ---------------------

NO_TOOL = "nonexistent-tool-xyz"


def gate_toml(town, run: str) -> None:
    """The project's own gate in orkcraft.toml: `run`, as written."""
    (town.repo / "orkcraft.toml").write_text(f"[gate]\nrun = {json.dumps(run)}\n", encoding="utf-8")


def events_of(town, name: str) -> list[dict]:
    from orkboard.realm import event_log
    return [r for r in event_log.read(town.repo) if r["event"] == name]


def node_project(town, install_command: str):
    """A Node project whose tests need `node_modules` (made by the install, which is `install_command`)."""
    (town.repo / "package.json").write_text(json.dumps({"name": "x", "dependencies": {"left-pad": "1"}}))
    gate_toml(town, f"test -d node_modules || {NO_TOOL}")
    return [{"dir": ".", "command": install_command}]


def test_a_gate_that_could_not_run_goes_to_review_after_one_try_and_no_session_is_asked_to_fix_it(town):
    gate_toml(town, f"sh -c {NO_TOOL}")
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.events = True
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert len(calls(town)) == 1                                                   # the session worked once; none was sent the red gate
    tests = task["tests"]
    assert tests["green"] is False and tests["exit"] == 127 and tests["install"] == []
    assert tests["env"] == f"The tests could not run: `{NO_TOOL}` is not installed."
    assert task["look"] == "the tests could not run" and task["error"] == "the tests could not run" and task["round"] == 1
    assert runner.log("demo", "k1").count("== the gate, try") == 1
    (ran,) = events_of(town, "gate_ran")
    assert (ran["verdict"], ran["missing"], ran["linked"], ran["attempt"], ran["round"], ran["exit"]) == ("could_not_run", NO_TOOL, 0, 1, 1, 127)
    assert ran["seconds"] >= 0 and ran["command"] and ran["task"] == "k1"
    (ready,) = events_of(town, "result_ready")
    assert ready["verdict"] == "could_not_run" and ready["exit"] == 127
    with pytest.raises(RunnerError, match="could not run"):
        runner.merge("demo", "k1")


def test_install_and_test_again_installs_links_and_runs_the_gate_with_no_session_and_no_new_round(town, monkeypatch):
    from orkboard.realm import gate_env
    rows = node_project(town, f"{sys.executable} -c \"import os; os.makedirs('node_modules'); print('installed')\"")
    monkeypatch.setattr(gate_env, "missing", lambda root: rows if not (Path(root) / "node_modules").is_dir() else [])
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.events = True
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["tests"]["env"] and task["tests"]["install"] == rows
    runner.regate("demo", "k1", True, device="phone")
    assert tasks_of(town)["k1"]["state"] == "running"
    task = wait_task(runner, "k1", "review")
    assert task["tests"]["green"] is True and not task["tests"].get("env") and task["round"] == 1 and task["error"] == ""
    assert len(calls(town)) == 1                                                   # no session was called
    (tree,) = list((town.repo / ".orkcraft" / "worktrees").glob("*"))
    assert (tree / "node_modules").is_symlink()
    log = runner.log("demo", "k1")
    assert f"== installing: .: {rows[0]['command']}" in log and "installed" in log and "== testing again" in log
    decided = events_of(town, "result_decided")
    assert [(d["decision"], d["device"], d["round"]) for d in decided] == [("install", "phone", 1)]
    ran = events_of(town, "gate_ran")
    assert [(r["verdict"], r["linked"]) for r in ran] == [("could_not_run", 0), ("green", 1)] and ran[1]["round"] == 1
    assert runner.merge("demo", "k1")


def test_a_send_back_that_changed_nothing_and_failed_the_same_way_says_so_and_a_changed_one_does_not(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fail_always")
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.events = True
    runner.start("demo")
    first = wait_task(runner, "k1", "review")
    assert not first["tests"].get("same")
    runner.back("demo", "k1", "Fix the failing tests", suggested=True)
    again = wait_task(runner, "k1", "review")
    assert again["round"] == 2 and again["tests"]["same"] is True
    runner.back("demo", "k1", "look at the value")
    assert wait_task(runner, "k1", "review")["tests"]["same"] is True              # still nothing changed
    kinds = [(d["decision"], d["why_kind"]) for d in events_of(town, "result_decided")]
    assert kinds == [("fix", "suggested"), ("fix", "typed")]


def test_a_task_that_changed_only_documents_runs_no_derived_gate_and_waits_for_a_look(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=docs")
    (town.repo / "orkcraft.toml").unlink()                                          # no gate written: the project's own is derived (its critical tests)
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)                                                    # `review` off: a result that holds lands by itself
    runner.events = True
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["look"] == "it changes only documents" and task["tests"]["docs"] is True and task["tests"]["ran"] is False
    assert task["tests"]["green"] is True and not task["tests"].get("env")
    (ran,) = events_of(town, "gate_ran")
    assert ran["verdict"] == "docs" and ran["command"] == ""
    assert git(town.repo, "rev-parse", "main") == git(town.origin, "rev-parse", "main")      # nothing landed
