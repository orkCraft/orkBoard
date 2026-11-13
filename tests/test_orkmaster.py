"""Spec 70 A (docs/specs/70-orkmaster-and-the-project.md §1, Tests → A): the Orkmaster's deal of the parties, a goal's party by its type and the
parties' teams, `project` in `ideas.map`, `@project` in `ideas.shown`. Code, no model."""
from __future__ import annotations


import pytest

from orkboard.realm import ideas, orkmaster, party_recipes
from tests.test_idea_route import events, flag, goal, host, party, wait_party  # noqa: F401  (`host`: the fixture of spec 68's route tests)

CRAFTS = list(party_recipes.CRAFTS)


@pytest.fixture
def bare(fake_repo):
    """A project with no party but General: the Orkmaster's first deal."""
    from orkboard.gui.board_host import Orkboard
    h = Orkboard(fake_repo)
    h.root, h.state = h.ideas.root(), h.ideas.state_dir
    return h


def rows(deal):
    return [(r["id"], r["why"], r["n"]) for r in deal]


def test_a_project_with_no_party_is_dealt_every_crafts_party_and_release_is_not_first_without_flags(bare):
    got = orkmaster.deal(bare.root, bare.state)
    assert [r["id"] for r in got] == list(party_recipes.CRAFTS) == CRAFTS and len(got) == 9      # one craft a party: no mixed preset, no Ideation (spec 99 §1.1)
    assert all(r["why"] == "" and r["n"] == 0 for r in got)


def test_flags_and_no_release_party_deal_release_first_with_their_count(host):
    h = host
    for n, party_slug in enumerate((h.app, h.app, h.web)):
        flag(h, goal(h, party_slug, f"Goal {n}"))
    flag(h, goal(h, h.talk, "A pitch's flag"))                                         # Ideation's flags are left out
    got = orkmaster.deal(h.root, h.state)
    assert rows(got)[:2] == [("release", "flags_wait", 3), ("product", "", 0)]
    assert sorted(r["id"] for r in got) == sorted(CRAFTS)                              # every craft once


def test_a_goal_type_goes_to_the_party_that_takes_it_whole_then_the_party_that_misses_someone_then_none(host):
    h = host
    got = orkmaster.party_for(h.state, h.root, "logo")
    assert got[0] == {"party": h.app, "name": "Mobile app", "fits": "whole", "missing": []}
    assert [r["fits"] for r in got] == ["whole", "none", "none"] and got[-1]["party"] == h.talk      # Ideation: none, always
    design = h.command("ideas.goal_save", {"title": "Design", "about": "Screens.", "craft": "design", "leader": "product-designer",
                                           "team": ["artist", "accessibility-reviewer"]})["slug"]
    wait_party(h, design)
    got = orkmaster.party_for(h.state, h.root, "logo")
    assert [(r["party"], r["fits"]) for r in got] == [(h.app, "whole"), (design, "whole"), (h.web, "none"), (h.talk, "none")]
    got = orkmaster.party_for(h.state, h.root, "screen")                                 # the designer designs, nobody there builds the kit
    by = {r["party"]: r for r in got}
    assert by[design]["fits"] == "missing" and by[design]["missing"] == [{"agent": "ui-kit", "name": "Design system designer"}]
    assert [r["fits"] for r in got] == sorted((r["fits"] for r in got), key=("whole", "missing", "none").index) and got[-1]["party"] == h.talk
    assert h.command("ideas.party_for", {"type": "screen"}) == {"parties": got, "suggested": next(r["party"] for r in got if r["fits"] != "none")}


def test_the_map_carries_the_project_counted_from_the_flags_it_read(host):
    h = host
    got = h.command("ideas.map", {})["project"]
    assert got["orkmaster"] == orkmaster.ORKMASTER and got["kind"]["id"] == "code"                  # (the project's kind, spec 75 §4.3)
    assert [r["id"] for r in got["deal"]][:5] == ["product", "design", "tech", "release", "run"]      # (the kind's proposals first, one craft a party; the website party the project has is Marketing's: last)
    flag(h, goal(h, h.app, "One"))
    flag(h, goal(h, h.web, "Two"))
    got = h.command("ideas.map", {})["project"]
    assert ("release", "flags_wait", 2) in rows(got["deal"]) and [r["id"] for r in got["deal"]][:3] == ["product", "design", "tech"]
    assert got["deal"] == orkmaster.deal_first(orkmaster.deal(h.root, h.state), ideas.tracks(h.root, make=False), "code", {})     # as the realm counts it
    assert h.command("ideas.map", {"goal": h.app})["project"]["deal"] == got["deal"]    # the project's, whatever party the Map is of

