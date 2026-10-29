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


def runner_of(town, limits=None, **ideas) -> tuple[IdeaRunner, list]:
    events = []
    bus = SimpleNamespace(publish=lambda topic, **data: events.append((topic, data)))
    settings = SimpleNamespace(ideas={"max_parallel": 1, "merge_into": "main", "push": True, "review": False, **ideas})
    return IdeaRunner(town.repo, town.state, settings, bus, limits=limits or (lambda: [])), events


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


def test_the_prompt_holds_the_page_the_brief_the_tasks_before_and_the_rules(town):
    plan_of(town, [{"id": "k1", "brief": "first brief"}, {"id": "k2", "brief": "second brief", "after": ["k1"]}])
    runner, _ = runner_of(town)
    plan = runner.plan("demo")
    plan["tasks"][0].update(state="merged", subjects=["k1: add k1.txt"])
    prompt = runner._prompt("demo", plan, plan["tasks"][1])
    # spec 35 §0, §13: the spec is named by its path, never pasted
    assert "llm-wiki/general/pages/ideas/demo.md" in prompt and "A demo idea." not in prompt
    assert "second brief" in prompt and "first brief" in prompt
    assert "k1: add k1.txt" in prompt
    assert "write ork, never orc" not in prompt      # spec 36 §6: Claude Code reads CLAUDE.md itself in the worktree


def test_max_parallel_runs_that_many_at_once(town, monkeypatch):
    monkeypatch.setenv("STUB_SLEEP", "1.5")
    plan_of(town, [{"id": "k1"}, {"id": "k2"}, {"id": "k3"}])
    runner, _ = runner_of(town, max_parallel=2)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    spans = sorted((c["start"], c["end"]) for c in calls(town))
    assert spans[1][0] < spans[0][1]                         # two at once …
    assert spans[2][0] >= min(spans[0][1], spans[1][1]) - 0.05   # … never three
    assert sorted(t["state"] for t in tasks_of(town).values()) == ["merged"] * 3


