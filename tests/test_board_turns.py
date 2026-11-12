"""Spec 171 B (`realm/board_turns.py`, `gui/ideas_mats.py`): the moves that wait, read from the Board's pages. A fixture Board of four goals; no model, no write."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import board_turns, idea_page, ideas

PARTIES = [{"slug": "product", "title": "Product"}, {"slug": "tech", "title": "Tech"}]
TALK = "### Talk\n- verdict: go\n- stance: fine"
SECTION = "### Why\nBecause.\n\n### Done when\n- [test] it works"


def page(phase: str, extra: str = "", body: str = "", route: str = "product, tech") -> str:
    return f"---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nphase: {phase}\nroute: {route}\n{extra}schema: 3\n---\n# Goal {phase}\n\n## Gist\nA goal.\n\n{body}"


ASKING = page("talk", "asks: person\n", "## Open questions\n- Which store? (**A** / B) — because\n- Old one?\n  - Answered: yes\n")
TALKED = page("talk", body=f"## Product\n{TALK}\n\n## Tech\n{TALK}\n")
SPEC = page("spec", body=f"## Product\n{SECTION}\n\n## Tech\n{SECTION}\n")
WORK = page("work", body=f"## Product\n{SECTION}\n\n## Tech\n{SECTION}\n")
HALF_TALK = page("talk", body=f"## Product\n{TALK}\n")
HALF_SPEC = page("spec", body=f"## Product\n{SECTION}\n")
HELD = page("talk", "queue: hold\nasks: person\n", "## Open questions\n- Which?\n")


def parsed(**texts: str) -> dict:
    return {k: idea_page.parse(v) for k, v in texts.items()}


def test_each_goal_that_waits_has_one_turn_and_a_goal_at_work_none():
    got = board_turns.turns(parsed(asking=ASKING, talked=TALKED, spec=SPEC, work=WORK), PARTIES, {"asking": "2026-11-12T10:00:00"})
    assert [(t["goal"], t["kind"]) for t in got] == [("asking", "asks"), ("talked", "talk"), ("spec", "spec")]
    assert got[0]["at"] == "2026-11-12T10:00:00" and got[1]["at"] == ""


def test_a_question_is_a_turn_with_its_ways_and_an_answered_one_is_left_out():
    (turn,) = board_turns.turns(parsed(asking=ASKING), PARTIES)
    assert [q["ask"] for q in turn["questions"]] == ["Which store?"]
    assert turn["questions"][0]["ways"] == ["A", "B"]


def test_a_goal_waits_only_when_every_party_of_its_route_has_spoken_or_written():
    assert board_turns.turns(parsed(a=HALF_TALK, b=HALF_SPEC, c=page("talk", route=""), d=page("new")), PARTIES) == []


def test_a_goal_on_hold_or_done_has_no_turn():
    assert board_turns.turns(parsed(held=HELD, done=page("done", "asks: person\n", "## Open questions\n- Which?\n")), PARTIES) == []


def _sums(root: Path) -> dict:
    return {str(p): hashlib.sha1(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file() and ".git" not in p.parts}


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_ideas_turns_on_a_fixture_board_runs_no_model_and_writes_no_file(host):
    root = host.ideas.root()
    ideas.add_track(root, "Product")
    ideas.add_track(root, "Tech")
    folder = root / ideas.IDEAS
    folder.mkdir(parents=True, exist_ok=True)
    for slug, text in {"asking": ASKING, "talked": TALKED, "spec": SPEC, "work": WORK}.items():
        (folder / f"{slug}.md").write_text(text, encoding="utf-8")

    def no_model(*a, **k):
        raise AssertionError("a model was called")

    host.ideas.keeper.call = no_model
    before = _sums(root), _sums(host.ideas.state_dir)
    assert "ideas.turns" in host.commands
    got = host.command("ideas.turns", {})["turns"]
    assert sorted((t["goal"], t["kind"]) for t in got) == [("asking", "asks"), ("spec", "spec"), ("talked", "talk")]
    assert (_sums(root), _sums(host.ideas.state_dir)) == before


def test_the_module_is_pure():
    text = Path(board_turns.__file__).read_text(encoding="utf-8")
    assert "subprocess" not in text and "write_text" not in text and "open(" not in text
