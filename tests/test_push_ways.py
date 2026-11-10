"""Spec 168 F3 (decisions §283.28, §283.31): `push` takes three ways, *no*, *main only* and *dev and main*, and the old boolean reads as it pushed: `True` is dev and main (a landing in dev was pushed, and so was
main after To main), `False` is no. The setting is kept as a boolean where it can be, so Orkline's frozen copy and an older file read it the same."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orkboard import settings
from orkboard.gui.board_host import Orkboard
from tests.test_goal_main import git, goal, task, to_main
from tests.test_goal_main import host, repo  # noqa: F401  (fixtures)


def test_the_old_boolean_reads_as_it_pushed_and_the_three_ways_read_as_themselves():
    assert settings.push_way(True) == "both" and settings.push_way(False) == "no", "true was dev and main, false nothing"
    assert [settings.push_way(v) for v in ("no", "main", "both")] == ["no", "main", "both"]
    assert [settings.push_way(v) for v in (None, "", "yes", 1, [])] == ["no"] * 5, "anything else pushes nothing"
    assert (settings.pushes_dev(True), settings.pushes_main(True)) == (True, True)
    assert (settings.pushes_dev("main"), settings.pushes_main("main")) == (False, True), "main only leaves dev here"
    assert (settings.pushes_dev(False), settings.pushes_main(False)) == (False, False)


def test_a_way_is_kept_as_a_boolean_where_it_can_be_and_a_bad_one_is_the_default():
    assert settings.PUSH_WAYS == ("no", "main", "both")
    kept = {v: settings.clean_ideas({"push": v})["push"] for v in (True, False, "no", "main", "both", "yes", 3, None)}
    assert kept == {True: True, False: False, "no": False, "main": "main", "both": True, "yes": False, 3: False, None: False}
    assert settings.clean_ideas({})["push"] is False and settings.IDEAS["push"] is False


def test_into_takes_the_three_ways_and_the_old_boolean(host, repo):  # noqa: F811
    seen = {}
    for given in (True, "main", "no", "both", False):
        host.command("ideas.into", {"push": given})
        seen[given] = (host.command("ideas.review_list")["push_way"], host.command("ideas.review_list")["push"])
    assert seen == {True: ("both", True), "main": ("main", True), "no": ("no", False), "both": ("both", True), False: ("no", False)}
    with pytest.raises(Exception, match="branch is missing"):
        host.command("ideas.into", {"push": "sometimes"})


def test_the_runner_pushes_a_landing_in_dev_only_for_dev_and_main(host, repo):  # noqa: F811
    runner = host.ideas.runner(need=True)
    for way, dev in (("no", False), ("main", False), ("both", True), (True, True), (False, False)):
        host.command("ideas.into", {"push": way})
        assert runner._pushes_into("dev") is dev, way
        assert runner._pushes_into("goal/x") is False, "a goal's own branch is never pushed"


def pushed(repo: Path, remote: Path, branch: str) -> bool:
    return git(remote, "rev-parse", branch) == git(repo, "rev-parse", branch)


@pytest.mark.parametrize("way,main_pushed", [("no", False), ("main", True), ("both", True), (True, True), (False, False)])
def test_to_main_pushes_main_for_main_only_and_for_dev_and_main(host, repo, tmp_path, way, main_pushed):  # noqa: F811
    remote = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "origin", "main")
    lobby = goal(host, "Lobby")
    task(host, repo, lobby, "k1", {"lobby.ts": "l\n"})
    host.command("ideas.into", {"push": way})
    got = to_main(host, lobby)
    assert pushed(repo, remote, "main") is main_pushed
    assert got["note"] == ""
    assert not git(remote, "branch", "--list", "dev"), "dev is not pushed by To main"
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.mark.parametrize("way,dev_pushed", [("no", False), ("main", False), ("both", True), (True, True)])
def test_a_goal_into_dev_pushes_dev_only_for_dev_and_main(host, repo, tmp_path, way, dev_pushed):  # noqa: F811
    from orkboard.realm import goal_branch
    from orkboard.realm.idea_git import IdeaGit
    from tests.test_goal_main_branch import land
    remote = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "origin", "main")
    lobby = goal(host, "Lobby")
    branch = goal_branch.begin(IdeaGit(repo), host.ideas.state_dir, lobby, {"tasks": []}, "dev", 1)
    land(host, repo, lobby, "k1", branch, {"lobby.ts": "l\n"})
    goal_branch.ready(host.ideas.state_dir, lobby)
    host.command("ideas.into", {"push": way})
    got = host.command("ideas.goal_to_dev", {"idea": lobby, "untested": True})
    assert bool(git(remote, "branch", "--list", "dev")) is dev_pushed
    assert (git(remote, "rev-parse", "dev") == got["commit"]) if dev_pushed else True
