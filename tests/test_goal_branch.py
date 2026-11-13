"""A goal's own branch (docs/specs/168 F1, decisions §283.26): realm/goal_branch.py on a real temporary repository."""
from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path

import pytest

from orkboard.realm import goal_branch, idea_git
from orkboard.realm.idea_git import IdeaGit

GATE = '[gate]\nalways = ["tests/test_ok.py"]\n'


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit_in(path: Path, name: str, text: str) -> None:
    (path / name).parent.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(text)
    git(path, "add", "-A")
    git(path, "commit", "-m", f"edit {name}")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-b", "dev")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    (r / ".gitignore").write_text(".orkcraft/\n__pycache__/\n")
    (r / "a.txt").write_text("a\n")
    (r / "tests").mkdir()
    (r / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    (r / "orkcraft.toml").write_text(GATE)
    git(r, "add", "-A")
    git(r, "commit", "-m", "start")
    return r


@pytest.fixture
def state(repo: Path) -> Path:
    return repo / ".orkcraft"


def land_task(g: IdeaGit, slug: str, tid: str, base: str, name: str, text: str = "x\n") -> str:
    path, branch = g.prepare(slug, tid, base)
    commit_in(path, name, text)
    commit, _subjects, _note = g.land(path, branch, base, push=False)
    g.remove(path)
    return commit


def test_a_goals_branch_is_made_from_dev_and_two_tasks_land_on_it_not_in_dev(repo, state):
    g = IdeaGit(repo)
    dev = git(repo, "rev-parse", "dev")
    branch = goal_branch.begin(g, state, "demo", {"tasks": []}, "dev")
    assert branch == "goal/demo" == goal_branch.name("demo") and git(repo, "rev-parse", branch) == dev
    first = land_task(g, "demo", "k1", branch, "b.txt")
    second = land_task(g, "demo", "k2", branch, "c.txt")
    assert git(repo, "rev-parse", "goal/demo") == second != first
    assert git(repo, "rev-parse", "dev") == dev                           # dev did not move
    assert git(repo, "show", "goal/demo:b.txt") == "x" and git(repo, "show", "goal/demo:c.txt") == "x"
    assert git(repo, "branch", "--list", "idea/demo/k1")                  # the task's ref lives beside goal/demo: no `x` and `x/y` clash
    assert goal_branch.in_use(state, "demo") == "goal/demo" and not goal_branch.waits_for_dev(state, "demo")


def test_a_second_begin_keeps_the_branch_and_a_gone_branch_stops_the_work(repo, state):
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev")
    land_task(g, "demo", "k1", "goal/demo", "b.txt")
    plan = {"tasks": [{"id": "k1", "state": "merged", "commit": "abc"}]}
    assert goal_branch.begin(g, state, "demo", plan, "dev", 1) == "goal/demo"          # a task merged on the branch is no sign of an old goal
    git(repo, "branch", "-D", "goal/demo")
    with pytest.raises(RuntimeError, match="is gone"):
        goal_branch.begin(g, state, "demo", plan, "dev", 2)


def test_a_goal_already_at_work_in_dev_has_no_branch_and_lands_as_before(repo, state):
    g = IdeaGit(repo)
    plan = {"tasks": [{"id": "k1", "state": "merged", "commit": "abc123"}, {"id": "k2", "state": "ready"}]}
    assert goal_branch.begin(g, state, "old", plan, "dev") == ""                      # a task of it landed in dev, and it has no file
    assert not goal_branch.read(state, "old") and not goal_branch.in_use(state, "old")
    assert not git(repo, "branch", "--list", "goal/old")
    assert goal_branch.row(state, "old") == {}
    assert goal_branch.drop(g, state, "old") is False                                 # nothing to delete: dropped as it always was
    # a clean check that merged with no commit is not work in dev
    assert goal_branch.begin(g, state, "fresh", {"tasks": [{"id": "c1", "state": "merged", "commit": ""}]}, "dev") == "goal/fresh"


def test_a_second_step_is_cut_from_the_branch_with_dev_merged_in_as_it_starts(repo, state):
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "design.txt")
    commit_in(repo, "other.txt", "another goal's work\n")                              # dev moved while step 1 worked
    goal_branch.step_started(g, state, "demo", 1, "dev")                              # step 1 was synced when the branch was cut: nothing happens
    assert not git(repo, "branch", "--contains", "dev", "goal/demo")
    goal_branch.step_started(g, state, "demo", 2, "dev")
    assert git(repo, "merge-base", "--is-ancestor", "dev", "goal/demo") == ""
    path, branch = g.prepare("demo", "k2", "goal/demo")
    assert (path / "design.txt").exists() and (path / "other.txt").exists()           # step 2 sees step 1's work and dev's
    g.remove(path)
    assert goal_branch.read(state, "demo")["synced"] == [1, 2]
    before = git(repo, "rev-parse", "goal/demo")
    goal_branch.step_started(g, state, "demo", 2, "dev")                              # once a step
    assert git(repo, "rev-parse", "goal/demo") == before


