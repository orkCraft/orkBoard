"""Goal 171 L2: the hand's one-press table is closed. Every command of `ONE_PRESS_BY` is played through its command (`from: "hand"`) with every model entry made to fail: none reaches a model."""
from __future__ import annotations

import sys

import pytest

from orkboard.core import idea_undo
from orkboard.gui import ideas_mats
from orkboard.gui.board_host import Orkboard
from orkboard.realm import harnesses, ideas

PAGE = ("---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nphase: talk\nasks: person\nschema: 3\n---\n# Goal\n\n## Gist\nA goal.\n\n"
        "## Open questions\n- Which store first? (**App Store** / Google Play) — most users\n")
PLAYED = {"ideas.drop": {"slug": "goal"}, "ideas.queue": {"slug": "goal", "queue": "hold"}, "ideas.answer_way": {"slug": "goal", "answers": ["Google Play"]}}
ENTRIES = ("ask", "call", "work_call", "_claude", "_claude_work", "board_ask", "read_now", "draft", "answer", "read_goal", "talk_answer")


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    root = h.ideas.root()
    ideas.add_track(root, "Tech")
    (root / ideas.IDEAS).mkdir(parents=True, exist_ok=True)
    (root / ideas.IDEAS / "goal.md").write_text(PAGE, encoding="utf-8")
    ideas.save_state(h.ideas.state_dir, "goal", state="raw")
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_every_one_press_command_is_played_here(host):
    assert set(PLAYED) == set(ideas_mats.ONE_PRESS_BY)               # a new one-press command must be added here, with its arguments


@pytest.mark.parametrize("name", sorted(ideas_mats.ONE_PRESS_BY))
def test_a_one_press_command_runs_no_model(host, monkeypatch, name):
    reached: list[str] = []

    def fail(entry):
        def boom(*a, **k):
            reached.append(entry)
            raise AssertionError(f"a model was reached through {entry}")
        return boom
    for entry in ENTRIES:
        if hasattr(host.ideas.keeper, entry):
            monkeypatch.setattr(host.ideas.keeper, entry, fail(f"keeper.{entry}"))
    monkeypatch.setattr(harnesses.Harness, "call", fail("Harness.call"))
    before = idea_undo.snapshot(host.ideas.root(), host.ideas.state_dir, "goal")
    host.command(name, {**PLAYED[name], "from": "hand"})
    assert reached == [] and not host.ideas.keeper.busy("goal")
    assert idea_undo.read(host.ideas.state_dir, "goal")["before"] == before          # its Undo is kept


def test_the_two_tables_leave_no_kind_between(host):
    for name in ideas_mats.ONE_PRESS_BY:
        assert idea_undo.way(ideas_mats.move_kind(name, PLAYED[name])) == "press"
    assert ideas_mats.move_kind("ideas.answer", {"slug": "goal", "from": "hand"}) == ""      # the keeper's pass is no hand's move
