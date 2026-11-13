"""Two hosts on one bare repository (spec 137 B.3, decisions §244.2–4): the computer's tick (gui/board_sync.py) on two clones, each with its own
state folder. One holds, the other reads and refuses to write; the holder gives back and the other takes and shows the same goals and pages;
a host offline loses nothing (what it changed is kept aside); the inbox's goal is laid once, by the holder; with no `[board]` nothing runs."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from orkboard.core.idea_keeper import IdeaKeeper
from orkboard.gui import board_sync as bs
from orkboard.gui.phone_journal import PhoneJournal
from orkboard.realm import board_branch as bb, board_lease as bl, event_log, remote_inbox as ri, remote_journal as rj
from tests.test_board_branch import WIKI, FakeTree, git, make_clone, make_origin, put, seed_board
from tests.test_remote_inbox import Board, drop, goal_file

T0 = dt.datetime(2026, 11, 4, 12, 0, 0, tzinfo=dt.timezone.utc)
TOML = '[board]\nremote = "origin"\nbranch = "orkboard/board"\n[journal]\ninbox = "orkboard/inbox"\n'


def sec(n: float) -> dt.timedelta:
    return dt.timedelta(seconds=n)


class FakeIdeas:
    """What the tick asks of a project's Board (gui/ideas.py): its state folder, its tree, the held words."""

    def __init__(self, state: Path) -> None:
        self.state_dir, self.tree, self.board_held, self.published = state, FakeTree(), "", 0

    def root(self, make: bool = True) -> Path:
        return self.state_dir / "board" / WIKI

    def wiki(self) -> Path:
        return self.state_dir.parent / WIKI

    def _tree(self, wiki: Path):
        return self.tree

    def tree_flush(self, now: float = 0.0, force: bool = False) -> None:
        pass

    def _publish(self, slug: str) -> None:
        self.published += 1


class Computer:
    """A host: a clone of the repository, its Board, its tick."""

    def __init__(self, origin: Path, where: Path, me: str) -> None:
        self.root = make_clone(origin, where)
        (self.root / "orkcraft.toml").write_text(TOML)
        self.state = self.root / ".orkcraft"
        self.me, self.origin = me, origin
        self.ideas = FakeIdeas(self.state)
        self.toasts: list[str] = []
        self.path = str(self.root)
        self.host = SimpleNamespace(demo=False, projects=SimpleNamespace(open_ones=[self]), phone_journal=None)
        self.sync = bs.BoardSync(self.host, me=me)
        self.host.board_sync = self.sync
        self.st = self.sync._state(self)

    def toast(self, message: str, title: str = "", severity: str = "information") -> None:
        self.toasts.append(message)

    def tick(self, now: dt.datetime, mono: float) -> None:
        self.sync.run(self, self.st, now, mono)

    def remote_lease(self) -> dict:
        return json.loads(git(self.origin, "show", "refs/heads/orkboard/board:lease.json"))

    def events(self) -> list[str]:
        return [r["event"] for r in event_log.read(self.root)]


@pytest.fixture
def world(tmp_path: Path):
    origin = make_origin(tmp_path)
    return origin, Computer(origin, tmp_path / "a", "alpha"), Computer(origin, tmp_path / "b", "beta")


def test_one_holds_the_other_reads_and_refuses_to_write(world):
    origin, a, b = world
    seed_board(a.state)
    a.tick(T0, 0)
    b.tick(T0 + sec(5), 0)
    assert a.sync.holds(a) and not b.sync.holds(b)
    assert b.sync.status(b)["board_held"]["by"] == "alpha" and b.sync.status(b)["board_held"]["kind"] == "computer"
    assert a.sync.status(a) == {}
    assert b.ideas.board_held and "gives it back" in b.ideas.board_held
    # beta read the Board from the branch's files, as a reader
    assert json.loads((b.state / "ideas/dark-mode/state.json").read_text())["state"] == "ready"
    assert (b.state / f"board/{WIKI}/pages/ideas/dark-mode.md").read_text() == "# Dark mode\n"
    # nothing that writes runs: the keeper refuses in the words it was given
    keeper = IdeaKeeper(b.root, b.state, lambda: b.root, lambda: {})
    keeper.board_held = lambda: b.ideas.board_held
    assert keeper._may_run() == b.ideas.board_held
    assert keeper.tick() is False
    from orkboard.core.idea_runner import IdeaRunner
    runner = IdeaRunner(b.root, b.state, SimpleNamespace(), None)
    runner.board_held = lambda: b.ideas.board_held
    with pytest.raises(RuntimeError, match="gives it back"):
        runner.start("dark-mode")
    assert runner.tick() is None