def test_dev_conflicting_with_the_branch_stops_the_step_without_forcing(repo, state):
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "a.txt", "the goal's line\n")
    commit_in(repo, "a.txt", "dev's line\n")
    branch_head, dev_head = git(repo, "rev-parse", "goal/demo"), git(repo, "rev-parse", "dev")
    with pytest.raises(goal_branch.GoalConflict) as e:
        goal_branch.step_started(g, state, "demo", 2, "dev")
    assert e.value.files == ["a.txt"] and "a.txt" in str(e.value)
    assert git(repo, "rev-parse", "goal/demo") == branch_head and git(repo, "rev-parse", "dev") == dev_head
    assert "a.txt" in goal_branch.read(state, "demo")["blocked"] and goal_branch.read(state, "demo")["synced"] == [1]
    assert not list((repo / ".orkcraft" / "worktrees").glob("goal-*"))                # the sync worktree is gone
    assert git(repo, "status", "--porcelain") == ""


def finished(g: IdeaGit, state: Path) -> None:
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "b.txt")
    land_task(g, "demo", "k2", "goal/demo", "c.txt")
    goal_branch.ready(state, "demo")


def test_the_goal_goes_into_dev_once_after_a_green_gate_by_fast_forward(repo, state):
    g = IdeaGit(repo)
    finished(g, state)
    commit_in(repo, "other.txt", "dev moved\n")                                        # dev has its own work: merged into the goal first
    got = goal_branch.to_dev(g, state, "demo", "dev")
    assert got["commit"] == git(repo, "rev-parse", "dev") and "edit b.txt" in got["subjects"] and "edit c.txt" in got["subjects"]
    assert (repo / "b.txt").exists() and (repo / "other.txt").exists()                # dev is checked out: its files followed
    assert not git(repo, "branch", "--list", "goal/demo")                              # the branch is gone once it is in dev
    assert goal_branch.read(state, "demo")["merged"] == got["commit"] and not goal_branch.in_use(state, "demo")
    assert git(repo, "log", "--merges", "--format=%s", "-1").startswith("Merge")       # dev was merged into the goal, never the other way round on dev
    with pytest.raises(RuntimeError, match="no branch waiting"):                       # once
        goal_branch.to_dev(g, state, "demo", "dev")
    # a goal sent back to work after dev goes on in dev
    assert goal_branch.begin(g, state, "demo", {"tasks": [{"id": "k1", "state": "merged", "commit": "x"}]}, "dev", 3) == ""


