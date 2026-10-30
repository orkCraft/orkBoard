"""Spec 111 §4.2 (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md, decisions §188.3): the checks on a goal's way into main —
`[gate.main]` in `orkcraft.toml` (realm/gate_config.py), the trial worktree and the run (realm/goal_main.py `trial`, realm/main_checks.py), and the
command and the bus (`ideas.to_main_checks`, `main.check`, gui/ideas_gate.py) — on a temporary git repository, with no network and no model."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from orkboard.core import bus
from orkboard.gui.board_host import CommandError
from orkboard.realm import gate_config, goal_main, main_checks

from tests.test_goal_main import commit_in, depends, git, goal, host, plan_of, repo, short, task, worktrees, work  # noqa: F401  (fixtures and helpers)


def toml(root: Path, text: str) -> None:
    (root / "orkcraft.toml").write_text(text, encoding="utf-8")


def steps_of(host, repo, slug, **more):
    seen: list[list[dict]] = []
    got = main_checks.run(repo, host.ideas.state_dir, slug, root=host.ideas.root(), into="dev", main="main", on_step=seen.append, **more)
    return got, seen


def states(steps):
    return [(s["name"], s["state"]) for s in steps]


def wait_done(host, slug, ms=20000):
    for _ in range(ms // 20):
        got = host.ideas._main_checks.get(slug)
        if got and not got["running"]:
            return got
        time.sleep(0.02)
    raise AssertionError("the checks never ended")


# -- the file -----------------------------------------------------------------------------------------------------

def test_with_none_written_the_checks_are_the_merge_and_tests(tmp_path):
    assert gate_config.main_checks(tmp_path) == [gate_config.Check("The merge"), gate_config.Check("Tests", gate=True)]
    toml(tmp_path, "[gate]\nrun = \"true\"\n")
    assert gate_config.main_checks(tmp_path) == [gate_config.Check("The merge"), gate_config.Check("Tests", gate=True)]
    assert gate_config.read(tmp_path).main == ()


def test_gate_main_writes_the_checks_each_a_name_and_a_command_after_the_merge(tmp_path):
    toml(tmp_path, '[gate]\nrun = "true"\n[gate.main]\nchecks = [{name = "Unit tests", run = "pytest -q tests/unit"}, {name = " Looks ", run = "npm run looks"}]\n')
    got = gate_config.read(tmp_path)
    assert got.run == "true" and got.error == ""
    assert gate_config.main_checks(tmp_path) == [gate_config.Check("The merge"), gate_config.Check("Unit tests", "pytest -q tests/unit"), gate_config.Check("Looks", "npm run looks")]


@pytest.mark.parametrize("text", ['[gate.main]\nchecks = "pytest"\n', '[gate.main]\nchecks = [{name = "No command"}]\n', '[gate.main]\nchecks = [{name = "", run = "x"}]\n',
                                  '[gate.main]\nchecks = ["pytest"]\n', '[gate]\nmain = 3\n'])
def test_a_bad_gate_main_is_said_in_the_gates_error_and_the_gate_runs_as_with_no_file(tmp_path, text):
    toml(tmp_path, text)
    got = gate_config.read(tmp_path)
    assert "orkcraft.toml is not usable" in got.error and "[gate.main]" in got.error
    assert got.main == () and gate_config.main_checks(tmp_path) == [gate_config.Check("The merge"), gate_config.Check("Tests", gate=True)]


# -- the run ------------------------------------------------------------------------------------------------------

def test_the_default_checks_pass_on_a_clean_trial_and_leave_main_dev_and_the_worktree_as_they_were(host, repo, work):
    lobby, *_ = work
    toml(repo, '[gate]\nrun = "test -f lobby/room.ts"\n')                                  # the trial holds the picks; main does not
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "gate")
    git(repo, "branch", "-f", "dev", "dev")
    main_before, dev_before, status = git(repo, "rev-parse", "main"), git(repo, "rev-parse", "dev"), git(repo, "status", "--porcelain")
    got, seen = steps_of(host, repo, lobby)
    assert states(got) == [("The merge", "passed"), ("Tests", "passed")]
    assert got[0]["words"] == "3 commits apply to main" and got[1]["words"] == ""
    assert states(seen[0]) == [("The merge", "waiting"), ("Tests", "waiting")] and states(seen[1]) == [("The merge", "running"), ("Tests", "waiting")]
    assert [states(s) for s in seen][-2:] == [[("The merge", "passed"), ("Tests", "running")], [("The merge", "passed"), ("Tests", "passed")]]
    assert worktrees(repo) == [] and not [ln for ln in git(repo, "worktree", "list").splitlines() if "gate-main" in ln]
    assert (git(repo, "rev-parse", "main"), git(repo, "rev-parse", "dev"), git(repo, "status", "--porcelain")) == (main_before, dev_before, status)
    assert not (repo / "lobby").exists()


def test_a_project_with_no_tests_passes_the_tests_check_saying_so(host, repo, work):
    lobby, *_ = work
    got, _seen = steps_of(host, repo, lobby)
    assert states(got) == [("The merge", "passed"), ("Tests", "passed")] and "no tests ran" in got[1]["words"]


def test_written_checks_run_in_order_in_the_trial_and_the_first_red_one_stops_the_run(host, repo, work):
    lobby, *_ = work
    toml(repo, '[gate.main]\nchecks = [{name = "Files", run = "test -f lobby/room.ts && test -f lobby/join.ts"}, {name = "Looks", run = "echo 2 looks differ; exit 1"},'
               ' {name = "Never", run = "false"}]\n')
    got, seen = steps_of(host, repo, lobby)
    assert got == [{"name": "The merge", "state": "passed", "words": "3 commits apply to main"}, {"name": "Files", "state": "passed", "words": ""},
                   {"name": "Looks", "state": "failed", "words": "2 looks differ"}, {"name": "Never", "state": "waiting", "words": ""}]
    assert ("Looks", "running") in [(s["name"], s["state"]) for step in seen for s in step]
    assert worktrees(repo) == []


def test_a_command_that_prints_nothing_says_its_exit_code_and_one_that_cannot_start_says_so(host, repo, work):
    lobby, *_ = work
    toml(repo, '[gate.main]\nchecks = [{name = "Quiet", run = "false"}]\n')
    assert steps_of(host, repo, lobby)[0][1]["words"] == "It ended with exit code 1"
    toml(repo, '[gate.main]\nchecks = [{name = "Missing", run = "no-such-program-here --x"}]\n')
    got = steps_of(host, repo, lobby)[0][1]
    assert got["state"] == "failed" and "no-such-program-here could not start" in got["words"]


def test_a_failing_gate_command_is_red_with_the_last_line_of_what_it_printed(host, repo, work):
    lobby, *_ = work
    toml(repo, '[gate]\nrun = "echo ===== 2 failed, 9 passed in 1.1s =====; exit 1"\n')
    got = steps_of(host, repo, lobby)[0]
    assert states(got) == [("The merge", "passed"), ("Tests", "failed")] and got[1]["words"] == "2 failed, 9 passed in 1.1s"


def test_a_command_that_takes_too_long_is_red_and_its_worktree_is_gone(host, repo, work):
    lobby, *_ = work
    toml(repo, '[gate.main]\nchecks = [{name = "Slow", run = "sleep 30"}]\n')
    start = time.monotonic()
    got = steps_of(host, repo, lobby, timeout_s=1)[0]
    assert got[1] == {"name": "Slow", "state": "failed", "words": "It took longer than 1 second"} and time.monotonic() - start < 15
    assert worktrees(repo) == []


def test_a_merge_that_conflicts_fails_the_merge_and_leaves_the_others_waiting(host, repo):
    lobby = goal(host, "Lobby")
    task(host, repo, lobby, "k1", {"a.txt": "dev's a\n"})
    commit_in(repo, "a.txt", "main's own a\n")
    toml(repo, '[gate.main]\nchecks = [{name = "Never", run = "true"}]\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "gate file")
    main_before = git(repo, "rev-parse", "main")
    got, seen = steps_of(host, repo, lobby)
    assert got == [{"name": "The merge", "state": "failed", "words": f"{short(host, lobby)} does not apply to main cleanly: a.txt"},
                   {"name": "Never", "state": "waiting", "words": ""}]
    assert git(repo, "rev-parse", "main") == main_before and worktrees(repo) == [] and git(repo, "status", "--porcelain") == ""
    assert plan_of(host, repo, lobby)["conflict"] is True                               # the plan says whose reason it is


def test_a_goal_that_cannot_go_has_no_trial_and_the_merge_says_why(host, repo):
    lobby = goal(host, "Lobby", state="raw")                                             # no plan at all
    got = steps_of(host, repo, lobby)[0]
    assert got[0]["state"] == "failed" and got[0]["words"] and worktrees(repo) == []


def test_a_stop_ends_the_run_and_the_worktree_goes(host, repo, work):
    lobby, *_ = work
    toml(repo, '[gate.main]\nchecks = [{name = "Slow", run = "sleep 30"}]\n')
    stop = threading.Event()
    box: list[str] = []

    def go():
        try:
            main_checks.run(repo, host.ideas.state_dir, lobby, root=host.ideas.root(), into="dev", main="main", cancel=stop)
        except InterruptedError as e:
            box.append(str(e))

    t = threading.Thread(target=go)
    t.start()
    time.sleep(1.0)
    stop.set()
    t.join(15)
    assert box == ["stopped"] and worktrees(repo) == []


def test_the_trial_keeps_its_worktree_while_the_block_runs_and_removes_it_after_an_error(host, repo, work):
    lobby, *_ = work
    with pytest.raises(RuntimeError, match="boom"):
        with goal_main.trial(repo, host.ideas.state_dir, lobby, root=host.ideas.root(), into="dev", main="main") as t:
            assert t.path is not None and (t.path / "lobby" / "room.ts").is_file() and len(worktrees(repo)) == 1
            raise RuntimeError("boom")
    assert worktrees(repo) == [] and not t.path.exists()


def test_a_plan_without_the_pick_tries_nothing_and_a_clean_plan_has_no_conflict_key(host, repo):
    lobby = goal(host, "Lobby")
    task(host, repo, lobby, "k1", {"a.txt": "dev's a\n"})
    commit_in(repo, "a.txt", "main's own a\n")
    seen = goal_main.plan(repo, host.ideas.state_dir, lobby, root=host.ideas.root(), into="dev", main="main", pick=False)
    assert seen["sealed"] is None and "conflict" not in seen
    assert "conflict" not in plan_of(host, repo, goal(host, "Other"))


# -- the command and the bus --------------------------------------------------------------------------------------

def test_the_command_runs_the_checks_in_the_background_and_publishes_each_step_on_the_bus(host, repo, work):
    lobby, *_ = work
    toml(repo, '[gate.main]\nchecks = [{name = "Files", run = "test -f lobby/room.ts"}]\n')
    heard: list[dict] = []
    host.ideas.host.bus.subscribe(bus.MAIN_CHECK, lambda e: heard.append(e.data))
    first = host.command("ideas.to_main_checks", {"idea": lobby})
    assert first["idea"] == lobby and first["running"] is True and [c["name"] for c in first["checks"]] == ["The merge", "Files"]
    wait_done(host, lobby)
    time.sleep(0.1)
    last = heard[-1]
    assert last["idea"] == lobby and states(last["checks"]) == [("The merge", "passed"), ("Files", "passed")]
    seq = [states(h["checks"]) for h in heard]
    assert seq[0] == [("The merge", "waiting"), ("Files", "waiting")] and [("The merge", "running"), ("Files", "waiting")] in seq and [("The merge", "passed"), ("Files", "running")] in seq
    assert {h["idea"] for h in heard} == {lobby}
    assert host.ideas.snapshot()["main_checks"] == {lobby: last["checks"]}               # the face reads them in the snapshot
    assert "main_checks" not in host.phone_snapshot()
    again = host.command("ideas.to_main_checks", {"idea": lobby})                        # the same plan: the last results, not run again
    assert again["running"] is False and states(again["checks"]) == [("The merge", "passed"), ("Files", "passed")]
    count = len(heard)
    time.sleep(0.2)
    assert len(heard) == count
    with pytest.raises(CommandError, match="idea is missing"):
        host.command("ideas.to_main_checks", {})


def test_to_main_is_refused_while_the_checks_run_and_after_one_is_red_and_goes_when_all_passed(host, repo, work):
    lobby, *_ = work
    toml(repo, '[gate.main]\nchecks = [{name = "Slow", run = "sleep 1.5 && test -f lobby/room.ts"}]\n')
    host.command("ideas.to_main_checks", {"idea": lobby})
    with pytest.raises(CommandError, match="Checking the way into main"):
        host.command("ideas.to_main", {"idea": lobby})
    assert git(repo, "log", "-1", "--format=%s", "main") == "edit old.txt"
    wait_done(host, lobby)
    assert host.command("ideas.to_main", {"idea": lobby})["ok"] is True


def test_a_red_check_seals_the_way_in_words_and_choosing_the_goal_anew_runs_the_checks_again(host, repo, work):
    lobby, *_ = work
    toml(repo, '[gate.main]\nchecks = [{name = "Regression", run = "echo 2 tests fail; exit 1"}]\n')
    host.command("ideas.to_main_checks", {"idea": lobby})
    wait_done(host, lobby)
    with pytest.raises(CommandError, match="Sealed: Regression is red: 2 tests fail"):
        host.command("ideas.to_main", {"idea": lobby})
    assert worktrees(repo) == [] and git(repo, "log", "-1", "--format=%s", "main") == "edit old.txt"
    kept = host.command("ideas.to_main_checks", {"idea": lobby})                         # asked again: the kept red result
    assert kept["running"] is False and kept["checks"][-1]["state"] == "failed"
    toml(repo, '[gate.main]\nchecks = [{name = "Regression", run = "true"}]\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixed")
    time.sleep(0.05)
    fresh = host.command("ideas.to_main_checks", {"idea": lobby, "again": True})         # the person chose it anew: run once more
    assert fresh["running"] is True or fresh["checks"][-1]["state"] == "passed"
    wait_done(host, lobby)
    assert host.command("ideas.to_main", {"idea": lobby})["ok"] is True


def test_results_of_an_older_plan_are_refused_and_a_goal_never_checked_goes_as_before(host, repo, work):
    lobby, chat, *_ = work
    host.command("ideas.to_main_checks", {"idea": lobby})
    wait_done(host, lobby)
    task(host, repo, lobby, "k3", {"lobby/more.ts": "more\n"})                           # a new commit in the plan
    with pytest.raises(CommandError, match="The way into main changed"):
        host.command("ideas.to_main", {"idea": lobby})
    assert host.command("ideas.to_main", {"idea": chat})["ok"] is True                   # Chat's checks were never asked: today's way


def test_a_seal_no_check_owns_is_answered_without_running_anything(host, repo, work):
    lobby, chat, *_ = work
    depends(host, lobby, chat)
    from orkboard.realm import ideas
    ideas.save_state(host.ideas.state_dir, chat, state="running")
    plan = ideas.plan(host.ideas.state_dir, chat)
    plan["tasks"].append({"id": "rv", "title": "Waiting", "state": "review", "commit": "", "after": [], "round": 1})
    ideas.save_plan(host.ideas.state_dir, chat, plan)
    got = host.command("ideas.to_main_checks", {"idea": lobby})
    assert got["checks"] == [] and got["sealed"] == f"{short(host, chat)} is not done yet" and got["running"] is False
    assert host.ideas.snapshot()["main_checks"] == {} and worktrees(repo) == []
