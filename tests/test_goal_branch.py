"""A goal's own branch (docs/specs/168 F1, decisions §283.26): realm/goal_branch.py on a real temporary repository."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from orkboard.realm import goal_branch
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


GUARDED_LOG = "# Decisions\n\n## 1. One\nPlain.\n\n## 2. The one the goal's test guards\nPlain.\n\n## 3. The one its passing test names\nPlain.\n"


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