def test_the_gate_runs_on_dev_with_the_goal_and_a_red_one_moves_nothing(repo, state):
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "tests/test_ok.py", "def test_ok():\n    assert False\n")   # the always-test fails with the goal in it
    goal_branch.ready(state, "demo")
    dev = git(repo, "rev-parse", "dev")
    with pytest.raises(goal_branch.GoalRed, match="red on dev with the goal"):
        goal_branch.to_dev(g, state, "demo", "dev")
    assert git(repo, "rev-parse", "dev") == dev and git(repo, "branch", "--list", "goal/demo")
    assert "red" in goal_branch.read(state, "demo")["blocked"]
    row = goal_branch.row(state, "demo")
    assert row["waits_for_dev"] is True and "red" in row["dev_why"] and row["goal_branch"] == "goal/demo"
    # mended on the branch, it goes
    land_task(g, "demo", "k2", "goal/demo", "tests/test_ok.py", "def test_ok():\n    assert True\n")
    assert goal_branch.to_dev(g, state, "demo", "dev")["commit"] == git(repo, "rev-parse", "dev")


def test_a_red_gate_keeps_its_failing_ids_and_files_and_a_green_one_after_clears_them(repo, state):
    """The battle and the gate, stage E: a red on the way to dev keeps what failed and what ran, beside `blocked`."""
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "tests/test_ok.py", "def test_ok():\n    assert False\n")
    goal_branch.ready(state, "demo")
    with pytest.raises(goal_branch.GoalRed):
        goal_branch.to_dev(g, state, "demo", "dev")
    got = goal_branch.read(state, "demo")
    assert got["blocked_kind"] == "red" and got["failing"] == ["tests/test_ok.py::test_ok"] and got["files"] == ["tests/test_ok.py"]
    land_task(g, "demo", "k2", "goal/demo", "tests/test_ok.py", "def test_ok():\n    assert True\n")
    goal_branch.to_dev(g, state, "demo", "dev")
    got = goal_branch.read(state, "demo")
    assert got["failing"] == [] and got["files"] == [] and got["named"] == {} and got["blocked"] == ""


def test_a_dropped_goal_forgets_what_its_red_gate_kept(repo, state):
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "tests/test_ok.py", "def test_ok():\n    assert False\n")
    goal_branch.ready(state, "demo")
    with pytest.raises(goal_branch.GoalRed):
        goal_branch.to_dev(g, state, "demo", "dev")
    goal_branch.drop(g, state, "demo")
    got = goal_branch.read(state, "demo")
    assert got["failing"] == [] and got["files"] == [] and got["named"] == {}


GUARDED_LOG = "# Decisions\n\n## 1. One\nPlain.\n\n## 2. The one the goal's test guards\nPlain.\n\n## 3. The one its passing test names\nPlain.\n"


def test_a_red_gate_keeps_the_decisions_its_tests_name_read_in_the_worktree_it_ran_in(repo, state):
    """Stage N3: the goal's branch adds a failing test naming `decisions §2` and a passing file naming §3, which the checkout (dev) never holds. The red keeps,
    beside `failing` and `files`, what they name as the worktree the gate ran in held them, and that worktree is gone after."""
    commit_in(repo, "docs/decisions.md", GUARDED_LOG)
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "tests/test_guard.py",
              '"""The goal\'s own test."""\n\n\ndef test_guarded():\n    """It holds decisions §2."""\n    assert False\n')
    land_task(g, "demo", "k2", "goal/demo", "tests/test_agrees.py", '"""Guards decisions §3."""\n\n\ndef test_fine():\n    pass\n')
    goal_branch.ready(state, "demo")
    with pytest.raises(goal_branch.GoalRed):
        goal_branch.to_dev(g, state, "demo", "dev")
    assert not (repo / "tests/test_guard.py").exists() and not (repo / "tests/test_agrees.py").exists()      # only the branch holds them
    assert not [ln for ln in git(repo, "worktree", "list").splitlines() if "goal-dev-" in ln]                # the gate's worktree is gone
    got = goal_branch.read(state, "demo")
    assert got["failing"] == ["tests/test_guard.py::test_guarded"]
    assert sorted(got["files"]) == ["tests/test_agrees.py", "tests/test_guard.py", "tests/test_ok.py"]
    assert got["named"] == {"failing": [{"id": "tests/test_guard.py::test_guarded", "file": "tests/test_guard.py", "decisions": [2], "from": "function"}],
                            "files": [2, 3], "titles": {"2": "The one the goal's test guards", "3": "The one its passing test names"}}