def test_the_holder_gives_back_and_the_other_takes_and_shows_the_same_board(world):
    origin, a, b = world
    seed_board(a.state)
    a.tick(T0, 0)
    b.tick(T0 + sec(5), 0)
    assert not b.sync.holds(b)
    put(a.state, "ideas/new-goal/state.json", json.dumps({"state": "raw"}))
    put(a.state, f"board/{WIKI}/pages/ideas/new-goal.md", "# New goal\n")
    a.sync.close(T0 + sec(60))                                           # the host's quit
    assert not a.sync.holds(a) and "board_given_back" in a.events() and a.remote_lease()["back"] is True
    b.tick(T0 + sec(70), bl.RENEW_S + 1)                                  # beta's next try
    assert b.sync.holds(b) and b.ideas.board_held == "" and b.sync.status(b) == {}
    for rel in ("ideas/dark-mode/state.json", "ideas/new-goal/state.json", f"board/{WIKI}/pages/ideas/new-goal.md", f"board/{WIKI}/pages/tracks/tech.md"):
        assert (b.state / rel).read_bytes() == (a.state / rel).read_bytes()
    assert b.ideas.tree.flushed and "taken from alpha" in b.ideas.tree.flushed[-1][1]
    assert b.remote_lease()["by"] == "beta"


def test_a_host_offline_keeps_working_and_what_it_changed_is_kept_aside_when_another_took_the_board(world, tmp_path):
    origin, a, b = world
    seed_board(a.state)
    a.tick(T0, 0)
    good = git(a.root, "remote", "get-url", "origin").strip()
    git(a.root, "remote", "set-url", "origin", str(tmp_path / "nowhere.git"))             # alpha is offline
    put(a.state, "ideas/dark-mode/state.json", json.dumps({"state": "alpha-offline"}))
    put(a.state, "ideas/alpha-only/state.json", json.dumps({"state": "raw"}))
    a.tick(T0 + sec(bl.RENEW_S + 1), bl.RENEW_S + 1)                                     # a renew that cannot push
    assert a.sync.holds(a) and a.st.offline                                              # it goes on working
    # the lease runs out; beta takes the Board and works
    late = T0 + sec(bl.LEASE_S + bl.SKEW_S + 120)
    b.tick(late, 0)
    assert b.sync.holds(b) and (b.state / "ideas/dark-mode/state.json").read_text().count("ready")
    put(b.state, "ideas/dark-mode/state.json", json.dumps({"state": "beta-online"}))
    b.tick(late + sec(bl.RENEW_S + 1), bl.RENEW_S + 1)
    # alpha is back online
    git(a.root, "remote", "set-url", "origin", good)
    a.tick(late + sec(bl.RENEW_S + 30), bl.RENEW_S + 300)
    assert not a.sync.holds(a)
    aside = sorted((a.state / bl.ASIDE_DIR).iterdir())
    assert len(aside) == 1
    assert json.loads((aside[0] / "ideas/dark-mode/state.json").read_text())["state"] == "alpha-offline"
    assert (aside[0] / "ideas/alpha-only/state.json").is_file()
    assert json.loads((a.state / "ideas/dark-mode/state.json").read_text())["state"] == "beta-online"        # the branch's Board, unpacked
    assert not (a.state / "ideas/alpha-only/state.json").exists()
    assert a.toasts and "kept aside" in a.toasts[-1] and "Another worker had the Board while you were offline" in a.toasts[-1]
    assert a.sync.status(a)["board_aside"]["path"] == str(aside[0])
    assert "board_aside" in a.events()
    assert b.remote_lease()["by"] == "beta"                                              # nothing of alpha's was pushed over beta's


