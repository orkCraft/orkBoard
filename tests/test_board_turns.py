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


def test_a_question_is_a_turn_with_its_ways_and_an_answered_one_is_left_out():
    (turn,) = board_turns.turns(parsed(asking=ASKING), PARTIES)
    assert [q["ask"] for q in turn["questions"]] == ["Which store?"]
    assert turn["questions"][0]["ways"] == ["A", "B"]


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


def test_a_card_the_record_holds_is_a_question_until_the_page_answers_it():
    card = {"q": "Keep the timer?", "choices": ["Keep it", "Move it"], "pick": 0}
    bare = idea_page.parse(page("talk", "asks: person\n", "## Open questions\n"))
    got = board_turns.turn_of("g", bare, PARTIES, "", [card])
    assert got["kind"] == "asks" and got["questions"] == [{"ask": "Keep the timer?", "ways": ["Keep it", "Move it"]}]
    answered = idea_page.parse(page("talk", "asks: person\n", "## Open questions\n- Keep the timer?\n  - Answered: Move it (the person, 2026-11-12)\n"))
    assert board_turns.turn_of("g", answered, PARTIES, "", [card]) is None          # the record still holds it; the page has its answer
    assert board_turns.turn_of("g", bare, PARTIES, "") is None                      # no card, no question: no turn that has no way
