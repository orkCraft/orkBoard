"""The lease (realm/board_lease.py, spec 137 B.1, decisions §244.2): taken by a push without force that decides, renewed, given back; the clock's
skew; a refused push read again once. Two clones of one bare repository, no network."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

import pytest

from orkboard.realm import board_branch as bb, board_lease as bl, event_log
from tests.test_board_branch import WIKI, git, make_clone, make_origin, put, seed_board

T0 = dt.datetime(2026, 11, 4, 12, 0, 0, tzinfo=dt.timezone.utc)
CFG = bb.BoardConfig()


def sec(n: float) -> dt.timedelta:
    return dt.timedelta(seconds=n)


class Host:
    """One computer: a clone of the repository with a state folder of its own."""

    def __init__(self, origin: Path, where: Path, me: str) -> None:
        self.root = make_clone(origin, where)
        self.state = self.root / ".orkcraft"
        self.me = me

    def take(self, now: dt.datetime, kind: str = "computer", **kw) -> dict:
        return bl.take(self.root, self.state, CFG, self.me, kind, now, wiki_rel=WIKI, **kw)

    def renew(self, now: dt.datetime, kind: str = "computer", **kw) -> dict:
        return bl.renew(self.root, self.state, CFG, self.me, kind, now, wiki_rel=WIKI, **kw)

    def give_back(self, now: dt.datetime, kind: str = "computer", **kw) -> dict:
        return bl.give_back(self.root, self.state, CFG, self.me, kind, now, wiki_rel=WIKI, **kw)

    def remote_lease(self) -> dict:
        got = bb.fetch(self.root, CFG)
        return json.loads(bb.files_at(self.root, bb.REMOTE_REF)[bb.LEASE]) if got["tip"] else {}

    def events(self) -> list[str]:
        return [r["event"] for r in event_log.read(self.root)]


@pytest.fixture
def world(tmp_path: Path):
    origin = make_origin(tmp_path)
    return origin, Host(origin, tmp_path / "a", "alpha"), Host(origin, tmp_path / "b", "beta")


def count(origin: Path) -> int:
    return int(git(origin, "rev-list", "--count", "refs/heads/orkboard/board").strip())


def test_take_on_an_empty_remote_makes_the_branch_from_this_board_with_no_parent(world):
    origin, a, _ = world
    seed_board(a.state)
    got = a.take(T0)
    assert got["held"] is True
    assert count(origin) == 1 and git(origin, "log", "-1", "--format=%P", "refs/heads/orkboard/board").strip() == ""
    on = git(origin, "ls-tree", "-r", "--name-only", "refs/heads/orkboard/board").split()
    assert "lease.json" in on and "ideas/dark-mode/state.json" in on and f"board/{WIKI}/pages/ideas/dark-mode.md" in on
    lease = a.remote_lease()
    assert lease["v"] == 1 and lease["by"] == "alpha" and lease["kind"] == "computer"
    assert dt.datetime.fromisoformat(lease["until"]) == T0 + sec(bl.LEASE_S) and dt.datetime.fromisoformat(lease["at"]) == T0
    assert "board_taken" in a.events()


def test_held_by_another_refuses_and_says_who(world):
    origin, a, b = world
    seed_board(a.state)
    assert a.take(T0)["held"]
    got = b.take(T0 + sec(30))
    assert got["held"] is False and got["by"] == "alpha" and got["kind"] == "computer"
    assert dt.datetime.fromisoformat(got["until"]) == T0 + sec(bl.LEASE_S)
    assert count(origin) == 1                                   # nothing was pushed
    assert "board_refused" in b.events() and "board_taken" not in b.events()


def test_renew_moves_until_on_and_pushes_what_changed(world):
    origin, a, _ = world
    seed_board(a.state)
    a.take(T0)
    put(a.state, "ideas/dark-mode/state.json", json.dumps({"state": "working"}))
    got = a.renew(T0 + sec(bl.RENEW_S))
    assert got["held"] and got["pushed"] and count(origin) == 2
    assert dt.datetime.fromisoformat(a.remote_lease()["until"]) == T0 + sec(bl.RENEW_S + bl.LEASE_S)
    assert json.loads(git(origin, "show", "refs/heads/orkboard/board:ideas/dark-mode/state.json"))["state"] == "working"
    assert "board_pushed" in a.events()


def test_give_back_frees_the_lease_at_once(world):
    origin, a, b = world
    seed_board(a.state)
    a.take(T0)
    put(a.state, "goals/tech/state.json", '{"last": 1}')
    got = a.give_back(T0 + sec(20))
    assert got["given"] is True and "board_given_back" in a.events()
    lease = a.remote_lease()
    assert dt.datetime.fromisoformat(lease["until"]) == T0 + sec(20) and lease["back"] is True
    assert json.loads(git(origin, "show", "refs/heads/orkboard/board:goals/tech/state.json")) == {"last": 1}       # pushed with the Board
    assert b.take(T0 + sec(21))["held"] is True                                                                     # not after the skew: at once


def test_a_refused_push_is_read_again_once_and_the_second_try_takes(world, monkeypatch):
    origin, a, b = world
    seed_board(a.state)
    a.take(T0)
    a.give_back(T0 + sec(5))
    # b's take is refused once: a pushes (a free lease again) between b's read and b's push
    real, calls = bb.push, []

    def racing(root, config, commit, run=subprocess.run):
        calls.append(commit)
        if len(calls) == 1:
            bl.renew(a.root, a.state, CFG, "alpha", "computer", T0 + sec(7), wiki_rel=WIKI, back=True)
        return real(root, config, commit, run)
    monkeypatch.setattr(bb, "push", racing)
    got = b.take(T0 + sec(10))
    assert got["held"] is True and len(calls) == 3                       # alpha's own push in between, b's refused, b's second try went through
    assert b.remote_lease()["by"] == "beta"


def test_offline_is_a_result_not_an_exception(world, tmp_path):
    _, a, _ = world
    seed_board(a.state)
    git(a.root, "remote", "set-url", "origin", str(tmp_path / "nowhere.git"))
    got = a.take(T0)
    assert got["held"] is False and got["offline"] is True and got["why"]
    assert bl.read_sync(a.state) == {}
    got = a.renew(T0)
    assert got["held"] is True and got["offline"] is True
    assert a.give_back(T0)["given"] is False