def test_the_gate_is_run_on_the_tip_dev_will_become_with_dev_as_its_base(repo, state, monkeypatch):
    g = IdeaGit(repo)
    finished(g, state)
    commit_in(repo, "other.txt", "dev moved\n")
    seen = {}
    real = IdeaGit.gate_run

    def spy(self, path, base, cancel, *a, **k):
        seen.update(tip=git(path, "rev-parse", "HEAD"), base=base, other=(path / "other.txt").exists(), b=(path / "b.txt").exists())
        return real(self, path, base, cancel, *a, **k)
    monkeypatch.setattr(IdeaGit, "gate_run", spy)
    got = goal_branch.to_dev(g, state, "demo", "dev")
    assert seen["tip"] == got["commit"] and seen["other"] and seen["b"] and seen["base"] != seen["tip"]


def test_dev_conflicting_with_the_goal_stops_the_merge_into_dev_and_says_so(repo, state):
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "a.txt", "goal\n")
    goal_branch.ready(state, "demo")
    commit_in(repo, "a.txt", "dev\n")
    dev, head = git(repo, "rev-parse", "dev"), git(repo, "rev-parse", "goal/demo")
    with pytest.raises(goal_branch.GoalConflict, match="a.txt"):
        goal_branch.to_dev(g, state, "demo", "dev")
    assert git(repo, "rev-parse", "dev") == dev and git(repo, "rev-parse", "goal/demo") == head
    assert "a.txt" in goal_branch.row(state, "demo")["dev_why"]


def test_dev_moving_while_the_tests_ran_makes_the_merge_and_the_tests_again(repo, state, monkeypatch):
    g = IdeaGit(repo)
    finished(g, state)
    runs = []
    real = IdeaGit.gate_run

    def moving(self, path, base, cancel, *a, **k):
        runs.append(base)
        if len(runs) == 1:
            commit_in(repo, "late.txt", "dev moved under the tests\n")
        return real(self, path, base, cancel, *a, **k)
    monkeypatch.setattr(IdeaGit, "gate_run", moving)
    got = goal_branch.to_dev(g, state, "demo", "dev")
    assert len(runs) == 2 and runs[0] != runs[1]
    assert (repo / "late.txt").exists() and (repo / "b.txt").exists() and got["commit"] == git(repo, "rev-parse", "dev")


def test_a_project_with_no_tests_waits_for_the_person_unless_told_to_go_untested(repo, state):
    git(repo, "rm", "-rq", "orkcraft.toml", "tests")
    git(repo, "commit", "-m", "no tests at all")
    g = IdeaGit(repo)
    finished(g, state)
    dev = git(repo, "rev-parse", "dev")
    with pytest.raises(goal_branch.GoalRed, match="no tests"):
        goal_branch.to_dev(g, state, "demo", "dev")
    assert git(repo, "rev-parse", "dev") == dev
    assert goal_branch.to_dev(g, state, "demo", "dev", untested=True)["commit"] == git(repo, "rev-parse", "dev")


def test_a_goal_dropped_before_dev_loses_its_branch_and_dev_is_exactly_as_it_was(repo, state):
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "b.txt")
    land_task(g, "demo", "k2", "goal/demo", "c.txt")
    dev, status = git(repo, "rev-parse", "dev"), git(repo, "status", "--porcelain")
    tree = git(repo, "rev-parse", "dev^{tree}")
    assert goal_branch.drop(g, state, "demo") is True
    assert not git(repo, "branch", "--list", "goal/demo")
    assert git(repo, "rev-parse", "dev") == dev and git(repo, "rev-parse", "dev^{tree}") == tree and git(repo, "status", "--porcelain") == status
    assert not (repo / "b.txt").exists()
    assert not goal_branch.in_use(state, "demo") and goal_branch.row(state, "demo") == {}
    assert goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1) == "goal/demo"          # a goal of the same name begins anew


