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


def test_take_back_is_a_drop_s_undo_only(host):
    host.command("ideas.queue", {"slug": "goal", "queue": "hold"})
    with pytest.raises(IdeasError):
        host.command("ideas.take_back", {"slug": "goal"})


def test_every_kind_is_one_press_with_its_reverse_or_sealed():
    assert not set(idea_undo.ONE_PRESS) & set(idea_undo.SEALED)
    assert set(idea_undo.SEALED) == {"merge_main", "send_branch", "ship_release", "paid_pass", "start_work"}
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


def test_start_is_sealed_where_a_card_plays_it_and_as_it_was_for_the_older_faces(host):
    """Goal 171 K: a card of the hand or a mat (`from: hand|mat`) starts the work only on its seal; a press with no `from` is the older faces' and goes by its own checks."""
    for origin in ("hand", "mat"):
        with pytest.raises(IdeasError, match="only on its seal"):
            host.command("ideas.start", {"slug": "goal", "from": origin})
    with pytest.raises(IdeasError, match="no plan yet"):
        host.command("ideas.start", {"slug": "goal", "from": "mat", "sealed": True})      # sealed: it reaches the host's own checks
    with pytest.raises(IdeasError, match="no plan yet"):
        host.command("ideas.start", {"slug": "goal"})


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


def test_every_page_call_of_a_sealed_command_sends_its_seal():
    """The page's own presses of a sealed move (the portal, the merge button) pass `sealed: true`; js/mock/ answers, it never calls."""
    import re
    from pathlib import Path
    from orkboard.gui.ideas_mats import SEALED_BY
    static, found = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static", 0
    for path in [*static.rglob("*.js"), *static.rglob("*.html")]:
        if "mock" in path.relative_to(static).parts or "vendor" in path.relative_to(static).parts:
            continue
        for m in re.finditer(r"""["'`](%s)["'`]\s*,\s*\{[^}]*\}?""" % "|".join(map(re.escape, SEALED_BY)), path.read_text(encoding="utf-8")):
            found += 1
            assert "sealed: true" in m.group(0), f"{path.name}: {m.group(1)} sends no seal"
    assert found >= 8
