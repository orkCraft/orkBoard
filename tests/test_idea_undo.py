"""Spec 171 D (`core/idea_undo.py`, `gui/ideas_mats.py`): one Undo in the history, the sealed kinds."""
from __future__ import annotations

import sys

import pytest

from orkboard.core import bus, idea_undo
from orkboard.gui.board_host import CommandError as IdeasError
from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, ideas

PAGE = "---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nphase: talk\nschema: 3\n---\n# Goal\n\n## Gist\nA goal.\n"


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


def shot(h):
    return idea_undo.snapshot(h.ideas.root(), h.ideas.state_dir, "goal")


def test_a_drop_is_undone_byte_for_byte(host):
    before = shot(host)
    host.command("ideas.drop", {"slug": "goal", "from": "hand"})
    assert ideas.idea_page(host.ideas.root(), "goal") is None
    host.command("ideas.take_back", {"slug": "goal"})
    assert shot(host) == before
    with pytest.raises(IdeasError, match="Nothing to undo"):
        host.command("ideas.undo", {"idea": "goal"})


def test_a_hold_is_undone_byte_for_byte(host):
    before = shot(host)
    host.command("ideas.queue", {"slug": "goal", "queue": "hold", "from": "mat"})
    assert shot(host) != before
    host.command("ideas.undo", {"idea": "goal"})
    assert shot(host) == before


def test_a_question_s_way_is_undone_byte_for_byte(host):
    before = shot(host)
    more = before["page"] + "\n- Answered: yes\n"
    (host.ideas.root() / ideas.IDEAS / "goal.md").write_text(more, encoding="utf-8")
    idea_undo.keep(host.ideas.state_dir, "goal", "answer", before, shot(host))
    host.command("ideas.undo", {"idea": "goal"})
    assert shot(host) == before


def test_a_page_changed_since_is_refused_and_nothing_changes(host):
    host.command("ideas.queue", {"slug": "goal", "queue": "hold"})
    ideas.save_state(host.ideas.state_dir, "goal", error="a pass failed")
    after = shot(host)
    with pytest.raises(IdeasError, match="It changed since: nothing undone"):
        host.command("ideas.undo", {"idea": "goal"})
    assert shot(host) == after


def test_take_back_is_a_drop_s_undo_only(host):
    host.command("ideas.queue", {"slug": "goal", "queue": "hold"})
    with pytest.raises(IdeasError):
        host.command("ideas.take_back", {"slug": "goal"})


def test_every_kind_is_one_press_with_its_reverse_or_sealed():
    assert not set(idea_undo.ONE_PRESS) & set(idea_undo.SEALED)
    assert set(idea_undo.SEALED) == {"merge_main", "send_branch", "ship_release", "paid_pass"}
    for kind in {*idea_undo.ONE_PRESS, *idea_undo.SEALED}:
        assert idea_undo.way(kind) in ("press", "sealed")
    assert all(idea_undo.ONE_PRESS.values())                         # a reverse for each
    with pytest.raises(KeyError):
        idea_undo.way("nothing")
    with pytest.raises(KeyError):
        idea_undo.keep(None, "goal", "merge_main", {}, {"a": 1})


def test_a_sealed_kind_moves_only_on_its_seal(host):
    for name in ("ideas.to_main", "ideas.goal_to_dev", "ideas.release_out"):
        with pytest.raises(IdeasError, match="only on its seal"):
            host.command(name, {"slug": "goal"})


def test_the_moves_are_logged_and_published(host):
    seen = []
    host.ideas.host.bus.subscribe(bus.ANY, lambda e: seen.append(e.topic) if e.topic.startswith("move.") else None)
    host.command("ideas.queue", {"slug": "goal", "queue": "hold", "from": "hand"})
    host.command("ideas.undo", {"idea": "goal"})
    assert seen == ["move.played", "move.undone"]
    rows = event_log.read(host.repo_root)
    played = [r for r in rows if r["event"] == "move_played"]
    assert played and played[0]["kind"] == "hold" and played[0]["from"] == "hand" and played[0]["idea"] == "goal"
    assert any(r["event"] == "move_undone" for r in rows)