def test_a_goal_dropped_after_dev_leaves_dev_as_it_has_always_been(repo, state):
    g = IdeaGit(repo)
    finished(g, state)
    goal_branch.to_dev(g, state, "demo", "dev")
    dev = git(repo, "rev-parse", "dev")
    assert goal_branch.drop(g, state, "demo") is False
    assert git(repo, "rev-parse", "dev") == dev and (repo / "b.txt").exists()


def test_the_row_says_what_waits_for_dev_and_why(repo, state):
    g = IdeaGit(repo)
    assert goal_branch.row(state, "demo") == {}
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    assert goal_branch.row(state, "demo") == {"goal_branch": "goal/demo", "waits_for_dev": False, "dev_why": "", "dev_blocked": False, "dev_kind": ""}
    goal_branch.ready(state, "demo")
    assert goal_branch.row(state, "demo")["waits_for_dev"] is True and goal_branch.row(state, "demo")["dev_why"] == ""
    assert "off" in goal_branch.row(state, "demo", review=True)["dev_why"]
    goal_branch.ready(state, "demo", False)
    assert goal_branch.row(state, "demo")["waits_for_dev"] is False


def test_the_branches_the_person_is_offered_leave_goal_branches_out(repo, state):
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "b.txt")
    assert g.branches() == ["dev"]


def test_the_boards_drop_deletes_the_branch_and_never_stops_on_git(repo, state):
    from types import SimpleNamespace

    from orkboard.gui.ideas_gate import GateMixin
    g = IdeaGit(repo)
    goal_branch.begin(g, state, "demo", {"tasks": []}, "dev", 1)
    land_task(g, "demo", "k1", "goal/demo", "b.txt")
    dev = git(repo, "rev-parse", "dev")
    me = SimpleNamespace(host=SimpleNamespace(repo_root=repo), state_dir=state)
    GateMixin._drop_branch(me, "demo")
    assert not git(repo, "branch", "--list", "goal/demo") and git(repo, "rev-parse", "dev") == dev
    GateMixin._drop_branch(SimpleNamespace(host=SimpleNamespace(repo_root=repo / "nowhere"), state_dir=state), "demo")      # a folder git cannot read: no raise


def test_the_command_refuses_in_words_and_reads_untested_as_a_literal_true():
    from types import SimpleNamespace

    from orkboard.core.idea_review import RunnerError
    from orkboard.gui.ideas_args import IdeasError
    from orkboard.gui.ideas_gate import GateMixin
    seen = []

    class Runner:
        def goal_to_dev(self, slug, untested=False):
            seen.append((slug, untested))
            if slug == "red":
                raise RunnerError("The tests are red on dev with the goal: x")
            return {"commit": "c", "subjects": [], "note": "", "branch": "goal/" + slug}
    me = SimpleNamespace(runner=lambda need=False: Runner(), changed=lambda slug: None)
    with pytest.raises(IdeasError, match="red on dev"):
        GateMixin.goal_to_dev(me, {"idea": "red"})
    assert GateMixin.goal_to_dev(me, {"idea": "ok", "untested": "yes"})["ok"] is True
    GateMixin.goal_to_dev(me, {"idea": "ok", "untested": True})
    assert seen == [("red", False), ("ok", False), ("ok", True)]


def test_the_goals_file_is_plain_json_next_to_its_state(repo, state):
    goal_branch.update(state, "demo", branch="goal/demo")
    assert json.loads((state / "ideas" / "demo" / "goal_branch.json").read_text())["branch"] == "goal/demo"
    assert idea_git.IdeaGit  # the module of the fixture
    assert isinstance(threading.Event(), threading.Event)