def test_a_host_back_online_whose_push_is_still_the_tip_pushes_and_renews(world, tmp_path):
    origin, a, _ = world
    seed_board(a.state)
    a.tick(T0, 0)
    good = git(a.root, "remote", "get-url", "origin").strip()
    git(a.root, "remote", "set-url", "origin", str(tmp_path / "nowhere.git"))
    put(a.state, "ideas/dark-mode/state.json", json.dumps({"state": "offline-work"}))
    a.tick(T0 + sec(bl.RENEW_S + 1), bl.RENEW_S + 1)
    git(a.root, "remote", "set-url", "origin", good)
    a.tick(T0 + sec(2 * bl.RENEW_S + 2), 2 * bl.RENEW_S + 2)
    assert a.sync.holds(a) and not (a.state / bl.ASIDE_DIR).exists()
    assert json.loads(git(origin, "show", "refs/heads/orkboard/board:ideas/dark-mode/state.json"))["state"] == "offline-work"


# -- the inbox is the holder's (B.2.4) ------------------------------------------------------------------------------

def test_the_inbox_goal_is_laid_once_and_by_the_holder(world, tmp_path):
    origin, a, b = world
    phone = make_clone(origin, tmp_path / "phone")
    seed_board(a.state)
    a.tick(T0, 0)
    b.tick(T0 + sec(5), 0)
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": json.dumps(goal_file("01JC0000000000000001", party="tech"))})
    boards = {"alpha": Board(), "beta": Board()}
    pjs = {}
    for c in (a, b):
        pj = PhoneJournal(c.host)
        pj.context = lambda p: ri.Context(parties={"tech"}, types=lambda x: {"bug"})
        pj.lay = lambda p, c=c: boards[c.me].lay
        pj.find = lambda p, c=c: boards[c.me].find
        pjs[c.me] = pj
        c.host.phone_journal = pj
    config = rj.read_config(a.root)
    for c in (b, a):                                                       # beta first: it is not the holder
        pjs[c.me].run(c, rj.read_config(c.root), dt.datetime(2026, 11, 4, 14, 0, 0), frozenset(), False)
    assert len(boards["alpha"].laid) == 1 and boards["beta"].laid == {}
    for c in (b, a):
        pjs[c.me].run(c, rj.read_config(c.root), dt.datetime(2026, 11, 4, 14, 5, 0), frozenset(), False)
    assert len(boards["alpha"].laid) == 1 and boards["beta"].laid == {}
    assert config is not None


# -- no [board]: nothing runs --------------------------------------------------------------------------------------

def test_with_no_board_table_nothing_runs(world, monkeypatch):
    origin, a, _ = world
    (a.root / "orkcraft.toml").write_text('[journal]\nremote = "origin"\n')
    seed_board(a.state)

    def boom(*args, **kw):
        raise AssertionError("something of the Board's branch ran")
    monkeypatch.setattr(bl, "take", boom)
    monkeypatch.setattr(bl, "renew", boom)
    monkeypatch.setattr(bl, "give_back", boom)
    monkeypatch.setattr(bb, "pack", boom)
    monkeypatch.setattr(threading.Thread, "start", boom)
    a.sync.tick()
    a.tick(T0, 0)
    a.sync.close(T0)
    assert a.sync._states == {} or not a.sync.holds(a)
    assert a.ideas.board_held == "" and a.sync.status(a) == {}
    assert subprocess.run(["git", "rev-parse", "--verify", "-q", "refs/orkboard/board"], cwd=a.root, capture_output=True).returncode != 0
    assert "board_taken" not in a.events() and not (a.state / bl.SYNC_FILE).exists()