def test_one_at_a_time_by_default(town, monkeypatch):
    monkeypatch.setenv("STUB_SLEEP", "0.5")
    plan_of(town, [{"id": "k1"}, {"id": "k2"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    wait_idle(runner)
    a, b = sorted((c["start"], c["end"]) for c in calls(town))
    assert b[0] >= a[1]


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


def test_no_commit_is_a_red_gate(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=nocommit")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "failed"
    assert "changed no file" in tasks_of(town)["k1"]["error"]


def test_what_the_session_left_uncommitted_is_committed_under_the_tasks_title_and_lands(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=uncommitted")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    assert tasks_of(town)["k1"]["state"] == "merged"
    assert git(town.origin, "log", "-1", "--format=%an", "main") == "Orkline"
    assert git(town.origin, "show", "main:k1.txt") == "done by k1"


def test_a_rebase_conflict_fails_and_main_keeps_its_own_line(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=conflict")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    state = wait_idle(runner)
    assert state["state"] == "failed"
    assert "conflict" in tasks_of(town)["k1"]["error"] and "shared.txt" in tasks_of(town)["k1"]["error"]
    assert git(town.repo, "show", "main:shared.txt") == "main's line"
    assert git(town.repo, "log", "-1", "--format=%s", "main") == "main moved"


def test_main_not_checked_out_moves_by_its_ref_only(town):
    git(town.repo, "checkout", "-b", "elsewhere")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    assert git(town.repo, "rev-parse", "--abbrev-ref", "HEAD") == "elsewhere"
    assert not (town.repo / "k1.txt").exists()
    assert git(town.repo, "show", "main:k1.txt") == "done by k1"
    assert git(town.origin, "rev-parse", "main") == git(town.repo, "rev-parse", "main")


def test_push_off_keeps_origin_where_it_was(town):
    before = git(town.origin, "rev-parse", "main")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town, push=False)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    assert git(town.origin, "rev-parse", "main") == before != git(town.repo, "rev-parse", "main")


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


def test_the_tool_saying_its_limit_is_hit_holds_the_task(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=limit")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    end = time.time() + 30
    while time.time() < end and (runner.busy() or tasks_of(town)["k1"]["state"] != "held"):
        time.sleep(0.1)
    task = tasks_of(town)["k1"]
    assert task["state"] == "held" and task["note"].startswith("after ")
    state = json.loads((town.state / "ideas" / "demo" / "state.json").read_text())
    assert state["state"] == "working"


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


def test_stop_all_stops_every_idea(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "*=slow")
    plan_of(town, [{"id": "k1"}])
    plan_of(town, [{"id": "k1"}], slug="other")
    runner, _ = runner_of(town, max_parallel=2)
    runner.start("demo")
    runner.start("other")
    time.sleep(1)
    runner.stop_all()
    for slug in ("demo", "other"):
        assert wait_idle(runner, slug, timeout=20)["state"] == "failed"


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


def test_a_restart_goes_on_with_working_ideas(town):
    plan_of(town, [{"id": "k1"}])
    (town.state / "ideas" / "demo" / "state.json").write_text(json.dumps({"state": "working"}))
    plan = json.loads((town.state / "ideas" / "demo" / "plan.json").read_text())
    plan["tasks"][0]["state"] = "running"
    (town.state / "ideas" / "demo" / "plan.json").write_text(json.dumps(plan))
    runner, _ = runner_of(town)
    assert wait_idle(runner)["state"] == "done"


def test_settings_are_read_however_they_are_carried():
    assert idea_runner.setting(SimpleNamespace(ideas={"max_parallel": 3}), "max_parallel") == 3
    assert idea_runner.setting({"ideas": {"push": False}}, "push") is False
    assert idea_runner.setting(SimpleNamespace(), "merge_into") == "dev"
    assert idea_runner.setting(SimpleNamespace(ideas_max_parallel=2), "max_parallel") == 2


# -- spec 33: Review ---------------------------------------------------------------------------------

from orkboard.core.idea_runner import RunnerError


def reviewing(town, **ideas):
    return runner_of(town, review=True, merge_into="dev", push=False, **ideas)


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


def test_merge_pushes_only_when_asked(town):
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town, review=True, merge_into="dev", push=True)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    commit = runner.merge("demo", "k1")
    assert git(town.origin, "rev-parse", "dev") == commit


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


def test_a_gate_without_pytest_says_no_counts():
    from orkboard.realm.idea_git import parse_tests
    assert parse_tests("no test files to run") == {"passed": 0, "failed": 0, "failing": [], "tail": "no test files to run"}
    got = parse_tests("FAILED tests/a.py::t1 - assert 1\nFAILED tests/a.py::t2\n2 failed, 18 passed in 1.2s")
    assert got["passed"] == 18 and got["failed"] == 2 and got["failing"] == ["tests/a.py::t1", "tests/a.py::t2"]
    many = "\n".join(f"FAILED tests/a.py::t{i}" for i in range(30)) + "\n30 failed in 2s"
    assert len(parse_tests(many)["failing"]) == 20 and len(parse_tests("x\n" * 100)["tail"].splitlines()) == 40


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


def test_drop_ends_the_task_as_dropped_removes_its_worktree_and_keeps_its_branch(town):
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    assert list((town.repo / ".orkcraft" / "worktrees").glob("*"))
    runner.drop_task("demo", "k1")
    task = tasks_of(town)["k1"]
    assert task["state"] == "dropped" and task["error"] == "dropped by you"          # gone from the plan, not failed
    assert not list((town.repo / ".orkcraft" / "worktrees").glob("*"))
    assert git(town.repo, "branch", "--list", "idea/demo/k1")
    state = json.loads((town.state / "ideas" / "demo" / "state.json").read_text())
    assert state["state"] == "plan" and state["error"] == ""                           # its only task gone, nothing merged: no failure, nothing to run


def goal_state(town, slug: str = "demo") -> dict:
    return json.loads((town.state / "ideas" / slug / "state.json").read_text())


def hand_of(town, slug: str = "demo") -> list[str]:
    """The kinds of stop the goal has in the hand (realm/board_map.py `idea_needs`), read from its files."""
    from orkboard.realm import board_map, ideas
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


def test_a_goal_that_failed_over_a_dropped_task_is_working_again_with_no_failed_stop(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=nocommit")
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    runner, _ = reviewing(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "failed"
    runner.drop_task("demo", "k1")
    wait_task(runner, "k2", "review")
    assert goal_state(town) == {"state": "working", "error": ""} and hand_of(town) == []         # k2 waits for the person at Review, nothing failed
    assert tasks_of(town)["k2"]["after"] == []


def test_a_goal_whose_last_tasks_are_dropped_is_done_where_something_merged_else_it_returns_to_its_plan(town):
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    runner.merge("demo", "k1")
    wait_task(runner, "k2", "review")
    runner.drop_task("demo", "k2")
    assert goal_state(town)["state"] == "done" and hand_of(town) == []
    assert [t["state"] for t in tasks_of(town).values()] == ["merged", "dropped"]
    plan_of(town, [{"id": "x1"}], slug="other")                                                  # nothing merged, the only task dropped
    runner.start("other")
    wait_task(runner, "x1", "review", slug="other")
    runner.drop_task("other", "x1")
    assert goal_state(town, "other") == {"state": "plan", "error": ""} and hand_of(town, "other") == []


def test_dropping_a_task_at_review_still_keeps_its_branch_records_the_decision_and_frees_the_next(town):
    from orkboard.realm import event_log
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    runner.drop_task("demo", "k1")
    assert git(town.repo, "branch", "--list", "idea/demo/k1") and not list((town.repo / ".orkcraft" / "worktrees").glob("*k1*"))
    assert [(r["task"], r["decision"]) for r in event_log.read(town.repo) if r["event"] == "result_decided"] == [("k1", "drop")]
    assert [r["state"] for r in event_log.read(town.repo) if r["event"] == "task_state" and r["task"] == "k1"][-1] == "dropped"
    wait_task(runner, "k2", "review")                                                           # it no longer waits for a result that will not come
    assert goal_state(town)["state"] == "working"


def test_a_task_dropped_before_it_had_its_own_state_is_dropped_when_the_goal_starts_again(town):
    """A plan the owner dropped a task of on 26 October holds it as `failed`, "dropped by you", and the goal failed."""
    plan_of(town, [{"id": "k1"}, {"id": "k2", "after": ["k1"]}])
    path = town.state / "ideas" / "demo" / "plan.json"
    plan = json.loads(path.read_text())
    plan["tasks"][0].update(state="failed", error="dropped by you")
    path.write_text(json.dumps(plan))
    (town.state / "ideas" / "demo" / "state.json").write_text(json.dumps({"state": "failed", "error": "Task k1: dropped by you"}))
    assert hand_of(town) == []                                                                   # the Board reads it as gone
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    tasks = tasks_of(town)
    assert tasks["k1"]["state"] == "dropped" and tasks["k2"]["state"] == "merged" and tasks["k2"]["after"] == []
    assert [c["tid"] for c in calls(town)] == ["k2"]


def test_stop_task_stops_one_and_the_others_go_on(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=slow")
    plan_of(town, [{"id": "k1"}, {"id": "k2"}])
    runner, _ = reviewing(town, max_parallel=2)
    runner.start("demo")
    end = time.time() + 30
    while time.time() < end and tasks_of(town)["k1"]["state"] not in ("running", "testing"):
        time.sleep(0.1)
    runner.stop_task("demo", "k1")
    wait_task(runner, "k2", "review")
    k1 = wait_task(runner, "k1", "ready")
    assert k1["note"] == "stopped by you" and k1["error"] == ""
    runner.tick()
    assert tasks_of(town)["k1"]["state"] == "ready"                  # it waits for Start
    with pytest.raises(RunnerError):
        runner.stop_task("demo", "k2")


def test_the_log_is_cut_to_its_last_lines_and_masks_a_secret(town):
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner._log("demo", "k1", "".join(f"line {i}\n" for i in range(2500)))
    path = town.state / "ideas" / "demo" / "k1.log"
    assert len(path.read_text().splitlines()) == 2000 and path.read_text().splitlines()[-1] == "line 2499"
    assert len(runner.log("demo", "k1").splitlines()) == 200
    runner._log("demo", "k1", "the key is s3cr3t-value here\n", {"API_KEY": "s3cr3t-value", "ORKCRAFT_ORC": "ideas/x"})
    assert "s3cr3t-value" not in runner.log("demo", "k1") and "••••" in runner.log("demo", "k1")


def test_the_testers_defaults(town):
    from orkboard import settings
    assert settings.IDEAS["merge_into"] == "dev" and settings.IDEAS["push"] is False and settings.IDEAS["review"] is False
    assert settings.clean_ideas({"merge_into": "main", "push": True})["merge_into"] == "main"
    assert settings.clean_ideas({"merge_into": "main", "push": True})["push"] is True


def test_the_runner_writes_its_events_to_the_event_log(town):
    from orkboard.realm import event_log
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    rows = event_log.read(town.repo)
    states = [(r["state"], r["was"]) for r in rows if r["event"] == "task_state"]
    assert ("running", "waiting") in states and ("review", "testing") in states
    (ready,) = [r for r in rows if r["event"] == "result_ready"]
    assert ready["idea"] == "demo" and ready["task"] == "k1" and ready["round"] == 1 and ready["passed"] >= 3 and ready["failed"] == 0
    assert ready["files"] == 1 and ready["added"] == 1 and ready["removed"] == 0 and ready["cost"] == 0.01
    first = next(r for r in rows if r["event"] == "task_state" and r["state"] == "running")
    assert first["tier"] == "laborer" and first["round"] == 1
    runner.merge("demo", "k1", device="phone")
    (d,) = [r for r in event_log.read(town.repo) if r["event"] == "result_decided"]
    assert d["decision"] == "merge" and d["into"] == "dev" and d["pushed"] is False and d["device"] == "phone" and d["seconds"] >= 0


def test_back_and_drop_are_decisions_with_their_line_and_a_stop_is_a_task_stopped(town, monkeypatch):
    from orkboard.realm import event_log
    monkeypatch.setenv("STUB_MODE", "k1=fix_conflict,k2=slow")
    plan_of(town, [{"id": "k1"}, {"id": "k2"}])
    runner, _ = reviewing(town, max_parallel=2)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    runner.back("demo", "k1", "rename it")
    wait_task(runner, "k1", "review")
    runner.stop_task("demo", "k2", device="phone")
    wait_task(runner, "k2", "ready")
    runner.drop_task("demo", "k1")
    rows = event_log.read(town.repo)
    decided = [(r["decision"], r.get("why")) for r in rows if r["event"] == "result_decided"]
    assert decided == [("back", "rename it"), ("drop", None)] or decided == [("back", "rename it"), ("drop", "")]
    (stop,) = [r for r in rows if r["event"] == "task_stopped"]
    assert stop["task"] == "k2" and stop["device"] == "phone"


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


def test_a_roles_max_parallel_is_held_besides_the_ideas(town, monkeypatch):
    from orkboard.realm import roles
    monkeypatch.setenv("STUB_SLEEP", "1.0")
    slug = roles.save(town.state, "Solo", "laborer", 1, "")
    roles.set_kind(town.state, "tests", slug)
    plan_of(town, [{"id": "k1", "kind": "tests"}, {"id": "k2", "kind": "tests"}, {"id": "k3"}])
    runner, _ = runner_of(town, max_parallel=3)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    spans = {c["tid"]: (c["start"], c["end"]) for c in calls(town)}
    assert spans["k2"][0] >= spans["k1"][1] - 0.05 or spans["k1"][0] >= spans["k2"][1] - 0.05   # the two Solo tasks never overlap


def test_the_events_carry_the_role(town):
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.events = True
    runner.start("demo")
    wait_task(runner, "k1", "review")
    from orkboard.realm import event_log
    rows = [r for r in event_log.read(town.repo) if r["event"] in ("task_state", "result_ready")]
    assert rows and all(r.get("role") == "grunt" for r in rows if r["event"] == "result_ready" or r["state"] in ("testing", "review"))


# -- spec 36: the ledger, Merge's `dear`, the prompt stable first ------------------------------------------------

def test_a_tasks_two_rounds_and_a_gate_retry_write_their_lines(town, monkeypatch):
    from orkboard.realm import idea_spend
    monkeypatch.setenv("STUB_MODE", "k1=fail_once,k2=fix_conflict")
    plan_of(town, [{"id": "k1"}, {"id": "k2"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    wait_task(runner, "k2", "review")
    runner.back("demo", "k2", "name it better")
    wait_task(runner, "k2", "review")
    rows = idea_spend.read(town.state / "ideas" / "demo" / "spend.jsonl")
    assert [(r["step"], r["task"], r["round"]) for r in rows] == [("task", "k1", 1), ("fix", "k1", 1), ("task", "k2", 1),
                                                                  ("task", "k2", 2)]
    tasks = tasks_of(town)
    for r in rows:
        assert r["role"] == "grunt" and r["tool"] == "claude" and r["model"] == tasks[r["task"]]["model"]
        assert r["tier"] == tasks[r["task"]]["ran_tier"] and r["effort"] == tasks[r["task"]]["effort"]
        assert r["cost"] == 0.01 and r["tokens"]["total"] == 15 and set(r["tokens"]) >= {"in", "out", "cache_read", "cache_write"}
    got = idea_spend.of_idea(town.state, "demo")
    assert got["tasks"]["k1"] == {"usd": 0.02, "work": 0.01, "rework": 0.01}
    assert got["tasks"]["k2"] == {"usd": 0.02, "work": 0.01, "rework": 0.01}


def test_merge_with_dear_writes_it_on_result_decided(town):
    from orkboard.realm import event_log
    plan_of(town, [{"id": "k1"}, {"id": "k2"}])
    runner, _ = reviewing(town)
    runner.events = True
    runner.start("demo")
    wait_task(runner, "k1", "review")
    runner.merge("demo", "k1", dear=True)
    wait_task(runner, "k2", "review")
    runner.merge("demo", "k2")
    decided = [r for r in event_log.read(town.repo) if r["event"] == "result_decided"]
    assert [(r["task"], r["dear"]) for r in decided] == [("k1", True), ("k2", False)]


def test_the_prompt_is_stable_first_and_lists_only_its_after_tasks(town):
    from orkboard.realm import roles
    roles.save(town.state, "Grunt", "", 8, "Keep it small. Name things plainly.", "grunt")
    (town.state).mkdir(parents=True, exist_ok=True)
    (town.state / "secrets.json").write_text(json.dumps({"ideas/demo/t1": "s3cret"}))
    todos = [{"id": "t1", "title": "API_KEY", "kind": "secret", "why": "", "choices": [], "steps": [],
              "for": ["k3"], "done": True, "value": "stored"}]
    plan_of(town, [{"id": "k1", "brief": "first brief"}, {"id": "k2", "brief": "second brief"},
                   {"id": "k3", "brief": "third brief", "after": ["k2"]}], todos)
    runner, _ = runner_of(town)
    plan = runner.plan("demo")
    plan["tasks"][1].update(state="merged", subjects=["k2: add k2.txt"])
    one, three = (runner._prompt("demo", plan, plan["tasks"][i]) for i in (0, 2))
    stable = one[:one.index("You do one task")]
    assert stable.startswith("# Your role: Grunt\n\nKeep it small. Name things plainly.") and "# When you are done" in stable
    assert three.startswith(stable) and "demo" not in stable and "API_KEY" not in stable
    assert "k2: add k2.txt" in three and "second brief" in three
    assert "first brief" not in three                       # not of its `after`: never listed (decisions §49.9)
    assert "# The tasks before yours" not in one
    assert three.rstrip().endswith("never print them, write them to a file or commit them.") and "API_KEY" in three
    assert "write ork, never orc" not in one + three        # CLAUDE.md is not pasted: Claude Code reads it itself


def test_a_long_instruction_from_before_goes_to_the_ork_cut_at_a_sentence_end(town):
    long = "Be careful. " * 60 + "And the tail."
    (town.state / "roles").mkdir(parents=True, exist_ok=True)
    (town.state / "roles" / "grunt.md").write_text(f"---\nname: Grunt\nmodel: \nmax_parallel: 8\n---\n{long}\n")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    plan = runner.plan("demo")
    prompt = runner._prompt("demo", plan, plan["tasks"][0])
    head = prompt.split("\n\n# When you are done")[0].removeprefix("# Your role: Grunt\n\n")
    assert len(head) <= 600 and head.endswith("Be careful.") and "And the tail." not in prompt


def test_a_to_do_gone_without_or_described_is_said_in_the_prompt_and_lets_the_task_run(town):
    todos = [{"id": "t1", "title": "Reference picture", "kind": "file", "why": "", "choices": [], "steps": [], "for": ["k1"], "done": True, "skipped": True, "value": None},
             {"id": "t2", "title": "Logo", "kind": "file", "why": "", "choices": [], "steps": [], "for": ["k1"], "done": True, "words": True, "value": "A grey ork."},
             {"id": "t3", "title": "Which port", "kind": "choice", "why": "", "choices": ["80", "81"], "steps": [], "for": ["k1"], "done": True, "skipped": True, "value": None},
             {"id": "t4", "title": "Other task's", "kind": "confirm", "why": "", "choices": [], "steps": [], "for": ["k2"], "done": True, "skipped": True, "value": None}]
    plan_of(town, [{"id": "k1"}, {"id": "k2"}], todos)
    runner, _ = runner_of(town)
    plan = runner.plan("demo")
    prompt = runner._prompt("demo", plan, plan["tasks"][0])
    assert "The person went without “Reference picture”: do the task without it; if it cannot be done without it, say what it blocks and stop." in prompt
    assert "The person left “Which port” to you: choose one of 80, 81, and say which and why in your result." in prompt
    assert "Instead of the file “Logo”, the person described it: A grey ork." in prompt
    assert "Other task's" not in prompt
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"


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


def test_test_again_without_an_install_relinks_and_runs_the_gate(town, monkeypatch):
    from orkboard.realm import gate_env
    node_project(town, "unused")
    monkeypatch.setattr(gate_env, "missing", lambda root: [{"dir": ".", "command": "npm ci"}])
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.events = True
    runner.start("demo")
    wait_task(runner, "k1", "review")
    (town.repo / "node_modules").mkdir()                                           # the person installed it themselves
    runner.regate("demo", "k1", False)
    task = wait_task(runner, "k1", "review")
    assert task["tests"]["green"] is True and "== installing" not in runner.log("demo", "k1")
    assert [d["decision"] for d in events_of(town, "result_decided")] == ["test again"]
    with pytest.raises(RunnerError, match="not waiting for its tests"):
        runner.regate("demo", "k1", False)                                         # it ran: nothing is waiting for its tests now


def test_an_install_that_fails_comes_back_to_review_with_its_last_line_and_the_round_stays(town, monkeypatch):
    from orkboard.realm import gate_env
    rows = node_project(town, f"{sys.executable} -c \"import sys; print('npm ERR! first'); print('npm ERR! network is down'); sys.exit(1)\"")
    monkeypatch.setattr(gate_env, "missing", lambda root: rows)
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.events = True
    runner.start("demo")
    wait_task(runner, "k1", "review")
    runner.regate("demo", "k1", True)
    task = wait_task(runner, "k1", "review")
    assert task["tests"]["env"] == "The install failed: npm ERR! network is down" and task["tests"]["install"] == rows
    assert task["round"] == 1 and task["look"] == "the tests could not run" and task["finished"]
    assert "npm ERR! first" in runner.log("demo", "k1") and len(calls(town)) == 1
    assert len(events_of(town, "gate_ran")) == 1                                   # the gate did not run the second time
    runner.regate("demo", "k1", True)                                              # it can be tried again
    assert wait_task(runner, "k1", "review")["tests"]["env"].startswith("The install failed")


def test_install_and_test_again_is_refused_for_a_result_that_did_not_fail_to_run(town):
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    with pytest.raises(RunnerError):
        runner.regate("demo", "k1", True)                                          # not at Review yet
    runner.start("demo")
    wait_task(runner, "k1", "review")
    with pytest.raises(RunnerError, match="That result is not waiting for its tests"):
        runner.regate("demo", "k1", True)                                          # its tests ran


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


def test_a_send_back_that_changed_the_code_is_not_the_same_failure(town, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "k1=fail_moving")
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    runner.back("demo", "k1", "try another value")
    again = wait_task(runner, "k1", "review")
    assert again["round"] == 2 and again["tests"]["green"] is False and "same" not in again["tests"]


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
