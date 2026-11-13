"""Spec 91 F (docs/specs/91-the-owners-list.md §8): the kind of a goal guessed from the line as it is typed — by words, no model, nothing written. `core/idea_kind.py` `guess` / `ranked` (the words of each
goal type of realm/goal_types.py) and `ideas.kind_for {text, party?}` (the kinds a party is offered, the guessed one first)."""
from __future__ import annotations

import pytest

from orkboard.core import idea_kind
from orkboard.gui.board_host import CommandError
from orkboard.realm import goal_types
from tests.test_idea_route import host  # noqa: F401  (the fixture of spec 68's route tests: a mobile app party, a website party, Ideation)

CATALOG = [t.id for t in goal_types.CATALOG]


@pytest.mark.parametrize("line, kind", [
    ("Fix the crash when the app opens", "bug"),
    ("Tidy up and refactor the sign-in code", "tidy"),
    ("A new logo for the shop", "logo"),
    ("A pixel icon for the app", "icon"),
    ("Add dark mode", "feature"),
    ("Write a launch post for LinkedIn", "post"),
    ("Balance the economy: the second level is too hard", "balance"),
    ("A tagline for the website", "tagline"),
    ("Keywords and screenshots for the App Store", "store"),
])
def test_a_line_says_the_kind_whose_words_it_says_most(line, kind):
    assert idea_kind.guess(line, CATALOG) == kind


def test_ranked_puts_the_guessed_kind_first_and_keeps_the_rest_as_they_came():
    assert idea_kind.ranked("Fix the crash", ["feature", "tidy", "bug"]) == ["bug", "feature", "tidy"]
    assert idea_kind.ranked("hello", ["feature", "tidy"]) == ["feature", "tidy"]
    assert idea_kind.ranked("Fix the crash", ["nope", "bug"]) == ["bug"]                     # a kind the catalog lacks is left out


def test_kind_for_says_the_kind_over_every_kind_and_over_a_partys(host):  # noqa: F811
    h = host
    got = h.command("ideas.kind_for", {"text": "Fix the crash when the app opens"})
    assert got["type"] == "bug" and got["types"][0] == "bug" and sorted(got["types"]) == sorted(CATALOG)
    own = h.command("ideas.kind_for", {"text": "Fix the crash when the app opens", "party": h.app})
    offered = [t.id for t, _missing in goal_types.offered(h.state, h.root, h.app)]
    assert own["type"] == "bug" and own["types"][0] == "bug" and sorted(own["types"]) == sorted(offered)


def test_ideation_is_offered_no_kind_and_a_party_the_project_lacks_is_refused(host):  # noqa: F811
    h = host
    assert h.command("ideas.kind_for", {"text": "Fix the crash", "party": h.talk}) == {"type": "", "types": []}      # a pitch has no kind
    with pytest.raises(CommandError, match="No such party"):
        h.command("ideas.kind_for", {"text": "Fix the crash", "party": "nope"})
    with pytest.raises(CommandError, match="text is not text"):
        h.command("ideas.kind_for", {"text": 3})


