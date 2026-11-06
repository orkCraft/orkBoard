"""Taking a goal (realm/goal_take.py, gui/goal_take_host.py; spec 151 D, decisions §255.8): two clones of one bare repository, no network, no model.
One takes and the other is refused; past `until` it is taken; two goals at once both get theirs; two on one goal, one wins; give back frees; no remote,
taken; and Orkboard does not start a goal held by a tool, nor run anything of D before the rules are written."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from orkboard.gui import goal_take_host as gth
from orkboard.gui.ideas_args import IdeasError
from orkboard.gui.ideas_board import BoardMixin
from orkboard.gui.ideas_route import RouteMixin
from orkboard.realm import board_branch as bb, event_log, goal_route, goal_take as gt, ideas
from tests.test_board_branch import git, make_clone, make_origin

T0 = dt.datetime(2026, 11, 6, 12, 0, 0, tzinfo=dt.timezone.utc)
RULES = "# Rules\n<!-- orkboard:begin schema=1 hash=0 -->\nthe rules\n<!-- orkboard:end -->\n"


def hrs(n: float) -> dt.timedelta:
    return dt.timedelta(hours=n)


@pytest.fixture
def world(tmp_path: Path):
    origin = make_origin(tmp_path)
    return origin, make_clone(origin, tmp_path / "a"), make_clone(origin, tmp_path / "b")


def remote_file(origin: Path, slug: str) -> dict:
    return json.loads(git(origin, "show", f"refs/heads/{gt.BRANCH}:{slug}.json"))


def commits(origin: Path) -> int:
    return int(git(origin, "rev-list", "--count", f"refs/heads/{gt.BRANCH}").strip())


def test_one_takes_and_the_other_is_refused_and_the_file_is_on_the_branch(world):
    origin, a, b = world
    got = gt.take(a, "login", "alpha", gt.TOOL, T0)
    assert got == {"taken": True, "until": (T0 + hrs(1)).isoformat(timespec="seconds")}
    assert remote_file(origin, "login") == {"v": 1, "by": "alpha", "kind": "tool", "until": got["until"], "at": T0.isoformat(timespec="seconds")}
    refused = gt.take(b, "login", "beta", gt.ORKBOARD, T0 + dt.timedelta(minutes=5))
    assert refused == {"taken": False, "by": "alpha", "kind": "tool", "until": got["until"]}
    assert commits(origin) == 1
    assert gt.held(b, "login", T0)["by"] == "alpha"
    assert [r["event"] for r in event_log.read(b)] == [event_log.GOAL_TAKE_REFUSED]
    assert event_log.read(a)[0]["event"] == event_log.GOAL_TAKEN


def test_the_same_holder_takes_again_and_renew_moves_until_on(world):
    origin, a, _ = world
    gt.take(a, "g", "alpha", gt.ORKBOARD, T0)
    got = gt.renew(a, "g", "alpha", gt.ORKBOARD, T0 + hrs(0.5))
    assert got["taken"] and remote_file(origin, "g")["until"] == (T0 + hrs(1.5)).isoformat(timespec="seconds")
    assert [r["event"] for r in event_log.read(a)] == [event_log.GOAL_TAKEN]      # a renew says nothing of itself


def test_past_until_and_its_skew_the_goal_is_taken_by_the_other(world):
    _, a, b = world
    gt.take(a, "g", "alpha", gt.TOOL, T0)
    assert not gt.take(b, "g", "beta", gt.ORKBOARD, T0 + hrs(1) + dt.timedelta(seconds=gt.SKEW_S - 5))["taken"]       # the skew: still held
    assert gt.take(b, "g", "beta", gt.ORKBOARD, T0 + hrs(1) + dt.timedelta(seconds=gt.SKEW_S + 5))["taken"]
    assert gt.held(a, "g", T0 + hrs(1.1))["by"] == "beta"


def test_two_clones_taking_two_goals_at_once_both_get_theirs_and_one_commits_again(world, monkeypatch):
    origin, a, b = world
    gt.take(a, "first", "alpha", gt.TOOL, T0)
    real, pushes = gt._read, []

    def stale_for_b(root, remote, run):
        if root == b and not pushes:               # b read the branch before a's second goal: its first push is refused
            out = real(root, remote, run)
            gt.take(a, "second", "alpha", gt.TOOL, T0)
            pushes.append(1)
            return out
        return real(root, remote, run)
    monkeypatch.setattr(gt, "_read", stale_for_b)
    assert gt.take(b, "third", "beta", gt.ORKBOARD, T0)["taken"]
    assert pushes and set(gt.read_all(a, T0)) == {"first", "second", "third"}
    assert commits(origin) == 3
    assert remote_file(origin, "third")["by"] == "beta" and remote_file(origin, "second")["by"] == "alpha"


def test_two_on_one_goal_the_push_decides_and_the_loser_is_told_who(world, monkeypatch):
    origin, a, b = world
    real, once = gt._read, []

    def raced(root, remote, run):
        out = real(root, remote, run)
        if root == b and not once:                 # b has read an empty branch; a takes the goal before b's push
            once.append(1)
            gt.take(a, "g", "alpha", gt.TOOL, T0)
        return out
    monkeypatch.setattr(gt, "_read", raced)
    got = gt.take(b, "g", "beta", gt.ORKBOARD, T0)
    assert got["taken"] is False and got["by"] == "alpha"
    assert remote_file(origin, "g")["by"] == "alpha"


def test_give_back_frees_the_goal_at_once(world):
    origin, a, b = world
    gt.take(a, "g", "alpha", gt.TOOL, T0)
    assert gt.give_back(b, "g", "beta", T0)["given"] is False                       # not b's to give
    assert gt.give_back(a, "g", "alpha", T0 + dt.timedelta(minutes=1), kind=gt.TOOL) == {"given": True}
    assert remote_file(origin, "g")["back"] is True
    assert gt.held(b, "g", T0 + dt.timedelta(minutes=1)) is None
    assert gt.take(b, "g", "beta", gt.ORKBOARD, T0 + dt.timedelta(minutes=1))["taken"]
    assert gt.give_back(a, "other", "alpha", T0)["given"] is True                   # nothing held: nothing written
    assert event_log.GOAL_GIVEN_BACK in [r["event"] for r in event_log.read(a)]


def test_a_repository_with_no_remote_takes_locally_and_always(tmp_path):
    root = tmp_path / "solo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    assert gt.take(root, "g", "alpha", gt.TOOL, T0) == {"taken": True, "until": (T0 + hrs(1)).isoformat(timespec="seconds"), "local": True}
    assert gt.take(root, "g", "beta", gt.ORKBOARD, T0)["taken"]
    assert gt.read_all(root, T0) == {} and gt.held(root, "g", T0) is None


def test_an_unreachable_remote_is_a_result_in_words_and_the_host_goes_on(world):
    _, a, _ = world
    git(a, "remote", "set-url", "origin", str(a / "nowhere.git"))
    got = gt.take(a, "g", "alpha", gt.ORKBOARD, T0)
    assert got["taken"] and got["offline"] and got["why"]
    assert gt.read_all(a, T0) is None


def test_the_first_take_makes_the_branch_without_touching_the_working_tree(world):
    origin, a, _ = world
    before = git(a, "status", "--porcelain"), git(a, "rev-parse", "HEAD")
    gt.take(a, "g", "alpha", gt.TOOL, T0)
    assert (git(a, "status", "--porcelain"), git(a, "rev-parse", "HEAD")) == before
    assert git(origin, "ls-tree", "--name-only", f"refs/heads/{gt.BRANCH}").split() == ["g.json"]
    with pytest.raises(subprocess.CalledProcessError):
        git(origin, "rev-parse", f"refs/heads/{gt.BRANCH}^")                       # no parent: its own history


# -- the host -------------------------------------------------------------------------------------------------------

class FakeProject:
    def __init__(self, root: Path) -> None:
        self.root, self.path = root, str(root)
        self.state_dir = root / ".orkcraft"
        self.ideas = SimpleNamespace(state_dir=self.state_dir, root=lambda make=True: root / "board", autostart=lambda slug: self.autostarted.append(slug) or "")
        self.autostarted: list[str] = []


@pytest.fixture(autouse=True)
def clean_cache(world):
    yield
    for r in world[1:]:
        gt.cache_clear(r)


def host_for(p: FakeProject, running: set[str]) -> gth.GoalTakeHost:
    h = gth.GoalTakeHost(SimpleNamespace(projects=SimpleNamespace(open_ones=[p]), demo=False), "Orkboard on test")
    h.running = lambda _p: set(running)            # type: ignore[method-assign]
    return h


def test_orkboard_takes_what_it_runs_renews_it_and_gives_back_what_waits_for_the_person(world):
    origin, a, _ = world
    (a / "AGENTS.md").write_text(RULES)
    p, running = FakeProject(a), {"one", "two"}
    h = host_for(p, running)
    st = gth._State()
    h.run(p, st, T0, mono=0.0)
    assert set(gt.read_all(a, T0)) == {"one", "two"} and remote_file(origin, "one")["kind"] == "orkboard"
    h.run(p, st, T0 + hrs(0.5), mono=1.0)                                           # within FETCH_S: no second fetch
    assert remote_file(origin, "one")["at"] == T0.isoformat(timespec="seconds")
    h.run(p, st, T0 + hrs(0.5), mono=100.0)                                         # half an hour left: not renewed, nothing pushed
    assert remote_file(origin, "one")["at"] == T0.isoformat(timespec="seconds")
    running.discard("two")                                                          # it now waits for the person
    h.run(p, st, T0 + hrs(0.75), mono=200.0)                                        # a quarter of an hour left: renewed
    assert set(gt.read_all(a, T0 + hrs(0.75))) == {"one"} and remote_file(origin, "one")["until"] == (T0 + hrs(1.75)).isoformat(timespec="seconds")
    running.clear()
    h.run(p, st, T0 + hrs(0.8), mono=300.0)
    assert gt.read_all(a, T0 + hrs(0.8)) == {}
    h.close()


def test_orkboard_does_not_take_a_goal_a_tool_holds_and_tries_it_again_when_it_is_free(world):
    origin, a, b = world
    (a / "AGENTS.md").write_text(RULES)
    gt.take(b, "g", "claude-code", gt.TOOL, T0)
    p = FakeProject(a)
    h, st = host_for(p, {"g"}), gth._State()
    h.run(p, st, T0 + dt.timedelta(minutes=1), mono=0.0)
    assert remote_file(origin, "g")["by"] == "claude-code" and not st.mine
    hold = gt.blocked(a, "g", T0 + dt.timedelta(minutes=1))
    assert hold["by"] == "claude-code" and gt.line_of(hold).startswith("Taken by claude-code until ")
    gt.give_back(b, "g", "claude-code", T0 + dt.timedelta(minutes=2), kind=gt.TOOL)
    h.run(p, st, T0 + dt.timedelta(minutes=3), mono=100.0)
    assert gt.blocked(a, "g", T0 + dt.timedelta(minutes=3)) is None and p.autostarted == ["g"] and st.mine == {"g"}


def test_the_start_points_read_only_the_cache_and_a_goal_held_by_a_tool_is_not_started(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    root.mkdir()
    gt.cache_set(root, {"g": {"by": "cursor", "kind": "tool", "until": (dt.datetime.now(dt.timezone.utc) + hrs(1)).isoformat()}}, "Orkboard on test")
    monkeypatch.setattr(ideas, "plan", lambda *a, **k: {"tasks": []})
    monkeypatch.setattr(gt.subprocess, "run", lambda *a, **k: pytest.fail("a start point reached for the network"), raising=False)
    me = SimpleNamespace(host=SimpleNamespace(repo_root=root), state_dir=root / ".orkcraft",
                         root=lambda make=True: root / "board", settings_now=lambda: {})
    with pytest.raises(IdeasError, match="Taken by cursor until "):
        BoardMixin.pass_plan(me, "g", "auto")
    me._routed = lambda args: ("g", {"route": "tech", "route_how": {}})
    monkeypatch.setattr(goal_route, "cost_of", lambda *a, **k: "")
    with pytest.raises(IdeasError, match="Taken by cursor until "):
        RouteMixin.route_talk(me, {"idea": "g"})
    assert not (root / ".orkcraft").exists()                                         # nothing was saved
    gt.cache_clear(root)
    monkeypatch.setattr(ideas, "plan", lambda *a, **k: None)
    with pytest.raises(IdeasError, match="no plan yet"):
        BoardMixin.pass_plan(me, "g", "auto")                                        # not held: it goes on to its own refusal


def test_a_hold_of_orkboards_own_blocks_nothing_and_a_run_out_one_neither(tmp_path):
    gt.cache_set(tmp_path, {"mine": {"by": "me", "kind": "orkboard", "until": (T0 + hrs(1)).isoformat()},
                            "old": {"by": "tool", "kind": "tool", "until": (T0 + hrs(1)).isoformat()}}, "me")
    assert gt.blocked(tmp_path, "mine", T0) is None
    assert gt.blocked(tmp_path, "old", T0)["by"] == "tool" and gt.refusal(tmp_path, "old", T0).startswith("Taken by tool until ")
    assert gt.refusal(tmp_path, "old", T0 + hrs(2)) == "" and gt.refusal(tmp_path, "unknown", T0) == ""
    gt.cache_clear(tmp_path)


def test_without_the_rules_nothing_of_d_runs(world, monkeypatch):
    origin, a, _ = world
    assert not gt.rules_written(a)
    p = FakeProject(a)
    h = host_for(p, {"g"})
    monkeypatch.setattr(gt, "read_all", lambda *a, **k: pytest.fail("the remote was asked before the rules were written"))
    st = gth._State()
    h.run(p, st, T0, mono=0.0)
    h.tick()
    assert st.thread is None and h._states == {} and gt.blocked(a, "g", T0) is None
    assert subprocess.run(["git", "ls-remote", str(origin), gt.BRANCH], capture_output=True, text=True).stdout == ""
    (a / "AGENTS.md").write_text("# Mine\n")
    assert not gt.rules_written(a)
    (a / "AGENTS.md").write_text(RULES)
    assert gt.rules_written(a)
