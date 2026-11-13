"""Spec 171 D (`core/idea_undo.py`, `gui/ideas_mats.py`): one Undo in the history, the sealed kinds."""
from __future__ import annotations

import sys

import pytest

from orkboard.core import bus, idea_undo
from orkboard.gui.board_host import CommandError as IdeasError
from orkboard.gui.board_host import Orkboard
from orkboard.realm import ideas

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


def test_a_question_s_way_played_from_the_hand_is_undone_byte_for_byte(host):
    page = PAGE.replace("phase: talk\n", "phase: talk\nasks: person\n") + "\n## Open questions\n- Which store first? (**App Store** / Google Play) — most users\n- Name it? (**Yes** / No)\n"
    (host.ideas.root() / ideas.IDEAS / "goal.md").write_text(page, encoding="utf-8")
    before = shot(host)
    host.command("ideas.answer_way", {"slug": "goal", "answers": ["Google Play", "Yes"], "from": "hand"})
    now = shot(host)["page"]
    assert "Answered: Google Play" in now and "Answered: Yes" in now          # written under its question; no pass began (tests/test_ideas_mats_closed.py)
    assert idea_undo.read(host.ideas.state_dir, "goal")["kind"] == "answer"
    host.command("ideas.undo", {"idea": "goal"})
    assert shot(host) == before


def test_a_page_changed_since_is_refused_and_nothing_changes(host):
    host.command("ideas.queue", {"slug": "goal", "queue": "hold"})
    ideas.save_state(host.ideas.state_dir, "goal", error="a pass failed")
    after = shot(host)
    with pytest.raises(IdeasError, match="It changed since: nothing undone"):
        host.command("ideas.undo", {"idea": "goal"})
    assert shot(host) == after


def test_every_kind_is_one_press_with_its_reverse_or_sealed():
    assert not set(idea_undo.ONE_PRESS) & set(idea_undo.SEALED)
    assert set(idea_undo.SEALED) == {"merge_main", "send_branch", "ship_release", "paid_pass", "start_work", "fix_stage"}
    assert set(idea_undo.ONE_PRESS) == {"drop", "hold", "answer", "fix_goal", "new_wins"}          # I: New wins, a battle's one press, its decision back; goal "The battle and the gate" G, H: Fix it after dev one press, its stage again sealed
    for kind in {*idea_undo.ONE_PRESS, *idea_undo.SEALED}:
        assert idea_undo.way(kind) in ("press", "sealed")
    assert all(idea_undo.ONE_PRESS.values())                         # a reverse for each
    with pytest.raises(KeyError):
        idea_undo.way("nothing")
    with pytest.raises(KeyError):
        idea_undo.keep(None, "goal", "merge_main", {}, {"a": 1})


def _lay(h, slug: str) -> dict:
    """A goal laid by a move on another (Fix it after dev): its page and state, none before."""
    (h.ideas.root() / ideas.IDEAS / f"{slug}.md").write_text(PAGE.replace("# Goal", "# Fix: a test"), encoding="utf-8")
    ideas.save_state(h.ideas.state_dir, slug, state="routed")
    return idea_undo.snapshot(h.ideas.root(), h.ideas.state_dir, slug)


def test_a_goal_a_move_laid_is_kept_on_the_goal_it_was_played_on_and_removed_by_its_undo(host):
    """Goal "The battle and the gate" G: `fix_goal` keeps the Fix goal laid (its page and state, none before) on the done goal's record; its reverse removes them."""
    goal = shot(host)
    seen = []
    assert idea_undo.keep(host.ideas.state_dir, "goal", "fix_goal", {"page": None, "state": None}, _lay(host, "fix-a"), lambda topic, **f: seen.append((topic, f)), "mat", laid="fix-a")
    assert seen == [(bus.MOVE_PLAYED, {"idea": "goal", "kind": "fix_goal", "origin": "mat"})]          # the move is the done goal's: it was played on its gate
    assert idea_undo.read(host.ideas.state_dir, "goal")["laid"] == "fix-a" and idea_undo.read(host.ideas.state_dir, "fix-a") is None
    host.command("ideas.undo", {"idea": "goal"})
    assert ideas.idea_page(host.ideas.root(), "fix-a") is None and not ideas.state_folder(host.ideas.state_dir, "fix-a").exists()
    assert shot(host) == goal                                                       # the goal it was played on, as it was

